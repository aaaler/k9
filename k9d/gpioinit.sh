#!/bin/sh
for i in `seq 1 1 74`; do echo $i > /sys/class/gpio/export; echo -n "$i "; done
