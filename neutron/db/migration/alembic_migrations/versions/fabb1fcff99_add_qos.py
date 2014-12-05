# Copyright 2014 OpenStack Foundation
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
#

"""add QOS

Revision ID: fabb1fcff99
Revises: icehouse
Create Date: 2014-11-17 14:21:35.425096

"""

# revision identifiers, used by Alembic.
revision = 'fabb1fcff99'
down_revision = 'icehouse'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.plugins.ryu.ryu_neutron_plugin.RyuNeutronPluginV2'
]

from alembic import op
import sqlalchemy as sa
from neutron.common import constants

from neutron.db import migration


def upgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return
    
    op.create_table(
        'qos_main',
        sa.Column('id', sa.String(length=36), primary_key=True),
        #sa.Column('policy_id', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('visible', sa.Boolean, nullable=False),
        sa.Column('default', sa.Boolean, nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        #sa.ForeignKeyConstraint(['policy_id'], ['qos_policy.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_table(
        'qos_policy',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column(constants.TYPE_QOS_DSCP, sa.Integer, nullable=False),
        sa.Column(constants.TYPE_QOS_INGRESS_RATE, sa.Integer, nullable=False),
        sa.Column(constants.TYPE_QOS_EGRESS_RATE, sa.Integer, nullable=False),
        sa.Column(constants.TYPE_QOS_BURST_RATE, sa.FLOAT(1,1), nullable=False),
        sa.Column('qos_id', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['qos_id'], ['qos_main.id'], ondelete='CASCADE'),
    )
        
    op.create_table(
        'qos_mapping',
#        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('port_id', sa.String(length=255)),
        sa.Column('qos_id', sa.String(length=255)),
        #sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['qos_id'], ['qos_main.id']),
        sa.ForeignKeyConstraint(['port_id'],['ports.id']),
                    )
    
    op.create_table(
        'qos_tenant_access',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('qos_id', sa.String(length=255)),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['qos_id'], ['qos_main.id']),
                    )

    pass


def downgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return
    
    op.drop_table('qos_main')
    op.drop_table('qos_policy')
    op.drop_table('qos_mapping')

    pass
