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

#Kind a config here
#arduino tracks bridge pinout
p1PWM=str(6)
p1FWD=str(7)
p1REV=str(8)
p2PWM=str(5)
p2FWD=str(4)
p2REV=str(3)
#ip
addr = "192.168.0.22"
UDP_IP = "0.0.0.0"
UDP_PORT = 9999
#sonar
sonaron = True
sonarfailsafe = 0
#mjpg_streamer related
videomode = 'OFF'
#init
ardustate = {}
tracktimeout = time.time()
trackmode = ""
sonardist = 0


def send (body,ip) :
#  return respsock.sendto(bytes(body, 'UTF-8'), ("192.168.0.22", UDP_PORT))
  global addr
  return respsock.sendto(body, (addr, UDP_PORT))


def spinal_write (data):
    debugmsg = "UART<" + data
    sys.stdout.write(debugmsg)
    sys.stdout.flush()
#    send (debugmsg,addr)
    return spinal.write(data)

def from_spinal (pkt):
  if pkt == "0_o\n" :
    #SPINAL BOOTED UP -- NEED INIT
    spinal_write ("1;0;")
  if pkt != "OK\r\n":
    debugmsg = "UART<" + pkt
    send (debugmsg,addr)
#hardcore hex debug output
#    print ":".join("{:02x}".format(ord(c)) for c in pkt)

def getbit(byteval,idx):
    return ((int(byteval)&(1<<int(idx)))!=0);

def parsestate(stat):
    global ardustate
    statusdebug = "";
    b = 0
    for i in range (2,11):
      if i in [5,6]: 
        ardustate['D'+str(i)]='N'
        continue
      bit = getbit(ord(stat[0]),b)
      b +=1
      ardustate['D'+str(i)]=bit
      statusdebug += (str(i) + ":" + str(int(bit)) + " ")
    statusdebug += ("s1:" + str(ord(stat[1])) + " ")
    ardustate['S1']=ord(stat[1])
    statusdebug += ("s2:" + str(ord(stat[2])) + " ") 
    ardustate['S2']=ord(stat[2])
    statusdebug += ("a1:" + str(ord(stat[4]) + (ord(stat[3])<<8)) + " ")
    ardustate['A1']=str(ord(stat[4]) + (ord(stat[3])<<8))
    statusdebug += ("a2:" + str(ord(stat[6]) + (ord(stat[5])<<8)) + " ")
    ardustate['A2']=str(ord(stat[6]) + (ord(stat[5])<<8))
    statusdebug += ("a3:" + str(ord(stat[8]) + (ord(stat[7])<<8)) + "\n")
    ardustate['A3']=str(ord(stat[8]) + (ord(stat[7])<<8))
    print (statusdebug);
    stateupload()


def tstateup ():
    while 1:
      if os.path.exists("/sys/class/power_supply/battery/capacity"):
        ardustate['cpu_bcap'] = int(open("/sys/class/power_supply/battery/capacity", "r").read().strip())
      if os.path.exists("/sys/class/power_supply/battery/current_now"):
        ardustate['cpu_bcur'] = int(open("/sys/class/power_supply/battery/current_now", "r").read().strip())/1000
      if os.path.exists("/sys/class/power_supply/ac/current_now"):
        ardustate['cpu_accur'] = int(open("/sys/class/power_supply/ac/current_now", "r").read().strip())/1000
      if os.path.exists("/sys/class/power_supply/battery/status"):
        ardustate['cpu_bstate'] = open("/sys/class/power_supply/battery/status", "r").read().strip()
      piwconfig = subprocess.Popen(["/sbin/iwconfig", "wlan7"], stdout=subprocess.PIPE)
      iwconfig_out, err = piwconfig.communicate()
      brre = re.compile (r"Bit Rate=([\d.]+ \S+)",re.M)
      lqre = re.compile (r"Link Quality=(\d+/\d+)  Signal level=(-\d+ dBm)",re.M)
      match = brre.search(iwconfig_out)
      if match: ardustate['wifi_br'] = match.group(1)
      else: ardustate['wifi_br'] = "n/a"
      match = lqre.search(iwconfig_out)
      if match:
        ardustate['wifi_lq'] = match.group(1)
        ardustate['wifi_sl'] = match.group(2)
      else:
        ardustate['wifi_lq'] = "n/a"
        ardustate['wifi_sl'] = "n/a"

 
      stateupload()
      time.sleep (1)

