# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from migrate.changeset import UniqueConstraint
from migrate import ForeignKeyConstraint
from sqlalchemy import Boolean, BigInteger, Column, DateTime, Enum
from sqlalchemy import ForeignKey, Index, Integer, MetaData, String, Table
from sqlalchemy import Text
from sqlalchemy.types import NullType

from cms.i18n import _
from cms.common import log as logging

LOG = logging.getLogger(__name__)


# Note on the autoincrement flag: this is defaulted for primary key columns
# of integral type, so is no longer set explicitly in such cases.

def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    clouds = Table('clouds', meta,
        
        # common
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Integer),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(length=36), nullable=False),
        Column('availability_zone', String(length=255), nullable=False),
        Column('region', String(length=255), nullable=False),
        Column('cloud_type', String(length=30), nullable=False),

        # vpninfo (openstack, vcloud)
        Column('public_ip', String(length=16), nullable=True),
        Column('api_ip', String(length=16), nullable=True),
        Column('api_subnet', String(length=16), nullable=True),
        Column('data_ip', String(length=16), nullable=True),
        Column('data_subnet', String(length=16), nullable=True),

        # openstack
        Column('domainname', String(length=255), nullable=True),

        # vcloud
        Column('org', String(length=255), nullable=True),
        Column('vdc', String(length=255), nullable=True),
        Column('username', String(length=255), nullable=True),
        Column('password', String(length=255), nullable=True),
        Column('external_id', String(length=255), nullable=True),

        # aws
        Column('aws_availabilityzone', String(length=255), nullable=True),
        Column('accesskey', String(length=255), nullable=True),
        Column('secretkey', String(length=255), nullable=True),

        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )


    clouds.create()
    Index('uuid', clouds.c.uuid, unique=True).create()
    # Common indexes (indexes we apply to all databases)
    # NOTE: order specific for MySQL diff support
    common_indexes = [ ]

    MYSQL_INDEX_SKIPS = [
        # we create this one manually for MySQL above
    ]

    for index in common_indexes:
        if migrate_engine.name == 'postgresql' and \
            index.name in POSTGRES_INDEX_SKIPS:
            continue
        if migrate_engine.name == 'mysql' and \
            index.name in MYSQL_INDEX_SKIPS:
            continue
        else:
            index.create(migrate_engine)

    if migrate_engine.name == 'mysql':
        # In Folsom we explicitly converted migrate_version to UTF8.
        migrate_engine.execute(
            'ALTER TABLE migrate_version CONVERT TO CHARACTER SET utf8')
        # Set default DB charset to UTF8.
        migrate_engine.execute(
            'ALTER DATABASE %s DEFAULT CHARACTER SET utf8' %
            migrate_engine.url.database)



def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    for table in ('clouds', ):
        for prefix in ('', 'shadow_'):
            table_name = prefix + table
            if migrate_engine.has_table(table_name):
                instance_extra = Table(table_name, meta, autoload=True)
                instance_extra.drop()
