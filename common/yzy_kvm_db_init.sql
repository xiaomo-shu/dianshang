/*
SQLyog Ultimate v12.08 (64 bit)
MySQL - 5.7.28-log : Database - yzy_kvm_db
*********************************************************************
*/


/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`yzy_kvm_db` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `yzy_kvm_db`;

/*Table structure for table `yzy_admin_user` */

DROP TABLE IF EXISTS `yzy_admin_user`;

CREATE TABLE `yzy_admin_user` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '管理员用户id',
  `username` varchar(32) NOT NULL COMMENT '账号',
  `password` varchar(64) NOT NULL COMMENT '密码',
  `last_login` datetime NOT NULL COMMENT '上次登录时间',
  `login_ip` varchar(20) NOT NULL DEFAULT '' COMMENT '登录ip',
  `real_name` varchar(64) NOT NULL DEFAULT '' COMMENT '真实姓名',
  `role_id` bigint(11) NOT NULL COMMENT '角色id',
  `email` varchar(100) NOT NULL DEFAULT '' COMMENT 'email',
  `is_superuser` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为超级管理员，0-否，1-是',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活，0-否，1-是',
  `desc` varchar(200) DEFAULT NULL COMMENT '备注',
  `deleted` int(11) NOT NULL DEFAULT '0' COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/*Table structure for table `yzy_auth` */

DROP TABLE IF EXISTS `yzy_auth`;
CREATE TABLE `yzy_auth` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sn` varchar(64) NOT NULL COMMENT '授权序列号',
  `organization` varchar(255) DEFAULT NULL COMMENT '单位名称',
  `remark` varchar(255) DEFAULT '',
  `deleted` int(11) NOT NULL DEFAULT 0,
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='授权信息表';


/*Table structure for table `yzy_base_images` */

DROP TABLE IF EXISTS `yzy_base_images`;

CREATE TABLE `yzy_base_images` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '基础镜像表格',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `pool_uuid` varchar(64) NOT NULL,
  `name` varchar(150) NOT NULL COMMENT '镜像名称',
  `path` varchar(200) NOT NULL COMMENT '路径',
  `md5_sum` varchar(64) NOT NULL COMMENT 'md5校验值',
  `os_type` varchar(32) NOT NULL COMMENT '系统类型',
  `os_bit` varchar(10) DEFAULT NULL COMMENT '系统位数 32， 64',
  `vcpu` int(11) NOT NULL COMMENT 'vcpu, 核',
  `ram` float NOT NULL COMMENT '内存：G',
  `disk` int(11) DEFAULT '0',
  `size` float NOT NULL COMMENT '大小，单位：M',
  `status` int(11) NOT NULL COMMENT '状态',
  `deleted` int(11) NOT NULL DEFAULT '0' COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/*Table structure for table `yzy_desktop` */

DROP TABLE IF EXISTS `yzy_desktop`;

CREATE TABLE `yzy_desktop` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '桌面组的uuid',
  `name` varchar(255) NOT NULL COMMENT '桌面组的名称',
  `owner_id` int(11) NOT NULL DEFAULT 0 COMMENT '创建者ID',
  `group_uuid` varchar(64) NOT NULL COMMENT '所属分组',
  `pool_uuid` varchar(64) NOT NULL COMMENT '资源池uuid',
  `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
  `network_uuid` varchar(64) NOT NULL COMMENT '网络uuid',
  `subnet_uuid` varchar(64) NOT NULL COMMENT '子网uuid',
  `vcpu` int(11) NOT NULL COMMENT 'vcpu个数',
  `ram` float NOT NULL COMMENT '虚拟内存，单位为G',
  `os_type` varchar(64) DEFAULT 'windows',
  `sys_restore` tinyint(4) DEFAULT 1 COMMENT '系统盘是否重启还原',
  `data_restore` tinyint(4) DEFAULT 1 COMMENT '数据盘是否重启还原',
  `instance_num` int(11) DEFAULT 1 COMMENT '包含的桌面数',
  `prefix` varchar(128) DEFAULT 'PC' COMMENT '桌面名称的前缀',
  `postfix` int(11) DEFAULT 1 COMMENT '桌面名称的后缀数字个数',
  `postfix_start` int(11) DEFAULT 1 COMMENT '桌面名称后缀的起始数字',
  `order_num` int(11) DEFAULT 99 COMMENT '排序号',
  `active` tinyint(4) DEFAULT 0 COMMENT '是否激活，0-未激活，1-激活',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='教学桌面组表';

/*Table structure for table `yzy_device_info` */

DROP TABLE IF EXISTS `yzy_device_info`;
CREATE TABLE `yzy_device_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '磁盘的uuid',
  `type` varchar(32) NOT NULL DEFAULT 'data' COMMENT '磁盘类型，system or data',
  `device_name` varchar(32) NOT NULL DEFAULT 'vda' COMMENT '设备名称，vda/vdb/...',
  `image_id` varchar(64) NOT NULL COMMENT '磁盘镜像uuid',
  `instance_uuid` varchar(64) NOT NULL COMMENT '虚机uuid',
  `boot_index` int(11) NOT NULL DEFAULT -1 COMMENT 'boot序列',
  `disk_bus` varchar(32) DEFAULT 'virtio' COMMENT '设备总线，如：virtio',
  `source_type` varchar(32) DEFAULT 'file' COMMENT '磁盘文件类型',
  `source_device` varchar(32) DEFAULT 'disk' COMMENT '设备类型',
  `size` int(11) DEFAULT 0 COMMENT '磁盘大小，单位为GB',
  `used` float DEFAULT 0 COMMENT '磁盘已使用大小，单位为GB，保留两位小数',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime NULL COMMENT '创建时间',
  `updated_at` datetime NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='虚拟机的磁盘信息表';


DROP TABLE IF EXISTS `yzy_device_modify`;
CREATE TABLE `yzy_device_modify` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `template_uuid` varchar(64) NOT NULL COMMENT '所属模板的uuid',
  `device_name` varchar(32) DEFAULT NULL,
  `boot_index` int(11) DEFAULT NULL,
  `origin` tinyint(4) DEFAULT 0 COMMENT '0 - 不是原有盘 1-是原有盘',
  `size` int(11) DEFAULT 0 COMMENT '磁盘大小，单位为GB',
  `used` float DEFAULT 0 COMMENT '磁盘已使用大小，单位为GB，保留两位小数',
  `state` int(11) DEFAULT 0 COMMENT '1-待删除 2-待添加',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime NULL COMMENT '创建时间',
  `updated_at` datetime NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='模板磁盘变化表';


/*Table structure for table `yzy_group` */

DROP TABLE IF EXISTS `yzy_group`;

CREATE TABLE `yzy_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL COMMENT '教学分组名称',
  `group_type` int(11) NOT NULL DEFAULT 1 COMMENT '分组类型，1-教学分组 2-用户分组',
  `network_uuid` varchar(64) DEFAULT NULL COMMENT '使用的网络uuid',
  `subnet_uuid` varchar(64) DEFAULT NULL COMMENT '使用的子网uuid',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '终端预设分组规则，默认启用',
  `start_ip` varchar(20) DEFAULT NULL COMMENT '预设终端的开始IP',
  `end_ip` varchar(20) DEFAULT NULL COMMENT '预设终端的结束IP',
  `desc` varchar(200) DEFAULT NULL COMMENT '分组描述',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='分组表';


/*Table structure for table `yzy_group_user` */

DROP TABLE IF EXISTS `yzy_group_user`;

CREATE TABLE `yzy_group_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `group_uuid` varchar(64) NOT NULL COMMENT '所属分组uuid',
  `user_name` varchar(128) NOT NULL COMMENT '用户名',
  `passwd` varchar(128) NOT NULL COMMENT '密码',
  `name` varchar(255) DEFAULT NULL COMMENT '姓名',
  `phone` varchar(32) DEFAULT NULL COMMENT '电话号码',
  `email` varchar(128) DEFAULT NULL COMMENT '邮箱',
  `enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `online` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否在线',
  `mac` varchar(32) DEFAULT NULL COMMENT '当前登录终端mac',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户表';


DROP TABLE IF EXISTS `yzy_group_user_session`;

CREATE TABLE `yzy_group_user_session` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '终端用户登录session',
  `session_id` varchar(64) NOT NULL COMMENT 'session id',
  `user_uuid` varchar(64) NOT NULL COMMENT 'user uuid',
  `expire_time` datetime NOT NULL COMMENT '失效时间',
  `deleted` int(11) NOT NULL DEFAULT 0,
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/*Table structure for table `yzy_instances` */

DROP TABLE IF EXISTS `yzy_instances`;

