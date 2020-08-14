#!/bin/bash

while ((num < 500))
do 
    let ++num
    echo $num
    nohup python3 -u client.py 2>&1 1>./log/log_$num.log &
    sleep 0.1 
done
