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

/*Table structure for table `yzy_block_device_mapping` */

DROP TABLE IF EXISTS `yzy_block_device_mapping`;

CREATE TABLE `yzy_block_device_mapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '块设备卷虚机映射关系',
  `device_name` varchar(32) NOT NULL COMMENT '设备名称，/dev/vda(vdb)',
  `volume_uuid` varchar(64) NOT NULL COMMENT '卷uuid',
  `volume_size` int(11) NOT NULL COMMENT '卷大小，单位：GB',
  `instance_uuid` varchar(64) NOT NULL COMMENT '虚机uuid',
  `destination_type` varchar(32) NOT NULL COMMENT '目标类型，如：volume',
  `device_type` varchar(32) NOT NULL COMMENT '设备类型， 如： disk',
  `disk_bus` varchar(32) NOT NULL COMMENT '设备总线，如：virtio',
  `boot_index` tinyint(2) NOT NULL COMMENT 'boot序列',
  `source_type` varchar(20) NOT NULL COMMENT '源类型，如：blank, image',
  `image_uuid` varchar(64) NOT NULL COMMENT '源镜像uuid',
  `deleted` tinyint(1) NOT NULL COMMENT '删除',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_block_device_mapping` */

/*Table structure for table `yzy_class` */

DROP TABLE IF EXISTS `yzy_class`;

CREATE TABLE `yzy_class` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '班级id',
  `name` varchar(32) NOT NULL COMMENT '名称',
  `network_uuid` varchar(64) NOT NULL COMMENT '网络uuid',
  `subnet_uuid` varchar(64) NOT NULL COMMENT '子网uuid',
  `ip_start` varchar(20) NOT NULL COMMENT '起始IP',
  `ip_end` varchar(20) NOT NULL COMMENT '结束IP',
  `deleted` tinyint(1) NOT NULL COMMENT '删除标记',
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_class` */

/*Table structure for table `yzy_data_networks` */

DROP TABLE IF EXISTS `yzy_data_networks`;

CREATE TABLE `yzy_data_networks` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '数据网络',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(32) NOT NULL COMMENT '网络名称',
  `vswitch_name` varchar(32) NOT NULL COMMENT '关联虚拟交换机名称',
  `vswitch_uuid` varchar(64) NOT NULL COMMENT '关联虚拟交换机uuid',
  `vswitch_type` varchar(32) NOT NULL COMMENT '关联虚拟交换机类型',
  `vlan_id` int(5) NOT NULL COMMENT 'vlan id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_data_networks` */

/*Table structure for table `yzy_instance_flavor` */

DROP TABLE IF EXISTS `yzy_instance_flavor`;

CREATE TABLE `yzy_instance_flavor` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '硬件模板',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `name` varchar(32) NOT NULL COMMENT '名称',
  `memory` int(11) NOT NULL COMMENT '内存，单位：MB',
  `cpu` int(11) NOT NULL COMMENT '单位：核',
  `system_disk` int(11) NOT NULL COMMENT '系统盘，单位：GB',
  `data_disks` varchar(200) NOT NULL COMMENT '数据盘，支持多盘 {''id'': 0 , ''size'': 50}， 单位：GB, 最多5块',
  `deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '状态(0:启用,>1=:删除)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_instance_flavor` */

/*Table structure for table `yzy_instance_images` */

DROP TABLE IF EXISTS `yzy_instance_images`;

CREATE TABLE `yzy_instance_images` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '实例镜像',
  `name` varchar(32) NOT NULL COMMENT '名称',
  `owner_id` int(11) NOT NULL COMMENT '创建者id',
  `os_type` varchar(32) NOT NULL COMMENT '系统类型',
  `flavor_uuid` varchar(64) NOT NULL COMMENT '硬件模板uuid',
  `is_64` tinyint(1) NOT NULL COMMENT '是否64位',
  `virtual_type` varchar(32) NOT NULL COMMENT '虚拟类型：kvm',
  `system_alloc_disk` int(11) NOT NULL COMMENT '系统盘大小， 单位：GB',
  `data_alloc_disk` varchar(100) NOT NULL COMMENT '数据盘分配',
  `enable_gpu` tinyint(1) NOT NULL COMMENT '是否启动GPU',
  `host_uuid` varchar(64) NOT NULL COMMENT 'host',
  `description` varchar(200) DEFAULT NULL COMMENT '描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_instance_images` */

/*Table structure for table `yzy_iso` */

DROP TABLE IF EXISTS `yzy_iso`;

