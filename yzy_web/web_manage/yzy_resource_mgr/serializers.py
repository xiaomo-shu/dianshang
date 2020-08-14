import psutil
from rest_framework import serializers
from .models import *
from web_manage.common.utils import create_uuid
from web_manage.common import constants
from web_manage.common.utils import DateTimeFieldMix
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_user_desktop_mgr import models as personal_model


class YzyResourcePoolsSerializer(DateTimeFieldMix):
    # TODO 问题：
    # 1、返回主机数量
    # 2、返回状态(0、正常，1、同步数据中，2、基础镜像异常，3、计算节点异常)
    # 3、添加时uuid自己生成
    # 4、返回的时间格式
    host_count = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    uuid = serializers.CharField(read_only=True)

    class Meta:
        model = YzyResourcePools
        fields = '__all__'
        # read_only_fields = ('deleted_at', 'updated_at', 'created_at', "host_count")

    def get_host_count(self, instance):
       return instance.yzy_nodes.count()

    def get_status(self, instance):
        """
        :return: 0-正常 1-数据同传中 2-基础镜像异常 3-计算节点异常
        1、首先判断计算节点状态，只要有一个异常则资源池异常
        2、镜像状态，只要有一个基础镜像异常则资源池异常
        3、镜像状态，无基础镜像异常，只要有一个基础镜像同传则资源池同传
        4、镜像状态，无异常无同传，则资源池正常
        """
        for node in instance.yzy_nodes.all():
            if constants.STATUS_SHUTDOWN == node.status:
                return 3
        state = list()
        for image in instance.yzy_base_images.all():
            hosts_state = list()
            # 获取每个基础镜像在所有节点的状态
            for host in instance.yzy_nodes.all():
                task = YzyTaskInfo.objects.filter(image_id=image.uuid, host_uuid=host.uuid, deleted=0). \
                    order_by('-progress').order_by('-id').first()
                if task:
                    if 'error' == task.status:
                        status = 2
                    elif 'end' == task.status:
                        status = 0
                    else:
                        status = 1
                else:
                    status = 0
                hosts_state.append(status)
            # 确定每个基础镜像状态
            if 2 in hosts_state:
                image_status = 2
            elif 1 in set(hosts_state):
                image_status = 1
            else:
                image_status = 0
            state.append(image_status)
        # 确定资源池状态
        if 2 in state:
            return 2
        elif 1 in set(state):
            return 1
        else:
            return 0

    # def create(self, validated_data):
    #     uuid = create_uuid()
    #     validated_data.update({"uuid": uuid})
    #     return super().create(validated_data)

    def validate_name(self, name):
        if YzyResourcePools.objects.filter(name=name).all():
            raise serializers.ValidationError('资源池名称已存在')

        return name

    def validate(self, attrs):
        attrs['uuid'] = create_uuid()
        # if User.objects.filter(phone=phone).all():
        #     raise serializers.ValidationError('手机号以被注册')
        return attrs


class YzyNodesSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyNodes
        # fields = '__all__'
        fields = ('id', 'name', 'uuid', 'hostname', 'ip', 'total_mem', 'running_mem', 'total_vcpus', 'running_vcpus',
                  'mem_utilization', 'server_version_info', 'gpu_info', 'cpu_info', 'mem_info', 'status', 'type', 'created_at',
                  'cpu_utilization', 'updated_at', 'deleted_at')

    def to_representation(self, instance):
        role_map = {'1': 'template_sys', '2': 'template_data', '3': 'instance_sys', '4': 'instance_data'}
        representation = super(YzyNodesSerializer, self).to_representation(instance)
        representation['cpu_info'] = representation['cpu_info'].split(',')
        representation['mem_info'] = representation['mem_info'].split(',')
        network_interfaces = YzyNodeNetworkInfoSerializer(instance.yzy_node_interfaces, many=True).data
        # network_interfaces只返回未绑定的物理网卡信息，不返回bond，不返回slave
        representation['network_interfaces'] = [ni for ni in network_interfaces if not ni["is_bond"] and not ni["is_slave"]]
        # new_network_interfaces返回未绑定的物理网卡和bond网卡信息，不返回slave
        representation['new_network_interfaces'] = [ni for ni in network_interfaces if not ni["is_slave"]]
        # bond_nics返回bond与slave之间的关系
        representation['bond_nics'] = YzyBondNicsSerializer(instance.yzy_node_interfaces.filter(type=1).all(), many=True).data
        storages = YzyNodeStorageSerializer(instance.yzy_node_storages, many=True).data
        storages = [storage for storage in storages if storage['path'] != '/boot/efi']
        representation['storages'] = storages
        # linux中系统有预留空间，所以used+free不会等于total
        sys_used = 0
        sys_free = 0
        sys_total = 0
        data_used = 0
        data_free = 0
        data_total = 0
        usage_mem = 0
        usage_vcpu = 0
        total_vm = 0
        running_vm = 0
        sys_usage = 0
        data_usage = 0
        sys_path = list()
        data_path = list()
        for storage in storages:
            roles = storage['role']
            for role in roles.split(','):
                if role in role_map:
                    representation[role_map[role]] = storage
                    if role in [str(constants.TEMPLATE_SYS), str(constants.INSTANCE_SYS)]:
                        if storage['path'] not in sys_path:
                            sys_path.append(storage['path'])
                            sys_used += storage['used']
                            sys_free += storage['available']
                            sys_total += storage['total']
                    else:
                        if storage['path'] not in data_path:
                            data_path.append(storage['path'])
                            data_used += storage['used']
                            data_free += storage['available']
                            data_total += storage['total']
        if sys_total:
            sys_usage = "%.2f" % ((sys_total - sys_free) / sys_total * 100)
        if data_total:
            data_usage = "%.2f" % ((data_total - data_free) / data_total * 100)
        instances = education_model.YzyInstances.objects.filter(host=instance)
        instance_templates = education_model.YzyInstanceTemplate.objects.filter(node=instance)
        running_instances = list(filter(lambda instance: instance.status == 'active', instances))
        running_instance_templates = list(filter(lambda instance_template: instance_template.status == 'active', instance_templates))
        total_vm = len(instances) + len(instance_templates)
        running_vm = len(running_instances) + len(running_instance_templates)
        total_vm_name = list(map(lambda instance: instance.name, instances)) + list(map(lambda instance_template: instance_template.name, instance_templates))
        running_vm_name = list(map(lambda running_instance: running_instance.name, running_instances)) + list(map(lambda running_instance_template: running_instance_template.name, running_instance_templates))
        representation['usage_sys'] = sys_usage
        representation['usage_data'] = data_usage
        representation['total_sys'] = sys_total
        representation['used_sys'] = sys_used
        representation['usage_mem'] = usage_mem
        representation['usage_vcpu'] = usage_vcpu
        representation['total_vm'] = total_vm
        representation['running_vm'] = running_vm
        representation['total_vm_name'] = total_vm_name
        representation['running_vm_name'] = running_vm_name
        return representation


class YzyBaseImagesSerializer(DateTimeFieldMix):

    os_type_simple = serializers.SerializerMethodField(read_only=True)
    count = serializers.SerializerMethodField(read_only=True)
    publish_count = serializers.SerializerMethodField(read_only=True)
    detail = serializers.SerializerMethodField(read_only=True)
    image_status = serializers.SerializerMethodField(read_only=True)
    cpu_count = serializers.SerializerMethodField(read_only=True)
    total_ram = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyBaseImages
        fields = '__all__'
        # fields = ('uuid', 'name', 'os_type', 'os_type_simple', 'md5_sum', 'path', 'size',
        #           'count', 'publish_count', 'status', 'detail', 'vcpu', 'ram', 'disk', 'os_bit')

    def get_image_status(self, obj):
        state = list()
        hosts = obj.resource_pool.yzy_nodes
        for host in hosts.get_queryset():
            task = YzyTaskInfo.objects.filter(image_id=obj.uuid, host_uuid=host.uuid, deleted=0). \
                order_by('-progress').order_by('-id').first()
            if task:
                if 'error' == task.status:
                    status = 2
                elif 'end' == task.status:
                    status = 0
                else:
                    status = 1
            else:
                status = 0
            state.append(status)
        if 2 in state:
            return 2
        elif 1 in set(state):
            return 1
        else:
            return 0

    def get_detail(self, obj):
        details = list()
        hosts = obj.resource_pool.yzy_nodes
        for host in hosts.get_queryset():
            task = YzyTaskInfo.objects.filter(image_id=obj.uuid, host_uuid=host.uuid, deleted=0).\
                order_by('-progress').order_by('-id').first()
            if not task:
                info = {
                    'host_name': host.name,
                    'ipaddr': host.ip,
                    'host_uuid': host.uuid,
                    'progress': 100,
                    'status': 0
                }
            else:
                if 'error' == task.status:
                    status = 2
                elif 'end' == task.status:
                    status = 0
                else:
                    status = 1
                info = {
                    'host_name': host.name,
                    'ipaddr': host.ip,
                    'host_uuid': host.uuid,
                    'progress': task.progress,
                    'status': status
                }
            details.append(info)
        return details

    def get_publish_count(self, obj):
        publish_count = 0
        hosts = obj.resource_pool.yzy_nodes
        for host in hosts.get_queryset():
            task = YzyTaskInfo.objects.filter(image_id=obj.uuid, host_uuid=host.uuid, deleted=0).\
                order_by('-progress').order_by('-id').first()
            if not task or task.status == 'end':
                publish_count += 1
        return publish_count

    def get_count(self, obj):
        count = obj.resource_pool.yzy_nodes.count()
        # count = YzyNodes.objects.filter(resource_pool=obj.resource_pool, deleted=0).count()
        return count

    def get_os_type_simple(self, obj):
        simple = constants.IMAGE_TYPE.get(obj.os_type)
        if simple:
            return simple
        return obj.os_type

    def get_cpu_count(self, obj):
        return psutil.cpu_count()

    def get_total_ram(self, obj):
        return round(psutil.virtual_memory().total/1024/1024/1024, 1)


