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

# This is a placeholder for Havana backports.
# Do not use this number for new Icehouse work.  New Icehouse work starts after
# all the placeholders.
#
# See blueprint backportable-db-migrations-icehouse
# http://lists.openstack.org/pipermail/openstack-dev/2013-March/006827.html


def _create_shadow_tables(migrate_engine):
    meta = MetaData(migrate_engine)
    meta.reflect(migrate_engine)
    table_names = meta.tables.keys()

    meta.bind = migrate_engine

    for table_name in table_names:
        table = Table(table_name, meta, autoload=True)

        columns = []
        for column in table.columns:
            column_copy = None
            # NOTE(boris-42): BigInteger is not supported by sqlite, so
            #                 after copy it will have NullType, other
            #                 types that are used in Nova are supported by
            #                 sqlite.
            if isinstance(column.type, NullType):
                column_copy = Column(column.name, BigInteger(), default=0)
            if table_name == 'instances' and column.name == 'locked_by':
                enum = Enum('owner', 'admin',
                            name='instances0locked_by'.upper())
                column_copy = Column(column.name, enum)
            else:
                column_copy = column.copy()
            columns.append(column_copy)

        shadow_table_name = 'shadow_' + table_name
        shadow_table = Table(shadow_table_name, meta, *columns,
                             mysql_engine='InnoDB')
        try:
            shadow_table.create(checkfirst=True)
        except Exception:
            LOG.info(repr(shadow_table))
            LOG.exception(_('Exception while creating table.'))
            raise

def upgrade(migrate_engine):
    _create_shadow_tables(migrate_engine)


def downgrade(migration_engine):
    pass
