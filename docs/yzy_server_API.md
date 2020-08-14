[TOC]

# Server接口文档 #

server端的接口`endpoint`为`http:127.0.0.1:5000/api/v1/`

## 首页

### 1、获取TOP5数据 ###


* URL

	`/index/top_data`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | statis_period  | int  | 节点top数据统计周期秒数(1< statis_period <60) |
    
    - 示例：
    
      ```json
      {
          "statis_period": 15
      }
      ```


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |utc| 查询时间的UTC值| int| data|linux上使用命令查看: date --date @1576751520 |
  |cpu_util| cpu使用率| array| data| 节点名字、使用率，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |disk_util| SSD磁盘使用率| array| data| 节点名字、使用率、总字节数、已使用字节数，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |memory_util| 内存使用率| array| data| 节点名字、使用率，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |nic_util| 管理网卡使用率| array| data| 节点名字、读写平均字节数每秒、读写最大字节数每秒，已经按照平均值从大到小排好顺序，最大5个，也可能为空|

  - 示例：

    ```json
	{
		"code": 0,
		"msg": "成功",
		"data": {
			"utc": 1588820301,
			"cpu_util": [
				["main_host", "51.48"],
				["computer1", "2.11"]
			],
			"disk_util": [
				["main_host", "7.89", 348691902464, 27500318720],
				["computer1", "3.66", 348559790080, 12763496448]
			],
			"memory_util": [
				["main_host", "81.70"],
				["computer1", "46.50"]
			],
			"nic_util": [
				["main_host", 12201, 19209],
				["computer1", 636, 4290]
			]
		}
	}
    ```


## 资源池

### 1、新增资源池 ###


* URL

	`/resource_pool/create`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | name(required) | string  | 资源池名称       |
    | desc           | string  | 资源池描述       |
    | default        | boolean | 是否是默认资源池 |
    
    - 示例：
    
      ```json
      {
          "name": "default",
          "description": "默认资源池"
      }
      ```


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```


### 2、删除资源池 ###


* URL

  `/resource_pool/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 资源池uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、更新资源池 ###


