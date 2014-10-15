#!/bin/sh
echo `cat /sys/class/power_supply/battery/status` `cat /sys/class/power_supply/battery/capacity` `cat /sys/class/power_supply/battery/voltage_now`