CREATE TABLE `yzy_iso` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ISO文件信息',
  `name` varchar(64) NOT NULL COMMENT '上传ISO文件名称',
  `md5_sum` varchar(64) NOT NULL COMMENT 'md5校验值',
  `size` int(11) NOT NULL COMMENT '文件大小',
  `type` varchar(20) NOT NULL COMMENT '类型',
  `description` varchar(200) NOT NULL COMMENT '描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_iso` */

/*Table structure for table `yzy_node` */

DROP TABLE IF EXISTS `yzy_node`;

CREATE TABLE `yzy_node` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '服务器节点',
  `uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `ip` varchar(20) NOT NULL COMMENT '节点ip',
  `node_name` varchar(32) NOT NULL COMMENT '节点名称',
  `is_controller` tinyint(1) NOT NULL COMMENT '是否为主控节点',
  `resource_pool_uuid` varchar(64) NOT NULL COMMENT '资源池uuid',
  `total_mem` int(11) NOT NULL COMMENT '节点内存',
  `running_mem` int(11) NOT NULL COMMENT '启动内存',
  `single_reserve_mem` int(11) NOT NULL COMMENT '虚机预留内存',
  `total_vcpus` int(11) NOT NULL COMMENT '节点cpu核数',
  `running_vcpus` int(11) NOT NULL COMMENT '运行cpu核数',
  `status` int(11) NOT NULL COMMENT '状态',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_node` */

/*Table structure for table `yzy_node_network_info` */

DROP TABLE IF EXISTS `yzy_node_network_info`;

CREATE TABLE `yzy_node_network_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '节点网络信息',
  `nic` varchar(32) NOT NULL,
  `mac` varchar(32) NOT NULL,
  `node_uuid` varchar(64) NOT NULL,
  `speed` int(11) NOT NULL,
  `state` varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_node_network_info` */

/*Table structure for table `yzy_operation_log` */

DROP TABLE IF EXISTS `yzy_operation_log`;

CREATE TABLE `yzy_operation_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '操作日志记录',
  `user_id` int(11) NOT NULL COMMENT '用户id',
  `ip` varchar(20) NOT NULL COMMENT '用户ip',
  `content` varchar(500) NOT NULL COMMENT '操作内容',
  `create_time` datetime NOT NULL COMMENT '操作时间',
  `result` varchar(100) NOT NULL COMMENT '操作结果',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统操作日志';

/*Data for the table `yzy_operation_log` */

/*Table structure for table `yzy_permisson` */

DROP TABLE IF EXISTS `yzy_permisson`;

CREATE TABLE `yzy_permisson` (
  `id` int(11) NOT NULL COMMENT '菜单权限id',
  `permission_name` varchar(32) NOT NULL COMMENT '菜单权限名称',
  `permission_title` varchar(32) NOT NULL COMMENT '菜单名称',
  `permission_url` varchar(255) NOT NULL COMMENT '菜单权限路径',
  `level` tinyint(1) NOT NULL DEFAULT '0' COMMENT '菜单权限等级(0-tab导航，1-主菜单，2-子菜单)',
  `parent_id` int(11) DEFAULT NULL COMMENT '父级菜单id',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_permisson` */

/*Table structure for table `yzy_resource_pools` */

DROP TABLE IF EXISTS `yzy_resource_pools`;

CREATE TABLE `yzy_resource_pools` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '资源池id',
  `uuid` varchar(64) NOT NULL COMMENT '资源池uuid',
  `name` varchar(32) NOT NULL COMMENT '资源池名称',
  `description` varchar(500) DEFAULT NULL COMMENT '描述',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_resource_pools` */

/*Table structure for table `yzy_role` */

DROP TABLE IF EXISTS `yzy_role`;

CREATE TABLE `yzy_role` (
  `id` int(11) NOT NULL COMMENT '角色id',
  `role_name` varchar(32) NOT NULL COMMENT '角色名称',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_role` */

/*Table structure for table `yzy_role_permisson` */

DROP TABLE IF EXISTS `yzy_role_permisson`;