* URL

  `/resource_pool/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 资源池uuid                     |
  | value(required) | dict   | 更新的资源池的属性，包含如下： |
  | name            | string | 资源池名字                     |
  | desc            | string | 资源池描述                     |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
        "value": {
            "name": "pool1",
            "desc": "this is pool1"
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 基础镜像

### 1、上传基础镜像 ###


* URL

  `/resource_pool/images/upload`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description        |
  | ------------------- | ------ | ------------------ |
  | pool_uuid(required) | string | 资源池uuid         |
  | image_id            | string | 基础镜像的uuid     |
| image_path          | string | 基础镜像的具体路径 |
  | md5_sum             | string | 基础镜像的md5值    |

  - 示例：
  
    ```json
    {
        "pool_uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
        "image_id": "d2699e42-380a-11ea-a26e-000c2902e179",
        "image_path": "/opt/slow/instances/_base/d2699e42-380a-11ea-a26e-000c2902e179",
        "md5_sum": "f6e5d9eb0dbd99457cdb775a73a27b55"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、重传基础镜像 ###


* URL

  `/resource_pool/images/retransmit`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description        |
  | ------------------- | ------ | ------------------ |
  | ipaddr(required)    | string | 需要重传的节点IP   |
  | host_uuid(required) | string | 需要重传的节点uuid |
  | image_id            | string | 基础镜像的uuid     |
| md5_sum             | string | 基础镜像的MD5      |
  
- 示例：
  
    ```json
    {
    	"ipaddr": "172.16.1.11",
    	"host_uuid": "a04ce3c0-488f-11ea-b1de-000c295dd728",
    	"image_id": "4315aa82-3b76-11ea-930d-000c295dd728",
        "md5_sum": "f6e5d9eb0dbd99457cdb775a73a27b55"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 节点操作

### 1、资源池添加节点 ###


* URL

  `/node/add`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                       | Type   | Description        |
  | -------------------------- | ------ | ------------------ |
  | password(required)         | string | 节点密码           |
  | ip(required)               | string | 节点IP             |
  | pool_uuid(required)        | string | 资源池的uuid       |
  | network_uuid(required)     | string | 数据网络uuid       |
  | switch_uuid(required)      | string | 虚拟交换机uuid     |
  | interface(required)        | string | 数据网络绑定的网卡 |
| manage_interface(required) | string | 管理网络绑定的网卡 |
  | image_interface(required)  | string | 镜像网络网卡       |
  
- 示例：
  
    ```json
    {
        "password": "123",
        "ip": "172.16.1.11",
        "pool_uuid": "ec92a530-4885-11ea-8e15-000c295dd728",
        "network_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
        "switch_uuid": "ec796624-4885-11ea-8e15-000c295dd728",
        "interface": "ens224",
        "manage_interface": "ens192",
        "image_interface": "ens192"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、初始化控制节点 ###

控制节点初始化，包括节点信息、节点网卡信息、节点存储信息、虚拟交换机、网络、子网和默认资源池


* URL

  `/controller/init`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type    | Description                                                  |
  | ---------------------- | ------- | ------------------------------------------------------------ |
  | ip(required)           | string  | 管理IP                                                       |
  | password               | string  | 节点密码                                                     |
  | manage_interface       | string  | 管理网络接口                                                 |
  | image_interface        | string  | 镜像网络接口                                                 |
  | data_interface         | string  | 数据网络接口                                                 |
  | network_name(required) | string  | 网络名称                                                     |
  | switch_name(required)  | string  | 虚拟交换机名称                                               |
  | switch_type(required)  | string  | 虚拟交换机的类型，`flat`或者`vlan`                           |
  | vlan_id                | int     | 如果是`vlan`网络，则需要提供此参数                           |
  |                        |         |                                                              |
  | storages(required)     | dict    | 存储设置信息，它的key-value介绍如下：                        |
  | key                    | string  | 系统的分区挂载点                                             |
  | value                  | string  | 该分区的角色，1-模板系统盘存储 2-模板数据盘存储 3-虚拟机系统盘存储 4-虚拟机数据盘存储。当一个分区有多个角色时，用逗号隔开 |
  |                        |         |                                                              |
  | is_compute(required)   | boolean | 是否设置为计算节点                                           |
  
  - 示例：
  
  ```json
    {
      "ip": "172.16.1.49",
        "password": "allinone",
        "manage_interface": "ens192",
        "image_interface": "ens192",
        "data_interface": "ens224",
        "network_name": "default",
        "switch_name": "default",
        "switch_type": "vlan",
        "vlan_id": 10,
        "storages": {
            "/opt/slow": "1,2,3,4"
        },
        "is_compute": false
    }
  ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、检测节点虚拟化特性 ###


* URL

  `/node/check`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name               | Type   | Description    |
  | ------------------ | ------ | :------------- |
  | ip(required)       | string | 节点IP         |
  | root_pwd(required) | string | 节点的root密码 |
| check              | string | false or true  |
  
- 示例：
  
    ```json
    {
        "ip": "172.16.1.49",
        "root_pwd": "123"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
        "code": 0,
        "data": {
            "default_network_info": {
                "network_info": {
                    "name": "network2",
                    "switch_name": "switch1",
                    "switch_type": "vlan",
                    "uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
                    "vlan_id": "10"
                },
                "virtual_switch": {
                    "desc": "this is switch1",
                    "name": "switch1",
                    "type": "vlan",
                    "uuid": "caa5d57e-3731-11ea-801e-000c295dd728"
                }
            },
            "hostname": "allinone",
            "interface_list": [
                {
                    "interface": "ens192",
                    "ip": "172.16.1.49",
                    "mac": "00:0c:29:5d:d7:28",
                    "mask": "255.255.255.0",
                    "speed": 10000,
                    "stat": true
                },
                {
                    "interface": "ens224",
                    "ip": "172.16.1.49",
                    "mac": "00:0c:29:5d:d7:32",
                    "mask": "255.255.255.0",
                    "speed": 10000,
                    "stat": true
                },
                {
                    "interface": "ens256",
                    "ip": "172.16.1.49",
                    "mac": "00:0c:29:5d:d7:3c",
                    "mask": "255.255.255.0",
                    "speed": 10000,
                    "stat": true
                }
            ]
        },
        "msg": "成功"
    }
    ```

### 4、删除节点 ###


* URL

  `/node/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 节点uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、节点关机 ###


* URL

  `/node/shutdown`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 节点uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、节点重启 ###


* URL

  `/node/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 节点uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



### 7、节点新增Bond ###


* URL

  `/node/add_bond`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                            | Type   | Description                                            |
  | ------------------------------- | ------ | ------------------------------------------------------ |
  | ipaddr(required)                | string | 节点管理网络IP                                         |
  | node_uuid(required)             | string | 节点uuid                                               |
  | slaves(required)                | string | 被绑定的物理网卡列表，元素是dict，包含以下2个参数      |
  | nic_uuid(required)              | string | 被绑定的物理网卡uuid                                   |
  | nic_name(required)              | string | 被绑定的物理网卡名称                                   |
  | ip_list(required)               | list   | 添加到bond网卡上的IP列表，元素是dict，包含以下4个参数  |
  | ip(required)                    | string | IP地址                                                 |
  | netmask(required)               | string | 子网掩码                                               |
  | is_manage(required)             | int    | 是否为管理网络                                         |
  | is_image(required)              | int    | 是否为镜像网络                                         |
  | gate_info(required)             | dict   | 添加到bond网卡上的网关/DNS信息，包含以下3个参数        |
  | gateway(required)               | string | 网关                                                   |
  | dns1(required)                  | string | dns1                                                   |
  | dns2(required)                  | string | dns2                                                   |
  | bond_info(required)             | dict   | bond的相关信息，元素是dict，包含以下3个参数            |
  | dev(required)                   | string | bond名称                                               |
  | mode(required)                  | int    | bond类型（只支持0，1，6三种）                          |
  | slaves(required)                | list   | 被绑定的物理网卡名称列表                               |

  - 示例：

    ```json
    {
        "ipaddr": "172.16.1.88",
        "node_uuid": "f819e839-e193-4356-b6b4-acc35652ce27",
        "slaves": [
            {
                "nic_uuid": "d206a470-5252-4d88-96d3-afb125aef1aa",
                "nic_name": "eth1"
            },
            {
                "nic_uuid": "c6c29155-9994-4e2c-a2f6-deba1397297b",
                "nic_name": "eth2"
            }
        ],
        "ip_list":[
            {
                "ip": "192.168.1.88",
                "netmask": "255.255.255.0",
                "is_manage": 0,
                "is_image": 0
            },
            {
                "ip": "192.168.1.89",
                "netmask": "255.255.255.0",
                "is_manage": 0,
                "is_image": 0
            }
        ],
        "gate_info": {
            "gateway": "192.168.1.254",
            "dns1": "8.8.8.8",
            "dns2": ""
         },
        "bond_info": {
            "dev": "bond0",
            "mode": 0,
            "slaves": ["eth1", "eth2"]
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



### 8、节点编辑Bond ###


* URL

  `/node/edit_bond`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                            | Type   | Description                                            |
  | ------------------------------- | ------ | ------------------------------------------------------ |
  | ipaddr(required)                | string | 节点管理网络IP                                         |
  | bond_uuid(required)             | string | bond网卡uuid                                           |
  | slaves(required)                | string | 被绑定的物理网卡列表，元素是dict，包含以下2个参数      |
  | nic_uuid(required)              | string | 被绑定的物理网卡uuid                                   |
  | nic_name(required)              | string | 被绑定的物理网卡名称                                   |
  | ip_list(required)               | list   | 添加到bond网卡上的IP列表，元素是dict，包含以下4个参数  |
  | ip(required)                    | string | IP地址                                                 |
  | netmask(required)               | string | 子网掩码                                               |
  | is_manage(required)             | int    | 是否为管理网络                                         |
  | is_image(required)              | int    | 是否为镜像网络                                         |
  | gate_info(required)             | dict   | 添加到bond网卡上的网关/DNS信息，包含以下3个参数        |
  | gateway(required)               | string | 网关                                                   |
  | dns1(required)                  | string | dns1                                                   |
  | dns2(required)                  | string | dns2                                                   |
  | bond_info(required)             | dict   | bond的相关信息，元素是dict，包含以下3个参数            |
  | dev(required)                   | string | bond名称                                               |
  | mode(required)                  | int    | bond类型（只支持0，1，6三种）                          |
  | slaves(required)                | list   | 被绑定的物理网卡名称列表                               |

  - 示例：

    ```json
    {
        "ipaddr": "172.16.1.88",
        "bond_uuid": "f819e839-e193-4356-b6b4-acc35652ce27",
        "slaves": [
            {
                "nic_uuid": "d206a470-5252-4d88-96d3-afb125aef1aa",
                "nic_name": "eth1"
            },
            {
                "nic_uuid": "c6c29155-9994-4e2c-a2f6-deba1397297b",
                "nic_name": "eth2"
            }
        ],
        "ip_list":[
            {
                "ip": "192.168.1.88",
                "netmask": "255.255.255.0",
                "is_manage": 0,
                "is_image": 0
            },
            {
                "ip": "192.168.1.89",
                "netmask": "255.255.255.0",
                "is_manage": 0,
                "is_image": 0
            }
        ],
        "gate_info": {
            "gateway": "192.168.1.254",
            "dns1": "8.8.8.8",
            "dns2": ""
         },
        "bond_info": {
            "dev": "bond0",
            "mode": 0,
            "slaves": ["eth1", "eth2"]
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



### 9、节点删除Bond ###


* URL

  `/node/unbond`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                            | Type   | Description                                            |
  | ------------------------------- | ------ | ------------------------------------------------------ |
  | ipaddr(required)                | string | 节点管理网络IP                                         |
  | bond_name(required)             | string | bond网卡名称                                           |
  | bond_uuid(required)             | string | bond网卡uuid                                           |
  | slaves(required)                | string | 被绑定的物理网卡列表，元素是dict，包含以下3个参数      |
  | nic_uuid(required)              | string | 被绑定的物理网卡uuid                                   |
  | nic_name(required)              | string | 被绑定的物理网卡名称                                   |
  | ip_list(required)               | list   | 添加到物理网卡上的IP列表，元素是dict，包含以下7个参数  |
  | ip(required)                    | string | IP地址                                                 |
  | netmask(required)               | string | 子网掩码                                               |
  | gateway(required)               | string | 网关                                                   |
  | dns1(required)                  | string | dns1                                                   |
  | dns2(required)                  | string | dns2                                                   |
  | is_manage(required)             | int    | 是否为管理网络                                         |
  | is_image(required)              | int    | 是否为镜像网络                                         |

  - 示例：

    ```json
    {
        "ipaddr": "172.16.1.88",
        "bond_name": "bond0",
        "bond_uuid": "f819e839-e193-4356-b6b4-acc35652ce27",
        "slaves": [
            {
                "nic_uuid": "d206a470-5252-4d88-96d3-afb125aef1aa",
                "nic_name": "eth1",
                "ip_list":[
                    {
                        "ip": "192.168.1.88",
                        "netmask": "255.255.255.0",
                        "gateway": "192.168.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "",
                        "is_manage": 0,
                        "is_image": 0
                    }
                ]
            }
        ]
    }

    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```




## 网络接口

### 1、添加虚拟交换机 ###


* URL

  `/vswitch/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                            |
  | ------------------- | ------ | -------------------------------------- |
  | name(required)      | string | 虚拟交换机名称                         |
  | type(required)      | string | 虚拟交换机类型                         |
  | desc                | string | 描述信息                               |
  | uplinks(required)   | list   | 列表，绑定的网卡信息，每个包括如下字段 |
| node_uuid(required) | string | 节点uuid                               |
  | nic_uuid(required)  | string | 网卡uuid                               |

  - 示例：
  
    ```json
    {
        "name": "switch1",
        "type": "vlan",
        "desc": "this is switch1",
        "uplinks": [
            {
                "node_uuid": "ec7259d8-4885-11ea-8e15-000c295dd728",
                "nic_uuid": "ec795346-4885-11ea-8e15-000c295dd728"
            },
            {
            	"node_uuid": "a04ce3c0-488f-11ea-b1de-000c295dd728",
            	"nic_uuid": "a053a4e4-488f-11ea-b1de-000c295dd728"
            }
        ]
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、删除虚拟交换机 ###


* URL

  `/vswitch/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description    |
  | -------------- | ------ | -------------- |
  | uuid(required) | string | 虚拟交换机uuid |

  - 示例：

    ```json
    {
        "uuid": "caa5d57e-3731-11ea-801e-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、修改虚拟交换机 ###


* URL

  `/vswitch/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                                    |
  | ------------------- | ------ | ---------------------------------------------- |
  | uuid(required)      | string | 修改的虚拟交换机的uuid                         |
  |                     |        |                                                |
  | value(required)     | dict   | 修改后虚拟交换机的属性，跟添加时参数一致，如下 |
  | name(required)      | string | 虚拟交换机名称                                 |
  | type(required)      | string | 虚拟交换机类型                                 |
  | desc                | string | 描述信息                                       |
  | uplinks(required)   | list   | 列表，绑定的网卡信息，每个包括如下字段         |
  | node_uuid(required) | string | 节点uuid                                       |
  | nic_uuid(required)  | string | 网卡uuid                                       |

  - 示例：

    ```json
    {
        "uuid": "ec796624-4885-11ea-8e15-000c295dd728",
        "value": {
            "name": "default",
            "type": "vlan",
            "desc": "this is switch1",
            "uplinks": [
                {
                    "node_uuid": "ec7259d8-4885-11ea-8e15-000c295dd728",
                    "nic_uuid": "ec7951de-4885-11ea-8e15-000c295dd728"
                },
                {
                    "node_uuid": "a04ce3c0-488f-11ea-b1de-000c295dd728",
                    "nic_uuid": "a053a4e4-488f-11ea-b1de-000c295dd728"
                }
            ]
        }
        }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



### 4、添加数据网络 ###


* URL

  `/network/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                  | Type   | Description                                      |
  | --------------------- | ------ | ------------------------------------------------ |
  | name(required)        | string | 网络名称                                         |
  | switch_uuid(required) | string | 虚拟交换机的uuid                                 |
  | vlan_id               | int    | 如果虚拟交换机类型为vlan，则需要提供该参数       |
  |                       |        |                                                  |
  | subnet_info           | dict   | 子网信息，创建网络同时创建子网时提供，具体如下： |
  | subnet_name(required) | string | 子网名称                                         |
  | start_ip(required)    | string | 子网的开始IP                                     |
  | end_ip(required)      | string | 子网的结束IP                                     |
  | netmask(required)     | string | 子网掩码                                         |
  | gateway(required)     | string | 网关                                             |
  | dns1(required)        | string | 首选DNS                                          |
  | dns2                  | string | 备用DNS                                          |

  - 示例：

    ```json
    {
        "name": "network1",
        "switch_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
        "vlan_id": 10,
        "subnet_info": {
            "subnet_name": "default",
            "start_ip": "172.16.1.10",
            "end_ip": "172.16.1.20",
            "netmask": "255.255.0.0",
            "gateway": "172.16.1.254",
            "dns1": "8.8.8.8"
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、删除数据网络 ###

删除网络，首先删除每个节点的网桥等设备，然后删除网络的子网，最后删除网络


* URL

  `/network/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 网络uuid    |

  - 示例：

    ```json
    {
        "uuid": "1a870202-3732-11ea-8a2d-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、修改数据网络 ###

目前数据网络只修改名称


* URL

  `/network/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                  |
  | --------------- | ------ | ---------------------------- |
  | uuid(required)  | string | 网络uuid                     |
  | value(required) | dict   | 需要修改的网络的属性，如下： |
  | name(required)  | string | 网络名称                     |

  - 示例：

    ```json
    {
        "uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
        "value": {
            "name": "network2"
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 7、初始化网络信息（目前已废弃，用控制节点初始化代替） ###

主要是默认的网络信息初始化，包括虚拟交换机、网络和子网


* URL

  `/network/init`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                        |
  | ---------------------- | ------ | ---------------------------------- |
  | network_name(required) | string | 网络名称                           |
  | switch_name(required)  | string | 虚拟交换机名称                     |
  | switch_type(required)  | string | 虚拟交换机的类型，`flat`或者`vlan` |
  | vlan_id                | int    | 如果是`vlan`网络，则需要提供此参数 |
  |                        |        |                                    |
  | subnet_info(required)  | dict   | 子网信息，具体如下：               |
  | name(required)         | string | 子网名称                           |
  | start_ip(required)     | string | 子网的开始IP                       |
  | end_ip(required)       | string | 子网的结束IP                       |
  | netmask(required)      | string | 子网掩码                           |
  | gateway(required)      | string | 网关                               |
  | dns1(required)         | string | 首选DNS                            |
  | dns2                   | string | 备用DNS                            |
|                        |        |                                    |
  | uplink(required)       | string | 虚拟交换机映射关系                 |
| node_uuid(required)    | string | 节点uuid                           |
  | nic_uuid(required)     | string | 映射的网卡uuid                     |
  | interface(required)    | string | 网卡名称                           |
  
  - 示例：
  
    ```json
    {
        "network_name": "default",
        "switch_name": "default",
        "switch_type": "vlan",
        "vlan_id": 10,
        "subnet_info": {
            "name": "default",
            "start_ip": "172.16.1.10",
            "end_ip": "172.16.1.20",
            "netmask": "255.255.0.0",
            "gateway": "172.16.1.254",
            "dns1": "8.8.8.8"
        },
        "uplink": {
        	"node_uuid": "c81b4904-47dc-11ea-be81-000c295dd728",
        	"nic_uuid": "c81da514-47dc-11ea-be81-000c295dd728",
            "interface": "ens224"
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 8、添加子网 ###


* URL

  `/subnet/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description  |
  | ---------------------- | ------ | ------------ |
  | name(required)         | string | 子网名称     |
  | network_uuid(required) | string | 数据网络uuid |
  | start_ip(required)     | string | 子网的开始IP |
  | end_ip(required)       | string | 子网的结束IP |
  | netmask(required)      | string | 子网掩码     |
  | gateway(required)      | string | 网关         |
  | dns1(required)         | string | 首选DNS      |
  | dns2                   | string | 备用DNS      |

  - 示例：

    ```json
    {
        "network_uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
        "name": "subnet2",
        "start_ip": "172.16.1.10",
        "end_ip": "172.16.1.20",
        "netmask": "255.255.0.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 9、删除子网 ###

删除网络的子网


* URL

  `/subnet/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 子网uuid    |

  - 示例：

    ```json
    {
        "uuid": "1a870202-3732-11ea-8a2d-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 10、修改子网 ###

修改子网


* URL

  `/network/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                            |
  | --------------- | ------ | -------------------------------------- |
  | uuid(required)  | string | 子网uuid                               |
  | name            | string | 子网名称                               |
  |                 |        |                                        |
  | value(required) | dict   | 需要更新的子网信息，具体的子网属性如下 |
  | name            | string | 子网名称                               |
  | start_ip        | string | 子网的开始IP                           |
  | end_ip          | string | 子网的结束IP                           |
  | netmask         | string | 子网掩码                               |
  | gateway         | string | 子网网关                               |
  | dns1            | string | DNS                                    |
| dns2            | string | DNS                                    |
  
- 示例：
  
    ```json
    {
        "name": "subnet",
        "uuid": "570a316e-27b5-11ea-9eac-562668d3ccea",
        "value": {
            "name": "subnet1",
            "start_ip": "172.16.1.10",
            "end_ip": "172.16.1.20",
            "netmask": "255.255.0.0",
            "gateway": "172.16.1.254",
            "dns1": "8.8.8.8",
            "dns2": ""
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 教学模板

### 1、新增模板 ###


* URL

  `/template/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                |
  | ---------------------- | ------ | -------------------------- |
  | name(required)         | string | 模板名称                   |
  | desc         | string | 模板描述                   |
  | owner_id(required)   | string | 模板所属用户uuid           |
  | os_type(required)      | string | 模板的系统类型             |
  | classify(required) | int | 模板分类：1-教学模板 2-个人模板 3-系统桌面 |
  | pool_uuid(required)    | string | 资源池uuid                 |
  | network_uuid(required) | string | 数据网络uuid               |
  | subnet_uuid(required)  | string | 子网uuid                   |
  | bind_ip      | string | 模板分配的IP，如果没有则代表系统分配 |
  | vcpu(required)         | int    | 虚拟CPU数目                |
  | ram(required)          | int    | 虚拟内存，单位为MB         |
  | iso | string | 路径，创建系统桌面时提供安装的ISO |
  | power_on | string | 创建完之后是否开机，默认为`false` |
  | template | string | 创建系统桌面时，需设置为`false`（不设置也只是会多加一个cdrom） |
  |                        |        |                            |
  | system_disk            | dict   | 系统盘信息，具体如下：     |
  | image_id(required)     | string | 基础镜像uuid               |
  | size(required)         | int    | 系统盘大小，单位为GB       |
|                        |        |                            |
  | data_disks(required)   | list   | 数据盘信息，单个信息如下： |
  | inx(required)          | int    | 启动顺序                   |
  | size(required)         | int    | 数据盘大小，单位为GB       |
  
- 示例：
  
    ```json
    {
        "name": "template2",
        "desc": "this is template2",
        "owner_id": "16e0a58a-31f2-11ea-b0df-000c2902e179",
        "os_type": "win7",
        "classify": 1,
        "pool_uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
        "network_uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
        "subnet_uuid": "b68bcc96-3732-11ea-b34d-000c295dd728",
        "bind_ip": "172.16.11.21",
    	"vcpu": 2,
    	"ram": 2,
    	"system_disk": {
    		 "image_id": "86d91e92-336b-11ea-ae5a-000c295dd728",
             "size": 50
    	},
        "data_disks": [
      		{
      			"inx": 0,
      			"size": 50
      		},
      		{
      			"inx": 1,
      			"size": 50
      		}
      	]
     }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、删除模板 ###

删除模板，会删除每个节点上面的镜像文件


* URL

  `/template/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 模板uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、模板开机 ###


* URL

  `/template/start`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 模板uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、模板关机 ###


* URL

  `/template/stop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 模板uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、保存模板 ###

在线编辑后进行模板更新，执行如下操作：

1、模板停机，然后将模板的磁盘文件移动到镜像存放目录下

2、资源池中其他节点同步模板的磁盘文件并进行合并

3、模板所在节点进行磁盘文件合并


* URL

  `/template/save`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 资源池uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、复制模板 ###

从已有模板复制一个新模板，底层就是复制模板的系统盘和数据盘，然后新建一个模板虚拟机


* URL

  `/template/copy`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                    | Type   | Description          |
  | ----------------------- | ------ | -------------------- |
  | template_uuid(required) | string | 待复制的模板uuid     |
  | name(required)          | string | 新模板的名字         |
  | desc             | string | 新模板描述           |
  | owner_id(required)    | string | 新模板所属用户       |
  | pool_uuid(required)     | string | 新模板所属资源池uuid |
  | network_uuid(required)  | string | 数据网络uuid         |
  | subnet_uuid(required)   | string | 子网uuid             |
  | bind_ip(required)       | string | 新模板分配的IP       |

  - 示例：

    ```json
    {
        "template_uuid": "9a327142-3b21-11ea-8339-000c295dd728",
        "name": "win7_template_copy",
        "desc": "this is win7 template copy",
        "owner_id": "16e0a58a-31f2-11ea-b0df-000c2902e179",
        "pool_uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
        "network_uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
        "subnet_uuid": "b68bcc96-3732-11ea-b34d-000c295dd728",
        "bind_ip": "172.16.1.28"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 7、下载模板 ###

下载模板，目前方案是在模板所在节点合并差异文件生成新的基础镜像（只有系统盘），该接口返回的是基础镜像的路径


* URL

  `/template/download`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 模板uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "path": "/var/lib/yzy_kvm/instances/_base/e4a53850-26e9-11ea-a72d-562668d3cceb"
        }
    }
    ```

### 8、加载ISO到模板 ###


* URL

  `/template/change_device`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description         |
  | -------------- | ------ | ------------------- |
  | uuid(required) | string | 模板uuid            |
  | name(required) | string | 模板名称            |
  | path(required) | string | 需要加载的ISO的路径 |

  - 示例：

    ```json
    {
    	"uuid": "92ff80a4-3c2a-11ea-87d5-000c295dd728",
    	"name": "template2",
    	"path": "/root/test.iso"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

## 分组

### 1、新增分组 ###

添加教学分组或者用户分组


* URL

  `/group/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type   | Description                                                  |
  | -------------------- | ------ | ------------------------------------------------------------ |
  | name(required)       | string | 分组名称                                                     |
  | group_type(required) | string | 分组类型，`education-教学分组 personal-用户分组`，默认为`education` |
  | desc                 | string | 分组描述                                                     |
  | network_uuid         | string | 数据网络uuid，教学分组时必需                                 |
  | subnet_uuid          | string | 子网uuid，教学分组时必需                                     |
  | start_ip             | string | 预设终端开始IP，教学分组时必需                               |
  | end_ip               | string | 预设终端结束IP，教学分组时必需                               |

- 示例：

  ```json
  {
      "name": "group5",
      "group_type": "education",
      "desc": "this is group1",
      "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
      "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
      "start_ip": "172.16.1.40",
      "end_ip": "172.16.1.60"
  }
  ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、删除分组 ###


* URL

  `/group/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 模板uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、修改分组 ###


* URL

  `/group/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 分组uuid                       |
  | value(required) | dict   | 需要修改的分组新的属性，如下： |
  | name(required)  | string | 分组名称                       |
  | desc            | string | 分组描述                       |
  | network_uuid    | string | 网络uuid                       |
  | subnet_uuid     | string | 子网uuid                       |
  | start_ip        | string | 预设终端开始IP                 |
  | end_ip          | string | 预设终端结束IP                 |

  - 示例：

    ```json
    {
    	"uuid": "02063e92-52ca-11ea-ba2e-000c295dd728",
        "value": {
            "name": "group2",
            "desc": "this is group2",
            "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
            "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
            "start_ip": "172.16.1.40",
            "end_ip": "172.16.1.50"
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 桌面组

### 1、新增教学桌面组 ###


* URL

  `/desktop/education/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                    | Type   | Description                                                |
  | ----------------------- | ------ | ---------------------------------------------------------- |
  | name(required)          | string | 桌面组名称                                                 |
  | owner_id(required)      | string | 创建者ID                                                   |
  | group_uuid(required)    | string | 桌面组所属分组                                             |
  | template_uuid(required) | string | 桌面组使用的模板uuid                                       |
  | pool_uuid(required)     | string | 资源池uuid                                                 |
  | network_uuid(required)  | string | 数据网络uuid                                               |
  | subnet_uuid(required)   | string | 子网uuid                                                   |
  | vcpu(required)          | int    | 虚拟CPU数目                                                |
  | ram(required)           | float  | 虚拟内存，单位为G                                          |
  | sys_restore(required)   | int    | 系统盘是否重启还原                                         |
  | data_restore(required)  | int    | 数据盘是否重启还原                                         |
  | instance_num(required)  | int    | 桌面组中桌面的数量                                         |
  | prefix(required)        | string | 桌面名称的前缀                                             |
| postfix(required)       | int    | 桌面名称后缀是几位数字                                     |
  | postfix_start           | int    | 桌面名称后缀的起始数字，默认为1                            |
  | create_info(required)   | dict   | 桌面在各个节点的分配信息，`key`值是节点IP，`value`则是数目 |
  
- 示例：
  
    ```json
    {
        "name": "desktop2",
        "owner_id": 1,
        "group_uuid": "1c7dff98-2dda-11ea-b565-562668d3ccea",
        "template_uuid": "9a327142-3b21-11ea-8339-000c295dd728",
        "pool_uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
        "network_uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
        "subnet_uuid": "b68bcc96-3732-11ea-b34d-000c295dd728",
        "vcpu": 1,
        "ram": 1,
        "sys_restore": 0,
        "data_restore": 0,
        "instance_num": 4,
        "prefix": "pc",
        "postfix": 3,
        "postfix_start": 5,
        "create_info": {
            "192.168.1.11": 2,
            "192.168.1.12": 2
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功"
    }
    ```

### 2、删除教学桌面组 ###

删除桌面组，数据盘也一并删除


* URL

  `/desktop/education/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、教学桌面组开机 ###

桌面组中的所有桌面开机


* URL

  `/desktop/education/start`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、教学桌面组关机 ###

桌面组中的所有桌面关机


* URL

  `/desktop/education/stop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、教学桌面组激活 ###

用于教学场景，用于终端程序界面，桌面资源枚举显示不显示


* URL

  `/desktop/education/active`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、教学桌面组未激活 ###

用于教学场景，用于终端程序界面，桌面资源枚举显示不显示


* URL

  `/desktop/education/inactive`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 7、修改教学桌面组 ###


* URL

  `/desktop/education/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 桌面组uuid                     |
  | value(required) | dict   | 更新的桌面组的属性，包含如下： |
  | name            | string | 桌面组名字                     |

  - 示例：

    ```json
    {
    	"uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
    	"value": {
    		"name": "desktop2"
    	}
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 8、教学桌面组重启 ###

桌面组中的所有桌面重启，根据还原的属性进行还原操作


* URL

  `/desktop/education/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 桌面

### 1、桌面开机 ###

指定的桌面开机操作


* URL

  `/instance/start`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                                  |
  | ---------------------- | ------ | -------------------------------------------- |
  | desktop_uuid(required) | string | 桌面组uuid                                   |
  | desktop_type(required) | int    | 桌面类型，`1-教学桌面 2-个人桌面`，默认为`1` |
| instances(required)    | list   | 待开机的桌面uuid列表                         |
  
- 示例：
  
    ```json
    {
    	"desktop_uuid": "fd6117ec-35e9-11ea-84ca-000c295dd728",
        "desktop_type": 1,
    	"instances": [
    			"fd61fc98-35e9-11ea-84ca-000c295dd728",
    			"fd620cd8-35e9-11ea-84ca-000c295dd728"
    		]
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、桌面关机 ###

指定的桌面关机操作


* URL

  `/instance/stop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                                  |
  | ---------------------- | ------ | -------------------------------------------- |
  | destop_uuid(required)  | string | 桌面组uuid                                   |
  | desktop_type(required) | int    | 桌面类型，`1-教学桌面 2-个人桌面`，默认为`1` |
| instances(required)    | list   | 待关机的桌面uuid列表                         |
  
- 示例：
  
    ```json
    {
    	"desktop_uuid": "fd6117ec-35e9-11ea-84ca-000c295dd728",
        "desktop_type": 1,
    	"instances": [
    			"fd61fc98-35e9-11ea-84ca-000c295dd728",
    			"fd620cd8-35e9-11ea-84ca-000c295dd728"
    		]
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、添加桌面 ###

向指定的桌面组中添加桌面


* URL

  `/instance/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                                                |
  | ---------------------- | ------ | ---------------------------------------------------------- |
  | destop_uuid(required)  | string | 桌面组uuid                                                 |
  | desktop_type(required) | int    | 桌面类型，`1-教学桌面 2-个人桌面`，默认为`1`               |
  | instance_num(required) | int    | 增加的桌面数                                               |
| create_info(required)  | dict   | 桌面在各个节点的分配信息，`key`值是节点IP，`value`则是数目 |
  
- 示例：
  
    ```json
    {
        "desktop_uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
        "desktop_type": 2,
        "instance_num": 1,
        "create_info": {
            "192.168.1.11": 1
        }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、桌面重启 ###

指定的桌面重启操作


* URL

  `/instance/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                                  |
  | ---------------------- | ------ | -------------------------------------------- |
  | destop_uuid(required)  | string | 桌面组uuid                                   |
  | desktop_type(required) | int    | 桌面类型，`1-教学桌面 2-个人桌面`，默认为`1` |
| instances(required)    | list   | 待重启的桌面uuid列表                         |
  
- 示例：
  
    ```json
    {
    	"desktop_uuid": "fd6117ec-35e9-11ea-84ca-000c295dd728",
        "desktop_type": 1,
    	"instances": [
    			"fd61fc98-35e9-11ea-84ca-000c295dd728",
    			"fd620cd8-35e9-11ea-84ca-000c295dd728"
    		]
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 用户管理

### 1、单用户添加 ###

添加单用户到分组


* URL

  `/group/user/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type    | Description                |
  | -------------------- | ------- | -------------------------- |
  | group_uuid(required) | string  | 用户所属的分组uuid         |
  | user_name(required)  | string  | 用户名                     |
  | passwd(required)     | string  | 用户密码                   |
  | name                 | string  | 用户姓名                   |
  | phone                | string  | 电话号码                   |
  | email                | string  | 邮箱                       |
  | enabled              | boolean | 启用或者禁用状态，默认启用 |

  - 示例：

    ```json
    {
        "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
        "user_name": "user2",
        "passwd": "password",
        "name": "john",
        "phone": "13144556677",
        "email": "345673456@qq.com",
        "enabled": 1
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、批量用户添加 ###

批量添加用户到分组中


* URL

  `/group/user/multi_create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                    | Type    | Description                |
  | ----------------------- | ------- | -------------------------- |
  | group_uuid(required)    | string  | 用户所属的分组uuid         |
  | prefix(required)        | string  | 用户名前缀                 |
  | postfix(required)       | int     | 用户后缀数字个数           |
  | postfix_start(required) | int     | 用户后缀起始数字，默认为1  |
  | user_num(required)      | int     | 用户数量                   |
  | passwd(required)        | string  | 用户密码                   |
  | enabled                 | boolean | 启用或者禁用状态，默认启用 |

  - 示例：

    ```json
    {
        "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
        "prefix": "ctx",
        "postfix": 2,
        "postfix_start": 1,
        "user_num": 5,
        "passwd": "12345",
        "enabled": 1
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、删除用户 ###

删除操作支持批量操作


* URL

  `/group/user/delete`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 用户uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、更新用户信息 ###


* URL

  `/group/user/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type    | Description                    |
  | -------------------- | ------- | ------------------------------ |
  | uuid(required)       | string  | 桌面组uuid                     |
  | value(required)      | dict    | 更新的桌面组的属性，包含如下： |
  | group_uuid(required) | string  | 用户所属的分组uuid             |
  | user_name(required)  | string  | 用户名                         |
  | passwd(required)     | string  | 用户密码                       |
  | name                 | string  | 用户姓名                       |
  | phone                | string  | 电话号码                       |
  | email                | string  | 邮箱                           |
  | enabled              | boolean | 启用或者禁用状态，默认启用     |

  - 示例：

    ```json
    {
    	"uuid": "ba63d8d0-579f-11ea-b1ca-000c295dd728",
    	"value": {
    		"group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
    		"user_name": "test",
            "passwd": "123"
    	}
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、用户启用 ###

设置用户状态为启用


* URL

  `/group/user/enable`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 用户uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、用户禁用 ###

设置用户状态为禁用


* URL

  `/group/user/disable`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description |
  | -------------- | ------ | ----------- |
  | uuid(required) | string | 用户uuid    |

  - 示例：

    ```json
    {
        "uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```



## 个人桌面组

### 1、添加个人桌面组


* URL

  `/desktop/personal/create`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                    | Type   | Description                                                  |
  | ----------------------- | ------ | ------------------------------------------------------------ |
  | name(required)          | string | 桌面组名称                                                   |
  | owner_id(required)      | string | 创建者ID                                                     |
  | template_uuid(required) | string | 桌面组使用的模板uuid                                         |
  | pool_uuid(required)     | string | 资源池uuid                                                   |
  | network_uuid            | string | 数据网络uuid，可选                                           |
  | subnet_uuid             | string | 子网uuid，可选                                               |
  | allocate_type(required) | int    | IP分配类型，`1-系统分配 2-固定分配`，当没有网络选择并且是`1-系统分配`时，由环境中DHCP负责IP分配 |
  | allocate_start          | string | 当选择了网络，并且分配类型为`2-固定分配`时，需要提供此参数，表示起始IP |
  | vcpu(required)          | int    | 虚拟CPU数目                                                  |
  | ram(required)           | int    | 虚拟内存，单位为MB                                           |
  | sys_restore(required)   | int    | 系统盘是否重启还原                                           |
  | data_restore(required)  | int    | 数据盘是否重启还原                                           |
  | desktop_type(required)  | int    | 桌面类型，`1-随机桌面 2-静态桌面`                            |
  | groups                  | list   | 当桌面类型为`1-随机桌面`时，需要提供此参数，表示个人桌面组关联的用户分组uuid列表 |
  | allocates               | list   | 当桌面类型为`2-静态桌面`时，需要提供此参数，表示桌面与具体用户的对应关系（只能对应一个用户分组中的用户），其中的每个元素包括(group_uuid, user_uuid, name)三个`key`以及对应的值，分别表示用户分组、用户、和桌面 |
  | instance_num(required)  | int    | 桌面组中桌面的数量                                           |
  | prefix(required)        | string | 桌面名称的前缀                                               |
  | postfix(required)       | int    | 桌面名称后缀是几位数字                                       |
  | postfix_start           | int    | 桌面名称后缀的起始数字，默认为1                              |
| create_info(required)   | dict   | 桌面在各个节点的分配信息，`key`值是节点IP，`value`则是数目   |
  
- 示例：
  
    ```json
    {
    	"action": "create",
    	"param": {
    		"name": "desktop2",
            "owner_id": 1,
    	    "template_uuid": "655a1b9c-592a-11ea-b491-000c295dd728",
    	    "pool_uuid": "9c888a04-5213-11ea-9d93-000c295dd728",
    	    "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
    	    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
    	    "allocate_type": 1,
    	    "vcpu": 1,
    	    "ram": 1,
    	    "sys_restore": 1,
    	    "data_restore": 1,
    	    "desktop_type": 2,
    	    "allocates": [
    	    		{
    	    			"group_uuid": "1c6d36be-593c-11ea-8fd0-000c295dd728",
    	    			"user_uuid": "01d0e1b8-593f-11ea-9d4b-000c295dd728",
    	    			"name": "pc03"
    	    		},
    	    		{
    	    			"group_uuid": "1c6d36be-593c-11ea-8fd0-000c295dd728",
    	    			"user_uuid": "01d1c902-593f-11ea-9d4b-000c295dd728",
    	    			"name": "pc04"
    	    		},
    	    		{
    	    			"group_uuid": "1c6d36be-593c-11ea-8fd0-000c295dd728",
    	    			"user_uuid": "01d27ca8-593f-11ea-9d4b-000c295dd728",
    	    			"name": "pc05"
    	    		}
    	    	],
    	    "instance_num": 3,
    	    "prefix": "pc",
    	    "postfix": 2,
    	    "postfix_start": 3,
    	    "create_info": {
    	    	"172.16.1.49": 2,
    	    	"172.16.1.11": 1
    	    }
    	}
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 2、个人桌面组开机

开机需要支持批量操作


* URL

  `/desktop/personal/start`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | uuid | string | 需要开机的桌面组uuid |

  - 示例：

    ```json
    {
    	"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、个人桌面组关机

关机需要支持批量操作


* URL

  `/desktop/personal/stop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | uuid | string | 需要关机的桌面组uuid |

  - 示例：

    ```json
    {
    	"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、删除个人桌面组 ###

删除需要支持批量操作


* URL

  `/desktop/personal/delete`

* Method

  **POST** 请求，**body** 使用 **json** 格式

* Parameters

  | Name | Type   | Description |
  | ---- | ------ | ----------- |
  | uuid | string | 桌面组uuid  |

  - 示例：

    ```json
    {
    	"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、修改桌面组信息 ###


* URL

  `/desktop/personal/update`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 桌面组uuid                     |
  | value(required) | dict   | 更新的桌面组的属性，包含如下： |
  | name            | string | 桌面组名字                     |

  - 示例：

    ```json
    {
    	"uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
    	"value": {
    		"name": "desktop2"
    	}
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 6、个人桌面组重启

重启需要支持批量操作


* URL

  `/desktop/personal/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | uuid | string | 需要重启的桌面组uuid |

  - 示例：

    ```json
    {
    	"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

## 终端管理服务
### 1、终端个人账号登录


* URL

  `/api/v1/terminal/personal/login`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | username | string | 个人账号 |
  | password | string | 密码 |
  | mac | string | 终端mac地址 |

  - 示例：

    ```json
    {
        "user_name": "test1",
        "password": "123456",
        "mac": "x1-12-54-e5-92-t5"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | uuid | str    | 用户uuid|
  | user_name| str| 用户名|
  |session_id| str| session id|
  |expire_time| str| session 过期时间|
  |group_uuid| str| 分组uuid|
  |phone    | str| 手机号码|
  |email    | str| 邮件地址|
  |old_mac| str| 已登录终端mac, 可选，存在即已有其他终端登录此账号|
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {
        "email": "admin@qq.com",
        "expire_time": "2020-04-09 09:58:07",
        "group_uuid": "2ed26ee2-7763-11ea-ac16-000c29893b03",
        "phone": "15811833118",
        "session_id": "80d72a65047ccd5fd1cc9cadf220413f",
        "user_name": "测试1",
        "uuid": "dae78168-7763-11ea-ac16-000c26893b03"
      },
      "msg": "成功"
    }
    ```
    
### 2、终端账号注销


* URL

  `/api/v1/terminal/personal/logout`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | session_id | string | session id |

  - 示例：

    ```json
    {
        "session_id": "dda54a4b50315f3e7d1352dfa723152d"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {
      },
      "msg": "成功"
    }
    ```
    
### 3、终端账号修改账号密码


* URL

  `/api/v1/terminal/personal/change_pwd`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | user_name | string | 用户名 |
  | password | string | 密码 |
  | new_password | string | 新密码 |

  - 示例：

    ```json
    {
        "user_name": "xxx",
        "password": "12345678",
        "new_password": "123456"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {
      },
      "msg": "成功"
    }
    ```
    
### 4、获取个人桌面组列表枚举


* URL

  `/api/v1/terminal/personal/person_desktops`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | session_id | string | session id |


  - 示例：

    ```json
    {
        "session_id": "dda54a4b50315f3e7d1352dfa723152d"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | uuid | str | 桌面组uuid |
  | name | str | 桌面组名称 |
  | desc | str | 桌面组描述 |
  | maintenance | bool | 维护状态， true 正常  false 维护|
  | order_num | int | 排序号|
  
  - 示例：

    ```json
    {
          "code": 0,
          "data": [
            {
              "maintenance": true,
              "desc": "this is person template1",
              "name": "desktop2",
              "uuid": "15a4f8fc-776f-11ea-86aa-000c29893b03",
              "order_num": 1
            },
            {
              "maintenance": true,
              "desc": "this is person template1",
              "name": "desktop3",
              "uuid": "807070de-7789-11ea-b65c-000c29893b03",
              "order_num": 2
            },
            {
              "maintenance": true,
              "desc": "this is person template1",
              "name": "desktop5",
              "uuid": "b4967c66-7a11-11ea-b406-000c29893b03",
              "order_num": 3
            }
          ],
          "msg": "成功"
    }
    ```
    
### 5、获取教学桌面组列表枚举


* URL

  `/api/v1/terminal/education/edu_desktops`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | terminal_id | int | 终端id |
  | terminal_ip | str | 终端ip|


  - 示例：

    ```json
    {
        "terminal_id": 1,
        "terminal_ip": "172.16.1.13"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | uuid | str | 桌面组uuid |
  | name | str | 桌面组名称 |
  | desc | str | 桌面组描述 |
  | active | bool | 激活状态， true 正常  false 维护|
  | order_num | int| 排序号|
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": [
        {
          "active": false,
          "desc": "this is template1",
          "name": "desktop2",
          "uuid": "4a45f592-755e-11ea-8f9c-000c29893b03",
          "order_num": 1
        },
        {
          "active": false,
          "desc": "this is template1",
          "name": "desktop3",
          "uuid": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
          "order_num": 2
        }
      ],
      "msg": "成功"
    }
    ```
    
### 6、点击进入个人桌面


* URL

  `/api/v1/terminal/personal/instance`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | session_id | str | session id |
  | desktop_uuid | str | 桌面组uuid|
  | desktop_name | str | 桌面组名称|


  - 示例：

    ```json
    {
    	 "session_id": "dda54a4b50315f3e7d1352dfa723152d",
        "desktop_uuid": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
        "desktop_name": "个人桌面1"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | uuid | str | 桌面组uuid |
  | name | str | 桌面组名称 |
  | spice_host | str | spice节点ip |
  | spice_token | str | spice登录passwd|
  | spice_port | int | spice链接端口|
  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {
      		"spice_host": "172.16.1.30",
            "spice_token": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
            "spice_port": 5905,
            "name": "pc001",
            "uuid": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
            "os_type": "win7"
      },
      "msg": "成功"
    }
    ```

### 7、点击进入教学桌面


* URL

  `/api/v1/terminal/education/instance`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | terminal_id | str | 终端 id |
  | mac 		| str| 终端mac |
  | ip 		| str| 终端ip |
  | desktop_uuid | str | 桌面组uuid|
  | desktop_name | str | 桌面组名称|


  - 示例：

    ```json
    {
    	"terminal_id": 1,
    	"mac": "xx-xx-xx-xx-xx-xx",
    	"ip": "192.168.1.20"
        "desktop_uuid": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
        "desktop_name": "教学桌面1"
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | uuid | str | 桌面组uuid |
  | name | str | 桌面组名称 |
  | spice_host | str | spice节点ip |
  | spice_token | str | spice登录passwd|
  | spice_port | str | spice链接端口|
  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {
      		"spice_host": "172.16.1.30",
            "spice_token": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
            "spice_port": 5905,
            "name": "pc001",
            "uuid": "0d89b3f0-76a8-11ea-ac4f-000c29893b03",
            "os_type": "win7"
      },
      "msg": "成功"
    }
    ```

### 8、查询终端与云桌面的ip绑定关系

* URL

  `/api/v1/terminal/instance/list`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| terminal_id | str | 终端 id |
| terminal_mac 		| str| 终端mac |
| terminal_ip 		| str| 终端ip |

```json
	[
		{"terminal_id": 1, "terminal_mac":"00:23:33", "terminal_ip": 			"192.168.1.10"},{"terminal_id": 2, "terminal_mac":"00:23:34", 			"terminal_ip": "192.168.1.3"},{"terminal_id": 5, 						"terminal_mac":"00:23:34", "terminal_ip": "192.168.1.34"}
	]
	
```

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | desktop_ip | str | 桌面ip |
  | terminal_id | str | 终端序号 |
  | terminal_ip |str | 终端ip|
  |terminal_mac| str| 终端mac|

  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": [
        {
          "desktop_ip": "172.16.1.10",
          "group_uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
          "terminal_id": 1,
          "terminal_ip": "192.168.1.10",
          "terminal_mac": "00:23:33"
        },
        {
          "desktop_ip": "172.16.1.11",
          "group_uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
          "terminal_id": 2,
          "terminal_ip": "192.168.1.3",
          "terminal_mac": "00:23:34"
        }
      ],
      "msg": "成功"
    }
    ```

### 9、查询终端与云桌面的ip绑定关系

* URL

  `/api/v1/terminal/instance/list`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| terminal_id | str | 终端 id |
| terminal_mac 		| str| 终端mac |
| terminal_ip 		| str| 终端ip |


```json
	{{"terminal_id": 1, "terminal_mac":"00:23:33", "terminal_ip": "192.168.1.10"},{"terminal_id": 2, "terminal_mac":"00:23:34", "terminal_ip": "192.168.1.3"},{"terminal_id": 5, "terminal_mac":"00:23:34", "terminal_ip": "192.168.1.34"}}
	
```

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | desktop_ip | str | 桌面ip |
  | terminal_id | str | 终端序号 |
  | terminal_ip |str | 终端ip|
  |terminal_mac| str| 终端mac|

  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": [
        {
          "desktop_ip": "172.16.1.10",
          "group_uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
          "terminal_id": 1,
          "terminal_ip": "192.168.1.10",
          "terminal_mac": "00:23:33"
        },
        {
          "desktop_ip": "172.16.1.11",
          "group_uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
          "terminal_id": 2,
          "terminal_ip": "192.168.1.3",
          "terminal_mac": "00:23:34"
        }
      ],
      "msg": "成功"
    }
    ```
    
### 10、终端关闭单个云桌面接口

* URL

  `/api/v1/terminal/instance/close`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| desktop_uuid | str | 桌面uuid |

```json
	{
		"desktop_uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f"
	}
```

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {},
      "msg": "成功"
    }
    ```

### 11、个人终端关闭云桌面接口

* URL

  `/api/v1/terminal/personal/close_instance`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| session_id | str | session id |
| mac| str| 终端mac|

```json
	{
		"session_id": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
		"mac": "xx-xx-xx-xx-xx-xx"
	}
```

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  

### 12、教学终端关闭云桌面接口

* URL

  `/api/v1/terminal/education/close_instance`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| mac  |str		| 终端mac				  |

```json
	{
		"mac": "xx-xx-xx-xx-xx-xx"
	}
```

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  

  
  
  - 示例：

    ```json
    {
      "code": 0,
      "data": {},
      "msg": "成功"
    }
    ```

### 13，桌面分组列表接口

* URL

  `/api/v1/terminal/instance/groups`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters



* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |name| str| 分组名称|
  |uuid| str| 分组uuid|
  |group_type| int | 分组类型 1- 教学分组，2-个人分组|
  |start_ip| str| 终端起始ip|
  |end_ip |str| 终端结束ip|
  
  - 示例：

    ```json
    {
        "code": 0,
        "data": [
            {
                "end_ip": "192.168.1.240",
                "group_type": 1,
                "name": "教学分组1",
                "start_ip": "192.168.1.2",
                "uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f"
            },
            {
                "end_ip": "",
                "group_type": 2,
                "name": "个人分组",
                "start_ip": "",
                "uuid": "a5ad57dd-8428-46fe-beff-ea3812e68394"
            }
        ],
        "msg": "成功"
    }
    ```
    
### 14，终端分组信息查询

* URL

  `/api/v1/terminal/education/group`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
| Name | Type   | Description          |
| :--- | :----- | :------------------- |
| terminal_ip | str    | 终端ip               |


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |name| str| 分组名称|
  |uuid| str| 分组uuid|
  
  - 示例：

    ```json
    {
        "code": 0,
        "data": {
                "name": "教学分组1",
                "uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f"
            },
        "msg": "成功"
    }
    ```
    

## 监控管理

### 1、上报节点监控数据 ###


* URL

	`/node/report_monitor`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | node_uuid  | str  | 节点uuid |
    |type| str| 上报数据类型，half_min_monitor - 30s秒的平均数据|
    |name| str| 节点名称|
    |timestamp | int | 时间戳| 
   	| data| object |监控数据|
    
   
    - 示例：
    
      ```json
       {
            "node_uuid": "xxxxxxxxxxx",
            "type": "half_min_monitor",
            "name": "xxxxxxxxxxxxx",
            "timestamp": 123456,
            "data": {
                "cpu": {
                    “user”: 0.0,
                    "system": 0.0,
                    "idle": 0.0
					"percent": 3.2
                },
                "mem": {
                    "total": 12345,
                    "used": 123421,
                    "percent": 24.7,
                    "free": 12344

                },
                "net": {
                    "eth0": {
                        "speed": 10000,
                        "up": "xxxxx",
                        "down": "xxxxxx",
                        "ipv4": [
                            {
                                "addr" : "", "netmask": ""
                            }
                        ]

                    },
                    "eth1": {
                        "speed": 10000,
                        "up": "xxxx",
                        "down": "xxxxx",
                        "ipv4": [

                        ]
                    }
                },
                "disk": {
                    "sda":{
                        "read_rate": "xxxxx",
                        "write_rate": "xxxxx",
                        "total": xxxxxx,
                        "used": xxxxxx
                    }
                }
            }
       }
      ```


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |utc| 查询时间的UTC值| int| data|linux上使用命令查看: date --date @1576751520 |
  |cpu_util| cpu使用率| array| data| 节点名字、使用率，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |disk_util| SSD磁盘使用率| array| data| 节点名字、使用率、总字节数、已使用字节数，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |memory_util| 内存使用率| array| data| 节点名字、使用率，已经按照使用率从大到小排好顺序，最大5个，也可能为空|
  |nic_util| 管理网卡使用率| array| data| 节点名字、读写平均字节数每秒、读写最大字节数每秒，已经按照平均值从大到小排好顺序，最大5个，也可能为空|

  - 示例：

    ```json
	{
		"code": 0,
		"msg": "成功",
		"data": {
			"utc": 1588820301,
			"cpu_util": [
				["main_host", "51.48"],
				["computer1", "2.11"]
			],
			"disk_util": [
				["main_host", "7.89", 348691902464, 27500318720],
				["computer1", "3.66", 348559790080, 12763496448]
			],
			"memory_util": [
				["main_host", "81.70"],
				["computer1", "46.50"]
			],
			"nic_util": [
				["main_host", 12201, 19209],
				["computer1", 636, 4290]
			]
		}
	}
    ```
