# coding=utf-8
import threading
import math
import smbus
import mpu6050
import time
from gpio.pin import pin


class GSens (object):
# Sensor initialization
    def __init__ (self, i2cdev = 0, cb_update = None, cb_error = None, cb_info = None, cb_debug = None):
        #turn on power with gpio
        self.power = pin(pin.port.PI0)
        self.power.on()

        self.cb_update = cb_update
        self.cb_error = cb_error
        self.cb_info = cb_info
        self.cb_debug = cb_debug

        self.calibrating = True
        self.calibration_time = -1.
        self.start_time = time.time()
        self.yaw0 = 0
        self.pitch0 = 0
        self.roll0 = 0
        self.ax0 = 0
        self.ay0 = 0
        self.az0 = 0
        self.precision = 100
        self.samplerate = 9 #1khz / (1 + 4) = 200 Hz [9 = 100 Hz]
        self.cycleActive = True

        mpu = mpu6050.MPU6050(
            address=mpu6050.MPU6050.MPU6050_DEFAULT_ADDRESS,
            bus=smbus.SMBus(i2cdev))
        mpu.dmpInitialize()
        mpu.setDMPEnabled(True)
        self.mpu = mpu      
        # get expected DMP packet size for later comparison
        self.packetSize = mpu.dmpGetFIFOPacketSize()
        
        self.readThread = threading.Thread(target=self.readcycle)
        self.readThread.setDaemon (1)
        self.readThread.start()

        self.info ("Turned on. Calibrating.")

    def __del__ (self):
        self.info ("Turned off.")
        self.cycleActive = False
        self.power.off()
        

    def debug (self, msg):
        if callable(self.cb_debug): self.cb_debug("[MPU] {}".format(msg))
    def info (self, msg):
        if callable(self.cb_info): self.cb_info("[Accel-Gyro MPU] {}".format(msg))
    def error (self, msg):
        if callable(self.cb_error): self.cb_error("[Accel-Gyro MPU] {}".format(msg))

    def ftoip(self,v):
        return int(self.precision * v)


    def equal(self,l1, l2):
        for k, v1 in enumerate(l1):
            v2 = l2[k]
            if self.ftoip(v1) != self.ftoip(v2):
                return False
        return True
    def updatefifoCount(self):
        self.fifoCount = self.mpu.getFIFOCount()


    def getPkt(self):
        mpu = self.mpu
        # wait for correct available data length, should be a VERY short wait
        while self.fifoCount < self.packetSize:
            self.updatefifoCount()

        result = mpu.getFIFOBytes(self.packetSize)
        q = mpu.dmpGetQuaternion(result)
        g = mpu.dmpGetGravity(q)
        self.ypr = mpu.dmpGetYawPitchRoll(q, g)
        a = mpu.dmpGetAccel(result)
        la = mpu.dmpGetLinearAccel(a, g)
        self.laiw = mpu.dmpGetLinearAccelInWorld(a, q)

        yaw = self.ypr['yaw'] * 180 / math.pi  # radians to degrees
        pitch = self.ypr['pitch'] * 180 / math.pi
        roll = self.ypr['roll'] * 180 / math.pi
        ax = self.laiw['x'] * 9.8
        ay = self.laiw['y'] * 9.8
        az = self.laiw['z'] * 9.8
        # Update timedelta
#        self.dt = time.time() - t0
        self.yaw   = yaw  
        self.pitch = pitch
        self.roll  = roll 
        self.ax    = ax   
        self.ay    = ay   
        self.az    = az   


        if self.calibrating:
            if self.equal(
                    [yaw, pitch, roll, ax, ay, az, ],
                    [self.yaw0, self.pitch0, self.roll0, self.ax0, self.ay0, self.az0, ]
            ):
                self.calibrating = False
                self.calibration_time = self.start_time - time.time()

                self.info ("Calibration complete in {:.2f} seconds.".format(self.calibration_time))
                self.setRate (self.samplerate)   #1khz / (1 + 4) = 200 Hz [9 = 100 Hz]

            else:
                self.yaw0 = yaw
                self.pitch0 = pitch
                self.roll0 = roll
                self.ax0 = ax
                self.ay0 = ay
                self.az0 = az
                #print(
                #    "Calibrating: dt:{: 8f} y:{: 4d} p:{: 4d} r:{: 4d} x:{: 4d} y:{: 4d} z:{: 4d} buf:{:4d}".format(dt, ftoip(yaw), ftoip(pitch), ftoip(roll), ftoip(ax), ftoip(ay), ftoip(az),fifoCount)
                #)
        else:
            pass
#        print ("dt:{: 8f} y:{: 4d} p:{: 4d} r:{: 4d} x:{: 4d} y:{: 4d} z:{: 4d}  buf:{:4d}".format(dt, ftoip(yaw), ftoip(pitch), ftoip(roll), ftoip(ax), ftoip(ay), ftoip(az),fifoCount ))



    def setRate (self, rate):
        self.mpu.setRate (rate)   #1khz / (1 + 4) = 200 Hz [9 = 100 Hz]
        freq = 1000 / (1 + self.mpu.getRate())
        self.info ("Sample rate set to {} Hz.".format(freq))

    def readcycle(self):
        while self.cycleActive:
            # Get INT_STATUS byte
            mpuIntStatus = self.mpu.getIntStatus()

            if mpuIntStatus >= 2:  # check for DMP data ready interrupt
                # get current FIFO count
                self.updatefifoCount()

                # check for overflow
                if self.fifoCount == 1024:
                    # reset so we can continue cleanly
                    self.mpu.resetFIFO()
                    self.error ("GSensor FIFO buffer overrun, resetting MPU")
                while self.fifoCount >= self.packetSize:
                    self.getPkt ()
                    self.fifoCount -= self.packetSize
                if callable(self.cb_update) : self.cb_update ()
            else:
                time.sleep (0.02)
