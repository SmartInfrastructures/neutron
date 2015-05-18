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

from neutron.common import constants
from neutron.common import exceptions
from neutron.db import model_base
from neutron.db import models_v2
from neutron.extensions import qos as ext_qos

from neutron.context import Context

import sqlalchemy as sa
from sqlalchemy import orm

import webob.exc

# list_avaible_policy = [constants.TYPE_QOS_BURST_RATE, constants.TYPE_QOS_DSCP,
#                        constants.TYPE_QOS_EGRESS_RATE, constants.TYPE_QOS_INGRESS_RATE]

list_avaible_policy = [constants.TYPE_QOS_DSCP,
                       constants.TYPE_QOS_EGRESS_RATE, constants.TYPE_QOS_INGRESS_RATE]


class QoSError(exceptions.NeutronException):
    message = _("Error in QOS: %(reason)s")
     
class QoSNotFound(exceptions.NotFound):
    message = _("QoS %(qos_id)s could not be found")


class QoSPortMappingNotFound(exceptions.NotFound):
    message = _("QoS mapping for port %(port_id)s"
                "and QoS %(qos_id)s could not be found")


class QoSNetworkMappingNotFound(exceptions.NotFound):
    message = _("QoS mapping for network %(net_id)s"
                "and QoS %(qos_id)s could not be found")
    
class AssociationNotPossible(exceptions.NotFound):
    message = _("QoS %(qos_id)s could not be associate because it is public")
    
def _convert_true_false(value):
    if value.encode('UTF-8').lower() == 'true':
        return 1    
    return 0


