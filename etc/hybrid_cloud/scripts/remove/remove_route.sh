#!/bin/bash
for subnet in $@
do
    ip route show | grep ${subnet} && ip route del ${subnet}
done