class YzyVirtualSwitchUplinkSerializer(DateTimeFieldMix):
    nic_uuid = serializers.CharField(source='network_interface.uuid')
    nic_name = serializers.CharField(source='network_interface.nic', read_only=True)
    node_name = serializers.CharField(source='network_interface.node.name', read_only=True)

    class Meta:
        model = YzyVirtualSwitchUplink
        fields = ('id', 'uuid', 'nic_name', 'node_name', 'nic_uuid', 'node_uuid', 'deleted_at'
                  ,'created_at', 'updated_at')


class YzyVirtualSwitchsSerializer(DateTimeFieldMix):
    uplinks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyVirtualSwitchs
        fields = ('id', 'uuid', 'name', 'type', 'desc', 'default', 'deleted_at', 'created_at', 'updated_at', 'uplinks')

    def get_uplinks(self, instance):
        uplinks = YzyVirtualSwitchUplinkSerializer(instance.yzy_virtual_switch_uplinks, many=True).data
        return uplinks


class YzyDataNetworksSerializer(DateTimeFieldMix):

    subnet_count = serializers.SerializerMethodField(read_only=True)
    quote_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyNetworks
        fields = '__all__'

    def get_subnet_count(self, instance):
        return instance.yzy_network_subnets.count()

    def get_quote_status(self, instance):
        quote_flag = False
        for model in [
            education_model.YzyInstanceTemplate,
            education_model.YzyGroup,
            education_model.YzyDesktop,
            personal_model.YzyPersonalDesktop
        ]:
            query_count = model.objects.filter(deleted=False, network=instance).count()
            if query_count > 0:
                quote_flag = True
                break
        return quote_flag


class YzyNodeNetworkInfoSerializer(DateTimeFieldMix):

    ip_info = serializers.SerializerMethodField(read_only=True)
    gate_info = serializers.SerializerMethodField(read_only=True)
    is_uplink = serializers.SerializerMethodField(read_only=True)
    is_slave = serializers.SerializerMethodField(read_only=True)
    is_bond = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyNodeNetworkInfo
        fields = ('id', 'uuid', 'nic', 'mac', 'speed', 'status', 'type', 'speed', 'deleted_at',
                  'updated_at', 'created_at', 'ip_info', 'is_uplink', 'is_slave', 'is_bond', 'gate_info')

    def get_is_uplink(self, instance):
        uplinks = instance.yzy_network_interface_uplinks.count()
        if uplinks > 0:
            return True
        return False

    def get_gate_info(self, instance):
        ip_infos = instance.yzy_interface_ips.get_queryset()
        for i in ip_infos:
            if i.gateway:
                _d = {"gateway": i.gateway, "dns1": i.dns1, "dns2": i.dns2}
                return _d
        return {}

    def get_ip_info(self, instance):
        ips = list()
        ip_infos = instance.yzy_interface_ips.get_queryset()
        for i in ip_infos:
            _d = {"uuid": i.uuid, "ip": i.ip, "netmask": i.netmask, "gateway": i.gateway, "dns1": i.dns1,
                  "dns2": i.dns2,  'is_manage': i.is_manage, 'is_image': i.is_image}
            ips.append(_d)
        return ips

    def get_is_slave(self, instance):
        slave_nics = YzyBondNics.objects.filter(deleted=False, node_uuid=instance.node.uuid).all()
        slave_uuids = [slave_obj.slave_uuid for slave_obj in slave_nics]
        if instance.uuid in slave_uuids:
            return True
        else:
            return False

    def get_is_bond(self, instance):
        slave_nics = YzyBondNics.objects.filter(deleted=False, node_uuid=instance.node.uuid).all()
        bond_uuids = [slave_obj.master_uuid for slave_obj in slave_nics]
        if instance.uuid in bond_uuids:
            return True
        else:
            return False


