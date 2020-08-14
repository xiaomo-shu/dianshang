from django.conf.urls import url  # noqa
from django.urls import path
from web_manage.yzy_resource_mgr import views

# from django.contrib import admin
# from django.urls import path, include
# from . import views
#
# urlpatterns = [
#     # path('users/', views.user_list, name='user-list'),
#     path('users/', views.UserList.as_view(), name='user-list'),
#     # path('users/<int:pk>/', views.user_detail, name='user-detail'),
#     path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
#
# ]

urlpatterns = [
    path('common/check_name_existence', views.Common.as_view({'get': 'check_name_existence'}), name='common'),
    path('controller_nodes', views.ControllerNode.as_view({'get': 'list'}), name='controller-nodes'),
    path('controller_nodes/<str:node_uuid>', views.ControllerNode.as_view({'put': 'update'}), name='controller-node-update'),
    path('controller_nodes/<str:node_uuid>/reboot', views.ControllerNode.as_view({'post': 'reboot'}), name='controller-node-reboot'),
    path('controller_nodes/<str:node_uuid>/shutdown', views.ControllerNode.as_view({'post': 'shutdown'}), name='controller-node-shutdown'),
    path('resource_pools', views.ResourcePool.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='resource-pools'),
    path('resource_pools/<str:resource_pool_uuid>', views.ResourcePool.as_view({'put': 'update'}), name='resource-pool'),
    path('resource_pools/<str:resource_pool_uuid>/base_images', views.BaseImage.as_view({'get': 'list', 'post': 'upload', 'delete': 'delete'}), name='base-images'),
    path('resource_pools/<str:resource_pool_uuid>/base_images/publish', views.BaseImage.as_view({'post': 'publish'}), name='base-image-publish'),
    path('resource_pools/<str:resource_pool_uuid>/base_images/destroy', views.BaseImage.as_view({'post': 'destroy'}), name='base-image-destroy'),
    path('resource_pools/<str:resource_pool_uuid>/base_images/<str:base_image_uuid>', views.BaseImage.as_view({'put': 'update', 'get': 'detail_info'}), name='base-image'),
    path('resource_pools/<str:resource_pool_uuid>/base_images/<str:base_image_uuid>/resync', views.BaseImage.as_view({'post': 'resync'}), name='base-image-resync'),
    path('resource_pools/<str:resource_pool_uuid>/nodes', views.Node.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='nodes'),
    path('check_node_virt', views.Node.as_view({'post': 'check'}), name='node-check'),
    path('check_node_password', views.Node.as_view({'post': 'check_password'}), name='node-check-password'),
    path('check_node_ip', views.Node.as_view({'get': 'check_ip'}), name='node-check-ip'),
    path('check_image_ip', views.Node.as_view({'get': 'check_image_ip'}), name='check-image-ip'),
    path('node_sources', views.Node.as_view({'get': 'sources'}), name='node-sources'),
    path('nodes/<str:node_uuid>', views.Node.as_view({'put': 'update', 'get': 'detail_info', 'delete': 'delete'}), name='node'),
    path('nodes/<str:node_uuid>/reboot', views.Node.as_view({'post': 'reboot'}), name='node-reboot'),
    path('nodes/<str:node_uuid>/shutdown', views.Node.as_view({'post': 'shutdown'}), name='node-shutdown'),
    path('nodes/<str:node_uuid>/storage_info', views.Node.as_view({'get': 'storage_info'}), name='node-storage-info'),
    path('nodes/<str:node_uuid>/nics', views.NodeNic.as_view({'get': 'list'}), name='node-nics'),
    path('nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos', views.NodeNic.as_view({'post': 'create_ip', 'put': 'update_gate_info'}), name='node-nic-ip-create'),
    path('nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos/<str:ip_info_uuid>', views.NodeNic.as_view({'delete': 'delete_ip', 'put': 'update_ip'}), name='node-nic-ip-delete'),
    path('nodes/<str:node_uuid>/bond', views.NodeBond.as_view({'get': 'list', 'post': 'create'}), name='node-bond'),
    path('nodes/<str:node_uuid>/bond/<str:bond_uuid>', views.NodeBond.as_view({'put': 'update', 'delete': 'delete'}), name='node-bond-update'),
    path('nodes/<str:node_uuid>/services', views.NodeService.as_view({'get': 'list'}), name='node-services'),
    path('nodes/<str:node_uuid>/services/<str:service_uuid>/reboot', views.NodeService.as_view({'post': 'reboot'}), name='node-service-reboot'),
    path('nodes/<str:node_uuid>/template_images', views.TemplateImage.as_view({'get': 'list', 'post': 'resync'}), name='template-images'),
    # path('nodes/<str:node_uuid>/template_images/<str:template_image_uuid>/resync', views.TemplateImage.as_view({'post': 'resync'}), name='template-image-resync'),
    path('data_networks', views.DataNetwork.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='data-networks'),
    path('data_networks/check_vlan_id', views.DataNetwork.as_view({'get': 'check_vlan_id'}), name='check-vlan-id'),
    path('data_networks/<str:data_network_uuid>', views.DataNetwork.as_view({'put': 'update'}), name='data-network'),
    path('data_networks/<str:data_network_uuid>/sub_networks', views.SubNetwork.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='sub-networks'),
    path('data_networks/<str:data_network_uuid>/sub_networks/<str:sub_network_uuid>', views.SubNetwork.as_view({'put': 'update'}), name='sub-network'),
    path('vswitchs', views.VSwitch.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='vswitchs'),
    path('vswitch_sources', views.VSwitch.as_view({'get': 'sources'}), name='vswitch_sources'),
    path('vswitchs/<str:vswitch_uuid>', views.VSwitch.as_view({'put': 'update'}), name='vswitch'),
    path('vswitchs/<str:vswitch_uuid>/node_map', views.VSwitch.as_view({'get': 'node_map_info', 'put': 'node_map_update'}), name='vswitch-node-map'),
    path('manage_networks', views.ManageNetwork.as_view({'get': 'list'}), name='manage-networks'),
    path('manage_networks/mn_node_map', views.ManageNetwork.as_view({'put': 'mn_node_map_update'}), name='mn-node-map'),
    path('manage_networks/in_node_map', views.ManageNetwork.as_view({'put': 'in_node_map_update'}), name='in-node-map'),
    path('isos', views.ISO.as_view({'get': 'list', 'post': 'upload', 'delete': 'delete'}), name='isos'),
    path('isos/<str:iso_uuid>', views.ISO.as_view({'put': 'update', 'get': 'download'}), name='iso'),
    path('base_images/', views.BaseImages.as_view({'get': 'list'}), name='base-image')
]