CREATE TABLE `yzy_instances` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '桌面的uuid',
  `name` varchar(255) NOT NULL COMMENT '桌面的名称',
  `host_uuid` varchar(64) NOT NULL,
  `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组的uuid',
  `sys_storage` varchar(64) NOT NULL COMMENT '系统盘对应的存储设备uuid',
  `data_storage` varchar(64) NOT NULL COMMENT '数据盘对应的存储设备uuid',
  `classify` int(11) NOT NULL DEFAULT 1 COMMENT '桌面类型，1-教学桌面，2-个人桌面',
  `terminal_id` int(1) DEFAULT NULL COMMENT '教学桌面对应的终端号',
  `terminal_mac` varchar(32) DEFAULT NULL COMMENT '教学桌面对应的终端mac',
  `terminal_ip` varchar(32) DEFAULT NULL COMMENT '终端ip',
  `ipaddr` varchar(20) DEFAULT NULL COMMENT '桌面的IP地址',
  `mac` varchar(64) DEFAULT '00:00:00:00:00:00',
  `status` varchar(32) DEFAULT 'active',
  `port_uuid` varchar(64) DEFAULT NULL COMMENT '网卡设备相关的port',
  `allocated` tinyint(4) DEFAULT 0 COMMENT '桌面是否已分配给终端',
  `user_uuid` varchar(64) DEFAULT '' COMMENT '桌面绑定的用户uuid',
  `spice_token` varchar(64) DEFAULT NULL COMMENT 'spice随机token',
  `spice_port` varchar(5) DEFAULT NULL COMMENT 'spice端口',
  `spice_link` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'spice链接状态',
  `link_time` datetime DEFAULT NULL COMMENT '链接时间',
  `message` varchar(255) DEFAULT '' COMMENT '桌面的启动错误信息',
  `up_time` datetime DEFAULT NULL COMMENT '桌面启动时间',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='桌面实例表';


/*Table structure for table `yzy_interface_ip` */

DROP TABLE IF EXISTS `yzy_interface_ip`;

CREATE TABLE `yzy_interface_ip` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '子网卡id',
  `uuid` varchar(64) NOT NULL COMMENT '子网卡uuid',
  `name` varchar(64) NOT NULL COMMENT '网卡子ip名称',
  `nic_uuid` varchar(64) NOT NULL COMMENT '网卡uuid',
  `ip` varchar(32) DEFAULT NULL COMMENT 'ip地址',
  `netmask` varchar(32) DEFAULT NULL COMMENT '子网掩码',
  `gateway` varchar(32) DEFAULT NULL COMMENT '网关地址',
  `dns1` varchar(32) DEFAULT '' COMMENT 'DNS1',
  `dns2` varchar(32) DEFAULT '' COMMENT 'DNS2',
  `is_image` tinyint(1) DEFAULT 0 COMMENT '状态, 0-非镜像网络，1-镜像网络',
  `is_manage` tinyint(1) DEFAULT 0 COMMENT '状态, 0-非管理网络，1-管理网络',
  `deleted` int(11) NOT NULL DEFAULT '0' COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `yzy_iso` */

DROP TABLE IF EXISTS `yzy_iso`;

CREATE TABLE `yzy_iso` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ISO文件信息',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(120) NOT NULL COMMENT '上传ISO文件名称',
  `md5_sum` varchar(64) NOT NULL COMMENT 'md5校验值',
  `size` float NOT NULL COMMENT '文件大小',
  `path` varchar(200) NOT NULL COMMENT '文件路径',
  `type` tinyint(1) NOT NULL DEFAULT '1' COMMENT '类型(1-软件包，2-工具包，3-系统包)',
  `os_type` varchar(64) NOT NULL COMMENT '系统类型',
  `desc` varchar(200) DEFAULT NULL COMMENT '描述',
  `status` int(11) NOT NULL,
  `deleted` int(11) NOT NULL DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `yzy_menu` */

DROP TABLE IF EXISTS `yzy_menu`;

CREATE TABLE `yzy_menu` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '菜单栏id',
  `name` varchar(64) NOT NULL COMMENT '菜单名称',
  `title` varchar(64) NOT NULL COMMENT '标题',
  `icon` varchar(128) NOT NULL DEFAULT '' COMMENT '图标',
  `path` varchar(128) NOT NULL DEFAULT '' COMMENT '路径',
  `parent_id` bigint(11) NOT NULL DEFAULT '0' COMMENT '父级菜单id,为0则是一级菜单',
  `status` tinyint(1) NOT NULL DEFAULT '1' COMMENT '状态：1-启用，0-未启用',
  `desc` varchar(128) NOT NULL COMMENT '描述',
  `deleted` int(11) NOT NULL DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `yzy_networks` */

DROP TABLE IF EXISTS `yzy_networks`;

CREATE TABLE `yzy_networks` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '网络ID',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(32) NOT NULL COMMENT '名称',
  `switch_name` varchar(32) NOT NULL COMMENT '虚拟交换机名称',
  `switch_uuid` varchar(64) NOT NULL COMMENT '虚拟交换机uuid',
  `switch_type` varchar(10) NOT NULL COMMENT '虚拟交换机类型, vlan\\flat',
  `vlan_id` int(1) DEFAULT 0 COMMENT 'vlan id',
  `default` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为默认',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='数据网络表';


/*Table structure for table `yzy_node_network_info` */

DROP TABLE IF EXISTS `yzy_node_network_info`;

CREATE TABLE `yzy_node_network_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '节点网络信息',
  `uuid` varchar(64) NOT NULL COMMENT '节点网络uuid',
  `nic` varchar(32) NOT NULL COMMENT '网络接口名称',
  `mac` varchar(200) DEFAULT NULL COMMENT 'mac地址',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `speed` int(11) DEFAULT NULL COMMENT '速度',
  `type` tinyint(1) DEFAULT 0 COMMENT '0-Ethernet，1-bond',
  `status` tinyint(1) DEFAULT 0 COMMENT '状态, 0-未知，1-未激活，2-激活',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='节点网卡信息表';


/*Table structure for table `yzy_node_storages` */

DROP TABLE IF EXISTS `yzy_node_storages`;

CREATE TABLE `yzy_node_storages` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '节点存储设备id',
  `uuid` varchar(64) NOT NULL COMMENT '节点存储设备uuid',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `path` varchar(64) NOT NULL COMMENT '节点存储设备分区路径',
  `role` varchar(64) DEFAULT '' COMMENT '分区的实际存储角色,1-模板系统盘 2-模板数据盘 3-虚拟机系统盘 4-虚拟机数据盘',
  `type` int(11) DEFAULT 1 COMMENT '分区类型，0-ssd 1-hdd',
  `used` bigint(20) NOT NULL COMMENT '已使用',
  `free` bigint(20) NOT NULL COMMENT '剩余',
  `total` bigint(20) NOT NULL COMMENT '总大小',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='节点存储信息表';


/*Table structure for table `yzy_node_services` */

DROP TABLE IF EXISTS `yzy_node_services`;

CREATE TABLE `yzy_node_services` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '节点服务id',
  `uuid` varchar(64) NOT NULL COMMENT '节点服务uuid',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `name` varchar(64) NOT NULL COMMENT '节点服务名称',
  `status` varchar(64) NOT NULL COMMENT '节点服务状态',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='节点服务信息表';

/*Table structure for table `yzy_nodes` */

DROP TABLE IF EXISTS `yzy_nodes`;

CREATE TABLE `yzy_nodes` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '服务器节点',
  `uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `ip` varchar(20) NOT NULL COMMENT '节点ip',
  `name` varchar(64) NOT NULL COMMENT '节点别称',
  `hostname` varchar(64) NOT NULL COMMENT '节点名称',
  `resource_pool_uuid` varchar(64) NOT NULL DEFAULT '' COMMENT '资源池uuid',
  `total_mem` float(5, 2) NOT NULL COMMENT '节点内存，单位：GB',
  `running_mem` float(5, 2) NOT NULL COMMENT '启动内存，单位：GB',
  `single_reserve_mem` int(11) NOT NULL COMMENT '虚机预留内存，单位：GB',
  `total_vcpus` int(11) NOT NULL COMMENT '节点cpu核数',
  `running_vcpus` int(11) NOT NULL COMMENT '运行cpu核数',
  `cpu_utilization` float(5, 2) NULL COMMENT '运行cpu核数',
  `mem_utilization` float(5, 2) NULL COMMENT '运行cpu核数',
  `status` varchar(20) NOT NULL COMMENT '节点状态  active - 正常开机， abnormal - 异常警告，shutdown - 关机',
  `server_version_info` varchar(64) DEFAULT NULL,
  `gpu_info` varchar(100) DEFAULT NULL,
  `cpu_info` varchar(100) DEFAULT NULL,
  `mem_info` varchar(100) DEFAULT NULL,
  `sys_img_uuid` varchar(64) DEFAULT NULL,
  `data_img_uuid` varchar(64) DEFAULT NULL,
  `vm_sys_uuid` varchar(64) DEFAULT NULL,
  `vm_data_uuid` varchar(64) DEFAULT NULL,
  `type` int(11) NOT NULL DEFAULT 0 COMMENT '1、计算和主控一体\n2、计算和备控一体\n3、主控\n4、备控\n5、计算',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='节点信息表';


/*Table structure for table `yzy_operation_log` */

DROP TABLE IF EXISTS `yzy_operation_log`;

CREATE TABLE `yzy_operation_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '操作日志记录',
  `user_id` int(11) DEFAULT NULL COMMENT '用户id',
  `user_name` varchar(255) DEFAULT NULL COMMENT '用户名',
  `user_ip` varchar(20) DEFAULT NULL COMMENT '用户ip',
  `content` text NOT NULL COMMENT '操作内容',
  `result` text NOT NULL COMMENT '操作结果',
  `module` text DEFAULT 'default' COMMENT '操作的模块',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统操作日志';


