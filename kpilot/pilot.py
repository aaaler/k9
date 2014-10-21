import sys
import socket
import threading
import time
import cPickle

udpinmsgs = []
direction = ""
speed = 130
rotspeed = 130
timeout = "1000"
stats = {}
statsdtime = 0;
laststatstime = time.time();


def udpreader (dummy1 = "", dummy2=""):
  global udpin, udpout, UDP_IP, UDP_PORT, udpinmsgs, stats, statsdtime, laststatstime
  try:
        data, addr = udpin.recvfrom(8192)#buffer size 
        if data[0:20] == "command done:msg was" : 
           return True
        elif data[0] == "#" : 
           # found stats in flow
           stats = cPickle.loads (data[1:])
           statsdtime = time.time() - laststatstime
           laststatstime = time.time()
           stats['size'] = len (data)
           #udpinmsgs.append(str(cPickle.loads (data[1:])))
           return True
        udpinmsgs.append(str(data))       
        return str(data)
        sys.stdout.write("udp:" + str(data) + "\n")
        sys.stdout.flush()        
  except socket.error:
        return False

  
def trackpoller ():
#  2do: refactor it 4 new tracks command with 2axis joypad  
  global udpin, udpout, UDP_IP, UDP_PORT, udpinmsgs, direction,speed,rotspeed
  while True:
    while direction != "":
      if direction == "FWD" or direction == "REV" :
        data = direction + " " + str(speed) + " " + timeout
      elif direction == "LEFT" or direction == "RIGHT" :
        data = direction + " " + str(rotspeed) + " " + timeout
      elif direction == "STOP":
        data = direction
        direction = ""        
      else: print ("TP: unknown direction")
      udpinmsgs.append(data);      
      send(data)
      time.sleep (0.3)
    time.sleep (0.05)



def udp_init ():
  global udpin, udpout, UDP_IP, UDP_IN_PORT, UDP_OUT_PORT
  UDP_IP = "192.168.0.99"
  UDP_OUT_PORT = 9999
  UDP_IN_PORT = 9999
  udpout = socket.socket(socket.AF_INET, # Internet
               socket.SOCK_DGRAM) # UDP
  udpin  = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
  udpin.setblocking(0)
  udpin.bind(("0.0.0.0", UDP_IN_PORT))


#  UDP reader go to kivytimers
#  r = threading.Thread(target=udpreader)
#  r.setDaemon (1)
#  r.start()


#  ttp = threading.Thread(target=trackpoller)
#  ttp.setDaemon (1)
#  ttp.start()
# 

def init(logger) :
  global log
  log = logger
  udp_init()
  speed = 130
  rotspeed = 130
  timeout = 500 
  servo1 = 90
  servo2 = 90
  
  print ("UDP target IP:", UDP_IP)
  print ("UDP target port:", UDP_OUT_PORT)
  print ("UDP local port:", UDP_IN_PORT)


def send (body) :
    log.debug (u"UDP {}:{}< {}".format(UDP_IP, UDP_OUT_PORT,body))
    return udpout.sendto(body, (UDP_IP, UDP_OUT_PORT))





if __name__ == '__main__':
  import msvcrt
  init()
  

  cycle = 1
  while cycle:
      out = "";
      ch = msvcrt.getch()
      if ch == b'|' :
        cycle = 0
        out += "Exiting."
      elif ch == b'w':
        UDPMSG = "FWD "+ str(speed) + " " + str(timeout) 
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b's':
        UDPMSG = "REV "+ str(speed) + " " + str(timeout) 
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b'a':
        UDPMSG = "LEFT "+ str(rotspeed) + " " + str(timeout) 
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b'd':
        UDPMSG = "RIGHT " + str(rotspeed) + " " + str(timeout)
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b' ':
        UDPMSG = "STOP"
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b'r':
        speed +=2;
        out += "speed set:" + str(speed)
      elif ch==b'f':
        speed -=2;
        out += "speed set:" + str(speed)
      elif ch==b'=':
        rotspeed +=2;
        out += "rotation speed set:" + str(rotspeed)
      elif ch==b'-':
        rotspeed -=2;
        out += "rotation speed set:" + str(rotspeed)
      elif ch==b'i':
        UDPMSG = "INFO"
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b't':
        servo1 += 1
        UDPMSG = "SERVO 1 " + str(servo1)
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b'g':
        servo1 -= 1
        UDPMSG = "SERVO 1 " + str(servo1)
        send (UDPMSG)
        out += "sent: " + UDPMSG;

      elif ch==b'q':
        servo2 += 1
        UDPMSG = "SERVO 2 " + str(servo2)
        send (UDPMSG)
        out += "sent: " + UDPMSG;
      elif ch==b'e':
        servo2 -= 1
        UDPMSG = "SERVO 2 " + str(servo2)
        send (UDPMSG)
        out += "sent: " + UDPMSG;

      else:
        out += "Got "+str(ch)+" key. "



      print (out);


