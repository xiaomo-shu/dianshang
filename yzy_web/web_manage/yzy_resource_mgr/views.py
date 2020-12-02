import logging
import threading
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from collections import defaultdict
from django.utils.encoding import escape_uri_path
from django.http import Http404, FileResponse, HttpResponseServerError

from .serializers import *
from web_manage.common.utils import JSONResponse, YzyWebPagination, get_error_result
from web_manage.common.http import server_post
from web_manage.common.general_query import GeneralQuery
from web_manage.common import constants
from web_manage.yzy_edu_desktop_mgr.serializers import NodeTemplateSerializer
from web_manage.yzy_edu_desktop_mgr import models as education_model
from .resource_manager.resource_pool_manager import resource_pool_mgr
from .resource_manager.node_manager import node_mgr
from .resource_manager.base_image_manager import base_image_mgr, iso_mgr
from .resource_manager.network_manager import network_mgr, subnet_mgr
from .resource_manager.virtual_switch_manager import virtual_switch_mgr
from .resource_manager.remote_storage_manager import remote_storage_mgr
from web_manage.yzy_system_mgr.models import YzyTask
from web_manage.common.utils import create_uuid


logger = logging.getLogger(__name__)


class Common(ViewSetMixin, APIView):
    def check_name_existence(self, request, *args, **kwargs):
        try:
            object_type = request.GET.get("object_type", None)
            object_name = request.GET.get("object_name", None)
            object_uuid = request.GET.get("object_uuid", None)
            network_uuid = request.GET.get("network_uuid", None)
            node_uuid = request.GET.get("node_uuid", None)
            if not (object_type and object_name):
                ret = get_error_result("ParamError")
                return JSONResponse(ret)
            if object_type == 'YzyNetworks':
                query_set = YzyNetworks.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzySubnets':
                query_set = YzySubnets.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
                if network_uuid:
                    network = YzyNetworks.objects.get(uuid=network_uuid)
                    query_set = query_set.filter(network=network.uuid)
            elif object_type == 'YzyISO':
                query_set = YzyISO.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzyResourcePools':
                query_set = YzyResourcePools.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzyNodes':
                query_set = YzyNodes.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzyVirtualSwitchs':
                query_set = YzyVirtualSwitchs.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzyBaseImages':
                query_set = YzyBaseImages.objects.filter(deleted=False, name=object_name)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            elif object_type == 'YzyBondNics':
                if not node_uuid:
                    return JSONResponse(get_error_result("ParamError"))
                query_set = YzyNodeNetworkInfo.objects.filter(deleted=False, nic=object_name, node=node_uuid)
                if object_uuid:
                    query_set = query_set.exclude(uuid=object_uuid)
            if len(query_set) > 0:
                return JSONResponse(get_error_result("NameAlreadyExistsError"))
            return JSONResponse(get_error_result("Success"))
        except Exception as e:
            return HttpResponseServerError()