class QoS(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    __tablename__ = 'qoses'
    type = sa.Column(sa.Enum(constants.TYPE_QOS_DSCP,
                             constants.TYPE_QOS_RATELIMIT, name='qos_types'))
    description = sa.Column(sa.String(255), nullable=False)
    policies = orm.relationship('QoSPolicy',
                                cascade='all, delete, delete-orphan')
    ports = orm.relationship('PortQoSMapping',
                             cascade='all, delete, delete-orphan')
    networks = orm.relationship('NetworkQoSMapping',
                                cascade='all, delete, delete-orphan')
    
class QoSCN(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    __tablename__ = 'qos_main'
    name = sa.Column(sa.String(255), nullable=False)
    default = sa.Column(sa.Boolean, nullable=False)
    shared = sa.Column(sa.Boolean, nullable=False)
    description = sa.Column(sa.String(255), nullable=True)
    policies = orm.relationship('PolicyCN',
                                cascade='all, delete, delete-orphan')
    public = sa.Column(sa.Boolean, nullable=False)
    #mapping = orm.relationship('PolicyCN',
    #                            cascade='all, delete, delete-orphan')
    

class PolicyCN(model_base.BASEV2, models_v2.HasId):#, models_v2.HasTenant):
    __tablename__ = 'qos_policy'
    qos_id = sa.Column(sa.String(36),
                       sa.ForeignKey('qos_main.id', ondelete='CASCADE'),
                       nullable=False,
                       primary_key=True)
    dscp = sa.Column(sa.Integer, nullable=False)
    ingress_rate = sa.Column(sa.Integer, nullable=False)
    egress_rate = sa.Column(sa.Integer, nullable=False)
    burst_percent = sa.Column(sa.FLOAT(1,1), nullable=False)

# Association between port and qos
class QosMappingCN(model_base.BASEV2):#, models_v2.HasId):
    __tablename__ = 'qos_mapping'
    qos_id = sa.Column(sa.String(36), sa.ForeignKey('qos_main.id',
                       ondelete='CASCADE'), nullable=False, primary_key=True)
    port_id = sa.Column(sa.String(36), sa.ForeignKey('ports.id',
                       ondelete='CASCADE'), nullable=False, primary_key=True)

# Association between tenant and qos
class TenantAccessMappingCN(model_base.BASEV2, models_v2.HasTenant, models_v2.HasId):
    __tablename__ = "qos_tenant_access"
    qos_id = sa.Column(sa.String(36), sa.ForeignKey('qos_main.id',
                       ondelete='CASCADE'), nullable=False)
    shared = sa.Column(sa.Boolean, nullable=False)


class QoSPolicy(model_base.BASEV2, models_v2.HasId):
    __tablename__ = 'qos_policies'
    qos_id = sa.Column(sa.String(36),
                       sa.ForeignKey('qoses.id', ondelete='CASCADE'),
                       nullable=False,
                       primary_key=True)
    key = sa.Column(sa.String(255), nullable=False,
                    primary_key=True)
    value = sa.Column(sa.String(255), nullable=False)


class NetworkQoSMapping(model_base.BASEV2):
    network_id = sa.Column(sa.String(36), sa.ForeignKey('networks.id',
                           ondelete='CASCADE'), nullable=False,
                           primary_key=True)
    qos_id = sa.Column(sa.String(36), sa.ForeignKey('qoses.id',
                       ondelete='CASCADE'), nullable=False, primary_key=True)


class PortQoSMapping(model_base.BASEV2):
    port_id = sa.Column(sa.String(36), sa.ForeignKey('ports.id',
                        ondelete='CASCADE'), nullable=False, primary_key=True)
    qos_id = sa.Column(sa.String(36), sa.ForeignKey('qoses.id',
                       ondelete='CASCADE'), nullable=False, primary_key=True)


class QoSDbMixin(ext_qos.QoSPluginBase, object):
    
    # return list of avaible qoses for given tenant
    def _list_qos_for_tenant(self, context, tenant_id=None):
        qoses = []
        if tenant_id == None:
            tenant_id = context.tenant_id
        
        if context.is_admin:
            qos_query =  self._model_query(context, QoSCN)
            for qos in qos_query:
                qoses.append(qos["id"])
            return qoses
        
        #Public qos
        public_qos = self._model_query(context, QoSCN).filter(QoSCN.public == 1)
        for qos in public_qos:
            qoses.append(qos["id"])
        
        #Qos Mapped in TenantAccessMappingCN
        private_qos = self._model_query(context, TenantAccessMappingCN).filter(TenantAccessMappingCN.tenant_id == tenant_id )
        for qos in private_qos:
            if qos not in qoses:
                qoses.append(qos["qos_id"])

        return qoses
    
    # return True if default is not present
    # return False if default is already present
    def _is_default_present(self, default, context):
        try:
            query = self._model_query(context, QoSCN)
            db = query.filter(QoSCN.default == 1).one()
        except:
            return False
        
        return True
        
    def _create_qos_dict(self, qos, fields=None):
        res = {'id': qos['id'],
               'tenant_id': qos['tenant_id'],
               'type': qos['type'],
               'description': qos['description'],
               'policies': {}}
        for item in qos.policies:
            res['policies'][item['key']] = item['value']
        return self._fields(res, fields)
    
    def _create_qos_cn_dict(self, qos, fields=None):
        res = {'id': qos['id'],
               'tenant_id': qos['tenant_id'],
               'description': qos['description'],
               'default': qos['default'],
               'shared': qos['shared'],
               'name':qos['name'],
               'policies': {}
               }
        for item in qos.policies:
            for pol in list_avaible_policy:
                res['policies'][pol] = item[pol]
        return self._fields(res, fields)
    
    def _create_qos_tenant_mapping(self, item, fields=None):
        res = {
               'tenant_id': item['tenant_id'],
               'qos_id': item['qos_id'],
               }
        return self._fields(res, fields)
    
    def _update_qos_rule(self, context, id, qos):
        pass
    
    def _associate_qos(self):
        pass
    
    def _disassociate_qos(self):
        pass

    def _db_delete(self, context, item):
        with context.session.begin(subtransactions=True):
            context.session.delete(item)
        
    def create_qos(self, context, qos):
        if not context.is_admin:
            raise exceptions.AdminRequired(reason=_("Only admin can create and modify qos"))
            return {}
        
        if self._is_default_present( _convert_true_false(qos['qos']['default'] ), context ) and _convert_true_false(qos['qos']['default']):
            raise ext_qos.QoSDefaultValue
            return {}
                               
        if 'policies' not in qos['qos']:
            raise ext_qos.QoSValidationError()
        else:
            self.validate_qos(qos['qos']['policies'])

        tenant_id = self._get_tenant_id_for_create(context, qos)

        with context.session.begin(subtransactions=True):
            qos_db_item = QoSCN( description = qos['qos']['description'],
                                 name = qos['qos']['name'],
                                 default = _convert_true_false(qos['qos']['default']),
                                 shared = 1,
                                 tenant_id=context.tenant_id,
                                 public = 1 if _convert_true_false(qos['qos']['default']) else _convert_true_false(qos['qos']['public'])
                                 )
            if constants.TYPE_QOS_DSCP in qos['qos']['policies']:
                _dscp = qos['qos']['policies'][constants.TYPE_QOS_DSCP]
            else:
                _dscp = 0
            if constants.TYPE_QOS_EGRESS_RATE in qos['qos']['policies']:
                _egress_rate = qos['qos']['policies'][constants.TYPE_QOS_EGRESS_RATE]
            else:
                _egress_rate = 0
            if constants.TYPE_QOS_INGRESS_RATE in qos['qos']['policies']:
                _ingress_rate = qos['qos']['policies'][constants.TYPE_QOS_INGRESS_RATE]
            else:
                _ingress_rate = 0
            if constants.TYPE_QOS_BURST_RATE in qos['qos']['policies']:
                _burst_percent = qos['qos']['policies'][constants.TYPE_QOS_BURST_RATE]
            else:
                _burst_percent = 0.2
                            
            policy_db_item = PolicyCN(qos_id = qos_db_item.id,
                                      dscp = _dscp, egress_rate = _egress_rate, 
                                      ingress_rate = _ingress_rate, burst_percent = _burst_percent)

            qos_db_item.policies.append(policy_db_item)
            context.session.add(qos_db_item)
            
        #return self._create_qos_dict(qos_db_item)
        return self._create_qos_cn_dict(qos_db_item)

    
    def update_qos(self, context, id, qos):
        if not context.is_admin:
            raise exceptions.AdminRequired(reason=_("Only admin can create and modify qos"))
            return {}
        try:
            tenant = qos['qos']['tenant']
            # Check if tenant exist
            query = self._model_query(context, TenantAccessMappingCN)
            db_tenant_access = query.filter(TenantAccessMappingCN.qos_id == id, TenantAccessMappingCN.tenant_id == tenant)
            
            if qos['qos']['association'] == "associate":
                # Add qos to tenant_access table if the relation is not present
                # and if qos rule is not public.
                public = True
                try:
                    self._model_query(context, QoSCN).filter(QoSCN.public == 0, QoSCN.id == id)[0]
                    public = False
                except Exception:
                    public = True
                
                if db_tenant_access.count() == 0 and not public:
                    with context.session.begin(subtransactions=True):
                        qos_associate_item = TenantAccessMappingCN(qos_id = id, tenant_id = tenant, shared = True)
                        context.session.add(qos_associate_item)
                    return self._create_qos_tenant_mapping(qos_associate_item)
                else:
                    raise exceptions.AdminRequired(reason=_("Cambia messaggio di errore"))
                    return {}
            elif qos['qos']['association'] == "disassociate":
                with context.session.begin(subtransactions=True):
                    context.session.delete(db_tenant_access[0])
                return {'message':"Correctly removed"}
            else:
                raise QoSError(reason=_("Malformed request"))
        except Exception:
            pass
        
        main_arg = {}
        main_arg_policies = {}
        if 'public' in qos['qos']:
            main_arg['public'] = _convert_true_false(qos['qos']['public'])
        if 'default' in qos['qos']:
            main_arg['default'] = _convert_true_false(qos['qos']['default'])
        if 'description' in qos['qos']:
            main_arg['description'] = qos['qos']['description']
            
        if constants.TYPE_QOS_DSCP in qos['qos']['policies']:
            main_arg_policies[constants.TYPE_QOS_DSCP] = qos['qos']['policies'][constants.TYPE_QOS_DSCP]
            
        if constants.TYPE_QOS_EGRESS_RATE in qos['qos']['policies']:
            main_arg_policies[constants.TYPE_QOS_EGRESS_RATE] = qos['qos']['policies'][constants.TYPE_QOS_EGRESS_RATE]
            
        if constants.TYPE_QOS_INGRESS_RATE in qos['qos']['policies']:
            main_arg_policies[constants.TYPE_QOS_INGRESS_RATE] = qos['qos']['policies'][constants.TYPE_QOS_INGRESS_RATE]
            
        try:
            
            db = self._model_query(context, QoSCN).filter(QoSCN.id == id)
            db.update(main_arg)
            
            if main_arg_policies:
                db = self._model_query(context, PolicyCN).filter(PolicyCN.qos_id == id)
                db.update(main_arg_policies)
        except Exception:
            pass
        
#         db = self._get_by_id(context, QoSCN, id)
#         with context.session.begin(subtransactions=True):
#             db.policies = []
#             for k, v in qos['qos']['policies'].iteritems():
#                 db.policies.append(
#                     QoSPolicy(qos_id=db, key=k, value=v))
#             del qos['qos']['policies']
#             db.update(qos)
        db_item = self._get_by_id(context, QoSCN, id)
        return self._create_qos_cn_dict(db_item)

    def create_qos_for_network(self, context, qos_id, network_id):
        with context.session.begin(subtransactions=True):
            db = NetworkQoSMapping(qos_id=qos_id, network_id=network_id)
            context.session.add(db)
        return db.qos_id

    def create_qos_for_port(self, context, qos_id, port_id):
        if qos_id not in self._list_qos_for_tenant(context):
            msg = _("Error: Impossible to assign qos=%s to port=%s") % (qos_id, port_id)
            raise webob.exc.HTTPBadRequest(msg)
            return None
        try:
            query = self._model_query(context, QosMappingCN)
            db = query.filter(QosMappingCN.port_id == port_id).one()
        except: # add new mapping
            with context.session.begin(subtransactions=True):
                db = QosMappingCN(qos_id=qos_id, port_id=port_id)
                context.session.add(db)
                return db.qos_id
        
        qos_to_update = {'qos_id': qos_id}
        db.update(qos_to_update)
        return db.qos_id

    def delete_qos(self, context, id):
        try:
            self._db_delete(context, self._get_by_id(context, QoSCN, id))
        except orm.exc.NotFound:
            raise QoSNotFound()

    def delete_qos_for_network(self, context, network_id):
        try:
            self._db_delete(context,
                            self._model_query(context,
                                              NetworkQoSMapping)
                            .filter_by(network_id=network_id).one())
        except orm.exc.NoResultFound:
            raise exceptions.NotFound

    def delete_qos_for_port(self, context, port_id):
        try:
            self._db_delete(context,
                            self._model_query(context, PortQoSMapping)
                            .filter_by(port_id=port_id).one())
        except orm.exc.NoResultFound:
            raise QoSPortMappingNotFound()

    def get_mapping_for_network(self, context, network_id):
        try:
            with context.session.begin(subtransactions=True):
                return self._model_query(context, NetworkQoSMapping).filter_by(
                    network_id=network_id).all()
        except orm.exc.NotFound:
            raise QoSNetworkMappingNotFound()

    def get_mapping_for_port(self, context, port_id):
        try:
            with context.session.begin(subtransactions=True):
                return self._model_query(context, PortQoSMapping).filter_by(
                    port_id=port_id).all()
        except orm.exc.NotFound:
            raise QoSPortMappingNotFound()

    def get_qos(self, context, id, fields=None):
        try:
            query = self._model_query(context, QoSCN).filter(QoSCN.id == id)[0]
            return self._create_qos_cn_dict(query, fields)
        except Exception:
            raise QoSNotFound()
        
    def get_default_policy(self, context):
        try:
            query = self._model_query(context, QoSCN).filter(QoSCN.default == 1)[0]
            return self._create_qos_cn_dict(query, None)
        except Exception:
            raise QoSNotFound()

    def get_qoses(self, context, filters=None, fields=None,
                  sorts=None, limit=None,
                  marker=None, page_reverse=False, default_sg=False):
        marker_obj = self._get_marker_obj(context, 'qos', limit, marker)
        
        if not context.is_admin:
            #1 filter: public=1
            filters["public"] = [1]
            public_qos = self._get_collection(context,
                                    QoSCN,
                                    self._create_qos_cn_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)
            del filters["public"]
            
            #2filter: qos_id in TenantAccessMappingCN (qos_tenant_access)
            db_tenant_access = self._model_query(context, TenantAccessMappingCN).filter(TenantAccessMappingCN.tenant_id == context.tenant_id )
            filters["public"] = [0]
            if "id" not in filters:
                filters["id"] = []
                for i in db_tenant_access:
                    filters["id"].append( str(i.get("qos_id")) )
            private_qos = self._get_collection(context,
                                    QoSCN,
                                    self._create_qos_cn_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)
                
            return (private_qos + public_qos)
        else:
            return self._get_collection(context,
                                    QoSCN,
                                    self._create_qos_cn_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit, marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def get_qosassociates(self, context, filters=None, fields=None,
                  sorts=None, limit=None, marker=None,
                  page_reverse=False):
        marker_obj = self._get_marker_obj(context, 'qosassociate', limit, marker)
        
        if not context.is_admin:
            raise exceptions.AdminRequired(reason=_("Only admin can get qos-tenant-list"))
            return {}
        
        return self._get_collection(context,
                        TenantAccessMappingCN,
                        self._create_qos_tenant_mapping,
                        filters=filters, fields=fields,
                        sorts=sorts,
                        limit=limit, marker_obj=marker_obj,
                        page_reverse=page_reverse)

    def update_mapping_for_network(self, context, mapping):
        db = self.get_mapping_for_network(context, mapping.network_id)[0]
        with context.session.begin(subtransactions=True):
            db.update(mapping)

    def update_mapping_for_port(self, context, mapping):
        db = self.get_mapping_for_port(context, mapping.port_id)[0]
        with context.session.begin(subtransactions=True):
            db.update(mapping)

    def validate_qos(self, policy):
        for type in policy:
            try:
                validator = getattr(self, 'validate_policy_' + type)
                validator(policy[type])
            except AttributeError:
                raise Exception(_('No validator found for type: %s') % type)
        

    def validate_policy_dscp(self, dscp):
        try:
            dscp = int(dscp)
        except:
            raise ext_qos.QoSValidationError() 
        if dscp>255 or dscp<1:
            raise ext_qos.QoSValidationError() 
        if dscp % 4 != 0:
            raise ext_qos.QoSValidationError()
        
    def validate_policy_ingress_rate(self, ingressrate):
        if ingressrate <50:
            raise ext_qos.QoSValidationError()
        
    def validate_policy_egress_rate(self, egressrate):
        if egressrate <50:
            raise ext_qos.QoSValidationError()
    
    def validate_policy_burst_percent(self, burst_percent):
        if float(burst_percent) > 1 or float(burst_percent) < 0:
            raise ext_qos.QoSValidationError()