/*Table structure for table `yzy_personal_desktop` */

DROP TABLE IF EXISTS `yzy_personal_desktop`;

CREATE TABLE `yzy_personal_desktop` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '桌面组的uuid',
  `name` varchar(255) NOT NULL COMMENT '桌面组的名称',
  `owner_id` int(11) NOT NULL DEFAULT 0 COMMENT '创建者ID',
  `pool_uuid` varchar(64) NOT NULL COMMENT '资源池uuid',
  `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
  `network_uuid` varchar(64) NOT NULL COMMENT '网络uuid',
  `subnet_uuid` varchar(64) DEFAULT NULL COMMENT '子网uuid',
  `allocate_type` int(11) DEFAULT 1 COMMENT 'IP分配方案，1-系统分配，2-固定分配',
  `allocate_start` varchar(64) DEFAULT '' COMMENT 'IP为固定分配时的起始IP',
  `vcpu` int(11) NOT NULL COMMENT 'vcpu个数',
  `ram` float NOT NULL COMMENT '虚拟内存，单位为G',
  `os_type` varchar(64) DEFAULT 'windows',
  `sys_restore` tinyint(4) DEFAULT 0 COMMENT '系统盘是否重启还原',
  `data_restore` tinyint(4) DEFAULT 0 COMMENT '数据盘是否重启还原',
  `instance_num` int(11) DEFAULT 1 COMMENT '包含的桌面数',
  `prefix` varchar(128) DEFAULT 'PC' COMMENT '桌面名称的前缀',
  `postfix` int(11) DEFAULT 1 COMMENT '桌面名称的后缀数字个数',
  `postfix_start` int(11) DEFAULT 1 COMMENT '桌面名称后缀的起始数字',
  `desktop_type` int(11) DEFAULT 1 COMMENT '桌面类型，1-随机桌面 2-静态桌面',
  `group_uuid` varchar(64) DEFAULT NULL COMMENT '静态桌面时，绑定的用户组',
  `order_num` int(11) DEFAULT 99 COMMENT '排序号',
  `maintenance` tinyint(4) DEFAULT 1 COMMENT '维护模式，0-否 1-是',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='个人桌面组表';


/*Table structure for table `yzy_random_desktop` */

DROP TABLE IF EXISTS `yzy_random_desktop`;

CREATE TABLE `yzy_random_desktop` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '对应关系的uuid',
  `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '分组uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='桌面随机分配对应关系表';


/*Table structure for table `yzy_resource_pools` */

DROP TABLE IF EXISTS `yzy_resource_pools`;

CREATE TABLE `yzy_resource_pools` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '资源池id',
  `uuid` varchar(64) NOT NULL COMMENT '资源池uuid',
  `name` varchar(64) DEFAULT NULL,
  `desc` varchar(500) DEFAULT NULL COMMENT '描述',
  `default` tinyint(1) DEFAULT 0 COMMENT '是否是默认资源池',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='资源池表';


/*Table structure for table `yzy_role` */

DROP TABLE IF EXISTS `yzy_role`;

CREATE TABLE `yzy_role` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '角色id',
  `role` varchar(64) NOT NULL COMMENT '角色名称',
  `desc` varchar(200) DEFAULT NULL COMMENT '角色描述',
  `enable` tinyint(1) DEFAULT 0 COMMENT '是否启用，0-否，1-是',
  `default` tinyint(1) DEFAULT 0 COMMENT '是否默认，0-否，1-是',
  `deleted` bigint(11) NOT NULL DEFAULT '0' COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `yzy_role_permission` */

DROP TABLE IF EXISTS `yzy_role_permission`;

CREATE TABLE `yzy_role_permission` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '角色权限id',
  `role_id` bigint(11) NOT NULL COMMENT '角色id',
  `menu_id` bigint(11) NOT NULL COMMENT '目录id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--/*Table structure for table `yzy_static_desktop` */
