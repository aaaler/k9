#!/bin/sh -e
echo Setting up LCD1x9
/root/K9/LCD1x9/lcd1x9 -init >/dev/null || echo Failed LCD INIT
/root/K9/LCD1x9/lcd1x9 'Hi there' >/dev/null || true


