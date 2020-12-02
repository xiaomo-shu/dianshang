#!/bin/bash

ori_mac="AA:BB:CC:01:01:01"

num_1=0
num_2=0
while ((num < 100))
do 
    let ++num
    #echo $num
    let ++num_2
    if [ "${num_2}" -gt "99" ]; then
        let ++num_1
        num_2=0
    fi
    #mac = "AA:BB:CC:01:" + "%02d" % num_1 + ":" + "%02d" % num_2
    mac=`printf "AA:BB:CC:01:%02d:%02d" ${num_1} ${num_2}`
    printf "%s\n" ${mac}
    nohup python3 -u simulate_uefi_client.py ${mac} 2>&1 1>./log/log_$num.log &
    # sleep 0.1 
done

# ps -ef|grep simulate_uefi_client.py|grep -vE 'vi|grep'| awk '{print $2}'|xargs kill -9