CREATE TABLE `yzy_role_permisson` (
  `id` int(11) NOT NULL COMMENT '角色权限映射表主键id',
  `role_id` int(11) NOT NULL COMMENT '角色id',
  `permission_id` int(11) NOT NULL COMMENT '权限id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_role_permisson` */

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
  `deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除',
  `enable_dhcp` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否开启DHCP',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_subnets` */

/*Table structure for table `yzy_teacher_group` */

DROP TABLE IF EXISTS `yzy_teacher_group`;

CREATE TABLE `yzy_teacher_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '教师组',
  `name` varchar(32) NOT NULL COMMENT '名称',
  `ip_start` varchar(20) NOT NULL COMMENT '起始IP',
  `ip_end` varchar(20) NOT NULL COMMENT '结束IP',
  `desc` varchar(200) NOT NULL COMMENT '描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_teacher_group` */

/*Table structure for table `yzy_teachers` */

DROP TABLE IF EXISTS `yzy_teachers`;

CREATE TABLE `yzy_teachers` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '老师账号',
  `account` varchar(32) NOT NULL COMMENT '账号',
  `password` varchar(64) NOT NULL COMMENT '密码',
  `name` varchar(32) DEFAULT NULL COMMENT '姓名',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `email` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '状态：0-未启用，1-启用',
  `enable_change_pwd` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否能修改密码，0-否，1-是',
  `group_id` int(11) NOT NULL COMMENT '所属组id',
  `desc` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_teachers` */

/*Table structure for table `yzy_user` */

DROP TABLE IF EXISTS `yzy_user`;

CREATE TABLE `yzy_user` (
  `id` int(11) NOT NULL COMMENT '用户uid',
  `username` varchar(32) NOT NULL COMMENT '用户名称',
  `password` varchar(64) NOT NULL COMMENT '用户密码',
  `user_role` int(11) NOT NULL COMMENT '用户角色id',
  `head_img` varchar(100) DEFAULT NULL COMMENT '用户头像',
  `last_login_ip` varchar(20) DEFAULT NULL COMMENT '用户登录ip',
  `last_login_time` datetime DEFAULT NULL COMMENT '用户登录时间',
  `status` tinyint(1) DEFAULT NULL COMMENT '用户状态(0-未启用，1-启用)',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `remark` varchar(255) DEFAULT NULL COMMENT '用户备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_user` */

/*Table structure for table `yzy_virtual_switch` */

DROP TABLE IF EXISTS `yzy_virtual_switch`;

CREATE TABLE `yzy_virtual_switch` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '虚拟交换机id',
  `uuid` varchar(64) NOT NULL COMMENT '虚拟交换机uuid',
  `name` varchar(32) NOT NULL COMMENT '虚拟交换名称',
  `type` varchar(10) NOT NULL COMMENT '虚拟交换机类型',
  `description` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_virtual_switch` */

/*Table structure for table `yzy_volumes` */

DROP TABLE IF EXISTS `yzy_volumes`;

CREATE TABLE `yzy_volumes` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '卷表',
  `uuid` varchar(64) NOT NULL COMMENT 'uuid',
  `size` int(11) NOT NULL COMMENT '单位：GB',
  `host` varchar(255) NOT NULL COMMENT '所在host',
  `display_name` varchar(100) NOT NULL COMMENT '显示名：9f8aa7b7-3114-4b68-8f0e-23e248f00de5-blank-vol',
  `location` varchar(100) NOT NULL COMMENT '路径',
  `bootable` tinyint(1) NOT NULL COMMENT '是否启动盘',
  `status` varchar(32) NOT NULL COMMENT '状态： in-use, available,deleted',
  `deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除 0 -未 1- 是',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_volumes` */

/*Table structure for table `yzy_vswitch_uplink` */

DROP TABLE IF EXISTS `yzy_vswitch_uplink`;

CREATE TABLE `yzy_vswitch_uplink` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '虚拟交换机连接网卡id',
  `vs_uuid` varchar(64) NOT NULL COMMENT '虚拟交换机uuid',
  `node_uuid` varchar(64) NOT NULL COMMENT '节点uuid',
  `interface` varchar(36) NOT NULL COMMENT '网卡设备',
  `ipaddr` varchar(20) NOT NULL COMMENT 'ip地址',
  `type` varchar(10) NOT NULL COMMENT '网络类型',
  `ext` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_vswitch_uplink` */

/*Table structure for table `yzy_warn_type` */

DROP TABLE IF EXISTS `yzy_warn_type`;

CREATE TABLE `yzy_warn_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '警告类型',
  `warn_name` varchar(32) NOT NULL COMMENT '警告名称',
  `warn_code` varchar(10) NOT NULL COMMENT '警告代码',
  `description` varchar(200) NOT NULL COMMENT '警告描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_warn_type` */

/*Table structure for table `yzy_warning_log` */

DROP TABLE IF EXISTS `yzy_warning_log`;

CREATE TABLE `yzy_warning_log` (
  `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '警告日志',
  `warn_id` int(11) NOT NULL COMMENT '警告类型id',
  `node_ip` varchar(20) NOT NULL COMMENT '警告节点ip',
  `warn_msg` varchar(500) NOT NULL COMMENT '警告内容',
  `create_time` datetime NOT NULL COMMENT '时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Data for the table `yzy_warning_log` */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
