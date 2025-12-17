#!/bin/bash
#/usr/bin/bmc_mon.sh

tl10_bmc_mon_enable=`cat /sys/kernel/d64p512t_fpga/bmc-mon-trigger | sed -n '1p' | awk -F' ' '{print $1}'`

# Enable:1, Disable: 0
# To turn off the monitor TL10 temperature sensor, and the BMC boot prediction is off.

echo "Current state tl10_bmc_mon_enable:$tl10_bmc_mon_enable" > /dev/kmsg
echo "BMC - TL10 Monitor Mode Control: Disable" > /dev/kmsg

tl10_bmc_mon_enable_mask=0xfeffffff

bmc_tl10_disable_value=$(($tl10_bmc_mon_enable & tl10_bmc_mon_enable_mask))
bmc_tl10_disable_str=`printf "%08x " $bmc_tl10_disable_value`
echo "0x$bmc_tl10_disable_str" > /sys/kernel/d64p512t_fpga/bmc-mon-trigger

echo "Wait 10 seconds for IFCS intialization" > /dev/kmsg
sleep 10

echo "BMC - TL10 Monitor Mode Control: Enable" > /dev/kmsg
# To turn on the monitor TL10 temperature sensor.

bmc_tl10_enable_value=$((($tl10_bmc_mon_enable & tl10_bmc_mon_enable_mask) | (1 << 24)))
bmc_tl10_enable_str=`printf "%08x " $bmc_tl10_enable_value`
echo "0x$bmc_tl10_enable_str" > /sys/kernel/d64p512t_fpga/bmc-mon-trigger
