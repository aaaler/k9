#!/usr/bin/env python
import socket
import serial
import threading
import sys
import struct
import time
import cPickle
import os
import subprocess
import re
import logging
import logging.handlers
from gpio.pwmpin import pwmpin
from gpio.pin import pin
from gpio.servo import servo

class K9dApp:
    #Compile RE for iwconfig ouput parsing
    brre = re.compile (r"Bit Rate=([\d.]+ \S+)",re.M)
    lqre = re.compile (r"Link Quality=(\d+/\d+)  Signal level=(-\d+ dBm)",re.M)

    def __init__ (self):
        #Kind a config here
        #arduino tracks bridge pinout
        self.p1PWM=str(6)
        self.p1FWD=str(7)
        self.p1REV=str(8)
        self.p2PWM=str(5)
        self.p2FWD=str(4)
        self.p2REV=str(3)
        #ip
        self.addr = "192.168.0.22"
        self.UDP_IP = "0.0.0.0"
        self.UDP_PORT = 9999
        #sonar
        self.sonaron = True
        self.sonarfailsafe = 0.
        #mjpg_streamer related
        self.videomode = 'OFF'
        #track calibration should be here
        self.cal_track_min = 180
       
        #init
        self.faststate = {}
        self.faststate["proxalert"] = False
        self.tracktimeout = time.time()
        self.trackmode = ""
        self.sonardist = 0
        self.sonarfailsafe_active = False
        self.festivalup = False
        self.log_init()
        #==============UDP INIT====================
        self.log.info ("spinal interface daemon for K-9 starting");
        self.servsock = socket.socket(socket.AF_INET, # Internet
                              socket.SOCK_DGRAM) # UDP
        self.servsock.bind((self.UDP_IP, self.UDP_PORT))
        self.respsock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        #============SERIAL INIT===================
        try:
          self.spinal = serial.Serial('/dev/ttyS2', 115200, timeout=0.5)
          self.spinal_enabled = True
        except:
          self.spinal_enabled = False
          self.log.info("Could not open port for arduino -- connection disabled ")                
        
        try:
          self.sonar = serial.Serial('/dev/ttyS1', 9600, timeout=0.5)
          self.sonar_enabled = True
        except:
          self.log.error("Could not open port for sonar -- sonar disabled")
          self.sonar_enabled = False
        
        #===========THREADING INIT=================
        
        self.faststate['S1']=-1
        self.faststate['S2']=-1
        self.faststate['A1']=-1
        self.faststate['A2']=-1
        self.faststate['A3']=-1

        if self.spinal_enabled:
            self.tSerialRead = threading.Thread(target=self.sreader)
            self.tSerialRead.setDaemon (1)
            self.tSerialRead.start()
        
        self.tTrackWatchdog = threading.Thread(target=self.cmdtimeout)
        self.tTrackWatchdog.setDaemon (1)
        self.tTrackWatchdog.start()
        
        self.tStateUpload = threading.Thread(target=self.tstateup)
        self.tStateUpload.setDaemon (1)
        self.tStateUpload.start()
    
        if self.sonar_enabled:        
            self.tSonar = threading.Thread(target=self.tsonar)
            self.tSonar.setDaemon (1)
            self.tSonar.start()
            
        
        self.log.info ("ready to play");

    def log_init(self):
         
        if hasattr(self, 'log'):
            self.log.removeHandler(self.stdoutloghandler)
            self.log.removeHandler(self.udploghandler)
	else:
            self.log = logging.getLogger('k9d')
        self.stdoutloghandler = logging.StreamHandler(sys.stdout)
        self.stdoutloghandler.setFormatter(logging.Formatter("%(asctime)s [%(name)s#%(levelname)s]: %(message)s"))
        self.stdoutloghandler.setLevel(logging.DEBUG)
        self.udploghandler = logging.handlers.DatagramHandler(self.addr, self.UDP_PORT)
        self.udploghandler.setFormatter(logging.Formatter("%(asctime)s [%(name)s#%(levelname)s]: %(message)s"))
        self.udploghandler.setLevel(logging.DEBUG)

        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.stdoutloghandler)
        self.log.addHandler(self.udploghandler)
 

    def mainloop (self):          
        while True:
            data,(addr,self.port) = self.servsock.recvfrom(1024) # buffer size is 1024 bytes   
            if addr != self.addr:
              self.log.warn ("New client ip: {}".format(addr))
              self.addr = addr
              self.log_init()
            out = "{}>{} &".format(str(self.addr),data)
  
            request = data.split(' ');
            CMD = request.pop(0) 
            CMD = CMD.strip("\n")
            if CMD == "STOP":
              self.trackstop()
              out += "OK"
            elif CMD == "EXEC":
              self.spinal_write (' '.join(request))
              out += "OK"
            elif CMD == "TRACKS":
              out += self.tracks(request[0],request[1]);
            elif CMD == "SERVO":
              self.servo (request[0],request[1]);
              out += "OK"
            elif CMD == "SON":
              if request[0] == 'Failsafe':
                self.sonaron = True
                if request[1] == 'off': self.sonarfailsafe = 0
                else: self.sonarfailsafe = float(request[1])
              elif request[0] == 'Sonar' and request[1] == 'off' :
                self.sonaron = False
                self.sonarfailsafe = 0
              out += "OK"
            elif CMD == "CAM":
              if request[0] == 'RES':
                if hasattr(self, 'pmjpg'):
                  if self.pmjpg.poll() == None:
                    self.pmjpg.kill()
                    self.videomode = "OFF"
                    t = threading.Timer(2.0,self.run_mjpg,[request[1]])
                    t.start() 
                    out += " deffered mjpg run"
                  else: 
                    out += self.run_mjpg(request[1])
                else: 
                  out += self.run_mjpg(request[1])
              elif request[0] == 'OFF':
                if hasattr(self, 'pmjpg') and self.pmjpg.poll() == None:
                    self.pmjpg.kill()
                self.videomode = "OFF"
                out += "OK"
  
              elif request[0] == 'ZOOM' and request[1] == 'OFF' :
                status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=1"])  
                out += "OK"
  
              elif request[0] == 'ZOOM' and request[1] == 'ON' :
                status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=5"])
                out += "OK"
            elif CMD == "FESTIVAL":
                if request[0] == 'ON':
                    if hasattr(self, 'pfestival'):
                        if self.pfestival.poll() == None:
                            self.pfestival.kill()
                            self.festivalup = False
                            t = threading.Timer(2.0,self.run_festival)
                            t.start() 
                            out += " deffered pfestival run"
                        else: 
                            out += self.run_festival()
                    else: 
                        out += self.run_festival()
                elif request[0] == 'OFF':
                    if hasattr(self, 'pfestival') and self.pfestival.poll() == None:
                        self.pfestival.kill()
                    self.festivalup = False

            elif CMD == "SAY":
                tts = cPickle.loads(data[4:])
                if self.festivalup:
                    self.pfestival.stdin.write ("(SayText \"{}\")".format( tts.encode("utf-8")))
                    self.pfestival.stdin.flush()
                    self.log.info ("Pronouncing '{}'".format(tts.encode("utf-8")))
                else:
                    self.log.err ("Can't SAY, festival down")
  
            else: 
              self.log.warn ("unknown command " + CMD + "")
              continue
           
            self.log.debug (out)
        #  send ("command done:" + out, addr);

            
    def send (self,body,ip) :
      #  return respsock.sendto(bytes(body, 'UTF-8'), ("192.168.0.22", UDP_PORT))
      return self.respsock.sendto(body, (self.addr, self.UDP_PORT))


    def spinal_write (self,data):
        if self.spinal_enabled:
            debugmsg = "UART< {}".format(data)
            self.log.debug(debugmsg)
            return self.spinal.write(data)
        else:
            self.log.debug ("Discard spinal msg: {}".format(data))
    
    def from_spinal (self,pkt):
        if pkt == "0_o\n" :
          #SPINAL BOOTED UP -- NEED INIT
          pass

        if pkt != "OK\r\n":
          debugmsg = "UART<" + pkt
          self.send (debugmsg,self.addr)
    #hardcore hex debug output
    #    print ":".join("{:02x}".format(ord(c)) for c in pkt)

    
    @staticmethod
    def getbit(byteval,idx):
        return ((int(byteval)&(1<<int(idx)))!=0);
    
    def parsestate(self, stat):
        statusdebug = "";
        b = 0
        for i in range (2,11):
          if i in [5,6]: 
            self.faststate['D'+str(i)]='N'
            continue
          bit = self.getbit(ord(stat[0]),b)
          b +=1
          self.faststate['D'+str(i)]=bit
          statusdebug += (str(i) + ":" + str(int(bit)) + " ")
        statusdebug += ("s1:" + str(ord(stat[1])) + " ")
        self.faststate['S1']=ord(stat[1])
        statusdebug += ("s2:" + str(ord(stat[2])) + " ") 
        self.faststate['S2']=ord(stat[2])
        statusdebug += ("a1:" + str(ord(stat[4]) + (ord(stat[3])<<8)) + " ")
        self.faststate['A1']=str(ord(stat[4]) + (ord(stat[3])<<8))
        statusdebug += ("a2:" + str(ord(stat[6]) + (ord(stat[5])<<8)) + " ")
        self.faststate['A2']=str(ord(stat[6]) + (ord(stat[5])<<8))
        statusdebug += ("a3:" + str(ord(stat[8]) + (ord(stat[7])<<8)) + "")
        self.faststate['A3']=str(ord(stat[8]) + (ord(stat[7])<<8))
