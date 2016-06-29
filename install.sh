#!/usr/bin/env bash

CONF_FILE="./etc/hybrid_cloud/*"
DEST_CONF_FILE="/home/hybrid_cloud/"
CMS_FILE="./code/*"
DEST_CMS_FILE_PATH="/usr/lib64/python2.6/site-packages/heat/engine/resources/"

files=$(find ./ -name "*.sh")
for file in $files
do
    dos2unix $file
done
install() {
    echo "init '/home/hybrid_cloud' dir..."
    cp -r ./etc/hybrid_cloud/* /home/hybrid_cloud/
    echo "copy orchard code to '/usr/lib64/python2.6/site-packages/heat/engine/resources/'..."
    cp -rf ./code/* /usr/lib64/python2.6/site-packages/heat/engine/resources/

    echo "modify permissions..."
    chown -R openstack:openstack /home/hybrid_cloud
    chown -R openstack:openstack /etc/ssl/*

    echo "install success..."
    echo "you should modify 'environment.conf' in "/home/hybrid_cloud/conf" according to your environment information"
}

update(){
    echo "update '/home/hybrid_cloud' dir..."
    cp -r ./etc/hybrid_cloud/code /home/hybrid_cloud/
    cp -r ./etc/hybrid_cloud/scripts /home/hybrid_cloud/
    echo "copy orchard code to '/usr/lib64/python2.6/site-packages/heat/engine/resources/'..."
    cp -rf ./code/* /usr/lib64/python2.6/site-packages/heat/engine/resources/

    echo "modify permissions..."
    chown -R openstack:openstack /home/hybrid_cloud
    chown -R openstack:openstack /etc/ssl/*

    echo "update success..."
    echo "you should modify 'environment.conf' in "/home/hybrid_cloud/conf" according to your environment information"
}

back_up() {
    date_str=$(date "+%Y%m%d-%H:%M:%S")
    cp -rf /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py.bak${date_str}
    cp -rf /etc/heat/heat.conf /etc/heat/heat.conf.bak${date_str}
    cp -rf ${DEST_CMS_FILE_PATH} ${DEST_CMS_FILE_PATH}/../"resources_bak_"${date_str}
    cp -rf ${DEST_CONF_FILE} ${DEST_CONF_FILE}/../"hybrid_cloud_bak_"${date_str}
    echo "back up success."
}

rollback(){
    bak_time=$1
    echo "rollback to : "${bak_time}
    #cp -rf ${DEST_CMS_FILE_PATH}/../"resources_bak_"${bak_time}/* ${DEST_CMS_FILE_PATH}
    #cp -rf /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py.bak /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py
    #cp -rf /etc/heat/heat.conf.bak${bak_time} /etc/heat/heat.conf
    cp -rf ${DEST_CONF_FILE}/../"hybrid_cloud_bak_"${bak_time}/* ${DEST_CONF_FILE}
    echo "modify permissions..."
    chown -R openstack:openstack /home/hybrid_cloud
    chown -R openstack:openstack /etc/ssl/*

}


if [ "$1" == "install" ]; then
    install
elif [ "$1" == "backup" ]; then
    back_up
elif [ "$1" == "update" ]; then
    update
elif [ "$1" == "rollback" ]; then
    rollback $2
else
    echo "Usage: sh $0 install {install|backup|update|rollback}"
fi