class YzyNodeServicesSerializer(DateTimeFieldMix):

    class Meta:
        model = YzyNodeServices
        fields = '__all__'


class YzySubnetsSerializer(DateTimeFieldMix):
    quote_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzySubnets
        fields = '__all__'

    def get_quote_status(self, instance):
        quote_flag = False
        for model in [
            education_model.YzyInstanceTemplate,
            education_model.YzyGroup,
            education_model.YzyDesktop,
            personal_model.YzyPersonalDesktop
        ]:
            if hasattr(model, 'subnet'):
                query_count = model.objects.filter(deleted=False, subnet_id=instance.uuid).count()
            else:
                query_count = model.objects.filter(deleted=False, subnet_uuid=instance.uuid).count()
            if query_count > 0:
                quote_flag = True
                break
        return quote_flag


class YzyISOSerializer(DateTimeFieldMix):
    cpu_count = serializers.SerializerMethodField(read_only=True)
    total_ram = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyISO
        # fields = '__all__'
        fields = ('id', 'name', 'type', 'uuid', 'desc', 'path', 'os_type', 'size',
                  'status', 'deleted', 'deleted_at', 'created_at', 'updated_at', 'cpu_count', 'total_ram')

    def get_cpu_count(self, obj):
        return psutil.cpu_count()

    def get_total_ram(self, obj):
        return round(psutil.virtual_memory().total/1024/1024/1024, 1)


class YzyNodeStorageSerializer(DateTimeFieldMix):

    used = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    usage = serializers.SerializerMethodField(read_only=True)
    available = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyNodeStorages
        fields = ('uuid', 'path', 'used', 'total', 'usage', 'role', 'available')

    def get_available(self, obj):
        return round(obj.free/1024/1024/1024, 2)

    def get_used(self, obj):
        return round(obj.used/1024/1024/1024, 2)

    def get_total(self, obj):
        return round(obj.total/1024/1024/1024, 2)

    def get_usage(self, obj):
        usage = "%.2f" % ((obj.total - obj.free) / obj.total * 100)
        return usage


class YzyBondNicsSerializer(DateTimeFieldMix):
    mode = serializers.SerializerMethodField(read_only=True)
    slaves = serializers.SerializerMethodField(read_only=True)
    ip_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YzyNodeNetworkInfo
        fields = ('uuid', 'nic', 'status', 'mode', 'slaves', 'ip_info', 'deleted_at', 'created_at', 'updated_at')

    def get_mode(self, instance):
        bond_nic = YzyBondNics.objects.filter(deleted=False, master_uuid=instance.uuid).first()
        return bond_nic.mode

    def get_slaves(self, instance):
        slaves = list()
        bond_nics = YzyBondNics.objects.filter(deleted=False, master_uuid=instance.uuid)
        for nic in bond_nics:
            node_network_info = YzyNodeNetworkInfo.objects.filter(deleted=False, uuid=nic.slave_uuid).first()
            slaves.append(
                {
                    "uuid": nic.slave_uuid,
                    "nic": nic.slave_name,
                    "status": node_network_info.status if hasattr(node_network_info, "status") else 0
                }
            )
        return slaves

    def get_ip_info(self, instance):
        ips = list()
        ip_infos = instance.yzy_interface_ips.get_queryset()
        for i in ip_infos:
            _d = {"uuid": i.uuid, "ip": i.ip, "netmask": i.netmask, "gateway": i.gateway, "dns1": i.dns1,
                  "dns2": i.dns2,  'is_manage': i.is_manage, 'is_image': i.is_image}
            ips.append(_d)
        return ips