#        self.log.debug (statusdebug);
        self.stateupload()
        

    def tstateup (self):
        while 1:
          if os.path.exists("/sys/class/power_supply/battery/capacity"):
            self.faststate['cpu_bcap'] = int(open("/sys/class/power_supply/battery/capacity", "r").read().strip())
          if os.path.exists("/sys/class/power_supply/battery/current_now"):
            self.faststate['cpu_bcur'] = int(open("/sys/class/power_supply/battery/current_now", "r").read().strip())/1000
          if os.path.exists("/sys/class/power_supply/ac/current_now"):
            self.faststate['cpu_accur'] = int(open("/sys/class/power_supply/ac/current_now", "r").read().strip())/1000
          if os.path.exists("/sys/class/power_supply/battery/status"):
            self.faststate['cpu_bstate'] = open("/sys/class/power_supply/battery/status", "r").read().strip()
          self.piwconfig = subprocess.Popen(["/sbin/iwconfig", "wlan0"], stdout=subprocess.PIPE)
          iwconfig_out, err = self.piwconfig.communicate()
          match = self.brre.search(iwconfig_out)
          if match: self.faststate['wifi_br'] = match.group(1)
          else: self.faststate['wifi_br'] = "n/a"
          match = self.lqre.search(iwconfig_out)
          if match:
            self.faststate['wifi_lq'] = match.group(1)
            self.faststate['wifi_sl'] = match.group(2)
          else:
            self.faststate['wifi_lq'] = "n/a"
            self.faststate['wifi_sl'] = "n/a"
          self.stateupload()
          time.sleep (1)

    def stateupload (self):
        self.send ("#"+cPickle.dumps (self.faststate),self.addr)
    
    def tsonar (self):
        while True:
          if self.sonaron:
            self.sonar.write("U")
    #      time.sleep(0.1)
            try:
              HighLen = ord(self.sonar.read(1));                   #High byte of distance
              LowLen  = ord(self.sonar.read(1));                   #Low byte of distance
              self.sonardist  = int(HighLen*256 + LowLen);             #Calculate the distance
    #        print ("SONAR H:"+ str( sonardist))
              self.faststate["Son"]=self.sonardist
              if float(self.sonardist)/1000 <= self.sonarfailsafe:
                if not self.sonarfailsafe_active:
                    self.sonarfailsafe_active = True
                    self.faststate["proxalert"] = True
                    self.log.info ("Sonar failsafe activated at distance {} meters".format(float(self.sonardist)/1000))
                if self.tracksy > 0: self.tracks (self.tracksx,0)
              else: 
                if self.sonarfailsafe_active:
                    self.log.info ("Sonar failsafe deactivated at distance {} meters".format(float(self.sonardist)/1000))
                    self.sonarfailsafe_active = False
                    self.faststate["proxalert"] = False
 
            except serial.SerialException:
              self.faststate["Son"]=65535
              self.log.info ("Sonar err")
              pass
          else:self.faststate["Son"]=65534
          time.sleep(.05)
          
    
    def sreader(self):
        """loop forever and copy serial->console"""
        sbuff="";
        while 1:
            data = self.spinal.read()
            sbuff += data;
            if data == "#":
              state = self.spinal.read(10)
              try:
                if state[9]== "#":
                  state = state[:-1]
                  sbuff = sbuff[:-1]
                  self.parsestate(state)
                else:
                  sbuff +=  state
              except IndexError: sbuff +=  state
            if data == "\n":
                self.from_spinal(sbuff)
                self.log.debug("UART> {}".format(sbuff[:-1]))
                sbuff=""
    
    def cmdtimeout(self):
        """stop tracks when command is timed out"""
        while 1:
          while self.trackmode != "":
            if self.tracktimeout < time.time():
              self.trackstop()
              self.log.info ("Timout alert STOP.")
          time.sleep(0.1)




    def tracks (self,X,Y) :
      fX = float(X);
      fY = float(Y);
      timeout = 100 #not impl.
      self.tracktimeout = time.time() + (int(timeout)/1000)
      if fY >= 0:
        #8 <LFWD> <LREV> <LPWM> <RFWD> <RREV> <RPWM>;
        self.trackl = fY + fX
        self.trackr = fY - fX
    #    out="8 %0d %0d %0d %0d %0d %0d;" % (1,0,abs(int(Y)),1,0,abs(int(Y)))
      elif fY < 0:
        self.trackl = fY + fX
        self.trackr = fY - fX
      if self.trackr > 1: self.trackr = 1
      if self.trackl > 1: self.trackl = 1
      if self.trackr < -1: self.trackr = -1
      if self.trackl < -1: self.trackl = -1
      if self.sonarfailsafe_active:
          if self.trackr > 0: self.trackr = 0
          if self.trackl > 0: self.trackl = 0
        
      out="8 %0d %0d %0d %0d %0d %0d;" % (self.trackl>0,self.trackl<0,abs(self.trackr)*(255-self.cal_track_min)+self.cal_track_min,self.trackr>0,self.trackr<0,abs(self.trackl)*(255-self.cal_track_min)+self.cal_track_min)
      self.spinal_write(out);
      self.faststate['trackr'] = self.trackr;
      self.faststate['trackl'] = self.trackl;
      self.tracksx = fX
      self.tracksy = fY
      return "OK"
    
 
    
    def trackstop (self) :
        self.spinal_write("2 "+self.p1PWM+" 0;")
        self.spinal_write("2 "+self/p2PWM+" 0;")
        self.trackmode = ""
    
    
    def servo (self,id,angle):
        self.spinal_write("4 "+str(id)+" "+str(angle)+";")
    
    def run_mjpg (self,params):
        out = ''
        (fpv_size,fpv_fps)=params.split('@')
        cmd = ("/root/K9/mjpg_streamer/mjpg_streamer", "-i", "/root/K9/mjpg_streamer/input_uvc.so --no_dynctrl -r {} -f {}".format(fpv_size,fpv_fps), "-o","/root/K9/mjpg_streamer/output_http.so -w /root/K9/mjpg_streamer/www")
        self.pmjpg = subprocess.Popen(cmd)
        if self.pmjpg.poll() == None:
          self.videomode = "{}@{}".format(fpv_size,fpv_fps)
          self.log.info ("Spawned mjpg_streamer with {}@{} PID: {}".format(fpv_size,fpv_fps,self.pmjpg.pid))
        else:
          self.log.error ("Failed to start mjpg_streamer with {}".format(self.videomode))
          self.videomode = "Failed"
        return "OK" 

    def run_festival (self):
        out = ''
        cmd = ("/usr/bin/festival", "--language", "russian")
        self.pfestival = subprocess.Popen(cmd,stdin=subprocess.PIPE)
        if self.pfestival.poll() == None:
          self.festivalup = True
          self.log.info ("Spawned festival with PID: {}".format(self.pfestival.pid))
        else:
          self.log.error ("Failed to start festival")
          self.festivalup = False
        return "OK" 
        

if __name__ == "__main__":
    app = K9dApp()
    app.mainloop()
        
    
    
    
    
    
