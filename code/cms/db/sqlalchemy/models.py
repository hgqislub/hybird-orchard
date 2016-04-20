# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
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
"""
SQLAlchemy models for cms data.
"""

from oslo.config import cfg
from oslo.db.sqlalchemy import models
from sqlalchemy import Column, Index, Integer, BigInteger, Enum, String, schema
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float

from cms.db.sqlalchemy import types
from cms.common import timeutils

BASE = declarative_base()


def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')


class CMSBase(models.SoftDeleteMixin,
               models.TimestampMixin,
               models.ModelBase):
    metadata = None

    # TODO(ekudryashova): remove this after both cms and oslo.db
    # will use oslo.utils library
    # NOTE: Both projects(cms and oslo.db) use `timeutils.utcnow`, which
    # returns specified time(if override_time is set). Time overriding is
    # only used by unit tests, but in a lot of places, temporarily overriding
    # this columns helps to avoid lots of calls of timeutils.set_override
    # from different places in unit tests.
    created_at = Column(DateTime, default=lambda: timeutils.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: timeutils.utcnow())

    def save(self, session=None):
        from cms.db.sqlalchemy import api

        if session is None:
            session = api.get_session()

        super(CMSBase, self).save(session=session)


class Cloud(BASE, CMSBase):
    """Represents a cloud."""
    __tablename__ = "clouds"
    __table_args__ = (
        # Index('uuid', 'uuid', unique=True), 
        # schema.UniqueConstraint("region", "name", "deleted", name="uniq_cloud0name0region0deleted"), 
    )

    # common
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    availability_zone = Column(String(255), nullable=False)
    region = Column(String(255), nullable=False)
    cloud_type = Column(String(30), nullable=False) # "openstack", "aws", "vcloud"

    # vpninfo (openstack, vcloud)
    public_ip = Column(String(16))
    api_ip = Column(String(16))
    api_subnet = Column(String(26))
    data_ip = Column(String(16))
    data_subnet = Column(String(26))

    # openstack
    domainname = Column(String(255))

    # vcloud
    org = Column(String(255))
    vdc = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    external_id = Column(String(255))

    # aws
    aws_availabilityzone = Column(String(255))
    accesskey = Column(String(255))
    secretkey = Column(String(255))
