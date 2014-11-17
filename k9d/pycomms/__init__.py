# coding=utf-8

# Python Standard Library Imports
from math import sqrt, cos, sin, acos, pi
import smbus

# External Imports
pass

# Custom Imports
pass

# ===========================================================================
# PyComms I2C Base Class (an rewriten Adafruit_I2C pythone class clone)
# ===========================================================================


class PyComms:
    def __init__(self, address, bus=None):
        if not bus:
            bus = smbus.SMBus(1)

        self.address = address
        self.bus = bus

    def reverseByteOrder(self, data):
        # Reverses the byte order of an int (16-bit) or long (32-bit) value
        # Courtesy Vishal Sapre
        dstr = hex(data)[2:].replace('L', '')
        byteCount = len(dstr[::2])
        val = 0
        for i, n in enumerate(range(byteCount)):
            d = data & 0xFF
            val |= (d << (8 * (byteCount - i - 1)))
            data >>= 8
        return val

    def readBit(self, reg, bitNum):
        b = self.readU8(reg)
        data = b & (1 << bitNum)
        return data

    def writeBit(self, reg, bitNum, data):
        b = self.readU8(reg)

        if data != 0:
            b = (b | (1 << bitNum))
        else:
            b = (b & ~(1 << bitNum))

        return self.write8(reg, b)

    def readBits(self, reg, bitStart, length):
        # 01101001 read byte
        # 76543210 bit numbers
        #    xxx   args: bitStart=4, length=3
        #    010   masked
        #   -> 010 shifted  

        b = self.readU8(reg)
        mask = ((1 << length) - 1) << (bitStart - length + 1)
        b &= mask
        b >>= (bitStart - length + 1)

        return b


    def writeBits(self, reg, bitStart, length, data):
        #      010 value to write
        # 76543210 bit numbers
        #    xxx   args: bitStart=4, length=3
        # 00011100 mask byte
        # 10101111 original value (sample)
        # 10100011 original & ~mask
        # 10101011 masked | value

        b = self.readU8(reg)
        mask = ((1 << length) - 1) << (bitStart - length + 1)
        data <<= (bitStart - length + 1)
        data &= mask
        b &= ~(mask)
        b |= data

        return self.write8(reg, b)

    def readBytes(self, reg, length):
        output = []

        i = 0
        while i < length:
            output.append(self.readU8(reg))
            i += 1

        return output

    def readBytesListU(self, reg, length):
        output = []

        i = 0
        while i < length:
            output.append(self.readU8(reg + i))
            i += 1

        return output

    def readBytesListS(self, reg, length):
        output = []

        i = 0
        while i < length:
            output.append(self.readS8(reg + i))
            i += 1

        return output

    def writeList(self, reg, list):
        # Writes an array of bytes using I2C format"
        try:
            self.bus.write_i2c_block_data(self.address, reg, list)
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
        return -1

    def write8(self, reg, value):
        # Writes an 8-bit value to the specified register/address
        try:
            self.bus.write_byte_data(self.address, reg, value)
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readU8(self, reg):
        # Read an unsigned byte from the I2C device
        try:
            result = self.bus.read_byte_data(self.address, reg)
            return result
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readS8(self, reg):
        # Reads a signed byte from the I2C device
        try:
            result = self.bus.read_byte_data(self.address, reg)
            if result > 127:
                return result - 256
            else:
                return result
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readU16(self, reg):
        # Reads an unsigned 16-bit value from the I2C device
        try:
            hibyte = self.bus.read_byte_data(self.address, reg)
            result = (hibyte << 8) + self.bus.read_byte_data(self.address,
                                                             reg + 1)
            return result
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readS16(self, reg):
        # Reads a signed 16-bit value from the I2C device
        try:
            hibyte = self.bus.read_byte_data(self.address, reg)
            if hibyte > 127:
                hibyte -= 256
            result = (hibyte << 8) + self.bus.read_byte_data(self.address,
                                                             reg + 1)
            return result
        except (IOError):
            print (
            "Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1


# Helper functions. @todo: Move into some package
def u_to_s(v):
    if v > 127:
        v -= 256
    return v


# Using quaternions to represent rotation is not difficult from an algebraic
# point of view. Personally, I find it hard to reason visually about
# quaternions, but the formulas involved in using them for rotations are
# quite simple. I'll provide a basic set of reference functions here; see
# this page for more.
#
# You can think of quaternions (for our purposes) as a scalar plus a 3-d
# vector -- abstractly, w + xi + yj + zk, here represented by a simple tuple
# (w, x, y, z). The space of 3-d rotations is represented in full by a
# sub-space of the quaternions, the space of unit quaternions, so you want
# to make sure that your quaternions are normalized. You can do so in just
# the way you would normalize any 4-vector (i.e. magnitude should be close
# to 1; if it isn't, scale down the values by the magnitude):
def normalize(v, tolerance=0.00001):
    mag2 = sum(n * n for n in v)
    if abs(mag2 - 1.0) > tolerance:
        mag = sqrt(mag2)
        v = tuple(n / mag for n in v)
    return v


# Every rotation is represented by a unit quaternion, and concatenations
# of rotations correspond to multiplications of unit quaternions. The
# formula for this is as follows:
def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return w, x, y, z


# To rotate a vector by a quaternion, you need the quaternion's
# conjugate too. That's easy:
def q_conjugate(q):
    q = normalize(q)
    w, x, y, z = q
    return w, -x, -y, -z


# Now quaternion-vector multiplication is as simple as converting a
# vector into a quaternion (by setting w = 0 and leaving x, y, and z the
# same) and then multiplying q * v * q_conjugate(q):
def qv_mult(q1, v1):
    v1 = normalize(v1)
    q2 = (0.0,) + v1
    return q_mult(q_mult(q1, q2), q_conjugate(q1))[1:]


# Finally, you need to know how to convert from axis-angle rotations to
# quaternions. Also easy!
def axisangle_to_q(v, theta):
    v = normalize(v)
    x, y, z = v
    theta /= 2
    w = cos(theta)
    x *= sin(theta)
    y *= sin(theta)
    z *= sin(theta)
    return w, x, y, z


# And back:
def q_to_axisangle(q):
    w, v = q[0], q[1:]
    theta = acos(w) * 2.0
    return normalize(v), theta


# Here's a quick usage example. A sequence of 90-degree rotations about
# the x, y, and z axes will return a vector on the y axis to its
# original position. This code performs those rotations:
#x_axis_unit = (1, 0, 0)
#y_axis_unit = (0, 1, 0)
#z_axis_unit = (0, 0, 1)
#r1 = axisangle_to_q(x_axis_unit, pi / 2)
#r2 = axisangle_to_q(y_axis_unit, pi / 2)
#r3 = axisangle_to_q(z_axis_unit, pi / 2)
#
#v = qv_mult(r1, y_axis_unit)
#v = qv_mult(r2, v)
#v = qv_mult(r3, v)
#
#print v
## output: (0.0, 1.0, 2.220446049250313e-16)

# Thanks to @senderle for the code: http://stackoverflow.com/a/4870905
