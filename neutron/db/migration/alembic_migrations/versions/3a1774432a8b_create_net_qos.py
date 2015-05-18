# Copyright 2015 OpenStack Foundation
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

"""create net QoS

Revision ID: 3a1774432a8b
Revises: kilo
Create Date: 2015-05-15 14:01:02.861701

"""

# revision identifiers, used by Alembic.
revision = '3a1774432a8b'
down_revision = 'kilo'

from alembic import op
import sqlalchemy as sa
from neutron.common import constants



def upgrade():
    op.create_table(
        'qos_main',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('shared', sa.Boolean, nullable=False),
        sa.Column('public', sa.Boolean, nullable=False),
        sa.Column('default', sa.Boolean, nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
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
        sa.Column('port_id', sa.String(length=255)),
        sa.Column('qos_id', sa.String(length=255)),
        sa.ForeignKeyConstraint(['qos_id'], ['qos_main.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['port_id'],['ports.id'], ondelete='CASCADE'),
                    )
    
    op.create_table(
        'qos_tenant_access',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('qos_id', sa.String(length=255)),
        sa.Column('tenant_id', sa.String(length=255)),
        sa.Column('shared', sa.Boolean),
        sa.ForeignKeyConstraint(['qos_id'], ['qos_main.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
                    )

    pass

def downgrade(active_plugins=None, options=None):
    
    op.drop_table('qos_main')
    op.drop_table('qos_policy')
    op.drop_table('qos_mapping')

    pass