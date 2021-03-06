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
import psutil
import pprint

from gpio.pwmpin import pwmpin
from gpio.pin import pin
from gpio.servo import servo

from tracks import Tracks
from gsens import GSens

class K9dApp:
    #Compile RE for iwconfig ouput parsing
    brre = re.compile (r"Bit Rate=([\d.]+ \S+)",re.M)
    lqre = re.compile (r"Link Quality=(\d+/\d+)  Signal level=(-\d+ dBm)",re.M)

    def __init__ (self):
        #Kind a config here
        #arduino tracks bridge pinout
        self.tracks = Tracks (pin.port.PB5, pin.port.PB6, 28, pin.port.PB7, pin.port.PB10, 29, 20)
        #ip
        self.addr = "192.168.0.22"
        self.UDP_IP = "0.0.0.0"
        self.UDP_PORT = 9999
        #sonar
        self.sonaron = True
        self.sonarfailsafe = 0.
        #mjpg_streamer related
        self.videomode = 'OFF'
       
        #init
        self.faststate = {}
        self.faststate["proxalert"] = False
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

    def __del__ (self):
        self.log.info("Shutting down daemon")
        self.gsens.__del__()
        self.gsens = None

    def gsens_update (self):
        if hasattr(self.gsens,'yaw'):
            self.faststate['yaw'] = self.gsens.yaw
            self.faststate['pitch'] = self.gsens.pitch
            self.faststate['roll'] = self.gsens.roll
            self.faststate['ax'] = self.gsens.ax
            self.faststate['ay'] = self.gsens.ay
            self.faststate['az'] = self.gsens.az
            self.stateupload()

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
              self.tracks.neutral()
              self.faststate['trackr'] = self.tracks.trackr
              self.faststate['trackl'] = self.tracks.trackl
              self.stateupload()
              self.log.debug ("Tracks vector set to neutral")
            elif CMD == "SPINAL":
              emsg = ' '.join(request)
              self.log.info ("Sending user packet to spinal: {}".format(emsg))
              self.spinal_write (emsg)
            elif CMD == "PING":
              self.log.info ("PING {} got".format(request[0]))
              self.send ("PONG {} {}".format(time.time(),request[0]),self.addr)
            elif CMD == "TRACKS":
              self.tracks.vector (request[0],request[1]);
              self.log.debug ("Tracks vector set to {},{}".format(request[0],request[1]))
              self.faststate['trackr'] = self.tracks.trackr
              self.faststate['trackl'] = self.tracks.trackl
              self.stateupload()
            elif CMD == "SERVO":
              self.servo (request[0],request[1]);
            elif CMD == "SON":
              if request[0] == 'Failsafe':
                self.sonaron = True
                if request[1] == 'off': self.sonarfailsafe = 0
                else: self.sonarfailsafe = float(request[1])
              elif request[0] == 'Sonar' and request[1] == 'off' :
                self.sonaron = False
                self.sonarfailsafe = 0
            elif CMD == "CAM":
              if request[0] == 'RES':
                if hasattr(self, 'pmjpg'):
                  if self.pmjpg.poll() == None:
                    pid = self.pmjpg.pid
                    self.pmjpg.kill()
                    self.videomode = "OFF"
                    t = threading.Timer(2.0,self.run_mjpg,[request[1]])
                    t.start() 
                    self.log.info ("Killed mjpg with pid {} and deferred run with {}".format(pid,request[1]))
                  else: 
                    self.run_mjpg(request[1])
                else: 
                  self.run_mjpg(request[1])
              elif request[0] == 'OFF':
                if hasattr(self, 'pmjpg') and self.pmjpg.poll() == None:
                    self.pmjpg.kill()
                self.videomode = "OFF" 
                self.log.info ("Killed mjpg.")                
              elif request[0] == 'ZOOM' and request[1] == 'OFF' :
                status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=1"])  
                self.log.info ("Zoom OFF")
              elif request[0] == 'ZOOM' and request[1] == 'ON' :
                status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=5"])
                self.log.info ("Zoom ON")
            elif CMD == "FESTIVAL":
                if request[0] == 'ON':
                    if hasattr(self, 'pfestival'):
                        if self.pfestival.poll() == None:
                            pid = self.pfestival.pid
                            self.pfestival.kill()
                            self.festivalup = False
                            t = threading.Timer(2.0,self.run_festival)
                            t.start() 
                            self.log.info ("Killed festival with pid {} and deferred run".format(pid))
                        else: 
                            self.run_festival()
                    else: 
                        self.run_festival()
                elif request[0] == 'OFF':
                    if hasattr(self, 'pfestival') and self.pfestival.poll() == None:
                        self.pfestival.kill()
                    self.festivalup = False
                    self.log.info ("Killed festival")
            elif CMD == "SAY":
                tts = cPickle.loads(data[4:])
                if self.festivalup:
                    self.pfestival.stdin.write ("(SayText \"{}\")".format( tts.encode("utf-8")))
                    self.pfestival.stdin.flush()
                    self.log.info ("Pronouncing '{}'".format(tts.encode("utf-8")))
                else:
                    self.log.err ("Can't SAY, festival down")
            elif CMD == 'EVAL':
                ecmd = " ".join(request)
                try:
                    output = eval("pprint.pformat({})".format(ecmd))
                    self.log.info ("{} = {}".format(ecmd, output))
                except Exception, e:
                    self.log.error("eval \"{}\" raised {} Exception: {}".format(ecmd,type(e).__name__ ,e))

            elif CMD == "GSENSOR":
                if request[0] == 'ON':
                    self.gsens = GSens (0, self.gsens_update, self.log.error, self.log.info, self.log.debug)
                elif request[0] == 'OFF':
                    self.gsens.__del__()
                    self.gsens = None

            else: 
              self.log.warn ("unknown command " + CMD + "")
              continue
           
            
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
#        statusdebug = "";
        b = 0
        for i in range (2,11):
          if i in [5,6]: 
            self.faststate['D'+str(i)]='N'
            continue
          bit = self.getbit(ord(stat[0]),b)
          b +=1
          self.faststate['D'+str(i)]=bit
