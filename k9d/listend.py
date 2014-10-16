#!/usr/bin/env python
import socket
import serial
import threading
import sys
import struct
import time
import cPickle
import os

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

      stateupload()
      time.sleep (1)

def stateupload ():
    global ardustate
    send ("#"+cPickle.dumps (ardustate),addr)

def tsonar ():
    global sonardist,ardust
    while 1:
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


#motor driver pin definition
p1PWM=str(6)
p1FWD=str(7)
p1REV=str(8)
p2PWM=str(5)
p2FWD=str(4)
p2REV=str(3)
addr = "192.168.0.22"
tracktimeout = time.time()
trackmode = ""
ardustate = {}
sonardist = 0

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

#==============UDP INIT====================
print ("spinal interface daemon for K-9 starting");
UDP_IP = "0.0.0.0"
UDP_PORT = 9999
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

  out = "msg was " + data
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
  else:
    out += "unkonown command " + CMD

  print (out)
#  send ("command done:" + out, addr);

    