def stateupload ():
    global ardustate
    send ("#"+cPickle.dumps (ardustate),addr)

def tsonar ():
    global sonardist
    while True:
      if sonaron:
        sonar.write("U")
#      time.sleep(0.1)
        try:
          HighLen = ord(sonar.read(1));                   #High byte of distance
          LowLen  = ord(sonar.read(1));                   #Low byte of distance
          sonardist  = int(HighLen*256 + LowLen);             #Calculate the distance
#        print ("SONAR H:"+ str( sonardist))
          ardustate["Son"]=sonardist
        except serial.SerialException:
          ardustate["Son"]=65535
          print ("Sonar err")
          pass
      else:ardustate["Son"]=65534
      time.sleep(.05)
      

def sreader():
    sbuff="";
    """loop forever and copy serial->console"""
    while 1:
        data = spinal.read()
        sbuff += data;
        if data == "#":
          state = spinal.read(10)
#          sys.stdout.write("Preapre to state:" + state)
          sys.stdout.flush()
          try:
            if state[9]== "#":
              state = state[:-1]
              sbuff = sbuff[:-1]
              parsestate(state)
            else:
              sbuff +=  state
          except IndexError: sbuff +=  state
        if data == "\n":
            from_spinal(sbuff)
            sys.stdout.write("UART>" + sbuff)
            sys.stdout.flush()
            sbuff=""

def cmdtimeout():
    """stop tracks when command is timed out"""
    global tracktimeout,trackmode
    while 1:
      while trackmode != "":
        if tracktimeout < time.time():
          trackstop()
          print ("Timout alert STOP.")
      time.sleep(0.1)




def tracks (X,Y) :
  global tracktimeout
  global trackl, trackr
  #calibration should be here
  cal_track_min = 180
  fX = float(X);
  fY = float(Y);
  timeout = 100 #not impl.
  tracktimeout = time.time() + (int(timeout)/1000)
  if fY >= 0:
    #8 <LFWD> <LREV> <LPWM> <RFWD> <RREV> <RPWM>;
    trackl = fY + fX
    trackr = fY - fX
#    out="8 %0d %0d %0d %0d %0d %0d;" % (1,0,abs(int(Y)),1,0,abs(int(Y)))
  elif fY < 0:
    trackl = fY + fX
    trackr = fY - fX
  if trackr > 1: trackr = 1
  if trackl > 1: trackl = 1
  if trackr < -1: trackr = -1
  if trackl < -1: trackl = -1
  out="8 %0d %0d %0d %0d %0d %0d;" % (trackl>0,trackl<0,abs(trackr)*(255-cal_track_min)+cal_track_min,trackr>0,trackr<0,abs(trackl)*(255-cal_track_min)+cal_track_min)
  spinal_write(out);
  ardustate['trackr'] = trackr;
  ardustate['trackl'] = trackl;
  return " OK"

def track (cmd, val, timeout) :
  global tracktimeout,trackmode
  tracktimeout = time.time() + (int(timeout)/1000)
  trackmode = cmd
  if cmd == "FWD":    
    spinal_write("2 "+p1FWD+" 1;")
    spinal_write("2 "+p2FWD+" 1;")
    spinal_write("2 "+p1REV+" 0;")
    spinal_write("2 "+p2REV+" 0;")
    spinal_write("3 "+p1PWM+" "+str(val)+";")
    spinal_write("3 "+p2PWM+" "+str(val)+";")
  elif cmd == "REV":
    spinal_write("2 "+p1FWD+" 0;")
    spinal_write("2 "+p2FWD+" 0;")
    spinal_write("2 "+p1REV+" 1;")
    spinal_write("2 "+p2REV+" 1;")
    spinal_write("3 "+p1PWM+" "+str(val)+";")
    spinal_write("3 "+p2PWM+" "+str(val)+";")
  elif cmd == "LEFT":
    spinal_write("2 "+p1FWD+" 1;")
    spinal_write("2 "+p2FWD+" 0;")
    spinal_write("2 "+p1REV+" 0;")
    spinal_write("2 "+p2REV+" 1;")
    spinal_write("3 "+p1PWM+" "+str(val)+";")
    spinal_write("3 "+p2PWM+" "+str(val)+";")
  elif cmd == "RIGHT":
    spinal_write("2 "+p1FWD+" 0;")
    spinal_write("2 "+p2FWD+" 1;")
    spinal_write("2 "+p1REV+" 1;")
    spinal_write("2 "+p2REV+" 0;")
    spinal_write("3 "+p1PWM+" "+str(val)+";")
    spinal_write("3 "+p2PWM+" "+str(val)+";")

  else:
    return "not implemened"
  return " ok"



