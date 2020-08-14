[toc]

# KVM管理平台yzy_compute模块接口文档

## 一、接口文档说明

### 1、通用报文:

### 2、返回码表：

	| 返回码 | 含义 |
	| :--- | :--- |
	|0     | 成功|
	|10001 | 登录失败|
	|10002 | 用户名错误|
	|30001 | 不支持的网络类型|
	|30002 | 网络命名空间不存在|
	|30003 | 网络设备不存在|
	|30004 | 不支持的设备操作|
	|30005 | 网络设备名称过长|
	|30006 | 无效的设备参数值|
	|30007 | 虚拟机不存在|
	|30008 | 虚拟机关机失败|
	|30009 | hypervisor连接失败|
	|30010 | NBD设备连接失败|
	|30011 | NBD设备断开连接失败|
	|30012 | 修改计算机名失败|
	|30013 | 设置IP失败|
	|40001 | 获取CPU信息失败 |
	|40101 | 获取内存信息失败|
	|40201 | 获取存储信息失败|
	|40301 | 获取网络信息失败|
	|40401 | 获取机器硬件信息失败|
	|40501 | 获取系统服务信息失败|
	|40502 | 获取虚拟机信息失败|
	|99999 | 系统异常，请稍后重试|
	|-1    | 未知异常|


​    	

### 3、修改记录:

	20191223
	1、初始版本

****

###  ###

## Network

### 1、创建网络

目前支持创建两种网络，flat和vlan，注意两种网络不要绑定在同一个物理设备上

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`create`

  - handler - 网络的操作都是使用`NetworkHandler`

  - data - 具体参数如下：

    | Name                         | Type   | Description                      |
    | ---------------------------- | ------ | -------------------------------- |
    | network_id(required)         | string | 网络的uuid                       |
    | network_type(required)       | string | 网络类型，`flat`或者`vlan`       |
    | physical_interface(required) | string | 绑定的物理网卡名称               |
    | vlan_id                      | int    | 如果是vlan网络，则需要提供此参数 |

- request

  ```json
   {
       "command": "create",
       "handler": "NetworkHandler",
       "data": {
           "network_id": "5b0503ba-1af4-11ea-baa2-000c2902e179",
           "network_type": "vlan",
           "physical_interface": "ens224",
           "vlan_id": "1001"
       }
   }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```
  
  

### 2、删除网络

删除网络

- Method

  - `POST`请求，`body`参数使用`json`格式

  - Parameters

    - command - 命令类型，表示某种操作，这里是`create`

    - handler - 网络的操作都是使用`NetworkHandler`

    - data - 具体参数如下：

      | Name                 | Type   | Description                      |
      | -------------------- | ------ | -------------------------------- |
      | network_id(required) | string | 网络的uuid                       |
      | vlan_id              | int    | 如果是vlan网络，则需要提供此参数 |

- Request

  ```python
   {
       "command": "delete",
       "handler": "NetworkHandler",
       "data": {
           "network_id": "5b0503ba-1af4-11ea-baa2-000c2902e179",
           "vlan_id": 1001
       }
   }
  ```

