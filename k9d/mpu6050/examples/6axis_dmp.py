# coding=utf-8
import math
import smbus
import mpu6050
from time import time

# Sensor initialization
mpu = mpu6050.MPU6050(
    address=mpu6050.MPU6050.MPU6050_DEFAULT_ADDRESS,
    bus=smbus.SMBus(1))
mpu.dmpInitialize()
mpu.setDMPEnabled(True)

# get expected DMP packet size for later comparison
packetSize = mpu.dmpGetFIFOPacketSize()

calibrating = True
t0 = time()
yaw0 = 0
pitch0 = 0
roll0 = 0
ax0 = 0
ay0 = 0
az0 = 0
precision = 100


def ftoip(v):
    return int(precision * v)


def equal(l1, l2):
    for k, v1 in enumerate(l1):
        v2 = l2[k]
        if ftoip(v1) != ftoip(v2):
            return False
    return True

print "Calibrating..."

while True:
    # Get INT_STATUS byte
    mpuIntStatus = mpu.getIntStatus()

    if mpuIntStatus >= 2:  # check for DMP data ready interrupt
        # get current FIFO count
        fifoCount = mpu.getFIFOCount()

        # check for overflow
        if fifoCount == 1024:
            # reset so we can continue cleanly
            mpu.resetFIFO()
            print('FIFO overflow!')

        # wait for correct available data length, should be a VERY short wait
        fifoCount = mpu.getFIFOCount()
        while fifoCount < packetSize:
            fifoCount = mpu.getFIFOCount()

        result = mpu.getFIFOBytes(packetSize)
        q = mpu.dmpGetQuaternion(result)
        g = mpu.dmpGetGravity(q)
        ypr = mpu.dmpGetYawPitchRoll(q, g)
        a = mpu.dmpGetAccel(result)
        la = mpu.dmpGetLinearAccel(a, g)
        laiw = mpu.dmpGetLinearAccelInWorld(a, q)

        yaw = ypr['yaw'] * 180 / math.pi  # radians to degrees
        pitch = ypr['pitch'] * 180 / math.pi
        roll = ypr['roll'] * 180 / math.pi
        ax = laiw['x'] * 9.8
        ay = laiw['y'] * 9.8
        az = laiw['z'] * 9.8
        # Update timedelta
        dt = time() - t0

        if calibrating:
            if equal(
                    [yaw, pitch, roll, ax, ay, az, ],
                    [yaw0, pitch0, roll0, ax0, ay0, az0, ]
            ):
                calibrating = False
                print("Calibration done in ", dt, "seconds")
            else:
                yaw0 = yaw
                pitch0 = pitch
                roll0 = roll
                ax0 = ax
                ay0 = ay
                az0 = az
                print(
                    "Calibrating:", int(dt), ftoip(yaw), ftoip(ax), ftoip(ay)
                )
        else:
            # Update time only when not calibrating!
            t0 = time()
            print(t0, dt, yaw, ax, ay)

        # track FIFO count here in case there is > 1 packet available
        # (this lets us immediately read more without waiting for an
        # interrupt)
        fifoCount -= packetSize