#          statusdebug += (str(i) + ":" + str(int(bit)) + " ")
#        statusdebug += ("s1:" + str(ord(stat[1])) + " ")
        self.faststate['S1']=ord(stat[1])
#        statusdebug += ("s2:" + str(ord(stat[2])) + " ") 
        self.faststate['S2']=ord(stat[2])
#        statusdebug += ("a1:" + str(ord(stat[4]) + (ord(stat[3])<<8)) + " ")
        self.faststate['A1']=str(ord(stat[4]) + (ord(stat[3])<<8))
#        statusdebug += ("a2:" + str(ord(stat[6]) + (ord(stat[5])<<8)) + " ")
        self.faststate['A2']=str(ord(stat[6]) + (ord(stat[5])<<8))
#        statusdebug += ("a3:" + str(ord(stat[8]) + (ord(stat[7])<<8)) + "")
        self.faststate['A3']=str(ord(stat[8]) + (ord(stat[7])<<8))
#        self.log.debug (statusdebug);
        self.stateupload()
        

    def tstateup (self):
        (netul, netdl) = psutil.network_io_counters(pernic = 1)["wlan0"][:2]
        lastnettime = time.time()
        while 1:
          # sysfs power stats
          if os.path.exists("/sys/class/power_supply/battery/capacity"):
            self.faststate['cpu_bcap'] = int(open("/sys/class/power_supply/battery/capacity", "r").read().strip())
          if os.path.exists("/sys/class/power_supply/battery/current_now"):
            self.faststate['cpu_bcur'] = int(open("/sys/class/power_supply/battery/current_now", "r").read().strip())/1000
          if os.path.exists("/sys/class/power_supply/ac/current_now"):
            self.faststate['cpu_accur'] = int(open("/sys/class/power_supply/ac/current_now", "r").read().strip())/1000
          if os.path.exists("/sys/class/power_supply/battery/status"):
            self.faststate['cpu_bstate'] = open("/sys/class/power_supply/battery/status", "r").read().strip()
          # iwconfig networking stats
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
          # cpu load
          self.faststate['cpu'] = psutil.cpu_percent()
          # current bandwidth
          (_netul, _netdl) = psutil.network_io_counters(pernic = 1)["wlan0"][:2]
          _nettime = time.time()
          _dnettime = _nettime - lastnettime
          self.faststate['ul'] = ((_netul - netul) / _dnettime) /1000000
          self.faststate['dl'] = ((_netdl - netdl) / _dnettime) /1000000
          (netul, netdl, lastnettime) = (_netul, _netdl,_nettime)

          self.stateupload()
          time.sleep (1)

    def stateupload (self):
        self.send ("#"+cPickle.dumps (self.faststate),self.addr)
    
    def tsonar (self):
        while True:
          if self.sonaron:
            self.sonar.write("U")
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
                  if self.tracks.vectory > 0: self.tracks.brake ()
                else: 
                  if self.sonarfailsafe_active:
                      self.log.info ("Sonar failsafe deactivated at distance {} meters".format(float(self.sonardist)/1000))
                      self.sonarfailsafe_active = False
                      self.faststate["proxalert"] = False
 
            except serial.SerialException:
                self.faststate["Son"]=65535
                self.log.info ("Sonar err")

          else:self.faststate["Son"]=65534
          inlen = self.sonar.inWaiting()
          if inlen > 0: 
              data = self.sonar.read(inlen)
              self.log.warn ("Discarded  {} packets from sonar: {}".format(inlen, data))
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
        pass
# TODO: Totally rewrite da shit
#        while 1:
#          while self.trackmode != "":
#            if self.tracktimeout < time.time():
#              self.tracks.stop()
#              self.log.info ("Timout alert STOP.")
#          time.sleep(0.1)


  
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
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.__del__()
        sys.exit(0)
        
    
    
    
    
    
