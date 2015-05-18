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

import abc

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron.common import constants
from neutron.common import exceptions as qexception
from neutron import manager

import six


RESOURCE_ATTRIBUTE_MAP = {
    'qos': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'policies': {'allow_post': True, 'allow_put': True,
                     'is_visible': True, 'default': '',
                     'validate': {'type:dict': None}},
        'description': {'allow_post': True, 'allow_put': True,
                        'is_visible': True, 'default': '',
                        'validate': {'type:string': None}},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'is_visible': True},
        
        'default': {'allow_post': True, 'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True},
            
        'public': {'allow_post': True, 'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True},
        
        'name': {'allow_post': True, 'allow_put': True,
               'is_visible': True},
        
        'tenant': {'allow_post': False, 'allow_put': True,
                   #'validate': {'type:uuid': None},
                   'default': ''},
        'association': {'allow_post': False, 'allow_put': True,
                   #'validate': {'type:value': ["associate", "disassociate"]},
                   'validate': {'type:string': None},
                   'default': ''},
    },
                          
    'qosassociate':{
        'associate': {'allow_post': True, 'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True},
        'qos_id': {'allow_post': True, 'allow_put': True,
               'validate': {'type:string': None},
               'is_visible': True},
        'tenant_id': {'allow_post': False, 'allow_put': False,
              'required_by_policy': True,
              'is_visible': True},
                     },
}

QOS = "qos"

EXTENDED_ATTRIBUTES_2_0 = {
    'ports': {QOS: {'allow_post': True,
                    'allow_put': True,
                    'is_visible': True,
                    'default': None,
                    'validate': {'type:uuid_or_none': None}}},
    'networks': {QOS: {'allow_post': True,
                       'allow_put': True,
                       'is_visible': True,
                       'default': None,
                       'validate': {'type:uuid_or_none': None}}},
}


class QoSValidationError(qexception.InvalidInput):
    message = _("Invalid QoS Policy")

class QoSDefaultValue(qexception.Conflict):
    message = _("Default already present. Impossible to add another default")


class Qos(extensions.ExtensionDescriptor):
    """Quality of Service extension."""

    @classmethod
    def get_name(cls):
        return "quality-of-service"

    @classmethod
    def get_alias(cls):
        return "quality-of-service"

    @classmethod
    def get_description(cls):
        return "The quality of service extension"

    @classmethod
    def get_namespace(cls):
        #TODO(scollins)
        pass

    def get_updated(cls):
        #TODO(scollins)
        pass

    @classmethod
    def get_resources(cls):
        #TODO(scollins)
        my_plurals = [(key + 'es', key) for key in
                      RESOURCE_ATTRIBUTE_MAP.keys()]
        attr.PLURALS.update(dict(my_plurals))
        exts = []
        plugin = manager.NeutronManager.get_plugin()
        params = RESOURCE_ATTRIBUTE_MAP.get("qos", dict())
        controller = base.create_resource("qoses",
                                          "qos",
                                          plugin, params, allow_bulk=True,
                                          allow_pagination=True,
                                          allow_sorting=True)
        ex = extensions.ResourceExtension("qoses",
                                          controller,
                                          attr_map=params)
        exts.append(ex)
        ###
        paramsTenantAccess = RESOURCE_ATTRIBUTE_MAP.get("qosassociate", dict())
        controllerTenantAccess = base.create_resource("qosassociates",
                                          "qosassociate",
                                          plugin, paramsTenantAccess, allow_bulk=True,
                                          allow_pagination=True,
                                          allow_sorting=True)
        exTenantAccess = extensions.ResourceExtension("qosassociates",
                                                      controllerTenantAccess,
                                                      attr_map=paramsTenantAccess)
        exts.append(exTenantAccess)
        
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return dict(EXTENDED_ATTRIBUTES_2_0.items() +
                        RESOURCE_ATTRIBUTE_MAP.items())
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class QoSPluginBase(object):

    @abc.abstractmethod
    def get_qoses(self, context, filters=None, fields=None,
                  sorts=None, limit=None, marker=None,
                  page_reverse=False):
        pass

    @abc.abstractmethod
    def create_qos(self, context, qos):
        pass

    @abc.abstractmethod
    def delete_qos(self, context, id):
        pass

    @abc.abstractmethod
    def update_qos(self, context, id, qos):
        pass

    @abc.abstractmethod
    def create_qos_for_network(self, context, qos_id, network_id):
        pass

    @abc.abstractmethod
    def delete_qos_for_network(self, context, network_id):
        pass

    @abc.abstractmethod
    def create_qos_for_port(self, context, qos_id, port_id):
        pass

    @abc.abstractmethod
    def delete_qos_for_port(self, context, port_id):
        pass

    @abc.abstractmethod
    def validate_qos(self, context, qos):
        pass
    
    @abc.abstractmethod
    def get_qosassociates(self, context, filters=None, fields=None,
                  sorts=None, limit=None, marker=None,
                  page_reverse=False):
        pass