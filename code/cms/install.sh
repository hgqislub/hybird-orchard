cd "$(dirname $0)"

cp cms-api cms-manage /usr/bin

# create  log directory
mkdir -p /var/log/fusionsphere/component/cms

# config file
mkdir /etc/cms
for f in cms.conf cms-paste.ini ; do
    cp $f /etc/cms
done 

# create cms database
su gaussdba -c "cd;/opt/gaussdb/app/bin/gsql -W FusionSphere123  POSTGRES -c 'CREATE DATABASE cms OWNER openstack;' "

# create cms db tables
python ./cms-manage --config-file=/etc/cms/cms.conf db sync

