#!/usr/bin/env python
# coding=utf-8

# hints from https://www.raspberrypi.org/forums/viewtopic.php?p=600515#p600515

from __future__ import print_function

# This module uses the services of the C pigpio library. pigpio must be running on the Pi(s) whose GPIO are to be manipulated. 
# cmd ref: http://abyz.me.uk/rpi/pigpio/python.html#i2c_write_byte_data
import pigpio # aptitude install python-pigpio
import time
import struct
import sys
import crcmod #ati python-crcmod


def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

PIGPIO_HOST = '::1'
PIGPIO_HOST = '127.0.0.1'

pi = pigpio.pi(PIGPIO_HOST)
if not pi.connected:
  eprint("no connection to pigpio daemon at " + PIGPIO_HOST + ".")
  exit(1)

I2C_SLAVE = 0x61
I2C_BUS = 1

try:
  pi.i2c_close(0)
except:
  if sys.exc_value and str(sys.exc_value) != "'unknown handle'":
    eprint("Unknown error: ", sys.exc_type, ":", sys.exc_value)

h = pi.i2c_open(I2C_BUS, I2C_SLAVE)

# read meas interval (not documented, but works)

def read_n_bytes(n):
  (count, data) = pi.i2c_read_device(h, n)
  if count == n:
    return data
  else:
    eprint("error: read measurement interval didnt return " + str(n) + "B")
    return -1

def read_meas_interval():
  pi.i2c_write_device(h, [0x46, 0x00])
  (count, data) = pi.i2c_read_device(h, 3)

  if count == 3:
    if len(data) == 3:
      interval = int(data[0])*256 + int(data[1])
      #print "measurement interval: " + str(interval) + "s, checksum " + str(data[2])
      return interval
    else:
      eprint("error: no array len 3 returned, instead " + str(len(data)) + "type: " + str(type(data)))
  else:
    "error: read measurement interval didnt return 3B"
  
  return -1

if read_meas_interval() != 2:
# if not every 2s, set it
  eprint("setting interval to 2")
  pi.i2c_write_device(h, [0x46, 0x00, 0x00, 0x02, 0xE3])
  read_meas_interval()


#trigger cont meas
pressure_mbar = 972
LSB = 0xFF & pressure_mbar
MSB = 0xFF & (pressure_mbar >> 8)
#print ("MSB: " + hex(MSB) + " LSB: " + hex(LSB))
#pressure_re = LSB + (MSB * 256)
#print("press " + str(pressure_re))
pressure = [MSB, LSB]

pressure_array = ''.join(chr(x) for x in [pressure[0], pressure[1]])
#pressure_array = ''.join(chr(x) for x in [0xBE, 0xEF]) # use for testing crc, should be 0x92
#print pressure_array

f_crc8 = crcmod.mkCrcFun(0x131, 0xFF, False, 0x00)

crc8 = f_crc8(pressure_array) # for pressure 0, should be 0x81
# print "CRC: " + hex(crc8)
pi.i2c_write_device(h, [0x00, 0x10, pressure[0], pressure[1], crc8])

# read ready status
while True:
  pi.i2c_write_device(h, [0x02, 0x02]) #fixme throws if two processes are running in paralell
  data = read_n_bytes(3)
  if data[1] == 1:
    #print "data ready"
    break
  else:
    eprint(".")
    time.sleep(0.1)

#read measurement
pi.i2c_write_device(h, [0x03, 0x00])
data = read_n_bytes(18)
  
#print "CO2: "  + str(data[0]) +" "+ str(data[1]) +" "+ str(data[3]) +" "+ str(data[4])

struct_co2 = struct.pack('>BBBB', data[0], data[1], data[3], data[4])
float_co2 = struct.unpack('>f', struct_co2)

struct_T = struct.pack('>BBBB', data[6], data[7], data[9], data[10])
float_T = struct.unpack('>f', struct_T)

struct_rH = struct.pack('>BBBB', data[12], data[13], data[15], data[16])
float_rH = struct.unpack('>f', struct_rH)

if float_co2 > 0.0:
  print("scd30_co2 %f" % float_co2)

print("scd30_T %f" % float_T)

if float_rH > 0.0:
  print("scd30_rH %f" % float_rH)

pi.i2c_close(h)
