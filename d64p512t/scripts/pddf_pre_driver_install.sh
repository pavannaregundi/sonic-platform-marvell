#!/bin/bash
modprobe -r i2c-i801
modprobe -r i2c_smbus
modprobe -r i2c-dev