--
--DROP TABLE IF EXISTS `yzy_static_desktop`;
--
--CREATE TABLE `yzy_static_desktop` (
--  `id` int(11) NOT NULL AUTO_INCREMENT,
--  `uuid` varchar(64) NOT NULL COMMENT '对应关系的uuid',
--  `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
--  `instance_uuid` varchar(64) NOT NULL COMMENT '桌面uuid',
--  `user_uuid` varchar(64) NOT NULL COMMENT '桌面绑定的用户uuid',
--  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
--  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
--  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
--  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
--  PRIMARY KEY (`id`)
--) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='桌面静态分配对应关系表';


/*Table structure for table `yzy_subnets` */

DROP TABLE IF EXISTS `yzy_subnets`;

CREATE TABLE `yzy_subnets` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '子网id',
  `uuid` varchar(64) NOT NULL COMMENT '子网uuid',
  `name` varchar(32) NOT NULL COMMENT '子网名称',
  `network_uuid` varchar(64) NOT NULL COMMENT '对应的网络uuid',
  `netmask` varchar(20) NOT NULL COMMENT '子网掩码',
  `gateway` varchar(20) NOT NULL COMMENT '网关',
  `cidr` varchar(20) NOT NULL COMMENT 'cidr段',
  `start_ip` varchar(20) NOT NULL COMMENT '子网段起始IP',
  `end_ip` varchar(20) NOT NULL COMMENT '自网段结束IP',
  `enable_dhcp` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否开启DHCP',
  `dns1` varchar(20) DEFAULT NULL COMMENT 'DNS1',
  `dns2` varchar(20) DEFAULT NULL COMMENT 'DNS2',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='子网信息表';


/*Table structure for table `yzy_task_info` */

DROP TABLE IF EXISTS `yzy_task_info`;

CREATE TABLE `yzy_task_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '任务进度记录',
  `task_id` varchar(64) NOT NULL COMMENT '任务ID',
  `image_id` varchar(64) DEFAULT NULL COMMENT '镜像同步时的镜像ID',
  `version` int(1) DEFAULT 0 COMMENT '镜像版本号',
  `progress` int(11) NOT NULL COMMENT '进度，1-100',
  `status` varchar(32) NOT NULL COMMENT '任务执行情况，begin, running, end',
  `step` int(11) DEFAULT 0 COMMENT '任务的步骤',
  `context` text COMMENT "详情",
  `host_uuid` varchar(64) NOT NULL COMMENT '任务所在的节点',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='同步任务信息表';


/*Table structure for table `yzy_template` */

DROP TABLE IF EXISTS `yzy_template`;

CREATE TABLE `yzy_template` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '桌面模板',
  `uuid` varchar(64) NOT NULL COMMENT '模板的uuid',
  `name` varchar(64) NOT NULL COMMENT '模板的名称',
  `os_type` varchar(20) NOT NULL COMMENT '系统类型，linux,win7,win10',
  `owner_id` varchar(64) NOT NULL COMMENT '所属用户',
  `host_uuid` varchar(64) NOT NULL COMMENT '宿主机uuid',
  `pool_uuid` varchar(64) NOT NULL,
  `network_uuid` varchar(64) NOT NULL COMMENT '网络uuid',
  `subnet_uuid` varchar(64) DEFAULT NULL COMMENT '子网uuid',
  `sys_storage` varchar(64) NOT NULL COMMENT '系统盘对应的存储设备uuid',
  `data_storage` varchar(64) NOT NULL COMMENT '数据盘对应的存储设备uuid',
  `bind_ip` varchar(20) NOT NULL COMMENT '绑定ip',
  `vcpu` int(11) DEFAULT NULL,
  `ram` float NOT NULL COMMENT '内存大小，单位：G',
  `version` int(11) NOT NULL COMMENT '版本号',
  `classify` int(11) DEFAULT 1 COMMENT '模板分类：1、教学模板 2、个人模板 3、系统桌面',
  `status` varchar(20) NOT NULL COMMENT '状态',
  `mac` varchar(64) NOT NULL DEFAULT '00:00:00:00:00:00',
  `port_uuid` varchar(64) NOT NULL COMMENT '模板的虚拟网卡分配',
  `attach` varchar(128) DEFAULT '' COMMENT '挂载的ISO的uuid',
  `desc` text DEFAULT NULL COMMENT '描述',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `updated_time` datetime DEFAULT NULL COMMENT '编辑模板更新时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='模板信息表';


/*Table structure for table `yzy_terminal` */

DROP TABLE IF EXISTS `yzy_terminal`;

CREATE TABLE `yzy_terminal` (
	`id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '记录的唯一编号',
	`terminal_id` INT(11) NOT NULL COMMENT '终端序号,不同组可以重复',
	`mac` CHAR(25) NOT NULL COMMENT '终端MAC地址',
	`ip` VARCHAR(15) NOT NULL COMMENT '终端IP地址',
	`mask` VARCHAR(15) NOT NULL COMMENT '子网掩码',
	`gateway` VARCHAR(15) NOT NULL COMMENT '网关地址',
	`dns1` VARCHAR(15) NOT NULL,
	`dns2` VARCHAR(15) NULL DEFAULT NULL,
	`is_dhcp` CHAR(1) NOT NULL DEFAULT '1' COMMENT 'dhcp: 1-自动 0-静态',
	`name` VARCHAR(256) NOT NULL COMMENT '终端名称',
	`platform` VARCHAR(20) NOT NULL COMMENT '终端CPU架构: arm/x86',
	`soft_version` VARCHAR(50) NOT NULL COMMENT '终端程序版本号: 16.3.8.0',
	`status` CHAR(1) NOT NULL DEFAULT '0' COMMENT '终端状态: 0-离线 1-在线',
	`register_time` DATETIME NULL DEFAULT NULL,
	`conf_version` VARCHAR(20) NOT NULL COMMENT '终端配置版本号',
	`setup_info` VARCHAR(1024) NULL DEFAULT NULL COMMENT '终端设置信息:模式、个性化、windows窗口',
	`group_uuid` CHAR(64) NULL DEFAULT NULL COMMENT '组UUID，默认NULL表示未分组',
	`reserve1` VARCHAR(512) NULL DEFAULT NULL,
	`reserve2` VARCHAR(512) NULL DEFAULT NULL,
	`reserve3` VARCHAR(512) NULL DEFAULT NULL,
	`deleted` INT(11) NULL DEFAULT '0' COMMENT '删除标记',
	`deleted_at` DATETIME NULL DEFAULT NULL,
	`created_at` DATETIME NULL DEFAULT NULL,
	`updated_at` DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `mac_index` (`mac`) USING BTREE,
	INDEX `terminal_id_ip_index` (`terminal_id`, `ip`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='终端配置信息表';


/*Table structure for table `yzy_virtual_switch` */

DROP TABLE IF EXISTS `yzy_virtual_switch`;

CREATE TABLE `yzy_virtual_switch` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '虚拟交换机id',
  `uuid` varchar(64) NOT NULL COMMENT '虚拟交换机uuid',
  `name` varchar(32) NOT NULL COMMENT '虚拟交换名称',
  `type` varchar(10) NOT NULL COMMENT '虚拟交换机类型',
  `default` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为默认',
  `desc` varchar(100) DEFAULT NULL COMMENT '描述',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='虚拟交换机表';


/*Table structure for table `yzy_vswitch_uplink` */

DROP TABLE IF EXISTS `yzy_vswitch_uplink`;

CREATE TABLE `yzy_vswitch_uplink` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '虚拟交换机连接网卡',
  `uuid` varchar(64) NOT NULL,
  `vs_uuid` varchar(64) NOT NULL COMMENT '虚拟交换机uuid',
  `nic_uuid` varchar(64) NOT NULL COMMENT '网卡uuid',
  `node_uuid` varchar(64) DEFAULT NULL COMMENT '节点uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='虚拟交换机映射关系表';

DROP TABLE IF EXISTS `yzy_database_back`;
CREATE TABLE `yzy_database_back` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '数据库备份记录id',
  `name` varchar(64) NOT NULL COMMENT '备份文件名称',
  `node_uuid` varchar(64) NOT NULL COMMENT '文件备份的节点',
  `path` varchar(200) NOT NULL COMMENT '备份文件路径',
  `size` float NOT NULL COMMENT '备份文件大小，单位：MB',
  `type` tinyint(1) NOT NULL DEFAULT '0' COMMENT '备份类型，0-自动备份，1-手动备份',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '0-成功，1-失败',
  `md5_sum` varchar(64) DEFAULT NULL COMMENT 'md5校验值',
  `deleted` int(11) NOT NULL DEFAULT '0' COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='数据库备份记录表';


DROP TABLE IF EXISTS `yzy_crontab_task`;
CREATE TABLE `yzy_crontab_task` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '定时任务id',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(32) NOT NULL COMMENT '定时任务名称',
  `desc` varchar(200) DEFAULT NULL COMMENT '描述',
  `type` tinyint(4) DEFAULT 0 COMMENT '类型(0-数据库自动备份，1-桌面定时任务，2-主机定时关机，3-终端定时关机，4-日志定时清理，5-课表定时任务)',
  `status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '状态 0 -未启用，1-启用',
  `deleted` int(11) NOT NULL DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='定时任务表';


DROP TABLE IF EXISTS `yzy_crontab_detail`;
CREATE TABLE `yzy_crontab_detail` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '详细任务id',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `task_uuid` varchar(64) NOT NULL COMMENT '定时任务uuid',
  `hour` int(11) DEFAULT NULL COMMENT '执行小时',
  `minute` int(11) DEFAULT NULL COMMENT '执行分钟',
  `cycle` varchar(10) DEFAULT '' COMMENT '周期，day/week/month/course：其中course表示课表定时任务的周期',
  `values` text DEFAULT '' COMMENT '记录周 如：1,2,3,4,5 或 json',
  `func` varchar(255) NOT NULL COMMENT '定时任务执行函数',
  `params` text DEFAULT '' COMMENT '执行参数',
  `deleted` int(11) NOT NULL DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='定时任务详细信息表';


DROP TABLE IF EXISTS `yzy_user_random_instance`;
CREATE TABLE `yzy_user_random_instance` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端与随机桌面分配表',
  `uuid` varchar(64) NOT NULL COMMENT '绑定关系uuid',
  `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
  `user_uuid` varchar(64) NOT NULL COMMENT '用户uuid',
  `instance_uuid` varchar(64) NOT NULL COMMENT '桌面uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_terminal_upgrade`;
CREATE TABLE `yzy_terminal_upgrade` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '升级包',
  `uuid` varchar(64) NOT NULL COMMENT '升级包uuid',
  `name` varchar(64) NOT NULL COMMENT '文件名称',
  `platform` varchar(32) NOT NULL DEFAULT '' COMMENT '平台',
  `os` varchar(32) NOT NULL DEFAULT '' COMMENT '系统版本',
  `version` varchar(32) NOT NULL DEFAULT '' COMMENT '版本号',
  `path` varchar(200) NOT NULL DEFAULT '' COMMENT '升级包路径',
  `size` float NOT NULL DEFAULT 0 COMMENT '文件大小',
  `upload_at` datetime DEFAULT NULL COMMENT '上传时间',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_voi_template`;
CREATE TABLE `yzy_voi_template` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT 'VOI模板',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(64) NOT NULL COMMENT '模板名称',
  `desc` text DEFAULT NULL COMMENT '模板描述',
  `os_type` varchar(20) NOT NULL COMMENT '系统类型',
  `owner_id` int(11) NOT NULL COMMENT '所属用户',
  `terminal_mac` varchar(64) NOT NULL DEFAULT '' COMMENT '上传终端mac',
  `host_uuid` varchar(64) NOT NULL COMMENT '所属节点uuid',
  `network_uuid` varchar(64) NOT NULL COMMENT '网络uuid',
  `subnet_uuid` varchar(64) DEFAULT '' COMMENT '子网uuid',
  `sys_storage` varchar(64) NOT NULL COMMENT '系统盘对应的存储设备uuid',
  `data_storage` varchar(64) NOT NULL COMMENT '数据盘对应的存储设备uuid',
  `bind_ip` varchar(20) DEFAULT '' COMMENT '绑定ip',
  `vcpu` int(11) NOT NULL COMMENT 'vcpu',
  `ram` float NOT NULL COMMENT '内存，单位G',
  `classify` int(11) DEFAULT 1 COMMENT '1-教学模板 2-个人模板',
  `version` int(11) NOT NULL DEFAULT 0 COMMENT '版本',
  `operate_id` int(11) NOT NULL DEFAULT 0 COMMENT '操作号',
  `status` varchar(32) NOT NULL COMMENT 'active-开机 inactive-关机 updating-更新中 error-异常',
  `mac` varchar(64) NOT NULL,
  `port_uuid` varchar(64) NOT NULL,
  `updated_time` datetime DEFAULT NULL COMMENT '编辑模板更新时间',
  `all_group` tinyint(1) DEFAULT 0 COMMENT '是否绑定所有教学分组',
  `attach` varchar(64) DEFAULT NULL COMMENT '挂载的ISO的uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_voi_template_to_groups`;
CREATE TABLE `yzy_voi_template_to_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'VOI模板分配教学分组关系表',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '教学分组',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='模板关联桌面分组';


DROP TABLE IF EXISTS `yzy_voi_device_info`;
CREATE TABLE `yzy_voi_device_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '磁盘的uuid',
  `type` varchar(32) NOT NULL DEFAULT 'data' COMMENT '磁盘类型，system or data',
  `device_name` varchar(32) NOT NULL DEFAULT 'vda' COMMENT '设备名称，vda/vdb/...',
  `image_id` varchar(64) DEFAULT '' COMMENT '磁盘镜像uuid',
  `instance_uuid` varchar(64) NOT NULL COMMENT '虚机uuid',
  `boot_index` int(11) NOT NULL DEFAULT -1 COMMENT 'boot序列',
  `disk_bus` varchar(32) DEFAULT 'virtio' COMMENT '设备总线，如：virtio',
  `source_type` varchar(32) DEFAULT 'file' COMMENT '磁盘文件类型',
  `source_device` varchar(32) DEFAULT 'disk' COMMENT '设备类型',
  `size` int(11) DEFAULT 0 COMMENT '磁盘大小，单位为GB',
  `section` bigint(20) DEFAULT 0 COMMENT '磁盘扇区个数，bytes / 512',
  `used` float DEFAULT 0 COMMENT '磁盘已使用大小，单位为GB，保留两位小数',
  `diff1_ver` int(11) DEFAULT 0 COMMENT '差分1的版本号',
  `diff2_ver` int(11) DEFAULT 0 COMMENT '差分2的版本号',
  `progress` int(11) DEFAULT 0 COMMENT '客户端上传时，上传的进度',
  `upload_path` varchar(255) DEFAULT '' COMMENT '客户端上传时，上传的镜像存放路径',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='虚拟机的磁盘信息表';


DROP TABLE IF EXISTS `yzy_voi_template_operate`;
CREATE TABLE `yzy_voi_template_operate` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '模板更新记录',
  `uuid` varchar(64) NOT NULL COMMENT '模板记录uuid',
  `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
  `remark` text DEFAULT NULL COMMENT '记录信息',
  `op_type` tinyint(4) NOT NULL DEFAULT 1 COMMENT '操作类型, 1-更新，2-版本回退',
  `exist` tinyint(1) NOT NULL DEFAULT 0 COMMENT '该版本是否还存在',
  `version` int(11) NOT NULL DEFAULT 0 COMMENT '版本号',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='模板操作记录';


DROP TABLE IF EXISTS `yzy_voi_desktop_group`;
CREATE TABLE `yzy_voi_desktop_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL COMMENT '桌面组的uuid',
  `name` varchar(128) NOT NULL COMMENT '桌面组的名称',
  `owner_id` int(11) NOT NULL DEFAULT 0 COMMENT '创建者ID',
  `group_uuid` varchar(64) NOT NULL COMMENT '所属分组',
  `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
  `os_type` varchar(64) DEFAULT 'windows_7_x64',
  `sys_restore` tinyint(4) DEFAULT 1 COMMENT '系统盘是否重启还原',
  `data_restore` tinyint(4) DEFAULT 1 COMMENT '数据盘是否重启还原，大于1代表没有数据盘',
  `sys_reserve_size` int(11) DEFAULT 0 COMMENT '系统盘保留空间',
  `data_reserve_size` int(11) DEFAULT 0 COMMENT '数据盘保留空间',
  `prefix` varchar(128) DEFAULT 'PC' COMMENT '桌面名称的前缀',
  `use_bottom_ip` tinyint(1) DEFAULT TRUE COMMENT '是否使用底层客户端IP作为桌面IP',
  `ip_detail` text DEFAULT '' COMMENT '不使用底层IP时的IP设置规则',
  `active` tinyint(1) DEFAULT FALSE COMMENT '是否激活，0-未激活，1-激活',
  `default` tinyint(1) DEFAULT FALSE COMMENT '是否为默认',
  `show_info` tinyint(1) DEFAULT FALSE COMMENT '是否显示桌面信息，0-不显示，1-显示',
  `auto_update` tinyint(1) DEFAULT FALSE COMMENT '是否自动更新桌面，0-否，1-是',
  `diff_mode` tinyint(1) DEFAULT 1 COMMENT '差分盘合并模式，0-不合并(覆盖模式)，1-合并(增量模式)',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='教学桌面组表';


DROP TABLE IF EXISTS `yzy_voi_group`;
CREATE TABLE `yzy_voi_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL COMMENT '教学分组名称',
  `desc` varchar(255) DEFAULT NULL,
  `group_type` int(11) DEFAULT 1 COMMENT '1-教学分组',
  `start_ip` varchar(20) DEFAULT NULL COMMENT '预设终端的开始IP',
  `end_ip` varchar(20) DEFAULT NULL COMMENT '预设终端的结束IP',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '终端预设分组规则，默认启用',
  `dhcp` text DEFAULT NULL COMMENT 'dhcp配置',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='分组表';


DROP TABLE IF EXISTS `yzy_voi_terminal`;
CREATE TABLE `yzy_voi_terminal` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'VOI终端信息表',
  `uuid` varchar(64) NOT NULL COMMENT '终端uuid',
  `terminal_id` int(11) NOT NULL COMMENT '终端序号,不同组可以重复',
  `name` varchar(64) NOT NULL COMMENT '终端名称',
  `status` tinyint(1) NOT NULL DEFAULT 0 COMMENT '终端状态: 0-离线 1-在线，2-维护状态，3-部署状态，4-UEFI模式',
  `ip` varchar(16) NOT NULL COMMENT '终端IP地址',
  `mac` varchar(20) NOT NULL COMMENT '终端MAC地址',
  `mask` varchar(15) NOT NULL COMMENT '子网掩码',
  `gateway` varchar(15) NOT NULL COMMENT '网关地址',
  `dns1` varchar(15) NOT NULL,
  `dns2` varchar(15) DEFAULT NULL,
  `is_dhcp` char(1) NOT NULL DEFAULT '1' COMMENT 'dhcp: 1-自动 0-静态',
  `platform` varchar(20) NOT NULL COMMENT '终端CPU架构: arm/x86',
  `soft_version` varchar(50) NOT NULL COMMENT '终端程序版本号: 16.3.8.0',
  `register_time` datetime DEFAULT NULL,
  `conf_version` varchar(20) NOT NULL COMMENT '终端配置版本号',
  `setup_info` varchar(1024) DEFAULT NULL COMMENT '终端设置信息:模式、个性化、windows窗口',
  `group_uuid` char(64) DEFAULT NULL COMMENT '组UUID，默认NULL表示未分组',
  `disk_residue` float DEFAULT NULL COMMENT '剩余磁盘容量，单位：G',
  `deleted` bigint(11) DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
--   UNIQUE KEY `mac_index` (`mac`) USING BTREE,
  KEY `terminal_id_ip_index` (`terminal_id`,`ip`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='终端配置信息表';

DROP TABLE IF EXISTS `yzy_warning_log`;
CREATE TABLE `yzy_warning_log` (
  `id` INT(11) NOT NULL,
  `number_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '编号',
  `option` INT(11) NOT NULL DEFAULT 0 COMMENT '警告项：1、CPU利用率\n2、内存利用率\n3、磁盘使用空间\n4、磁盘IO利用率\n5、网络上下行速度\n6、云桌面运行时间\n7、系统授权过期剩余日期',
  `ip` VARCHAR(32) NOT NULL COMMENT 'ip地址',
  `content` VARCHAR(64) NOT NULL COMMENT '警告内容',
  `deleted` INT(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `created_at` DATETIME DEFAULT NULL COMMENT '创建时间',
  `deleted_at` DATETIME DEFAULT NULL COMMENT '删除时间',
  `updated_at` DATETIME DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `number_id` (`number_id`)
)ENGINE=INNODB DEFAULT CHARSET=utf8 COMMENT='警告日志表';


DROP TABLE IF EXISTS `yzy_voi_torrent_task`;
CREATE TABLE `yzy_voi_torrent_task` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '任务',
  `uuid` varchar(64) NOT NULL COMMENT '任务uuid',
  `torrent_id` varchar(64) NOT NULL COMMENT '种子id',
  `torrent_name` varchar(64) NOT NULL COMMENT '种子名称',
  `torrent_path` varchar(200) NOT NULL COMMENT '种子路径',
  `torrent_size` int(11) NOT NULL DEFAULT 0 COMMENT '种子文件大小',
  `desktop_name` varchar(32) NOT NULL COMMENT '桌面组名称',
  `template_uuid` varchar(64) NOT NULL COMMENT '对应模板uuid',
  `disk_uuid` varchar(64) NOT NULL COMMENT '磁盘uuid',
  `disk_name` varchar(64) NOT NULL COMMENT '磁盘名称',
  `disk_size` float NOT NULL COMMENT '磁盘文件大小，单位G',
  `disk_type` varchar(32) NOT NULL COMMENT '磁盘类型，系统盘-system,数据盘-data',
  `save_path` varchar(200) NOT NULL COMMENT '文件保存路径',
  `terminal_mac` varchar(32) NOT NULL COMMENT '终端mac',
  `terminal_ip` varchar(32) NOT NULL COMMENT '终端ip',
  `type` tinyint(1) NOT NULL COMMENT '任务类型，0-上传，1-下载',
  `status` tinyint(1) NOT NULL DEFAULT 0 COMMENT '任务状态，0-初始状态，1-进行中，2-完成',
  `batch_no` bigint(11) NOT NULL DEFAULT 0 COMMENT '任务批次号',
  `sum` int(5) NOT NULL DEFAULT 1 COMMENT '批次任务的任务总数',
  `state` varchar(32) NOT NULL DEFAULT '' COMMENT '任务状态',
  `process` int(5) NOT NULL DEFAULT 0 COMMENT '任务进度',
  `download_rate` int(5) NOT NULL DEFAULT 0 COMMENT '下载速率',
  `upload_rate` int(5) NOT NULL DEFAULT 0 COMMENT '上传速率',
  `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_warn_setup`;
CREATE TABLE `yzy_warn_setup` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '告警设置表',
  `status` INT(11) NOT NULL DEFAULT 0 COMMENT '启用状态，0-未启用，1-启用',
  `option` VARCHAR(1024) NOT NULL COMMENT '告警项',
  `deleted` INT(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `created_at` DATETIME DEFAULT NULL,
  `deleted_at` DATETIME DEFAULT NULL,
  `updated_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=INNODB DEFAULT CHARSET=utf8 COMMENT='告警设置表';


DROP TABLE IF EXISTS `yzy_voi_terminal_to_desktops`;
CREATE TABLE `yzy_voi_terminal_to_desktops` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端与桌面组的关联表',
  `uuid` varchar(64) NOT NULL,
  `terminal_uuid` varchar(64) NOT NULL COMMENT '终端uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '分组uuid',
  `desktop_group_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
  `terminal_mac` varchar(20) NOT NULL COMMENT '终端MAC地址',
  `desktop_is_dhcp` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'dhcp: 1-自动 0-静态',
  `desktop_ip` varchar(16) NOT NULL COMMENT '桌面IP',
  `desktop_mask` varchar(16) NOT NULL COMMENT '桌面IP子网掩码',
  `desktop_gateway` varchar(16) NOT NULL COMMENT '桌面IP网关',
  `desktop_dns1` varchar(16) NOT NULL COMMENT '桌面DNS1',
  `desktop_dns2` varchar(16) DEFAULT '' COMMENT '桌面DNS2',
  `desktop_status` tinyint(1) NOT NULL DEFAULT 0 COMMENT '0-离线 1-在线',
  `desktop_is_sent` tinyint(1) NOT NULL DEFAULT 0 COMMENT '桌面是否已经下发标志 0-未下发 1-已下发',
  `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=UTF8;

DROP TABLE IF EXISTS `yzy_voi_terminal_share_disk`;
CREATE TABLE `yzy_voi_terminal_share_disk` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端共享数据盘',
  `uuid` varchar(64) NOT NULL COMMENT '共享数据盘uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '所属分组uuid',
  `disk_size` int(11) NOT NULL COMMENT '数据盘大小，单位:G',
  `restore` tinyint(1) NOT NULL DEFAULT 0 COMMENT '数据盘还原与不还原，0-还原，1-还原',
  `enable` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否启用，0-未启用，1-启用',
  `version` int(11) NOT NULL DEFAULT 0 COMMENT '共享盘版本',
  `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_voi_share_to_desktops`;
CREATE TABLE `yzy_voi_share_to_desktops` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '共享盘与桌面组的绑定',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '共享盘所属终端分组',
  `disk_uuid` varchar(64) NOT NULL COMMENT '共享数据盘uuid',
  `desktop_uuid` varchar(64) NOT NULL COMMENT '桌面组uuid',
  `desktop_name` varchar(64) NOT NULL COMMENT '桌面组name',
  `deleted` bigint(11) NOT NULL COMMENT '删除标志',
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `yzy_bond_nics`;
CREATE TABLE `yzy_bond_nics` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'bond逻辑网卡与物理网卡映射关系id',
  `uuid` varchar(64) NOT NULL COMMENT 'bond逻辑网卡与物理网卡映射关系uuid',
  `mode` int(11) DEFAULT NULL COMMENT 'bond类型',
  `master_uuid` varchar(64) NOT NULL COMMENT 'bond逻辑网卡uuid',
  `master_name` varchar(32) NOT NULL COMMENT 'bond逻辑网卡name',
  `slave_uuid` varchar(64) NOT NULL COMMENT '物理网卡uuid',
  `slave_name` varchar(32) NOT NULL COMMENT '物理网卡',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='bond逻辑网卡与物理网卡映射关系表';


DROP TABLE IF EXISTS `yzy_monitor_half_min`;
CREATE TABLE `yzy_monitor_half_min` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `node_datetime` datetime NOT NULL COMMENT '节点监控时间',
  `monitor_info` mediumtext DEFAULT NULL COMMENT '监控信息json',
  `auto` tinyint(1) DEFAULT 0 COMMENT '是否为自动补齐，默认补齐为前一条数据',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `node_uuid_index` (`node_uuid`,`node_datetime`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='节点30s监控信息表';


DROP TABLE IF EXISTS `yzy_menu_permission`;

CREATE TABLE `yzy_menu_permission` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `pid` bigint(20) DEFAULT NULL COMMENT '上级菜单ID',
  `type` int(11) DEFAULT NULL COMMENT '菜单类型',
  `title` varchar(255) DEFAULT NULL COMMENT '菜单标题',
  `name` varchar(255) DEFAULT NULL COMMENT '组件名称',
  `component` varchar(255) DEFAULT NULL COMMENT '组件',
  `bread_num` tinyint(1) DEFAULT NULL COMMENT '面包屑层级',
  `menu_sort` int(5) DEFAULT NULL COMMENT '排序',
  `icon_show` varchar(255) DEFAULT NULL COMMENT '图标展示',
  `icon_click` varchar(255) DEFAULT NULL COMMENT '图标点击',
  `path` varchar(255) DEFAULT NULL COMMENT '链接地址',
  `redirect` varchar(255) DEFAULT NULL COMMENT '设置默认打开的页面',
  `login` tinyint(1) DEFAULT 1 COMMENT '是否需要登录',
  `hidden` tinyint(1) NOT NULL DEFAULT 0 COMMENT '隐藏',
  `permission` varchar(255) DEFAULT NULL COMMENT '权限',
  `deleted` bigint(20) NOT NULL DEFAULT 0,
  `deleted_at` varchar(255) DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `inx_pid` (`pid`),
  KEY `uniq_name` (`name`),
  KEY `uniq_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='系统菜单';

DROP TABLE IF EXISTS `yzy_ha_info`;
CREATE TABLE `yzy_ha_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'HA配置记录',
  `uuid` varchar(64) NOT NULL COMMENT 'HA配置记录uuid',
  `vip` varchar(20) NOT NULL COMMENT '浮动IP',
  `netmask` varchar(20) NOT NULL COMMENT '浮动IP子网掩码',
  `quorum_ip` varchar(20) NOT NULL COMMENT '仲裁IP',
  `sensitivity` int(11) NOT NULL COMMENT '敏感度',
  `master_ip` varchar(20) NOT NULL COMMENT '初始主控节点管理IP',
  `backup_ip` varchar(20) NOT NULL COMMENT '初始备控节点管理IP',
  `master_nic` varchar(32) NOT NULL COMMENT '初始主控节点心跳网卡名称',
  `backup_nic` varchar(32) NOT NULL COMMENT '初始备控节点心跳网卡名称',
  `master_nic_uuid` varchar(64) NOT NULL COMMENT '初始主控节点心跳网卡uuid',
  `backup_nic_uuid` varchar(64) NOT NULL COMMENT '初始备控节点心跳网卡uuid',
  `master_uuid` varchar(64) NOT NULL COMMENT '初始主控节点uuid',
  `backup_uuid` varchar(64) NOT NULL COMMENT '初始备控节点uuid',
  `ha_enable_status` int(11) DEFAULT 0 COMMENT 'HA启用状态：0已启用，1未启用',
  `ha_running_status` int(11) DEFAULT 0 COMMENT 'HA运行状态：0正常，1故障',
  `data_sync_status` int(11) DEFAULT 0 COMMENT '数据同步状态：0已同步，1同步中，2同步失败',
  `master_net_status` int(11) DEFAULT 0 COMMENT '初始主控节点网络连接状态：0正常，1断开，2未知',
  `backup_net_status` int(11) DEFAULT 0 COMMENT '初始备控节点网络连接状态：0正常，1断开，2未知',
  `deleted` int(11) DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='HA配置表';


CREATE TABLE `yzy_term` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '学期id',
  `uuid` varchar(64) NOT NULL COMMENT '学期uuid',
  `name` varchar(32) NOT NULL COMMENT '学期名称',
  `start` varchar(10) NOT NULL COMMENT '学期开始日期',
  `end` varchar(10) NOT NULL COMMENT '学期结束日期',
  `duration` int(11) NOT NULL COMMENT '课堂时长',
  `break_time` int(11) NOT NULL COMMENT '课间时长',
  `morning` varchar(5) NOT NULL COMMENT '上午开始时间',
  `afternoon` varchar(5) NOT NULL COMMENT '下午开始时间',
  `evening` varchar(5) NOT NULL COMMENT '晚上开始时间',
  `morning_count` int(11) NOT NULL COMMENT '上午上课节数',
  `afternoon_count` int(11) NOT NULL COMMENT '下午上课节数',
  `evening_count` int(11) NOT NULL COMMENT '晚上上课节数',
  `course_num_map` text NOT NULL COMMENT '上课时间映射表:{"1": "08:00-08:45", "2": "09:00-09:45", ...,  "10": "20:00-20:45"}',
  `weeks_num_map` text NOT NULL COMMENT '学期周映射表:{''1'': [''2020/08/31'', ''2020/09/06''], ''2'': [''2020/09/07'', ''2020/09/13''], ...}',
  `crontab_task_uuid` varchar(64) NOT NULL COMMENT '定时任务uuid',
  `group_status_map` text NOT NULL COMMENT '教学桌面组uuid与启用状态映射表，状态: 0-已禁用,1-已启用：{"41b212d6-3ef4-49f1-851d-424cb4559261": 1, "f33d3ff2-af44-437e-9c78-7b5be9e4f09f":  0, ...} ',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT 'updated_at',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学期表';

CREATE TABLE `yzy_course_schedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '周课表id',
  `uuid` varchar(64) NOT NULL COMMENT '周课表uuid',
  `term_uuid` varchar(64) NOT NULL COMMENT '学期uuid',
  `group_uuid` varchar(64) NOT NULL COMMENT '教学分组uuid',
  `course_template_uuid` varchar(64) NOT NULL COMMENT '周课表模板uuid',
  `week_num` int(11) NOT NULL COMMENT '第几周',
  `course_md5` varchar(64) NOT NULL COMMENT '课程内容md5',
  `status` int(11) NOT NULL COMMENT '状态: 0-已禁用,1-已启用',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='周课表';

CREATE TABLE `yzy_course_template` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '周课表模板id',
  `uuid` varchar(64) NOT NULL COMMENT '周课表模板uuid',
  `desktops` text NOT NULL COMMENT '教学桌面组uuid与名称映射表: {''f56036ca-e91d-440c-8e33-26a18c1f7220'': ''数学'', ''71775fe7-c8b9-48e9-a1fd-898bd0e804f6'':  ''英语'',  ''9f9959c7-339a-40a5-9ee0-7bde87296bf4'': ''计算机'' }',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='周课表模板';

CREATE TABLE `yzy_course` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '课程id',
  `uuid` varchar(64) NOT NULL COMMENT '课程uuid',
  `course_template_uuid` varchar(64) NOT NULL COMMENT '周课表模板uuid',
  `desktop_uuid` varchar(64) NOT NULL COMMENT '教学桌面组uuid',
  `weekday` int(11) NOT NULL COMMENT '星期几',
  `course_num` int(11) NOT NULL COMMENT '第几节课',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='课程';

DROP TABLE IF EXISTS `yzy_task`;
CREATE TABLE `yzy_task` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '任务id',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `task_uuid` varchar(64) NOT NULL COMMENT '任务uuid',
  `name` varchar(64) NOT NULL COMMENT '任务名称',
  `status` varchar(20) NOT NULL COMMENT '任务状态',
  `type` int(11) DEFAULT 0 COMMENT '任务类型',
  `deleted` int(11) DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='任务信息表';

/*Table structure for table `yzy_remote_storages` */

DROP TABLE IF EXISTS `yzy_remote_storages`;

CREATE TABLE `yzy_remote_storages` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '远端存储设备id',
  `uuid` varchar(64) NOT NULL COMMENT '远端存储设备uuid',
  `name` varchar(32) NOT NULL COMMENT '远端存储名称',
  `server` varchar(100) NOT NULL COMMENT '远端存储远程地址',
  `role` varchar(64) DEFAULT '' COMMENT '分区的实际存储角色,1-模板系统盘 2-模板数据盘 3-虚拟机系统盘 4-虚拟机数据盘',
  `type` int(11) DEFAULT 0 COMMENT '远端存储类型，0-nfs',
  `used` bigint(20) DEFAULT NULL COMMENT '已使用',
  `free` bigint(20) DEFAULT NULL COMMENT '剩余',
  `total` bigint(20) DEFAULT NULL COMMENT '总大小',
  `allocated` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已分配给资源池，0-否，1-是',
  `allocated_to` varchar(64) DEFAULT NULL COMMENT '分配资源池uuid',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='远端存储信息表';

DROP TABLE IF EXISTS `yzy_voi_terminal_performance`;
CREATE TABLE `yzy_voi_terminal_performance` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'voi终端性能id',
  `uuid` varchar(64) NOT NULL COMMENT 'voi终端性能uuid',
  `terminal_uuid` varchar(64) NOT NULL COMMENT '终端uuid',
  `terminal_mac` varchar(32) NOT NULL COMMENT '终端mac地址',
  `cpu_ratio` float(5, 2) NULL COMMENT '运行cpu速率',
  `network_ratio` float(5, 2) NULL COMMENT '网络速率',
  `memory_ratio` float(5, 2) NULL COMMENT '内存占有率',
  `cpu_temperature` float(5, 2) NULL COMMENT 'cpu温度',
  `hard_disk` float(5, 2) NULL COMMENT '硬盘占有率',
  `cpu` text COMMENT 'cpu信息',
  `memory` text COMMENT '内存信息',
  `network` text COMMENT '网络信息',
  `hard` text COMMENT '硬盘信息',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='voi终端性能监控表';

DROP TABLE IF EXISTS `yzy_voi_terminal_hard_ware`
CREATE TABLE `yzy_voi_terminal_hard_ware` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'voi硬件记录id',
  `uuid` varchar(64) NOT NULL COMMENT 'voi硬件记录uuid',
  `terminal_uuid` varchar(64) NOT NULL COMMENT '终端uuid',
  `terminal_mac` varchar(32) NOT NULL COMMENT '终端mac地址',
  `content` text COMMENT '硬件变更详情',
  `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='voi终端硬件记录表';

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
insert  into `yzy_role`(`id`,`role`,`desc`,`enable`,`default`,`deleted`,`deleted_at`,`updated_at`,`created_at`) values (1,'超级管理员','超级管理员默认角色',1,1,0,NULL,'2020-05-06 11:41:15','2020-05-06 11:41:17');
insert  into `yzy_admin_user`(`id`,`username`,`password`,`last_login`,`login_ip`,`real_name`,`role_id`,`email`,`is_superuser`,`is_active`,`desc`,`deleted`,`deleted_at`,`updated_at`,`created_at`) values (1,'admin','ADMIN_PASSWORD','2020-03-18 17:34:03','127.0.0.1','123',1,'11@qq.com',1,1,NULL,0,NULL,NULL,'2020-03-07 15:49:53');
insert  into `yzy_terminal_upgrade`(`id`,`uuid`,`name`,`platform`,`os`,`version`,`path`,`size`,`upload_at`,`deleted`,`deleted_at`,`created_at`,`updated_at`) values (1,'e2dfad28-8050-11ea-a129-562668d3ccea','ARM端','ARM','linux','','',0,'2020-04-21 12:46:48',0,NULL,'2020-04-17 10:13:22','2020-04-17 10:13:19'),(2,'2d5842fe-8051-11ea-aa53-562668d3ccea','Linux端','x86','linux','','',0,'2020-04-18 08:45:27',0,NULL,'2020-04-17 10:15:21','2020-04-17 10:15:41'),(3,'785298fe-8051-11ea-9f01-562668d3ccea','Windows端','x86','windows','','',0,'2020-04-18 08:40:38',0,NULL,'2020-04-17 10:17:09','2020-04-17 10:17:11');
insert  into `yzy_menu_permission`(`id`,`pid`,`type`,`title`,`name`,`component`,`bread_num`,`menu_sort`,`icon_show`,`icon_click`,`path`,`redirect`,`login`,`hidden`,`permission`,`deleted`,`deleted_at`,`created_at`,`updated_at`) values
(1,NULL,1,'首页','home','home/home',0,NULL,'../assets/images/home_n.png','../assets/images/home_p.png','/home/home',NULL,1,0,'home',0,NULL,NULL,NULL),
(2,NULL,1,'资源管理','resManagement',NULL,NULL,NULL,'/assets/navIcon/ziyuan_n.png','/assets/navIcon/ziyuan_p.png',NULL,NULL,1,0,'resMge',0,NULL,NULL,NULL),
(3,NULL,1,'教学桌面管理','teachDesktopManage',NULL,NULL,NULL,'/assets/navIcon/jiaoxuetable_n.png','/assets/navIcon/jiaoxuetable_p.png',NULL,NULL,1,0,'teachDeskMge',0,NULL,NULL,NULL),
(4,NULL,1,'个人桌面管理','personalDesktopManage',NULL,NULL,NULL,'/assets/navIcon/peple-table_n.png','/assets/navIcon/peple-table_p.png',NULL,NULL,1,0,'perDeskMge',0,NULL,NULL,NULL),
(5,NULL,1,'监控管理','monitor',NULL,NULL,NULL,'/assets/images/jiankong_n.png','/assets/images/jiankong_p.png',NULL,NULL,1,0,'monitorMge',0,NULL,NULL,NULL),
(6,NULL,1,'终端管理','terminalManage',NULL,NULL,NULL,'/assets/images/zhongduan_n.png','/assets/images/zhongduan_p.png',NULL,NULL,1,0,'terminalMge',0,NULL,NULL,NULL),
(7,NULL,1,'系统管理','systemManage',NULL,NULL,NULL,'/assets/images/xitong_n.png','/assets/images/xitong_p.png',NULL,NULL,1,0,'systemMge',0,NULL,NULL,NULL),
(8,2,1,'主控管理','masterControlManagement','resManagement/masterControlManagement',1,NULL,NULL,NULL,'/resManagement/masterControlManagement',NULL,1,0,'resMge:masterMge',0,NULL,NULL,NULL),
(9,2,3,'资源池管理','resPoolManagement','resManagement/resPoolManagement',1,NULL,NULL,NULL,'/resManagement/resPoolManagement',NULL,1,0,'resMge:resPoolMge',0,NULL,NULL,NULL),
(10,2,1,'网络管理','networkManagement','resManagement/networkManagement',1,NULL,NULL,NULL,'/resManagement/networkManagement',NULL,1,0,'resMge:networkMge',0,NULL,NULL,NULL),
(11,2,1,'ISO库','isoLibrary','resManagement/isoLibrary',1,NULL,NULL,NULL,'/resManagement/isoLibrary',NULL,1,0,'resMge:isoLib',0,NULL,NULL,NULL),
(15,8,2,'本地网络','localNetwork',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(16,8,2,'服务','service',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(17,8,2,'模板磁盘文件','diskFile',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(18,8,2,'存储配置','stoarge',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(19,9,4,'基础镜像','baseImage','resManagement/jumpPage/baseImage',2,NULL,NULL,NULL,'/resManagement/jumpPage/baseImage/:uuid/:name',NULL,1,0,'resMge:resPoolMge:baseImage',0,NULL,NULL,NULL),
(20,10,2,'数据网络','dataNetwork',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(21,10,2,'分布式虚拟交换机','distributedVirtualSwitch',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(22,10,2,'管理网络','manageNetwork',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(23,3,2,'VDI场景','teachDesktopVDI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(24,3,2,'VOI场景','teachDesktopVOI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(25,23,1,'教学模板','teachTem','teachDesktopManage/teachTem',1,NULL,NULL,NULL,'/teachDesktopManage/teachTem',NULL,1,0,'teachDeskMge:teachTem',0,NULL,NULL,NULL),
(26,24,5,'教学模板','teachTem','teachDesktopManage/teachTem',1,NULL,NULL,NULL,'/teachDesktopManage/teachTem',NULL,1,0,'teachDeskMge:teachTem',0,NULL,NULL,NULL),
(27,23,1,'教学分组','teachgroup','teachDesktopManage/teachgroup',1,NULL,NULL,NULL,'/teachDesktopManage/teachgroup',NULL,1,0,'teachDeskMge:teachGroup',0,NULL,NULL,NULL),
(28,24,5,'教学分组','teachgroup','teachDesktopManage/teachgroup',1,NULL,NULL,NULL,'/teachDesktopManage/teachgroup',NULL,1,0,'teachDeskMge:teachGroup',0,NULL,NULL,NULL),
(29,23,1,'教学桌面组','teachDeskGroup','teachDesktopManage/teachDeskGroup',1,NULL,NULL,NULL,'/teachDesktopManage/teachDeskGroup',NULL,1,0,'teachDeskMge:teachDeskGroup',0,NULL,NULL,NULL),
(30,24,5,'教学桌面组','teachDeskGroup','teachDesktopManage/teachDeskGroup',1,NULL,NULL,NULL,'/teachDesktopManage/teachDeskGroup',NULL,1,0,'teachDeskMge:teachDeskGroup',0,NULL,NULL,NULL),
(31,4,1,'个人模板','personalTem','personalDesktopManage/personalTem',1,NULL,NULL,NULL,'/personalDesktopManage/personalTem',NULL,1,0,'perDeskMge:personalTem',0,NULL,NULL,NULL),
(32,4,1,'用户管理','userManage','personalDesktopManage/userManage',1,NULL,NULL,NULL,'/personalDesktopManage/userManage',NULL,1,0,'perDeskMge:userMge',0,NULL,NULL,NULL),
(33,4,1,'个人桌面组','personalDeskGroup','personalDesktopManage/personalDeskGroup',1,NULL,NULL,NULL,'/personalDesktopManage/personalDeskGroup',NULL,1,0,'perDeskMge:perDeskGroup',0,NULL,NULL,NULL),
(34,6,1,'终端列表','terminalManageList','terminalManage/terminalManageList',1,NULL,NULL,NULL,'/terminalManage/terminalManageList',NULL,1,0,'terminalMge:terminalList',0,NULL,NULL,NULL),
(35,34,2,'VDI场景','terminalVDI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(36,34,2,'VOI场景','terminalVOI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(37,7,1,'系统桌面','systemDesktop','systemManage/systemDesktop',1,NULL,NULL,NULL,'/systemManage/systemDesktop',NULL,1,0,'systemMge:systemDesktop',0,NULL,NULL,NULL),
(38,7,1,'策略设置','strategySet','systemManage/strategySet',1,NULL,NULL,NULL,'/systemManage/strategySet',NULL,1,0,'systemMge:strategySet',0,NULL,NULL,NULL),
(39,7,1,'数据库备份','databaseBackup','systemManage/databaseBackup',1,NULL,NULL,NULL,'/systemManage/databaseBackup',NULL,1,0,'systemMge:dbBackup',0,NULL,NULL,NULL),
(40,7,1,'管理员管理','administratorManagement','systemManage/administratorManagement',1,NULL,NULL,NULL,'/systemManage/administratorManagement',NULL,1,0,'systemMge:adminMge',0,NULL,NULL,NULL),
(41,7,1,'定时任务','timingTask','systemManage/timingTask',1,NULL,NULL,NULL,'/systemManage/timingTask',NULL,1,0,'systemMge:timingTask',0,NULL,NULL,NULL),
(42,7,3,'日志管理','logManagement','systemManage/logManagement',1,NULL,NULL,NULL,'/systemManage/logManagement',NULL,1,0,'systemMge:logMge',0,NULL,NULL,NULL),
(43,7,3,'授权与服务','authorization','systemManage/authorization',1,NULL,NULL,NULL,'/systemManage/authorization',NULL,1,0,'systemMge:authMge',0,NULL,NULL,NULL),
(44,7,1,'升级管理','upgradeManagement','systemManage/upgradeManagement',1,NULL,NULL,NULL,'/systemManage/upgradeManagement',NULL,1,0,'systemMge:upgradeMge',0,NULL,NULL,NULL),
(45,38,2,'VDI场景','strategySetVDI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(46,38,2,'VOI场景','strategySetVOI',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(47,40,2,'角色管理','roleManager',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(48,40,2,'管理员列表','adminList',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(49,41,2,'桌面定时开关机','desktopTimingSwitch',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(50,41,2,'主机定时开关机','nodeTimingSwitch',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(51,41,2,'终端定时关机','terminalTimingSwitch',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(52,42,2,'警告日志','warningLog',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(53,42,2,'操作日志','operationLog',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(54,42,2,'系统日志导出','systemLogExport',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(55,23,4,'详情','teachDeskGroupDeatil','teachDesktopManage/teachDeskGroupDeatil',2,NULL,NULL,NULL,'/teachDesktopManage/teachDeskGroupDeatil/:id',NULL,1,0,'teachDesktopManage:teachDeskGroupDeatil',0,NULL,NULL,NULL),
(56,24,4,'详情','teachDeskGroupDeatil','teachDesktopManage/teachDeskGroupDeatilVoi',2,NULL,NULL,NULL,'/teachDesktopManage/teachDeskGroupDeatilVoi/:id',NULL,1,0,'teachDesktopManage:teachDeskGroupDeatil',0,NULL,NULL,NULL),
(57,33,4,'详情','personalDeskGroupDeatil','personalDesktopManage/personalDeskGroupDeatil',2,NULL,NULL,NULL,'/personalDesktopManage/personalDeskGroupDeatil/:id',NULL,1,0,'personalDesktopManage:personalDeskGroupDeatil',0,NULL,NULL,NULL),
(58,9,4,'计算节点','computeNode','resManagement/jumpPage/computeNode',2,NULL,NULL,NULL,'/resManagement/jumpPage/computeNode/:uuid/:name',NULL,1,0,'resManagement:computeNode',0,NULL,NULL,NULL),
(59,9,4,'节点信息','nodeToMaster','resManagement/jumpPage/nodeToMaster',3,NULL,NULL,NULL,'/resManagement/jumpPage/nodeToMaster',NULL,1,0,'resManagement:nodeToMaster',0,NULL,NULL,NULL),
(60,40,4,'添加成员','addMembers','systemManage/jumpPage/addMembers',2,NULL,NULL,NULL,'/systemManage/jumpPage/addMembers',NULL,1,0,'systemManage:addMembers',0,NULL,NULL,NULL),
(61,40,4,'编辑成员','editMembers','systemManage/jumpPage/editMembers',2,NULL,NULL,NULL,'/systemManage/jumpPage/editMembers',NULL,1,0,'systemManage:editMembers',0,NULL,NULL,NULL),
(62,43,2,'激活','authActivation',NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,0,NULL,NULL,NULL),
(63,40,4,'权限设置','setAuthority','systemManage/jumpPage/set-authority',2,NULL,NULL,NULL,'/systemManage/jumpPage/setAuthority',NULL,1,0,'systemManage:setAuthority',0,NULL,NULL,NULL),
(64,5,1,'主机监控','hostMonitor','monitor/hostMonitor',1,NULL,NULL,NULL,'/monitor/hostMonitor',NULL,1,0,'monitor:hostMonitor',0,NULL,NULL,NULL),
(65,3,1,'排课管理','scheduleManage','teachDesktopManage/scheduleManage',1,NULL,NULL,NULL,'/teachDesktopManage/scheduleManage',NULL,1,0,'scheduleManage:teachDesktopManage',0,NULL,NULL,NULL),
(66,65,4,'课程设置','classSchedule','teachDesktopManage/classSchedule',2,NULL,NULL,NULL,'/teachDesktopManage/classSchedule',NULL,1,0,'classSchedule:teachDesktopManage',0,NULL,NULL,NULL),
(67,2,1,'存储管理','storageManagement','resManagement/storageManagement',1,NULL,NULL,NULL,'/resManagement/storageManagement',NULL,1,0,'storageManagement:resManagement',0,NULL,NULL,NULL);


