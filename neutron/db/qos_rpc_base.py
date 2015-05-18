# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
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
# @author: Daniel Depaoli <daniel.depaoli(at)create-net.org>

from neutron.db import qos_db


class QoSServerRpcMixin(qos_db.QoSDbMixin):

    def _process_create_qos_for_network(self, context, qos_id, network_id):
        super(QoSServerRpcMixin, self).create_qos_for_network(
            context, qos_id, network_id)
        self.notifier.network_qos_updated(context, qos_id, network_id)

    def _process_create_qos_for_port(self, context, qos_id, port_id):
        super(QoSServerRpcMixin, self).create_qos_for_port(
            context, qos_id, port_id)
        self.notifier.port_qos_updated(context, qos_id, port_id)

    def _process_delete_qos_for_network(self, context, qos_id, network_id):
        super(QoSServerRpcMixin, self).delete_qos_for_network(
            context, network_id)
        self.notifier.network_qos_deleted(context, qos_id, network_id)

    def _process_delete_qos_for_port(self, context, qos_id, port_id):
        super(QoSServerRpcMixin, self).delete_qos_for_port(
            context, port_id)
        self.notifier.port_qos_deleted(context, qos_id, port_id)

    def _process_update_mapping_for_network(self, context, mapping):
        super(QoSServerRpcMixin, self).update_mapping_for_network(
            context, mapping)
        self.notifier.network_qos_updated(context,
                                          mapping.qos_id,
                                          mapping.network_id)

    def _process_update_mapping_for_port(self, context, mapping):
        super(QoSServerRpcMixin, self).update_mapping_for_port(
            context, mapping)
        self.notifier.port_qos_updated(context,
                                       mapping.qos_id,
                                       mapping.port_id)


class QoSServerRpcCallbackMixin(object):

    def get_policy_for_qos(self, context, **kwargs):
        result = {}
        qos_id = kwargs.get('qos_id')
        query = context.session.query(qos_db.QoS)
        query.filter(qos_db.QoS.id.in_(qos_id))
        for policy in query.one().policies:
            result[policy['key']] = policy['value']
        return result