- Returns

  ```python
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

  
### 3、新增Bond

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`bond`

  - handler - 网络的操作都是使用`NetworkHandler`

  - data - 具体参数如下：

    | Name                         | Type   | Description                                           |
    | ---------------------------- | ------ | ----------------------------------------------------- |
    | bond_info(required)          | dict   | bond的相关信息，元素是dict，包含以下3个参数           |
    | dev(required)                | string | bond名称                                              |
    | mode(required)               | int    | bond类型（只支持0，1，6三种）                         |
    | slaves(required)             | list   | 被绑定的物理网卡名称列表                              |
    | ip_list(required)            | list   | 添加到bond网卡上的IP列表，元素是dict，包含以下2个参数 |
    | ip(required)                 | string | IP地址                                                |
    | netmask(required)            | string | 子网掩码                                              |
    | gate_info(required)          | dict   | 添加到bond网卡上的网关/DNS信息，包含以下3个参数       |
    | gateway(required)            | string | 网关                                                  |
    | dns1(required)               | string | dns1                                                  |
    | dns2(required)               | string | dns2                                                  |

- request

  ```json
   {
       "command": "bond",
       "handler": "NetworkHandler",
       "data": {
            "bond_info": {
                "dev": "bond0",
                "mode": 0,
                "slaves": ["eth1", "eth2", "eth3"],
            "ip_list":[
                {
                    "ip": "192.168.1.1",
                    "netmask": "255.255.255.0"
                }
            ],
            "gate_info": {
                "gateway": "192.168.1.254",
                "dns1": "8.8.8.8",
                "dns2": "",
            }
       }
   }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "bond_nic_info": {
              "mac": "00:0c:29:8c:be:47",
              "nic": "bond0",
              "speed": 30000,
              "status": 2
          }
      },
      "msg": "成功"
  }
  ```



### 4、编辑Bond

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`edit_bond`

  - handler - 网络的操作都是使用`NetworkHandler`

  - data - 具体参数如下：
    | Name                         | Type   | Description                                           |
    | ---------------------------- | ------ | ----------------------------------------------------- |
    | bond_info(required)          | dict   | bond的相关信息，元素是dict，包含以下3个参数           |
    | dev(required)                | string | bond名称                                              |
    | mode(required)               | int    | bond类型（只支持0，1，6三种）                         |
    | slaves(required)             | list   | 被绑定的物理网卡名称列表                              |
    | remove_slaves(required)      | list   | 要解绑的物理网卡名称列表                              |
    | ip_list(required)            | list   | 添加到bond网卡上的IP列表，元素是dict，包含以下2个参数 |
    | ip(required)                 | string | IP地址                                                |
    | netmask(required)            | string | 子网掩码                                              |
    | gate_info(required)          | dict   | 添加到bond网卡上的网关/DNS信息，包含以下3个参数       |
    | gateway(required)            | string | 网关                                                  |
    | dns1(required)               | string | dns1                                                  |
    | dns2(required)               | string | dns2                                                  |

- request

  ```json
   {
       "command": "bond",
       "handler": "NetworkHandler",
       "data": {
            "bond_info": {
                "dev": "bond0",
                "mode": 1,
                "slaves": ["eth1", "eth2"],
            "remove_slaves": ["eth3"],
            "ip_list":[
                {
                    "ip": "192.168.2.100",
                    "netmask": "255.255.255.0"
                }
            ],
            "gate_info": {
                "gateway": "192.168.1.254",
                "dns1": "8.8.8.8",
                "dns2": "",
            }
       }
   }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "bond_nic_info": {
              "mac": "00:0c:29:8c:be:47",
              "nic": "bond0",
              "speed": 20000,
              "status": 2
          }
      },
      "msg": "成功"
  }
  ```



### 5、删除Bond

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`unbond`

  - handler - 网络的操作都是使用`NetworkHandler`

  - data - 具体参数如下：

    | Name                         | Type   | Description                                             |
    | ---------------------------- | ------ | ------------------------------------------------------- |
    | bond_name(required)          | string | 要删除的bond名称                                        |
    | slaves(required)             | list   | 要解绑的物理网卡信息列表，元素是dict，包含以下2个参数   |
    | nic(required)                | string | 要解绑的物理网卡名称                                    |
    | ip_list(required)            | list   | 添加到物理网卡上的IP列表，元素是dict，包含以下5个参数   |
    | ip(required)                 | string | IP地址                                                  |
    | netmask(required)            | string | 子网掩码                                                |
    | gateway(required)            | string | 网关                                                    |
    | dns1(required)               | string | dns1                                                    |
    | dns2(required)               | string | dns2                                                    |

- request

  ```json
   {
       "command": "bond",
       "handler": "NetworkHandler",
       "data": {
            "bond_name": "bond0",
            "slaves": [
                {
                    "nic": "eth1",
                    "ip_list":[
                        {
                            "ip": "192.168.2.100",
                            "netmask": "255.255.255.0",
                            "gateway": "192.168.1.254",
                            "dns1": "8.8.8.8",
                            "dns2": "",
                        }
                    }
                }
            ]
       }
   }
  ```

- Returns

  ```json
  {
      "code": 0,
      "msg": "成功"
  }
  ```



## Instance

### 1、创建实例

创建实例

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`create`

  - handler - 网络的操作都是使用`InstanceHandler`

  - data - 具体参数如下：

    | Name                   | Type   | Description                                                  |
    | ---------------------- | ------ | ------------------------------------------------------------ |
    | instance(required)     | dict   | 实例的相关信息，具体参数如下                                 |
    | uuid(required)         | string | 实例的uuid，唯一                                             |
    | name(required)         | string | 实例的名称                                                   |
    | base_name(required)    | string | 底层虚拟机的名称，用来解决命名冲突                           |
    | ram(required)          | int    | 实例分配的虚拟内存，单位为MB                                 |
    | vcpus(required)        | int    | 实例分配的虚拟CPU个数                                        |
    | os_type                | string | `windows` or `linux`，实例的操作系统类型，给出能针对不同系统做一些差异配置，如果未给定，默认使用`windows` |
    |                        |        |                                                              |
    | network_info(required) | list   | 实例的网卡信息，每个元素为字典，具体单个的参数在下面         |
    | fixed_ip(required)     | string | 固定的IP值（暂时不考虑DHCP方式）                             |
    | netmask(required)      | string | 子网掩码                                                     |
    | gateway(required)      | string | 网关                                                         |
    | dns_server             | list   | DNS地址                                                      |
    | mac_addr(required)     | string | 网卡的mac地址                                                |
    | bridge(required)       | string | 网卡连接的网桥                                               |
    | port_id(required)      | string | 网卡分配的port_id，用于tap设备命名                           |
    |                        |        |                                                              |
    | disk_info(required)    | list   | 实例的磁盘信息，单个磁盘的信息如下                           |
    | uuid                   | string | 磁盘的uuid，当磁盘不是cdrom floppy等类型时，该字段必需       |
    | dev(required)          | string | 磁盘的命名，virtio驱动的命名为`vda vdb ...`，ide驱动的命名为`hda hdb ...` |
    | boot_index(required)   | int    | `0`表示为系统盘，其他为数据盘                                |
    | bus                    | string | 驱动，默认为`virtio`，可选`ide`、`scsi`等                    |
    | type                   | string | 磁盘类型，默认为`disk`，可选`cdrom`、`floppy`等              |
    | image_id               | string | 用于指明backing_file，如果指定了image_id，会将以image_id为名称的磁盘文件作为backing_file |
    | image_version          | int    | image_id对应镜像的版本，版本用于差异文件的关系维护           |
    | size                   | string | 如果没有指定image_id，则该参数必须给出，表示创建大小为size的磁盘文件。支持以下单位：'k' or 'K' (kilobyte, 1024), 'M' (megabyte, 1024k), 'G' (gigabyte, 1024M), 'T' (terabyte, 1024G), 'P' (petabyte, 1024T) and 'E' (exabyte, 1024P)。例如：30G |
    | path                   | string | 磁盘文件的位置，这个主要用来添加`cdrom`，当提供了此参数时，`boot_index`为可选 |

- request

  ```json
  {
      "command": "create",
      "handler": "InstanceHandler",
      "data": {
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "instance1",
              "base_name": "instance-00000001",
              "ram": 2048,
              "vcpus": 2,
              "os_type": "windows"
          },
          "network_info": [
              {
                  "fixed_ip": "172.16.1.13",
                  "netmask": "255.255.255.0",
                  "dns_server": ["114.114.114.114"],
                  "mac_addr": "fa:16:3e:8f:be:ff",
                  "bridge": "brqa72e4f85-28",
                  "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
              }
          ],
          "disk_info": [
              {
                  "uuid": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
                  "dev": "vda",
                  "boot_index": 0,
                  "image_id": "30417b12-1cb7-11ea-834c-000c2902e179",
                  "image_version": 1
              },
              {
                  "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                  "dev": "vdb",
                  "boot_index": -1,
                  "size": "30G"
              },
              {
                  "bus": "ide",
                  "dev": "hda",
                  "type": "cdrom",
                  "path": "/data/cloudbase.iso"
              }
          ]
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

  

### 2、启动实例

执行`virsh start`操作

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`start`

  - handler - 网络的操作都是使用`InstanceHandler`

  - data - 参数如下

    | Name           | Type   | Description      |
    | -------------- | ------ | ---------------- |
    | uuid(required) | string | 实例的uuid，唯一 |
    | name(required) | string | 实例的名称       |

- request

  ```json
  {
      "command": "start",
      "handler": "InstanceHandler",
      "data": {
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "test1"
          }
      }
  }
  ```
  
- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

  

### 3、停止实例

执行`virsh shutdown`操作，关闭失败时执行`virsh destroy`操作

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，分为`stop`和`stop_restore`，参数相同。`stop`操作就是正常关机，`stop_restore`针对重启还原的情况，会删除掉系统盘

  - handler - 网络的操作都是使用`InstanceHandler`

  - data - 参数如下

    | Name           | Type    | Description                           |
    | -------------- | ------- | ------------------------------------- |
    | instance       | dict    | 实例信息，包含属性如下：              |
    | uuid(required) | string  | 实例的uuid，唯一                      |
    | name(required) | string  | 实例的名称                            |
    |                |         |                                       |
    | data_restore   | boolean | `true` or `false`，标识数据盘是否还原 |

- request

  ```json
  {
      "command": "stop",
      "handler": "InstanceHandler",
      "data": {
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "instance1"
          }
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

  

### 4、删除实例

执行`virsh undefine`操作，会删除所有磁盘信息

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`delete`

  - handler - 网络的操作都是使用`InstanceHandler`

  - data - 参数如下

    | Name           | Type    | Description                      |
    | -------------- | ------- | -------------------------------- |
    | uuid(required) | string  | 实例的uuid，唯一                 |
    | name(required) | string  | 实例的名称                       |
    | destroy        | boolean | 默认取`true`，表示是否删除数据盘 |

- request

  ```json
  {
      "command": "delete",
      "handler": "InstanceHandler",
      "data": {
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "instance1"
          }
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

  

### 5、重启实例

支持软重启和硬重启

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`delete`

  - handler - 网络的操作都是使用`InstanceHandler`

  - data - 参数如下

    | Name                  | Type   | Description                |
    | --------------------- | ------ | -------------------------- |
    | reboot_type(required) | string | 重启类型，`soft` or `hard` |
    | instance(required)    | dict   | 实例信息，参数如下         |
    | uuid(required)        | string | 实例的uuid，唯一           |
    | name(required)        | string | 实例的名称                 |

    如果是硬重启，还需提供`network_info`和`disk_info`，可参考创建实例的参数

- request

  ```json
  {
      "command": "reboot",
      "handler": "InstanceHandler",
      "data": {
          "reboot_type": "soft",
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "instance1"
          }
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```




## Template

### 1、创建模板

创建模板实际就是创建实例，不同之处是会提供一个空磁盘以及系统ISO进行系统安装

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`create`

  - handler - 网络的操作都是使用`TemplateHandler`

  - data - 参数参考实例的创建，不过模板这里提供一个额外参数，`power_on`表示开不开机，模板创建了默认是不开机的

- request

  ```json
  {
      "command": "create",
      "handler": "TemplateHandler",
      "data": {
          "power_on": true,
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "template1",
              "base_name": "template-00000001",
              "ram": 1024,
              "vcpus": 2,
              "os_type": "windows"
          },
          "network_info": [
              {
                  "fixed_ip": "203.0.113.203",
                  "netmask": "255.255.255.0",
                  "gateway": "203.0.113.1",
                  "dns_server": ["114.114.114.114", "114.114.114.115"],
                  "mac_addr": "fa:16:3e:8f:be:ff",
                  "bridge": "brqa72e4f85-28",
                  "port_id": "12fb86f2-b87b-44f0-b44e-38189314bdbd"
              }
          ],
          "disk_info": [
              {
                  "uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                  "dev": "vda",
                  "boot_index": 0,
                  "image_id": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
                  "image_version": 0
              },
              {
                  "uuid": "1d07aaa0-2b92-11ea-a62d-000c29b3ddb9",
                  "dev": "vdb",
                  "boot_index": -1,
                  "size": "50G"
              },
              {
                  "bus": "ide",
                  "dev": "hdb",
                  "type": "cdrom",
                  "path": "/data/virtio-win-0.1.171.iso"
              }
          ]
      }
  }
  ```
  
- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

### 2、删除模板

删除模板包含两部分，一部分是模板本身的差异磁盘。另一部分则是模板作为镜像的那一部分差异磁盘

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`delete`

  - handler - 网络的操作都是使用`TemplateHandler`

  - data - 参数如下

    | Name                    | Type   | Description                                |
    | ----------------------- | ------ | ------------------------------------------ |
    | image_version(required) | string | 模板目前的版本                             |
    | instance(required)      | dict   | 实例信息，参数如下                         |
    | uuid(required)          | string | 实例的uuid，唯一                           |
    | name(required)          | string | 实例的名称                                 |
    |                         |        |                                            |
    | images                  | list   | 需要下载的镜像信息，包括系统镜像和数据镜像 |
    | image_id                | string | 镜像的uuid                                 |
    | image_type              | string | `system` or `data`，分别表示系统和数据镜像 |

- request

  ```json
  {
      "command": "delete",
      "handler": "TemplateHandler",
      "data": {
          "image_version": 2,
          "instance": {
              "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
              "name": "instance1"
          },
          "images": [
              {
                  "image_id": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                  "image_type": "system"
              },
              {
                  "image_id": "f613f8ac-30ed-11ea-9764-000c2902e179",
                  "image_type": "data"
              },
              {
                  "image_id": "777003cc-3112-11ea-bae9-000c2902e179",
                  "image_type": "data"
              }
          ]
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

### 3、下载模板

该方法可用于同步原始镜像和差异磁盘

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`sync`

  - handler - 网络的操作都是使用`TemplateHandler`

  - data - 参数如下

    | Name                    | Type   | Description                                    |
    | ----------------------- | ------ | ---------------------------------------------- |
    | image_version(required) | string | 镜像的版本                                     |
    | endpoint(required)      | string | 下载镜像的地址，例如：`http://controller:2222` |
    | url(required)           | string | 路由路径                                       |
    |                         |        |                                                |
    | images                  | list   | 需要下载的镜像信息，包括系统镜像和数据镜像     |
    | image_id                | string | 镜像的uuid                                     |
    | image_type              | string | `system` or `data`，分别表示系统和数据镜像     |

- request

  ```json
  {
      "command": "download",
      "handler": "TemplateHandler",
      "data": {
          "image_version": 2,
          "endpoint": "http://172.16.1.11:50001",
          "url": "/api/v1/image/download",
          "images": [
              {
                  "image_id": "dfcd91e8-30ed-11ea-9764-000c2902e179",
                  "image_type": "system"
              },
              {
                  "image_id": "f613f8ac-30ed-11ea-9764-000c2902e179",
                  "image_type": "data"
              },
              {
                  "image_id": "777003cc-3112-11ea-bae9-000c2902e179",
                  "image_type": "data"
              }
          ]
      }
  }
  ```
  
- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

### 4、保存模板

模板安装完成后，进行模板的保存，保存完后，模板虚拟机被删除

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`save`

  - handler - 网络的操作都是使用`TemplateHandler`

  - data - 参数如下

    | Name              | Type   | Description      |
    | ----------------- | ------ | ---------------- |
    | instance          | dict   | 具体参数包括下面 |
    | uuid(required)    | string | 镜像的uuid       |
    | name(required)    | string | 镜像的名字       |
    | version(required) | int    | 镜像的版本       |

- request

  ```json
  {
      "command": "save",
      "handler": "TemplateHandler",
      "data": {
          "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
          "name": "instance1",
          "version": 1
      }
  }
  ```
  
- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

### 5、复制模板

复制模板实际是将差异磁盘和原始镜像进行`qemu-img convert`操作生成一个全新的合并的新镜像

- Method

  `POST`请求，`body`参数使用`json`格式

- Parameters

  - command - 命令类型，表示某种操作，这里是`convert`

  - handler - 网络的操作都是使用`TemplateHandler`

  - data - 参数如下

    | Name                    | Type   | Description                                                  |
    | ----------------------- | ------ | ------------------------------------------------------------ |
    | new_image_id(required)  | string | 新生成的模板的uuid                                           |
    | template                | dict   | 要复制的模板的信息，具体参数包括下面                         |
    | uuid(required)          | string | 模板的uuid                                                   |
    | system_uuid(required)   | string | 模板系统盘的uuid                                             |
    | image_version(required) | string | 模板的版本                                                   |
    | image_id                | string | 原始镜像uuid，在模板版本为0时会用到（规划是模板创建后会自动保存一个版本，所以这种情况暂时不会存在） |

- request

  ```json
  {
      "command": "convert",
      "handler": "TemplateHandler",
      "data": {
          "new_image_id": "ef0b7c2c-31c1-11ea-ae30-000c2902e179",
          "template": {
              "uuid": "dfcd91e8-30ed-11ea-9764-111c2902e179",
              "system_uuid": "dfcd91e8-30ed-11ea-9764-000c2902e179",  # 系统盘的uuid
              "image_version": 0,
              "image_id": "196df26e-2b92-11ea-a62d-000c29b3ddb9",
          }
      }
  }
  ```

- Returns

  ```json
  {
      "code": 0,
      "data": {
          "api_version": "1.0"
      },
      "msg": "成功"
  }
  ```

