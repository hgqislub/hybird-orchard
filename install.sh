#!/usr/bin/env bash

install() {
    echo "init '/home/hybrid_cloud' dir..."
    rm -rf /home/hybrid_cloud
    mkdir /home/hybrid_cloud
    cp -r ./etc/hybrid_cloud/* /home/hybrid_cloud/

    echo "copy code to '/usr/lib64/python2.6/site-packages/heat/engine/resources/'..."
    cp -rf ./code/* /usr/lib64/python2.6/site-packages/heat/engine/resources/

    echo "modify permissions..."
    chown -R openstack:openstack /home/hybrid_cloud
    chown -R openstack:openstack /etc/ssl/*

    echo "install success..."
    echo "you should modify '/home/hybrid_cloud/conf/environment.conf' according to your environment information"
}

back_up() {
    cp /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py /usr/lib64/python2.6/site-packages/heat/engine/resources/instance.py.bak
    cp /etc/heat/heat.conf /etc/heat/heat.conf.bak
    echo "back up success."
}

if [ "$1" == "install" ]; then
    install
elif [ "$1" == "backup" ]; then
    back_up
else
    echo "Usage: sh $0 install {install|backup}"
fi