class ControllerNode(ViewSetMixin, APIView):
    """
        控制节点管理
    """
    def list(self, request, *args, **kwargs):
        try:
            if request.GET.get("backup", None):
                type_list = [constants.ROLE_SLAVE_AND_COMPUTE, constants.ROLE_SLAVE]
            else:
                type_list = [constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER]

            page = YzyWebPagination()
            query_set = YzyNodes.objects.filter(deleted=False,
                                                type__in=type_list)
            controller_nodes = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyNodesSerializer(instance=controller_nodes, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            logger.exception("get controller node info failed:%s", e)
            return HttpResponseServerError()

    def reboot(self, request, *args, **kwargs):
        node = request.data.get("node")
        ret = node_mgr.reboot_controller_node(node)
        return JSONResponse(ret)

    def shutdown(self, request, *args, **kwargs):
        node = request.data.get("node")
        compute_node = request.data.get("compute_node", False)
        ret = node_mgr.shutdown_controller_node(node, compute_node)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        try:
            node_uuid = kwargs.get("node_uuid")
            ret = node_mgr.update_node(request.data, node_uuid)
            return JSONResponse(ret)
        except Exception as identifier:
            return HttpResponseServerError()


class ResourcePool(ViewSetMixin, APIView):
    """
        资源池管理
    """
    def list(self, request, *args, **kwargs):
        try:
            page = YzyWebPagination()
            query_set = YzyResourcePools.objects.filter(deleted=False)
            resource_pools = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyResourcePoolsSerializer(instance=resource_pools, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def storage_list(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, YzyResourcePools, YzyStoragesSerializer, query_dict)

    def update_storages(self, request, *args, **kwargs):
        """
        :param request:
            {
                1: "/opt/slow",
                2: "/opt/slow",
                3: "/opt/slow",
                4: "/opt/slow"
            }
        :param args:
        :param kwargs:
        :return:
        """
        try:
            data = request.data
            config = dict()
            storages = dict()
            if data.get('resource_pool_uuid'):
                config['resource_pool_uuid'] = data['resource_pool_uuid']
            if data.get('type') and int(data['type']): # 远端存储
                remote_storage = YzyRemoteStorage.objects.filter(deleted=False, uuid=data['remote_storage_uuid']).first()
                remote_storage.role = '1,2,3,4'
                remote_storage.save()
                storages[constants.NFS_MOUNT_POINT_PREFIX + remote_storage.name] = '1,2,3,4'
            else: # 本地存储
                if str(constants.TEMPLATE_SYS) not in data.keys() or str(constants.TEMPLATE_DATA) not in data.keys() \
                        or str(constants.INSTANCE_SYS) not in data.keys() or str(constants.INSTANCE_DATA) not in data.keys():
                    ret = get_error_result("StorageRoleMissing")
                    return JSONResponse(ret)
                storage_list = defaultdict(list)
                for k, v in data.items():
                    if k not in ['type', 'resource_pool_uuid']:
                        storage_list[v].append(k)
                for k, v in storage_list.items():
                    storages[k] = ",".join(v)
                if data.get('resource_pool_uuid'):
                    remote_storage = YzyRemoteStorage.objects.filter(deleted=False,
                                                                     allocated_to=data['resource_pool_uuid']).first()
                    remote_storage.role = None
                    remote_storage.save()
            config['storages'] = storages
            ret = server_post("/api/v1/resource_pool/storages", config)
            logger.info("update storages return:%s", ret)
            return JSONResponse(ret)
        except Exception as e:
            logger.exception("update storages error:%s", e)
            ret = get_error_result("OtherError")
            return JSONResponse(ret)

    def create(self, request, *args, **kwargs):
        ret = resource_pool_mgr.create_resource_pool(request, request.data)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        resource_pool = None
        try:
            resource_pool = YzyResourcePools.objects.get(uuid=resource_pool_uuid)
        except Exception as e:
            return JSONResponse(get_error_result("ResourcePoolNotExist"))
        ret = resource_pool_mgr.update_resource_pool(resource_pool, request.data)
        return JSONResponse(ret)

    def delete(self, request, *args, **kwargs):
        uuids = request.data.get("uuids")
        ret = resource_pool_mgr.delete_resource_pool(uuids)
        return JSONResponse(ret)


class Node(ViewSetMixin, APIView):
    """
        计算节点管理
    """
    def update_monitor_info(self, data):
        t = threading.Thread(target=server_post, args=("/api/v1/node/monitor_update", data,))
        t.start()
        return

    def list(self, request, *args, **kwargs):
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        try:
            data = {
                "pool_uuid": resource_pool_uuid
            }
            self.update_monitor_info(data)
            page = YzyWebPagination()
            query_set = YzyNodes.objects.filter(deleted=False, resource_pool=resource_pool_uuid, type__in=[1,2,5])
            nodes = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyNodesSerializer(instance=nodes, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            logger.error("get nodes error:%s", e, exc_info=True)
            return HttpResponseServerError()

    def detail_info(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        try:
            node = YzyNodes.objects.filter(deleted=False, uuid=node_uuid).get()
            ser = YzyNodesSerializer(instance=node, context={'request': request})
            return JSONResponse(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def check_password(self, request, *args, **kwargs):
        data = request.data
        ret = node_mgr.check_node_password(data)
        return JSONResponse(ret)

    def check(self, request, *args, **kwargs):
        data = request.data
        ret = node_mgr.check_node(data)
        return JSONResponse(ret)

    def create(self, request, *args, **kwargs):
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        data = request.data
        ret = node_mgr.add_node(resource_pool_uuid, data)
        return JSONResponse(ret)

    def reboot(self, request, *args, **kwargs):
        """
        {
            "nodes": [
                {"uuid": "xxxxx", "name": "xxx"},
                {"uuid": "xxxxx", "name": "xxx"},
                {"uuid": "xxxxx", "name": "xxx"}
            ]
        }
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        nodes = request.data.get("nodes")
        ret = node_mgr.reboot_node(nodes)
        return JSONResponse(ret)

    def shutdown(self, request, *args, **kwargs):
        nodes = request.data.get("nodes")
        ret = node_mgr.shutdown_node(nodes)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        try:
            node_uuid = kwargs.get("node_uuid")
            ret = node_mgr.update_node(request.data, node_uuid)
            return JSONResponse(ret)
        except Exception as identifier:
            return HttpResponseServerError()

    def delete(self, request, *args, **kwargs):
        uuids = request.data.get("uuids")
        ret = node_mgr.delete_node(uuids)
        return JSONResponse(ret)

    def storage_info(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        try:
            storages = YzyNodeStorages.objects.filter(node_uuid=node_uuid, deleted=False)
            parts = YzyNodeStorageSerializer(instance=storages, many=True, context={'request': request})
            return JSONResponse(parts)
        except Exception as e:
            return HttpResponseServerError()

    def sources(self, request, *args, **kwargs):
        try:
            nodes = YzyNodes.objects.filter(deleted=False)
            ser = YzyNodesSerializer(instance=nodes, many=True, context={'request': request})
            return JSONResponse(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def check_node_ip(self, request, *args, **kwargs):
        try:
            ip = request.GET.get('ip', None)
            if ip:
                node_count = YzyNodes.objects.filter(deleted=False, ip=ip).exclude(type=3).count()
                if node_count > 1:
                    return JSONResponse(get_error_result('NodeIPAlreadyExist', ip=ip))
                elif node_count == 1:
                    node = YzyNodes.objects.filter(deleted=False, ip=ip, type=1).first()
                    if not node:
                        return JSONResponse(get_error_result('NodeIPAlreadyExist', ip=ip))
                    try:
                        if node.resource_pool:
                            return JSONResponse(get_error_result('NodeIPAlreadyExist', ip=ip))
                    except ObjectDoesNotExist as e:
                        return JSONResponse(get_error_result("Success"))
                else:
                    ret = node_mgr.ping_node(ip)
                    return JSONResponse(ret)
            else:
                return JSONResponse(get_error_result("ParamError"))
        except Exception as e:
            return HttpResponseServerError()

    def check_image_ip(self, request, *args, **kwargs):
        try:
            ip = request.GET.get('ip', None)
            speed = request.GET.get('speed', None)
            if ip and speed:
                ret = node_mgr.check_image_ip(ip, speed)
                return JSONResponse(ret)
            else:
                return JSONResponse(get_error_result("ParamError"))
        except Exception as e:
            return HttpResponseServerError()

    def ping_ip(self, request, *args, **kwargs):
        try:
            ip = request.GET.get('ip', None)
            if ip:
                ret = node_mgr.ping_ip(ip)
                return JSONResponse(ret)
            else:
                return JSONResponse(get_error_result("ParamError"))
        except Exception as e:
            return HttpResponseServerError()

    def get_devices(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        ret = server_post("/node/disk_part", {"node_uuid": node_uuid})
        if ret.get('code') != 0:
            logger.error("get disk part info error:%s", ret)
        return JSONResponse(ret)

    def vg_detail(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        ret = server_post("/node/vg_detail", {"node_uuid": node_uuid})
        if ret.get('code') != 0:
            logger.error("get vg info error:%s", ret)
        return JSONResponse(ret)

    def extend_vg(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        param = request.data
        param['node_uuid'] = node_uuid
        ret = server_post("/node/extend_vg", param)
        if ret.get('code') != 0:
            logger.error("extend vg error:%s", ret)
        return JSONResponse(ret)

    def extend_lv(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        param = request.data
        param['node_uuid'] = node_uuid
        ret = server_post("/node/extend_lv", param)
        if ret.get('code') != 0:
            logger.error("extend lv error:%s", ret)
        return JSONResponse(ret)

    def create_lv(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        param = request.data
        param['node_uuid'] = node_uuid
        ret = server_post("/node/create_lv", param)
        if ret.get('code') != 0:
            logger.error("create lv error:%s", ret)
        return JSONResponse(ret)


class NodeNic(ViewSetMixin, APIView):
    """
        节点网卡管理
    """
    def list(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        network_infos = YzyNodeNetworkInfo.objects.filter(deleted=False, node=node_uuid)
        ser = YzyNodeNetworkInfoSerializer(instance=network_infos, many=True, context={'request': request})
        return JSONResponse(ser.data)

    def create_ip(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        nic_uuid = kwargs.get("nic_uuid")
        try:
            ret = node_mgr.add_ip_node(request.data, node_uuid, nic_uuid)
        except Exception as e:
            logger.exception("add ip failed:%s", e)
            ret = get_error_result("OtherError")
        return JSONResponse(ret)

    def delete_ip(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        nic_uuid = kwargs.get("nic_uuid")
        ip_info_uuid = kwargs.get("ip_info_uuid")
        ret = node_mgr.delete_ip_node(node_uuid, nic_uuid, ip_info_uuid)
        return JSONResponse(ret)
    
    def update_ip(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        nic_uuid = kwargs.get("nic_uuid")
        ip_info_uuid = kwargs.get("ip_info_uuid")
        ret = node_mgr.update_ip_node(request.data, node_uuid, nic_uuid, ip_info_uuid)
        return JSONResponse(ret)

    def update_gate_info(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        nic_uuid = kwargs.get("nic_uuid")
        try:
            node_obj = YzyNodes.objects.filter(deleted=False).filter(uuid=node_uuid).first()
            if not node_obj:
                return JSONResponse(get_error_result("NodeNotExist"))
            nic_obj = YzyNodeNetworkInfo.objects.filter(deleted=False).filter(uuid=nic_uuid).first()
            if not nic_obj:
                return JSONResponse(get_error_result("NodeNICNotExist"))

            # 已启用HA的网卡不能添加编辑网关
            ha_nic_uuids = list()
            ha_info_objs = YzyHaInfo.objects.filter(deleted=False).all()
            if ha_info_objs:
                for ha_info_obj in ha_info_objs:
                    ha_nic_uuids.append(ha_info_obj.master_nic_uuid)
                    ha_nic_uuids.append(ha_info_obj.backup_nic_uuid)
            if nic_obj.uuid in ha_nic_uuids:
                return JSONResponse(get_error_result("HaNicEditIPError"))

            data = request.data
            data['node_uuid'] = node_obj.uuid
            data['node_ip'] = node_obj.ip
            data['nic_uuid'] = nic_obj.uuid
            data['nic_name'] = nic_obj.nic
            ret = node_mgr.update_gate_info(data)
            return JSONResponse(ret)
        except Exception as e:
            logger.exception(e)
            return JSONResponse(get_error_result("OtherError"))



class NodeService(ViewSetMixin, APIView):
    """
        节点服务管理
    """
    def list(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        # 只展示该节点应有的服务
        node_obj = YzyNodes.objects.filter(deleted=False, uuid=node_uuid).first()
        if node_obj.type in [constants.ROLE_MASTER, constants.ROLE_MASTER_AND_COMPUTE]:
            services = constants.MASTER_SERVICE
        else:
            services = constants.COMPUTE_SERVICE
        page = YzyWebPagination()
        query_set = YzyNodeServices.objects.filter(deleted=False, node=node_uuid, name__in=services)
        services = page.paginate_queryset(queryset=query_set, request=request, view=self)
        ser = YzyNodeServicesSerializer(instance=services, many=True, context={'request': request})
        return page.get_paginated_response(ser.data)

    def reboot(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        service_uuid = kwargs.get("service_uuid")
        ret = node_mgr.restart_service(node_uuid, service_uuid)
        return JSONResponse(ret)


class BaseImage(ViewSetMixin, APIView):
    """
        基础镜像管理
    """
    def list(self, request, *args, **kwargs):
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        try:
            page = YzyWebPagination()
            query_set = YzyBaseImages.objects.filter(resource_pool=resource_pool_uuid)
            base_images = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyBaseImagesSerializer(instance=base_images, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def upload(self, request, *args, **kwargs):
        image_name = create_uuid()
        uuid = create_uuid()
        YzyTask.objects.create(uuid=uuid, task_uuid=image_name, name="上传镜像", type=1, status=constants.TASK_RUNNING)
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        try:
            resource_pool = YzyResourcePools.objects.get(uuid=resource_pool_uuid)
        except Exception as e:
            return JSONResponse(get_error_result("ResourcePoolNotExist"))

        file_obj = request.FILES.get("file", None)
        name = request.data.get("name", None)
        os_type = request.data.get("os_type", None)
        logger.info("go to upload func")
        return base_image_mgr.upload(file_obj, name, os_type, resource_pool, request, image_name)

    def publish(self, request, *args, **kwargs):
        data = request.data.get("data")
        return base_image_mgr.publish(data, request)

    def destroy(self, request, *args, **kwargs):
        data = request.data.get("data")
        return base_image_mgr.destroy(data, request)

    def resync(self, request, *args, **kwargs):
        image_uuid = kwargs.get("base_image_uuid")
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        node_uuid = request.data.get("node_uuid")
        ret = base_image_mgr.resync(image_uuid, node_uuid)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        uuid = kwargs.get("base_image_uuid")
        name = request.data.get("name")
        os_type = request.data.get("os_type")
        try:
            images = YzyBaseImages.objects.filter(deleted=False, name=name).exclude(uuid=uuid)
            if images:
                logger.error("update Base Image file: %s is exist" % name)
                return JSONResponse(get_error_result("ISOFileExistError"))
            base_image = YzyBaseImages.objects.get(uuid=uuid)
            ret = base_image_mgr.update(request.data, base_image)
            return JSONResponse(ret)
        except Exception as e:
            logger.exception("update base image failed:%s", e)
            return get_error_result("BaseImageUpdateError")

    def detail_info(self, request, *args, **kwargs):
        image_uuid = kwargs.get("base_image_uuid")
        try:
            base_image = YzyBaseImages.objects.filter(deleted=False, uuid=image_uuid).get()
            ser = YzyBaseImagesSerializer(instance=base_image, context={'request': request})
            return JSONResponse(ser.data, status=status.HTTP_200_OK)
        except Exception as e:
            return HttpResponseServerError()

    def delete(self, request, *args, **kwargs):
        resource_pool_uuid = kwargs.get("resource_pool_uuid")
        uuids = request.data.get("uuids")
        ret = base_image_mgr.delete(resource_pool_uuid, uuids)
        return JSONResponse(ret)

class TemplateImage(ViewSetMixin, APIView):
    """
        模版磁盘管理
    """
    def list(self, request, *args, **kwargs):
        query = GeneralQuery()
        node_uuid = kwargs.get("node_uuid")
        # 把kwargs中的node_uuid放入到request中，NodeTemplateSerializer需要用到
        # 在正常的请求/响应周期中访问时，QueryDicts request.POST和request.GET将是不可变的
        data = request.GET
        _mutable = data._mutable
        data._mutable = True
        data['node_uuid'] = node_uuid
        data._mutable = _mutable
        # 根据当前节点查到所在资源池，然后查询所有属于该资源池的模板进行返回
        node = YzyNodes.objects.filter(uuid=node_uuid, deleted=False).first()
        if not node:
            ret = get_error_result("ParamError")
            return JSONResponse(ret)
        query_dict = {
            "search_type": "all",
            "page_size": 1000,
            "pool": node.resource_pool.uuid,
            "classify__in": [1, 2]
        }
        return query.model_query(request, education_model.YzyInstanceTemplate, NodeTemplateSerializer, query_dict)

    def resync(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        data = request.data.get("data")
        template_image_uuid = data.get("image_id")
        logger.info("resync template image:%s", template_image_uuid)
        node = YzyNodes.objects.filter(uuid=node_uuid, deleted=False).first()
        if not node:
            ret = get_error_result("ParamError")
            return JSONResponse(ret)
        template_image = education_model.YzyInstanceDeviceInfo.objects.filter(uuid=template_image_uuid, deleted=False).first()
        if not template_image:
            logger.info("resync template image error, it is not exists")
            return get_error_result("ImageNotFound")
        data["ipaddr"] = node.ip
        ret = server_post("/api/v1/template/resync", data)
        logger.info("resync template image end")
        return JSONResponse(ret)

class DataNetwork(ViewSetMixin, APIView):
    """
        数据网络管理
    """
    def check_vlan_id(self, request, *args, **kwargs):
        try:
            vlan_id=request.GET.get("vlan_id", None)
            if not vlan_id:
                return JSONResponse(get_error_result("ParamError"))

            data_networks = YzyNetworks.objects.filter(deleted=False, vlan_id=vlan_id)
            if len(data_networks) > 0:
                return JSONResponse(get_error_result("VlanIDExistError"))
            return JSONResponse(get_error_result("Success"))
        except Exception as e:
            return HttpResponseServerError()

    def list(self, request, *args, **kwargs):
        try:
            page = YzyWebPagination()
            query_set = YzyNetworks.objects.filter(deleted=False)
            data_networks = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyDataNetworksSerializer(instance=data_networks, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def create(self, request, *args, **kwargs):
        _data = request.data
        ret = network_mgr.create_network(_data)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        _data = request.data
        uuid = kwargs.get("data_network_uuid")
        ret = network_mgr.update_network(_data, uuid)
        return JSONResponse(ret)

    def delete(self, request, *args, **kwargs):
        uuids = request.data.get("uuids")
        ret = network_mgr.delete_network(uuids)
        return JSONResponse(ret)


class SubNetwork(ViewSetMixin, APIView):
    """
        数据子网管理
    """
    def list(self, request, *args, **kwargs):
        try:
            data_network_uuid = kwargs.get("data_network_uuid")
            page = YzyWebPagination()
            query_set = YzySubnets.objects.filter(deleted=False, network=data_network_uuid)
            sub_networks = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzySubnetsSerializer(instance=sub_networks, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def update(self, request, *args, **kwargs):
        _data = request.data
        sub_network_uuid = kwargs.get("sub_network_uuid")
        data_network_uuid = kwargs.get("data_network_uuid")
        ret = subnet_mgr.update_subnet(_data, data_network_uuid, sub_network_uuid)
        return JSONResponse(ret)

    def delete(self, request, *args, **kwargs):
        uuids = request.data.get("uuids")
        ret = subnet_mgr.delete_subnet(uuids)
        return JSONResponse(ret)

    def create(self, request, *args, **kwargs):
        data_network_uuid = kwargs.get("data_network_uuid")
        _data = request.data
        ret = subnet_mgr.create_subnet(_data, data_network_uuid, request)
        return JSONResponse(ret)


class VSwitch(ViewSetMixin, APIView):
    """
        分布式虚拟交换机管理
    """
    def list(self, request, *args, **kwargs):
        try:
            page = YzyWebPagination()
            query_set = YzyVirtualSwitchs.objects.filter(deleted=False)
            vswitchs = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyVirtualSwitchsSerializer(instance=vswitchs, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def sources(self, request, *args, **kwargs):
        try:
            type = request.GET.get("type", None)
            if type:
                vswitchs = YzyVirtualSwitchs.objects.filter(deleted=False, type=type)
            else:
                vswitchs = YzyVirtualSwitchs.objects.filter(deleted=False)
            ser = YzyVirtualSwitchsSerializer(instance=vswitchs, many=True, context={'request': request})
            return JSONResponse(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def update(self, request, *args, **kwargs):
        try:
            vswitch_uuid = kwargs.get("vswitch_uuid")

            data = request.data
            data['uuid'] = vswitch_uuid
            ret = virtual_switch_mgr.update_virtual_switch(data)
            return JSONResponse(ret)
        except Exception as e:
            return HttpResponseServerError()

    def delete(self, request, *args, **kwargs):
        uuids = request.data.get("uuids")
        ret = virtual_switch_mgr.delete_virtual_switch(uuids)
        return JSONResponse(ret)

    def create(self, request, *args, **kwargs):
        _data = request.data
        ret = virtual_switch_mgr.create_virtual_switch(_data)
        return JSONResponse(ret)

    def node_map_info(self, request, *args, **kwargs):
        try:
            vswitch_uuid = kwargs.get("vswitch_uuid")
            vswitch = YzyVirtualSwitchs.objects.filter(deleted=False, uuid=vswitch_uuid).get()
            ser = YzyVirtualSwitchsSerializer(instance=vswitch, context={'request': request})
            return JSONResponse(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def node_map_update(self, request, *args, **kwargs):
        try:
            vswitch_uuid = kwargs.get("vswitch_uuid")

            data = request.data
            data['uuid'] = vswitch_uuid
            ret = virtual_switch_mgr.node_map_update(data)
            return JSONResponse(ret)
        except Exception as e:
            return HttpResponseServerError()


class ManageNetwork(ViewSetMixin, APIView):
    """
        管理网络管理
    """
    def list(self, request, *args, **kwargs):
        try:
            results = list()
            page = YzyWebPagination()
            query_set = YzyNodes.objects.filter(deleted=False)
            nodes = page.paginate_queryset(queryset=query_set, request=request, view=self)
            for node in nodes:
                _d = {
                    "hostname": node.name,
                    "type": node.type,
                    "node_uuid": node.uuid,
                    "manage": {},
                    "image": {}
                }


            query_set = YzyInterfaceIp.objects.filter(Q(deleted=False), Q(is_manage=1) | Q(is_image=1))
            interface_ips = page.paginate_queryset(queryset=query_set, request=request, view=self)
            for interface_ip in interface_ips:
                network_info = YzyNodeNetworkInfo.objects.get(uuid=interface_ip.interface.uuid)
                node = YzyNodes.objects.get(uuid=network_info.node.uuid)
                _d = {
                    "hostname": node.name,
                    "type": node.type,
                    "node_uuid": node.uuid,
                    "manage": {},
                    "image": {}
                }
                filter_results = [result for result in results if result['node_uuid'] == node.uuid]
                if len(filter_results) > 0:
                    if interface_ip.is_manage:
                        filter_results[0]["manage"]["manage_network"] = "%s/%s" % (network_info.nic, interface_ip.ip)
                        filter_results[0]["manage"]["manage_network_uuid"] = network_info.uuid
                        filter_results[0]["manage"]["manage_network_interface_uuid"] = interface_ip.uuid
                    if interface_ip.is_image:
                        filter_results[0]["image"]["image_network"] = "%s/%s" % (network_info.nic, interface_ip.ip)
                        filter_results[0]["image"]["image_network_uuid"] = network_info.uuid
                        filter_results[0]["image"]["image_network_interface_uuid"] = interface_ip.uuid
                else:
                    if interface_ip.is_manage:
                        _d["manage"]["manage_network"] = "%s/%s" % (network_info.nic, interface_ip.ip)
                        _d["manage"]["manage_network_uuid"] = network_info.uuid
                        _d["manage"]["manage_network_interface_uuid"] = interface_ip.uuid
                    if interface_ip.is_image:
                        _d["image"]["image_network"] = "%s/%s" % (network_info.nic, interface_ip.ip)
                        _d["image"]["image_network_uuid"] = network_info.uuid
                        _d["image"]["image_network_interface_uuid"] = interface_ip.uuid
                    results.append(_d)
            return page.get_paginated_response(results)
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

    def mn_node_map_update(self, request, *args, **kwargs):
        try:
            _data = request.data
            uplinks = _data.get('uplinks')
            ret = node_mgr.mn_node_map_update(uplinks)
            return JSONResponse(ret)
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

    def in_node_map_update(self, request, *args, **kwargs):
        try:
            _data = request.data
            uplinks = _data.get('uplinks')
            ret = node_mgr.in_node_map_update(uplinks)
            return JSONResponse(ret)
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

class ISO(ViewSetMixin, APIView):
    """
        ISO管理
    """
    def list(self, request, *args, **kwargs):
        try:
            _type = request.GET.get('type')
            name = request.GET.get('name')
            page = YzyWebPagination()
            query_set = YzyISO.objects.filter(deleted=False)
            if _type:
                query_set = query_set.filter(type=_type)
            if name:
                query_set = query_set.filter(name__contains=name)
            isos = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyISOSerializer(instance=isos, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return JSONResponse(get_error_result("OtherError"))

    def update(self, request, *args, **kwargs):
        uuid = kwargs.get("iso_uuid")
        name = request.data.get("name")
        os_type = request.data.get("os_type")
        try:
            isos = YzyISO.objects.filter(deleted=False, name=name).exclude(uuid=uuid)
            if isos:
                logger.error("upload ISO file: %s is exist" % name)
                return JSONResponse(get_error_result("ISOFileExistError"))
            iso = YzyISO.objects.get(uuid=uuid)
            iso.name = name
            iso.os_type = os_type
            data = {
                "uuid": iso.uuid,
                "name": iso.name,
                "os_type": iso.os_type,
                "path": iso.path,
                "type": iso.type,
                "md5_sum": iso.md5_sum,
                "size": iso.size
            }
            iso.save()
            return JSONResponse(data)
        except Exception as e:
            return JSONResponse(get_error_result("ISOFileUpdateError"))

    def download(self, request, *args, **kwargs):
        try:
            uuid = kwargs.get("iso_uuid")
            iso = YzyISO.objects.get(uuid=uuid)
            iso_name = iso.name
            file_path = iso.path
            response = FileResponse(open(file_path, 'rb'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(iso_name))
            return response
        except Exception:
            return JSONResponse(get_error_result("ISOFileNotExistError"))

    def delete(self, request, *args, **kwargs):
        _uuids = request.data.get("uuids")
        try:
            ret = iso_mgr.delete(_uuids)
            return JSONResponse(ret)
        except Exception:
            return JSONResponse(get_error_result("OtherError"))  

    def upload(self, request, *args, **kwargs):
        """
        上传文件，打包成ISO文件
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        iso_type = request.data.get("iso_type", None)
        os_type = request.data.get("os_type", None)
        file_obj = request.FILES.get("file", None)
        if not file_obj:
            logger.error("ISO file upload error")
            return JSONResponse(get_error_result("ISOFileUploadError"))
        return iso_mgr.upload(request, iso_type, os_type, file_obj)


class BaseImages(ViewSetMixin, APIView):

    def list(self, request, *args, **kwargs):
        query = GeneralQuery()
        query_dict = query.get_query_kwargs(request)
        return query.model_query(request, YzyBaseImages, YzyBaseImagesSerializer, query_dict)


class NodeBond(ViewSetMixin, APIView):
    """
        节点网卡bond管理
    """

    def list(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid")
        bond_nics = YzyNodeNetworkInfo.objects.filter(deleted=False, node=node_uuid, type=1)
        ser = YzyBondNicsSerializer(instance=bond_nics, many=True, context={'request': request})
        return JSONResponse(ser.data)

    def create(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid", None)
        bond_name = request.data.get("bond_name", None)
        mode = request.data.get("mode", None)
        if not node_uuid or not bond_name:
            return get_error_result("ParameterError")
        if mode not in constants.BOND_MODE.keys():
            return get_error_result("BondModeNotSupport")
        ret = node_mgr.add_bond(request.data, node_uuid, bond_name, mode)
        return JSONResponse(ret)

    def update(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid", None)
        bond_uuid = kwargs.get("bond_uuid", None)
        mode = request.data.get("mode", None)
        if not node_uuid or not bond_uuid:
            return get_error_result("ParameterError")
        if mode not in constants.BOND_MODE.keys():
            return get_error_result("BondModeNotSupport")
        ret = node_mgr.edit_bond(request.data, node_uuid, bond_uuid, mode)
        return JSONResponse(ret)

    def delete(self, request, *args, **kwargs):
        node_uuid = kwargs.get("node_uuid", None)
        bond_uuid = kwargs.get("bond_uuid", None)
        if not node_uuid or not bond_uuid:
            return get_error_result("ParameterError")
        ret = node_mgr.delete_bond(request.data, node_uuid, bond_uuid)
        return JSONResponse(ret)
    #
    # def update_ip(self, request, *args, **kwargs):
    #     node_uuid = kwargs.get("node_uuid")
    #     nic_uuid = kwargs.get("nic_uuid")
    #     ip_info_uuid = kwargs.get("ip_info_uuid")
    #     ret = node_mgr.update_ip_node(request.data, node_uuid, nic_uuid, ip_info_uuid)
    #     return JSONResponse(ret)


class HaConfig(ViewSetMixin, APIView):
    def enable_ha(self, request, *args, **kwargs):
        master_uuid = request.data.get("master_uuid", None)
        backup_uuid = request.data.get("backup_uuid", None)
        sensitivity = request.data.get("sensitivity", 60)
        quorum_ip = request.data.get("quorum_ip", None)
        new_master_ip = request.data.get("new_master_ip", None)
        backup_pwd = request.data.get("backup_pwd", None)
        # master_ip = request.data.get("master_ip", None)
        # master_nic = request.data.get("master_nic", None)
        if not master_uuid or not backup_uuid or not quorum_ip or not new_master_ip or not backup_pwd or not isinstance(sensitivity, int):
            ret = get_error_result("ParameterError")
        else:
            ret = node_mgr.enable_ha(master_uuid, backup_uuid, new_master_ip, sensitivity, quorum_ip, backup_pwd)
        return JSONResponse(ret)

    def list(self, request, *args, **kwargs):
        ha_info_obj = YzyHaInfo.objects.filter(deleted=False).first()
        if not ha_info_obj:
            ret = get_error_result("Success", data=None)
        else:
            ser = YzyHaInfoSerializer(instance=ha_info_obj, many=False, context={'request': request})
            ret = ser.data
        return JSONResponse(ret)

    def ha_status(self, request, *args, **kwargs):
        ha_info_uuid = kwargs.get("ha_info_uuid", None)
        if not ha_info_uuid:
            ret = get_error_result("ParameterError")
        else:
            ret = node_mgr.ha_status(ha_info_uuid)
        return JSONResponse(ret)

    def switch_master(self, request, *args, **kwargs):
        ha_info_uuid = kwargs.get("ha_info_uuid", None)
        new_vip_host_ip = request.data.get("new_vip_host_ip", None)
        if not ha_info_uuid or not new_vip_host_ip:
            ret = get_error_result("ParameterError")
        else:
            ret = node_mgr.switch_ha_master(ha_info_uuid, new_vip_host_ip)
        return JSONResponse(ret)

    def disable_ha(self, request, *args, **kwargs):
        ha_info_uuid = kwargs.get("ha_info_uuid", None)
        if not ha_info_uuid:
            ret = get_error_result("ParameterError")
        else:
            ret = node_mgr.disable_ha(ha_info_uuid)
        return JSONResponse(ret)

    def ha_data_sync_network(self, request, *args, **kwargs):
        master_node_obj = YzyNodes.objects.filter(deleted=False,
                                type__in=[constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER]).first()
        master_ip = master_node_obj.ip
        master_ip_obj = YzyInterfaceIp.objects.filter(deleted=False, ip=master_ip).first()
        master_nic = master_ip_obj.name

        ret = {
            "ha_data_sync_network": "%s(%s)" % (master_nic, master_ip),
            "manage_gateway": master_ip_obj.gateway
        }
        return JSONResponse(ret)


class VersionView(APIView):
    """登录认证"""
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        return JSONResponse(server_post("/api/v1/controller/check_ha_done", {}))


class SystemRunningTimeView(APIView):
    """节点系统运行时间"""

    def get(self, request, *args, **kwargs):
        logger.info("get system run time")
        node_uuid = request.GET.get("uuid", "")
        if not node_uuid:
            return JSONResponse(get_error_result("ParameterError"))
        data = {
            "node_uuid": node_uuid
        }
        url = "/api/v1/controller/get_system_time"
        ret = server_post(url, data=data)
        return JSONResponse(ret)


class RemoteStorageView(ViewSetMixin, APIView):

    def list(self, request, *args, **kwargs):
        try:
            page = YzyWebPagination()
            group = request.GET.get('group', 'all')
            if group == 'all':
                query_set = YzyRemoteStorage.objects.filter(deleted=False)
            elif group == 'allocated':
                query_set = YzyRemoteStorage.objects.filter(deleted=False).filter(allocated=1)
            elif group == 'unallocated':
                query_set = YzyRemoteStorage.objects.filter(deleted=False).filter(allocated=0)
            else:
                return JSONResponse(get_error_result("ParameterError"))
            remote_storages = page.paginate_queryset(queryset=query_set, request=request, view=self)
            ser = YzyRemoteStorageSerializer(instance=remote_storages, many=True, context={'request': request})
            return page.get_paginated_response(ser.data)
        except Exception as e:
            return HttpResponseServerError()

    def create(self, request, *args, **kwargs):
        _data = request.data
        ret = remote_storage_mgr.create_remote_storage(_data)
        return JSONResponse(ret)

    def delete(self, request, *args, **kwargs):
        uuid = request.data.get("uuid")
        ret = remote_storage_mgr.delete_remote_storage(uuid)
        return JSONResponse(ret)

    def allocate(self, request, *args, **kwargs):
        remote_storage_uuid = kwargs.get("remote_storage_uuid")
        resource_pool_uuid = request.data.get("uuid")
        ret = remote_storage_mgr.allocate_remote_storage(remote_storage_uuid, resource_pool_uuid)
        return JSONResponse(ret)

    def reclaim(self, request, *args, **kwargs):
        remote_storage_uuid = kwargs.get("remote_storage_uuid")
        ret = remote_storage_mgr.reclaim_remote_storage(remote_storage_uuid)
        return JSONResponse(ret)

    def list_nfs_mount_point(self, request, *args, **kwargs):
        nfs_server_ip = request.GET.get('nfs_server_ip', None)
        ret = remote_storage_mgr.list_nfs_mount_point(nfs_server_ip)
        return JSONResponse(ret)

    def resource_pool_remote_storages(self, request, *args, **kwargs):
        resource_pool_uuid = request.GET.get('resource_pool_uuid', None)
        res = YzyRemoteStorage.objects.filter(deleted=False, allocated_to=resource_pool_uuid)
        ret = list()
        for r in res:
            remote_storage = {
                'uuid': r.uuid,
                'name': r.name
            }
            ret.append(remote_storage)
        return JSONResponse(ret)

    def resource_pool_local_storages(self, request, *args, **kwargs):
        resource_pool_uuid = request.GET.get('resource_pool_uuid', None)
        nodes = YzyNodes.objects.filter(deleted=False, resource_pool_id=resource_pool_uuid).all()
        if not nodes:
            return JSONResponse([])
        storages = YzyNodeStorages.objects.filter(deleted=False, node_id=nodes[0].uuid)
        local_storages = list()
        for storage in storages:
            if '/opt/nfs' not in storage.path:
                storage_dict = {
                    'uuid': storage.uuid,
                    'path': storage.path,
                    'role': storage.role,
                    'total': round(storage.total/1024/1024/1024, 2),
                    'available': round(storage.free/1024/1024/1024, 2),
                }
                local_storages.append(storage_dict)
        return JSONResponse(local_storages)
