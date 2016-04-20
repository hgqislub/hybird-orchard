conf=/etc/fs-gateway/fs-gateway.conf
restart_service()
{
    pkill -f fs-gateway-proxy
    sleep 2
    (python /usr/bin/fs-gateway-proxy 2>/dev/null &)
}
[ "a$1" = aadd ] && {
    shift
    awk -v key=$1 -v value=$2 '/^cascaded_keystone_url_map/{sub("[, ]+"key":[^,]+",FS);$0=$0($3?",":FS)key":"value}1' $conf> conf$$ && mv conf$$ $conf
    restart_service
    exit
}

[ "a$1" = adelete ] && {
    shift
    awk -v key=$1 '{/^cascaded_keystone_url_map/&&sub("[, ]+"key":[^,]+",e)}1' $conf> conf$$ && mv conf$$ $conf
    restart_service
    exit
}
