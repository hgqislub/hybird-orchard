#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/modify_dns_server_address

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/modify_dns_server_address_run.sh
RUN_LOG=${dir}/modify_dns_server_address_run.log

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
dns_list=`cps template-params-show --service dns dns-server | awk -F "|" 'begin{flag=0}{if(flag==0 && $2~"address"){flag=1;print $3}else if(flag==1 && !($2~"network")){print $3}else{flag=0}}'`
str=""
for line in `echo ${dns_list}`
do
        str=${str}${line}
done

if [ "$1" == "add" ]; then
    str=${str//","${2}/""}
    str=${str//${2}","/""}
    str=${str}","${2}
elif [ "$1" == "remove" ]; then
    str=${str//","${2}/""}
    str=${str//${2}","/""}
elif [ "$1" == "replace" ]; then
    str=${2}
fi

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo cps template-params-update --parameter address=${str} --service dns dns-server >> ${RUN_SCRIPT}
echo cps commit >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

temp=`cat ${RUN_LOG}`
if [ -n "${temp}" ]; then
    exit 127
fi
exit 0