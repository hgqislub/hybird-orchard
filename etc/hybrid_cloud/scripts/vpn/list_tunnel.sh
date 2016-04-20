#!/bin/sh
#2015.8.18 test ok
LOCAL_CONFIG=/etc/ipsec.d/ipsec.local.conf

awk '/^conn/&&$2{a=a (a?",":"")$2}END{print a}' ${LOCAL_CONFIG}
