#!/bin/sh
#2015.8.18 test ok

LOCAL_CONFIG=/etc/ipsec.d/ipsec.local.conf

add_tunnel_config() {
    tunnel_name=$1
    left=$2
    leftsubnet=$3
    right=$4
    rightsubnet=$5

#    echo '* *: PSK "K8jsjm4n2dkkfy8ZTJue3iti6NbhsMCFu94zKvLw88z5Tqtkhh37gfujnE4hxwvn"' > /etc/ipsec.secrets
	
    flag="#add for ${tunnel_name}#"
    cat  >> ${LOCAL_CONFIG} <<CONFIG
${flag}
conn ${tunnel_name}
	type=tunnel
	authby=secret
	left=%defaultroute
	leftid=${left}
	leftsubnet=${leftsubnet}
	leftnexthop=%defaultroute
	right=${right}
	rightid=${right}
	rightsubnet=${rightsubnet}
	rightnexthop=%defaultroute
	pfs=yes
	auto=start
${flag}
CONFIG
}


if [ $# != 5 ]; then
    echo "Usage: sh $0 tunnel_name left leftsubnet right rightsubnet"
    exit 127
fi

flag="#add for ${1}#"
sed -i "/${flag}/,/${flag}/d" ${LOCAL_CONFIG}
add_tunnel_config $1 $2 $3 $4 $5
exit 0