def trackstop () :
  global tracktimeout,trackmode
  spinal_write("2 "+p1PWM+" 0;")
  spinal_write("2 "+p2PWM+" 0;")
  trackmode = ""


def servo (id,angle):
  spinal_write("4 "+str(id)+" "+str(angle)+";")

def run_mjpg (params):
      global pmjpg, videomode
      out = ''
      (fpv_size,fpv_fps)=params.split('@')
      cmd = ("/root/K9/mjpg_streamer/mjpg_streamer", "-i", "/root/K9/mjpg_streamer/input_uvc.so -r {} -f {}".format(fpv_size,fpv_fps), "-o","/root/K9/mjpg_streamer/output_http.so -w /root/K9/mjpg_streamer/www")
      pmjpg = subprocess.Popen(cmd)
      if pmjpg.poll() == None:
        out+= "Spawned mjpg_streamer with {}@{} PID: {}\n".format(fpv_size,fpv_fps,pmjpg.pid)
        videomode = "{}@{}".format(fpv_size,fpv_fps)
      else:
        out+= "Failed to start mjpg_streamer"
        videomode = "Failed"
      return out
 
#==============UDP INIT====================
print ("spinal interface daemon for K-9 starting");
servsock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP
servsock.bind((UDP_IP, UDP_PORT))
respsock = socket.socket(socket.AF_INET, # Internet
             socket.SOCK_DGRAM) # UDP
#============SERIAL INIT===================
try:
  spinal = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
except:
  sys.stderr.write("Could not open port for spinal\n")
  sys.exit(1)


try:
  sonar = serial.Serial('/dev/ttyS1', 9600, timeout=0.5)
except:
  sys.stderr.write("Could not open port for sonar\n")
  sys.exit(1)

#===========THREADING INIT=================

tSerialRead = threading.Thread(target=sreader)
tSerialRead.setDaemon (1)
tSerialRead.start()

tTrackWatchdog = threading.Thread(target=cmdtimeout)
tTrackWatchdog.setDaemon (1)
tTrackWatchdog.start()

tStateUpload = threading.Thread(target=tstateup)
tStateUpload.setDaemon (1)
tStateUpload.start()

tSonar = threading.Thread(target=tsonar)
tSonar.setDaemon (1)
tSonar.start()


print ("ready to play");
spinal.write("1;");


while True:
  data,(addr,port) = servsock.recvfrom(1024) # buffer size is 1024 bytes

  sys.stdout.write(str(addr))
  sys.stdout.flush()
  out = ''
  request = data.split(' ');
  CMD = request.pop(0) 
  CMD = CMD.strip("\n")
  if CMD == "STOP":
    trackstop()
  elif CMD == "EXEC":
    spinal_write (' '.join(request))
  elif CMD in ["FWD","REV","LEFT","RIGHT","BREAK"]:
    out += track(CMD,request[0],request[1]);
  elif CMD == "TRACKS":
    out += tracks(request[0],request[1]);
  elif CMD == "SERVO":
    servo (request[0],request[1]);
  elif CMD == "SON":
    if request[0] == 'Failsafe':
      sonaron = True
      if request[1] == 'off': sonarfailsafe = 0
      else: sonarfailsafe = float(request[1])
    elif request[0] == 'Sonar' and request[1] == 'off' :
      sonaron = False
      sonarfailsafe = 0
  elif CMD == "CAM":
    if request[0] == 'RES':
      if 'pmjpg' in globals():
        if pmjpg.poll() == None:
          pmjpg.kill()
          videomode = "OFF"
          t = threading.Timer(2.0,run_mjpg,[request[1]])
	  t.start() 
	else:
	  out += run_mjpg(request[1])
      else: out += run_mjpg(request[1])
    elif request[0] == 'OFF':
      if 'pmjpg' in globals():
        if pmjpg.poll() == None:
          pmjpg.kill()
      videomode = "OFF"
    elif request[0] == 'ZOOM' and request[1] == 'OFF' :
      status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=1"])  
    elif request[0] == 'ZOOM' and request[1] == 'ON' :
      status = subprocess.call(["/usr/bin/v4l2-ctl", "--set-ctrl=zoom_absolute=5"])
  else:
    out += "unknown command " + CMD + "\n"
 
  print (out)
#  send ("command done:" + out, addr);

    
