[TOC]

# Web接口文档 #

web端的接口`endpoint`为`http://127.0.0.1:50004/api/v1.0/`

## 主页 ##
### 1、获取TOP5节点监控数据 ###
* URL

	`/index/get_top_data/`

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
	
### 2、获取系统统计数据 ###
* URL

	`/index/get_resource_statistic/`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns
  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |online_node_cnt| 在线节点数| int| data| |
  |sum_node_cnt| 节点总数| int| data| |
  |online_instance_cnt| 在线虚拟机数| int| data| |
  |sum_instance_cnt| 虚拟机总数| int| data| |
  |online_terminal_cnt| 在线终端数| int| data| |
  |sum_terminal_cnt| 终端总数| int| data| |
  |resource_pool_cnt| 资源池数| int| data| |
  |alarm_node_cnt| 告警节点数| int| data| |
  |alarm_records_cnt| 告警记录总条数| int| data| |
  |license_status| 授权状态| int| data| 0-试用版 1-正式版|
  |trial_days| 试用天数| int| data||
  |license_terminal_cnt| 授权终端总数| int| data| |

  - 示例：

    ```json
	{
		"code":0,
		"msg":"成功",
		"data":{
			"online_node_cnt":2,
			"sum_node_cnt":2,
			"online_instance_cnt":5,
			"sum_instance_cnt":25,
			"online_terminal_cnt":3,
			"sum_terminal_cnt":4,
			"resource_pool_cnt":2,
			"alarm_node_cnt":6,
			"alarm_records_cnt":666,
			"license_status":0,
			"trial_days":30,
			"license_terminal_cnt":300
		}
	}
    ```
	
### 3、获取系统操作日志 ###
* URL

	`/index/get_operation_log/?page=2&page_size=20`

* Method

	**GET** 请求，**body** 无 **json** 格式
	
* Returns
  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |user_name| 管理员名称| str| data| |
  |create_at| 操作时间| str| data| |
  |content| 操作内容| str| data| |


  - 示例：

    ```json
	{
		"code":0,
		"msg":"成功",
		"data":{
		"count":101,
		"next":"http://172.16.1.33:50004/api/v1.0/index/get_operation_log/?page=2&page_size=5",
		"previous":null,
		"results":[
			{"id":101,"deleted_at":null,"updated_at":"2020-05-06 21:56:15","created_at":"2020-05-06 21:56:15","deleted":0,"user_id":null,"user_name":"admin","user_ip":null,"content":"修改管理员用户信息: 7","result":"{'code': 0, 'msg': '成功'}","module":"default"},
			{"id":100,"deleted_at":null,"updated_at":"2020-05-06 21:56:07","created_at":"2020-05-06 21:56:07","deleted":0,"user_id":null,"user_name":"admin","user_ip":null,"content":"修改管理员用户信息: 1","result":"{'code': 0, 'msg': '成功'}","module":"default"},
			{"id":99,"deleted_at":null,"updated_at":"2020-05-06 21:44:34","created_at":"2020-05-06 21:44:34","deleted":0,"user_id":null,"user_name":"admin","user_ip":null,"content":"创建管理员用户: ck","result":"{'code': 0, 'msg': '成功'}","module":"default"},
			{"id":98,"deleted_at":null,"updated_at":"2020-05-06 21:42:11","created_at":"2020-05-06 21:42:11","deleted":0,"user_id":1,"user_name":"admin","user_ip":"172.16.1.56","content":"删除模板'asdfasd'","result":"成功","module":"default"},
			{"id":97,"deleted_at":null,"updated_at":"2020-05-06 21:40:20","created_at":"2020-05-06 21:40:20","deleted":0,"user_id":1,"user_name":"admin","user_ip":"172.16.1.56","content":"删除模板'asdfasd'","result":"模板'asdfasd'删除失败","module":"default"}
			]
		}
	}
	```


## 控制节点管理 ##

### 1、控制节点列表基本信息 ###

* URL

	`/api/v1.0/resource_mgr/controller_nodes`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |count|int|数据总数|
  |results|object|当前页的数据数组|
  |uuid| str| 节点uuid|
  |name| str| 节点名称|
  |hostname|str|节点hostname|
  |ip| str| 节点IP|
  |usage_sys|str|系统存储使用率|
  |usage_data|str|数据存储使用率|
  |total_sys|str|总系统存储|
  |used_sys|str|已使用系统存储|
  |server_version_info|str|服务器版本|
  |cpu_info|str|CPU信息|
  |mem_info|str|内存信息|
  |gpu_info|str|显卡信息|
  |total_vm|int|虚拟机总数量|
  |running_vm|int|虚拟机运行数量|
  |status|str|节点状态 shutdown- active-|
  |type|int| 节点类型：1-计算和主控一体, 2-计算和备控一体, 3-主控, 4-备控,5-计算|
  |total_vcpus| int| 虚拟cpu核数|
  |running_vcpus| int| 运行cpu核数|
  |usage_vcpus|str| cpu使用率|
  |total_mem| int| 总内存，单位：G|
  |running_mem|int| 运行内存，单位：G|
  |usage_mem|str| 内存使用率|
  |network_interfaces| object| 网卡信息|
  |storages| object| 存储设备信息|
  |deleted|int|是否删除 0 -否|
  |deleted_at|str|删除时间|
  |updated_at|str|更新时间|
  |created_at|str|创建时间|
  

  - 示例：

    ```json
     {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 2,
                    "name": "bcb15c5fcf.cloud.com",
                    "uuid": "96f8b109-7613-4aab-b455-26f69d299c01",
                    "hostname": "bcb15c5fcf.cloud.com",
                    "ip": "172.16.1.66",
                    "total_mem": 0,
                    "running_mem": 0,
                    "total_vcpus": 0,
                    "running_vcpus": 0,
                    "server_version_info": null,
                    "gpu_info": null,
                    "cpu_info": null,
                    "mem_info": null,
                    "status": "active",
                    "type": 5,
                    "created_at": "2020-04-13 09:52:29",
                    "updated_at": "2020-04-13 09:52:29",
                    "deleted_at": null,
                    "network_interfaces": [
                        {
                            "id": 4,
                            "uuid": "c941a7af-f9f1-48a8-984b-c360f5051d5d",
                            "nic": "eth0",
                            "mac": "00:0c:29:a2:95:8d",
                            "speed": 10000,
                            "status": 2,
                            "type": 0,
                            "deleted_at": null,
                            "updated_at": "2020-04-13 09:52:29",
                            "created_at": "2020-04-13 09:52:29",
                            "ip_info": [
                                {
                                    "uuid": "ca430ee3-b2c1-448f-8853-45f8ee360035",
                                    "ip": "172.16.1.66",
                                    "netmask": "255.255.255.0",
                                    "gateway": "172.16.1.254",
                                    "dns1": "114.114.114.114",
                                    "dns2": "8.8.8.8",
                                    "is_manage": 1,
                                    "is_image": 1
                                }
                            ]
                        }
                    ],
                    "storages": [
                        {
                            "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                            "path": "/opt/slow",
                            "used": 46161920,
                            "total": 27579797504,
                            "usage": "0.17",
                            "role": "1,2,3,4"
                        }
                    ],
                    "TEMPLATE_SYS": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "TEMPLATE_DATA": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "INSTANCE_SYS": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "INSTANCE_DATA": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "usage_sys": "0.17",
                    "usage_data": "0.17",
                    "total_sys": 55159595008,
                    "used_sys": 92323840,
                    "usage_mem": 0,
                    "usage_vcpu": 0,
                    "total_vm": 0,
                    "running_vm": 0
                }
            ]
        }
    }
    ```

### 2、控制节点重启 ###

* URL

  `/api/v1.0/resource_mgr/controller_nodes/<str:controller_node_uuid>/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 3、控制节点关机 ###

* URL

  `/api/v1.0/resource_mgr/controller_nodes/<str:controller_node_uuid>/shutdown`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 4、控制节点修改名称 ###

* URL

  `/api/v1.0/resource_mgr/controller_nodes/<str:controller_node_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | name             |string| 新的显示名称|
  | add_compute_function |boolean| 是否加入计算节点|
  
  - 示例：

    ```json
    {
      "name": "xxx",
      "add_compute_function": false
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功"
    }
    ```

### 5、节点服务列表 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/services?page=1&page_size=10`

* Parameters

  | Name |Type|Description|
  | :------- | :----| :-----|
  |page |int | 页面 |
  |page_size |str | 当前页条数|

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

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
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "xxx",
                    "name": "mysql",
                    "status": 0
                },
                {
                    "uuid": "xxx",
                    "name": "redis",
                    "status": 0
                }
            ]
        }
    }
    ```

### 6、节点重启服务 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/services/<str:service_uuid>/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

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

### 7、节点网卡添加附属IP ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | ip_info             |object|               |
  
  - 示例：

    ```json
    {
        "ip": "192.168.1.49",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.245",
        "dns1": "114.114.114.114",
        "dns2": "8.8.8.8"
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
            "dns1": "114.114.114.114",
            "dns2": "8.8.8.8",
            "gateway": "192.168.2.245",
            "ip": "192.168.2.229",
            "name": "eth2:0",
            "netmask": "255.255.255.0",
            "uuid": "b7877c75-0c0b-4c0f-b81f-6080728301e9"
        }
    }
    ```

### 8、节点网卡修改附属IP ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos/<str:ip_info_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | ip             |object|               |
  
  - 示例：

    ```json
    {
        "ip": "192.168.1.49",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.245",
        "dns1": "114.114.114.114",
        "dns2": "8.8.8.8"
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
            "dns1": "114.114.114.114",
            "dns2": "8.8.8.8",
            "gateway": "192.168.2.245",
            "ip": "192.168.2.229",
            "name": "eth2:0",
            "netmask": "255.255.255.0",
            "uuid": "b7877c75-0c0b-4c0f-b81f-6080728301e9"
        }
    }
    ```

### 9、节点网络信息 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

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
        "data": [
            {
                "id": 1,
                "uuid": "3db171a7-1650-4921-a825-99ee4ff4e655",
                "nic": "eth0",
                "mac": "52:54:00:a7:a6:49",
                "speed": 0,
                "status": 2,
                "type": 0,
                "deleted_at": null,
                "updated_at": "2020-04-10 15:23:24",
                "created_at": "2020-04-10 15:23:24",
                "ip_info": [
                    {
                        "uuid": "8a71b5ba-73de-11ea-87ba-000c29893b03",
                        "ip": "172.16.1.32",
                        "netmask": "255.255.255.0",
                        "gateway": "172.16.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "114.114.114.114",
                        "is_manage": 1,
                        "is_image": 1
                    }
                ]
            }
        ]
    }
    ```


### 10、节点Bond信息 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/bond`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

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
      "data": [
        {
          "uuid": "4c237462-1fb0-44ad-ba41-fb8027ce06d7",
          "nic": "bond0",
          "status": 2,
          "mode": 0,
          "slaves": [
            {
              "uuid": "df24b3df-0a8d-4b95-bbf3-67d0033b9080",
              "nic": "eth1"
            },
            {
              "uuid": "b1b3c657-9ee4-49eb-91f6-968a005a129e",
              "nic": "eth2"
            }
          ],
          "ip_info": [
            {
              "uuid": "a05c3b9c-78fe-4354-9aac-71ef8822f0cc",
              "ip": "192.168.1.71",
              "netmask": "255.255.255.0",
              "gateway": "192.168.1.254",
              "dns1": "8.8.8.8",
              "dns2": "",
              "is_manage": 0,
              "is_image": 1
            },
            {
              "uuid": "e34ddfcd-c698-4648-8cf3-e87d0411db43",
              "ip": "192.168.1.76",
              "netmask": "255.255.255.0",
              "gateway": "192.168.1.254",
              "dns1": "8.8.8.8",
              "dns2": "",
              "is_manage": 0,
              "is_image": 0
            }
          ],
          "deleted_at": null,
          "created_at": "2020-07-18 00:42:50",
          "updated_at": "2020-07-18 02:44:12"
        }
      ]
    }
    ```



### 11、节点新增Bond ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/bond`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                            |
  | ---------------------- | ------ | -------------------------------------- |
  | bond_name(required)    | str    | bond名称                               |
  | mode(required)         | int    | bond类型（只支持0，1，6三种）          |
  | slaves(required)       | list   | 被绑定的物理网卡uuid列表               |
  | ip_list(required)      | list   | 添加到bond网卡上的IP列表，元素是object |
  | ip(required)           | str    | IP地址                                 |
  | netmask(required)      | str    | 子网掩码                               |
  | gate_info(required)    | object | 添加到bond网卡上的网关/DNS信息         |
  | gateway(required)      | str    | 网关                                   |
  | dns1(required)         | str    | dns1                                   |
  | dns2(required)         | str    | dns2                                   |

  - 示例：

    ```json
    {
        "bond_name": "bond0",
        "mode": 0,
        "slaves": [
            "df24b3df-0a8d-4b95-bbf3-67d0033b9080",
            "b1b3c657-9ee4-49eb-91f6-968a005a129e"
        ],
        "ip_list":[
            {
                "ip": "192.168.1.76",
                "netmask": "255.255.255.0"
            }
        ],
        "gate_info": {
            "gateway": "192.168.1.254",
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
        "msg": "成功",
        "data": {}
    }
    ```



### 12、节点编辑Bond ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/bond/<str:bond_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                            |
  | ---------------------- | ------ | -------------------------------------- |
  | mode(required)         | int    | bond类型（只支持0，1，6三种）          |
  | slaves(required)       | list   | 被绑定的物理网卡uuid列表               |
  | ip_list(required)      | list   | 添加到bond网卡上的IP列表，元素是object |
  | ip(required)           | str    | IP地址                                 |
  | netmask(required)      | str    | 子网掩码                               |
  | gate_info(required)    | object | 添加到bond网卡上的网关/DNS信息         |
  | gateway(required)      | str    | 网关                                   |
  | dns1(required)         | str    | dns1                                   |
  | dns2(required)         | str    | dns2                                   |

  - 示例：

    ```json
    {
        "mode": 1,
        "slaves": [
            "df24b3df-0a8d-4b95-bbf3-67d0033b9080",
            "b1b3c657-9ee4-49eb-91f6-968a005a129e",
            "d07d1845-ddf4-461c-ac6a-f11ddfdc7915"
        ],
        "ip_list":[
            {
                "ip": "192.168.1.77",
                "netmask": "255.255.255.0"
            }
        ],
        "gate_info": {
            "gateway": "192.168.1.254",
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
        "msg": "成功",
        "data": {}
    }
    ```



### 13、节点删除Bond ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/bond/<str:bond_uuid>`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                            |
  | ---------------------- | ------ | -------------------------------------- |
  | inherit_infos(required)| list   | 继承IP列表，元素是object               |
  | nic_uuid(required)     | str    | 继承IP的物理网卡uuid                   |
  | ip_uuid(required)      | str    | 继承IP的uuid                           |

  - 示例：

    ```json
    {
        "inherit_infos":[
                {
                    "nic_uuid": "df24b3df-0a8d-4b95-bbf3-67d0033b9080",
                    "ip_uuid": "e165aa3d-2d2a-4ea7-a339-fb67561829a7"
                },
                {
                    "nic_uuid": "b1b3c657-9ee4-49eb-91f6-968a005a129e",
                    "ip_uuid": "36b626e6-16de-4eac-a7bc-8c38a6a1573c"
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
        "msg": "成功",
        "data": {}
    }
    ```



## 资源池管理 ##

### 1、资源池列表 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools?page=1&page_size=10`

* Method

	**GET** 请求，**body** 无 **json** 格式

* Parameters

  | Name |Type|Description|
  | :------- | :----| :-----|
  |page|int | 页面 |
  |page_size |str | 当前页条数|

* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |count|int|数据总数|
  |results|object|当前页的数据数组|
  |uuid| str| 资源池uuid|
  |name| str| 资源池名称|
  |desc|str|资源池描述|
  |host_count| int| 计算节点数量 |
  |status| int | 状态 0 - 正常， 1 - 数据同步中，2 - 异常 |
  |default| int |是否为默认资源池|
  |deleted|int|是否删除 0 -否|
  |deleted_at|str|删除时间|
  |updated_at|str|更新时间|
  |created_at|str|创建时间|
  

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "deleted_at": null,
                    "updated_at": "2020-04-01 08:30:55",
                    "created_at": "2020-04-01 08:30:55",
                    "host_count": 0,
                    "status": 0,
                    "uuid": "0cfd7534-73b0-11ea-bc42-000c29893b03",
                    "deleted": 0,
                    "name": "default",
                    "desc": null,
                    "default": 1
                }
            ]
        }
    }
    ```

### 2、新增资源池 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式
	
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | name(required) | string  | 资源池名称       |
    | desc(required) | string  | 资源池描述       |
    
    - 示例：
    
      ```json
    {
        "name": "royin008",
        "desc": "royin008 测试"
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
        "msg": "success",
        "data": {
            "id": 15,
            "host_count": 0,
            "status": 0,
            "deleted_at": null,
            "updated_at": null,
            "created_at": "2020-03-02 19:19:44",
            "uuid": "b7a42080-5c77-11ea-8cee-562668d3ccea",
            "deleted": 0,
            "name": "test19",
            "desc": "资源池19",
            "default": 0
        }
    }
    ```

### 3、编辑资源池 ###

* URL

  `/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | name            | string | 资源池名字                     |
  | desc            | string | 资源池描述                     |

  - 示例：

    ```json
    {
        "name": "royin004 test",
        "desc": "royin004 test1222"
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

### 4、删除资源池 ###

* URL

  `/api/v1.0/resource_mgr/resource_pools`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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
    	"msg": "success"
    }
    ```


## 基础镜像 ##

### 1、基础镜像列表 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images?page=1&page_size=10`

* Method

	**GET** 请求，**body** 无 **json** 格式

* Parameters

  | Name |Type|Description|
  | :------- | :----| :-----|
  |page|int | 页面 |
  |page_size |str | 当前页条数|
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |count|int|数据总数|
  |result|object|结果数组|
  |uuid| str |基础镜像uuid|
  |name| str |基础镜像的名称|
  |path| str |基础镜像的路径|
  |os_type|str|系统类型|
  |os_type_simple|str|系统类型简写|
  |md5_sum|str|镜像的md5值|
  |size|float|镜像大小，单位为GB|
  |count|int|需要同传节点总数|
  |publish_count|int|同传完成数|
  |status|int|镜像状态，0- 正常，1-同传中，2-异常|
  |detail|dict|镜像同传的具体信息|
  |host_name|str|节点名|
  |ipaddr|str|节点IP|
  |host_uuid|str|节点的uuid|
  |progress|int|同传进度|
  |status|int|镜像在这个节点的同传状态，0- 正常，1-同传中，2-异常|
  
  
  - 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "8bb7f9f8-7257-11ea-b0e2-000c29e84b9c",
                    "name": "win7",
                    "os_type": "Windows 7 bit 64",
                    "os_type_simple": "win7",
                    "md5_sum": "c7be43f3af1f7c3539375e9638cf1826",
                    "path": "/opt/slow/instances/_base/8bb7f9f8-7257-11ea-b0e2-000c29e84b9c",
                    "size": "7.55",
                    "count": 2,
                    "publish_count": 1,
                    "status": 2,
                    "detail": [
                        {
                            "host_name": "controller",
                            "ipaddr": "172.16.1.14",
                            "host_uuid": "c7fa4d00-6fad-11ea-a3ed-000c29e84b9c",
                            "progress": 100,
                            "status": 0
                        },
                        {
                            "host_name": "compute1",
                            "ipaddr": "172.16.1.15",
                            "host_uuid": "9ebb8d9a-72f6-11ea-b93e-000c29e84b9c",
                            "progress": 100,
                            "status": 2
                        }
                    ]
                },
                {
                    "uuid": "a3ea0f3a-7283-11ea-86be-000c29e84b9c",
                    "name": "win7-1",
                    "os_type": "Windows 7 bit 64",
                    "os_type_simple": "win7",
                    "md5_sum": "c7be43f3af1f7c3539375e9638cf1826",
                    "path": "/opt/slow/instances/_base/a3ea0f3a-7283-11ea-86be-000c29e84b9c",
                    "size": "7.59",
                    "count": 2,
                    "publish_count": 2,
                    "status": 0,
                    "detail": [
                        {
                            "host_name": "controller",
                            "ipaddr": "172.16.1.14",
                            "host_uuid": "c7fa4d00-6fad-11ea-a3ed-000c29e84b9c",
                            "progress": 100,
                            "status": 0
                        },
                        {
                            "host_name": "compute1",
                            "ipaddr": "172.16.1.15",
                            "host_uuid": "9ebb8d9a-72f6-11ea-b93e-000c29e84b9c",
                            "progress": 100,
                            "status": 0
                        }
                    ]
                }
            ]
        }
    }
    ```

### 2、基础镜像上传 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式
	
	- 示例
	
	```
	    http://172.16.1.49:8000/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images?name=test&os_type=windows7
	    
	    {
	        file: File
	    }
	```
	
	

* Parameters    from-data

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | name(required)    | string  | 基础镜像名称       |
    | os_type(required) | string  | 基础镜像系统类型       |
    | file              |  File   | 基础镜像       |
    
    - 示例：
    
      ```from-data
      
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

### 3、基础镜像删除 ###

* URL

  `/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images`
  
* Method

  **DELETE** 请求，**body** 无 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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

### 4、基础镜像编辑 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images/<str:base_image_uuid>`

* Method

	**PUT** 请求，**body** 参数使用 **json** 格式
	
* Parameters    from-data

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | name(required)    | string  | 修改后基础镜像名称       |
    | os_type(required) | string  | 修改后基础镜像系统类型      |
    
    - 示例：
    
      ```JSON
      {
      		"name": "xxx",
      		"os_type": "xxxx"
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

### 5、基础镜像重传 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images/<str:base_image_uuid>/resync`

* Method

	**POST** 请求，**body** 参数使用 **json** 格式
	
* Parameters    from-data

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | node_uuid(required) | string  | 节点uuid      |
    
    - 示例：
    
      ```JSON
      {
      		"node_uuid": "xxxx"
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

### 6、基础镜像详细信息 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/base_images/<str:base_image_uuid>`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |uuid| str |基础镜像uuid|
  |name| str |基础镜像的名称|
  |path| str |基础镜像的路径|
  |os_type|str|系统类型|
  |os_type_simple|str|系统类型简写|
  |md5_sum|str|镜像的md5值|
  |size|float|镜像大小，单位为GB|
  |count|int|需要同传节点总数|
  |publish_count|int|同传完成数|
  |status|int|镜像状态，0- 正常，1-同传中，2-异常|
  |detail|dict|镜像同传的具体信息|
  |host_name|str|节点名|
  |ipaddr|str|节点IP|
  |host_uuid|str|节点的uuid|
  |progress|int|同传进度|
  |status|int|镜像在这个节点的同传状态，0- 正常，1-同传中，2-异常|
  
  
  - 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "uuid": "8bb7f9f8-7257-11ea-b0e2-000c29e84b9c",
            "name": "win7",
            "os_type": "Windows 7 bit 64",
            "os_type_simple": "win7",
            "md5_sum": "c7be43f3af1f7c3539375e9638cf1826",
            "path": "/opt/slow/instances/_base/8bb7f9f8-7257-11ea-b0e2-000c29e84b9c",
            "size": "7.55",
            "count": 2,
            "publish_count": 1,
            "status": 2,
            "detail": [
                {
                    "host_name": "controller",
                    "ipaddr": "172.16.1.14",
                    "host_uuid": "c7fa4d00-6fad-11ea-a3ed-000c29e84b9c",
                    "progress": 100,
                    "status": 0
                },
                {
                    "host_name": "compute1",
                    "ipaddr": "172.16.1.15",
                    "host_uuid": "9ebb8d9a-72f6-11ea-b93e-000c29e84b9c",
                    "progress": 100,
                    "status": 2
                }
            ]
        }
    }
    ```


## 计算节点 ##

### 1、计算节点基本信息列表 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/nodes`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |count|int|数据总数|
  |results|object|当前页的数据数组|
  |uuid| str| 节点uuid|
  |name| str| 节点名称|
  |hostname|str|节点hostname|
  |ip| str| 节点IP|
  |usage_sys|str|系统存储使用率|
  |usage_data|str|数据存储使用率|
  |total_sys|str|总系统存储|
  |used_sys|str|已使用系统存储|
  |server_version_info|str|服务器版本|
  |cpu_info|str|CPU信息|
  |mem_info|str|内存信息|
  |gpu_info|str|显卡信息|
  |total_vm|int|虚拟机总数量|
  |running_vm|int|虚拟机运行数量|
  |status|int|节点状态 0 - 正常， 1 - 异常警告，2 - 关机|
  |type|int| 节点类型：1-计算和主控一体, 2-计算和备控一体, 3-主控, 4-备控,5-计算|
  |total_vcpus| int| 虚拟cpu核数|
  |running_vcpus| int| 运行cpu核数|
  |usage_vcpus|str| cpu使用率|
  |total_mem| int| 总内存，单位：G|
  |running_mem|int| 运行内存，单位：G|
  |usage_mem|str| 内存使用率|
  |network_interfaces| object| 网卡信息|
  |storages| object| 存储设备信息|
  |deleted|int|是否删除 0 -否|
  |deleted_at|str|删除时间|
  |updated_at|str|更新时间|
  |created_at|str|创建时间|
  

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 2,
                    "name": "bcb15c5fcf.cloud.com",
                    "uuid": "96f8b109-7613-4aab-b455-26f69d299c01",
                    "hostname": "bcb15c5fcf.cloud.com",
                    "ip": "172.16.1.66",
                    "total_mem": 0,
                    "running_mem": 0,
                    "total_vcpus": 0,
                    "running_vcpus": 0,
                    "server_version_info": null,
                    "gpu_info": null,
                    "cpu_info": null,
                    "mem_info": null,
                    "status": "active",
                    "type": 5,
                    "created_at": "2020-04-13 09:52:29",
                    "updated_at": "2020-04-13 09:52:29",
                    "deleted_at": null,
                    "network_interfaces": [
                        {
                            "id": 4,
                            "uuid": "c941a7af-f9f1-48a8-984b-c360f5051d5d",
                            "nic": "eth0",
                            "mac": "00:0c:29:a2:95:8d",
                            "speed": 10000,
                            "status": 2,
                            "type": 0,
                            "deleted_at": null,
                            "updated_at": "2020-04-13 09:52:29",
                            "created_at": "2020-04-13 09:52:29",
                            "ip_info": [
                                {
                                    "uuid": "ca430ee3-b2c1-448f-8853-45f8ee360035",
                                    "ip": "172.16.1.66",
                                    "netmask": "255.255.255.0",
                                    "gateway": "172.16.1.254",
                                    "dns1": "114.114.114.114",
                                    "dns2": "8.8.8.8",
                                    "is_manage": 1,
                                    "is_image": 1
                                }
                            ]
                        }
                    ],
                    "storages": [
                        {
                            "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                            "path": "/opt/slow",
                            "used": 46161920,
                            "total": 27579797504,
                            "usage": "0.17",
                            "role": "1,2,3,4"
                        }
                    ],
                    "TEMPLATE_SYS": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "TEMPLATE_DATA": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "INSTANCE_SYS": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "INSTANCE_DATA": {
                        "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                        "path": "/opt/slow",
                        "used": 46161920,
                        "total": 27579797504,
                        "usage": "0.17",
                        "role": "1,2,3,4"
                    },
                    "usage_sys": "0.17",
                    "usage_data": "0.17",
                    "total_sys": 55159595008,
                    "used_sys": 92323840,
                    "usage_mem": 0,
                    "usage_vcpu": 0,
                    "total_vm": 0,
                    "running_vm": 0
                }
            ]
        }
    }
    ```

### 2、计算节点虚拟化检测并获取基础信息 ###

* URL

	`/api/v1.0/resource_mgr/check_node_virt`

* Method

	**POST** 请求，**body** 无 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | ip              | string| IP地址|
  | root_pwd | string | root密码 |
  
  - 示例
  
  ```json
     {
        "ip": "172.16.1.49",
        "root_pwd": "123456"
     } 
  ```
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |default_network_info| object|默认网络信息，包括network_info, virtual_switch|
  |network_info| object|默认数据网络|
  |virtual_switch| object|默认虚拟交换机|

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "interface_list": [
                {
                    "interface": "eth0",
                    "ip": "172.16.1.66",
                    "mac": "00:0c:29:a2:95:8d",
                    "mask": "255.255.255.0",
                    "speed": 10000,
                    "stat": 1
                }
            ],
            "storage_list": [
                {
                    "path": "/opt/slow",
                    "total": 27579797504,
                    "type": 1,
                    "used": 46161920,
                    "utilization": 0.2
                }
            ],
            "virtual_switch_list": {
                "desc": null,
                "name": "default",
                "type": "vlan",
                "uuid": "7b8a2b26-e413-443f-b361-48f4212e0813"
            }
        }
    }
    ```

### 2、计算节点新增 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/nodes`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                       | Type   | Description        |
  | -------------------------- | ------ | ------------------ |
  | password(required)         | string | 节点密码           |
  | ip(required)               | string | 节点IP             |
  | network(required)      | object |     |
  | switch_uuid(required)        | string | 分布式虚拟交换机uuid |
  | interface_uuid(required)        | string | 网卡uuid |
  | manage_interface_uuid(required) | string | 管理网络绑定的网卡uuid |
  | image_interface_uuid(required)  | string | 镜像网络网卡uuid      |
  
- 示例：
  
    ```json
    {
        "password": "123",
        "ip": "172.16.1.11",
        "network": [
            {
                "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                "interface": "eth0"
            },
            {
                "switch_uuid": "ec796fde-4885-11ea-8e15-000c295dd728",
                "interface": "eth0"
            }
        ],
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

### 3、计算节点修改名称 ###

* URL

	`/api/v1.0/resource_mgr/nodes/<str:node_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | name             |string| 新的显示名称|
  
  - 示例：

    ```json
    {
        "name": "xxx"
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

### 4、计算节点重启 ###

* URL

	`/api/v1.0/resource_mgr/nodes/<str:node_uuid>/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | nodes(required) | object  | 节点的数组       |
    | uuid | str |  节点uuid|
    | name | str | 节点名称 |
    
    - 示例
    
    ```json
        {
          "nodes" : [
          {
          	"uuid":"5ea1aef4-3c26-11ea-b688-000c295dd728",
          	"name":"node1"
          	},
          {
          	"uuid": "51a1aef4-3c26-11ea-b688-000c295dd728", 
          	"name":"node2"
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

### 5、计算节点关机###

* URL

	`/api/v1.0/resource_mgr/nodes/<str:node_uuid>/shutdown`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | nodes(required) | object  | 节点的数组       |
    | uuid | str |  节点uuid|
    | name | str | 节点名称 |
    
    - 示例
    
    ```json
        {
          "nodes" : [
          {
          	"uuid":"5ea1aef4-3c26-11ea-b688-000c295dd728",
          	"name":"node1"
          	},
          {
          	"uuid": "51a1aef4-3c26-11ea-b688-000c295dd728", 
          	"name":"node2"
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

### 6、计算节点删除 ###

* URL

	`/api/v1.0/resource_mgr/nodes`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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
    	"msg": "success"
    }
    ```

### 8、计算节点模版磁盘文件列表 ###

* URL

	`/api/v1.0/resource_mgr/nodes/<str:node_uuid>/template_images`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |results|object|当前页的数据数组|

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "name": "test",
                    "uuid": "dfc55ebe-5600-4a64-b3fe-18b0b8b2dfa5",
                    "storages": [
                        {
                            "role": 1,
                            "path": "/opt/fast",
                            "image_id": "deb2a29a-b0e5-4803-9791-6fdefc4800ec",
                            "version": 1,
                            "status": 0
                        },
                        {
                            "role": 2,
                            "path": "/opt/slow",
                            "image_id": "e62a026b-b89b-4aa6-9d27-74a6c653c422",
                            "version": 1,
                            "status": 0
                        }
                    ]
                }
            ]
        }
    }
    ```

### 9、计算节点模版磁盘文件重传 ###

* URL

	`/api/v1.0/resource_mgr/nodes/<str:node_uuid>/template_images/<str:template_image_uuid>/resync`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`resync`

  - param - 下载模板的参数

    | Name               | Type   | Description                                       |
    | ------------------ | ------ | ------------------------------------------------- |
    | role(required)     | string | 需要重传的模板镜像类型：1-系统盘镜像 2-数据盘镜像 |
    | image_id(required) | string | 镜像的uuid，对应模板的磁盘的uuid                  |
    | path(required)     | string | 镜像的存储位置，在初始化时配置的路径              |
    | version(required)  | int    | 模板的版本号                                      |

  - 示例

    ```json
    {
        "data": {
            "ipaddr": "172.16.1.15",
            "role": 2,
            "path": "/opt/slow",
            "image_id": "c2133168-7aca-11ea-994b-000c29e84b9c",
            "version": 2
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
    	"msg": "success"
    }
    ```

### 10、节点服务列表 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/services?page=1&page_size=10`

* Parameters

  | Name |Type|Description|
  | :------- | :----| :-----|
  |page |int | 页面 |
  |page_size |str | 当前页条数|

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

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
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "xxx",
                    "name": "mysql",
                    "status": 0
                },
                {
                    "uuid": "xxx",
                    "name": "redis",
                    "status": 0
                }
            ]
        }
    }
    ```

### 11、节点重启服务 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/services/<str:service_uuid>/reboot`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

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

### 12、节点网卡添加附属IP ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | ip_info             |object|               |
  
  - 示例：

    ```json
    {
        "ip": "192.168.1.49",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.245",
        "dns1": "114.114.114.114",
        "dns2": "8.8.8.8"
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

### 13、节点网卡修改附属IP ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics/<str:nic_uuid>/ip_infos/<str:ip_info_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | ip             |object|               |
  
  - 示例：

    ```json
    {
        "ip": "192.168.1.49",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.245",
        "dns1": "114.114.114.114",
        "dns2": "8.8.8.8"
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

### 14、节点网络信息 ###

* URL

  `/api/v1.0/resource_mgr/nodes/<str:node_uuid>/nics`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

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
        "data": [
            {
                "id": 1,
                "uuid": "3db171a7-1650-4921-a825-99ee4ff4e655",
                "nic": "eth0",
                "mac": "52:54:00:a7:a6:49",
                "speed": 0,
                "ip": "172.16.1.58",
                "netmask": "255.255.255.0",
                "gateway": "172.16.1.254",
                "dns1": "114.114.114.114",
                "dns2": "",
                "status": 2,
                "type": 0,
                "is_manage": 1,
                "is_image": 1,
                "deleted_at": null,
                "updated_at": "2020-04-10 15:23:24",
                "created_at": "2020-04-10 15:23:24",
                "ip_info": [
                    {
                        "uuid": "8a71b5ba-73de-11ea-87ba-000c29893b03",
                        "ip": "172.16.1.32",
                        "netmask": "255.255.255.0",
                        "gateway": "172.16.1.254",
                        "dns1": "8.8.8.8",
                        "dns2": "114.114.114.114"
                    }
                ]
            }
        ]
    }
    ```

### 15、计算节点详细信息 ###

* URL

	`/api/v1.0/resource_mgr/resource_pools/<str:resource_pool_uuid>/nodes`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |count|int|数据总数|
  |results|object|当前页的数据数组|
  |uuid| str| 节点uuid|
  |name| str| 节点名称|
  |hostname|str|节点hostname|
  |ip| str| 节点IP|
  |usage_sys|str|系统存储使用率|
  |usage_data|str|数据存储使用率|
  |total_sys|str|总系统存储|
  |used_sys|str|已使用系统存储|
  |server_version_info|str|服务器版本|
  |cpu_info|str|CPU信息|
  |mem_info|str|内存信息|
  |gpu_info|str|显卡信息|
  |total_vm|int|虚拟机总数量|
  |running_vm|int|虚拟机运行数量|
  |status|int|节点状态 0 - 正常， 1 - 异常警告，2 - 关机|
  |type|int| 节点类型：1-计算和主控一体, 2-计算和备控一体, 3-主控, 4-备控,5-计算|
  |total_vcpus| int| 虚拟cpu核数|
  |running_vcpus| int| 运行cpu核数|
  |usage_vcpus|str| cpu使用率|
  |total_mem| int| 总内存，单位：G|
  |running_mem|int| 运行内存，单位：G|
  |usage_mem|str| 内存使用率|
  |network_interfaces| object| 网卡信息|
  |storages| object| 存储设备信息|
  |deleted|int|是否删除 0 -否|
  |deleted_at|str|删除时间|
  |updated_at|str|更新时间|
  |created_at|str|创建时间|
  

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "id": 2,
            "name": "bcb15c5fcf.cloud.com",
            "uuid": "96f8b109-7613-4aab-b455-26f69d299c01",
            "hostname": "bcb15c5fcf.cloud.com",
            "ip": "172.16.1.66",
            "total_mem": 0,
            "running_mem": 0,
            "total_vcpus": 0,
            "running_vcpus": 0,
            "server_version_info": null,
            "gpu_info": null,
            "cpu_info": null,
            "mem_info": null,
            "status": "active",
            "type": 5,
            "created_at": "2020-04-13 09:52:29",
            "updated_at": "2020-04-13 09:52:29",
            "deleted_at": null,
            "network_interfaces": [
                {
                    "id": 4,
                    "uuid": "c941a7af-f9f1-48a8-984b-c360f5051d5d",
                    "nic": "eth0",
                    "mac": "00:0c:29:a2:95:8d",
                    "speed": 10000,
                    "status": 2,
                    "type": 0,
                    "deleted_at": null,
                    "updated_at": "2020-04-13 09:52:29",
                    "created_at": "2020-04-13 09:52:29",
                    "ip_info": [
                        {
                            "uuid": "ca430ee3-b2c1-448f-8853-45f8ee360035",
                            "ip": "172.16.1.66",
                            "netmask": "255.255.255.0",
                            "gateway": "172.16.1.254",
                            "dns1": "114.114.114.114",
                            "dns2": "8.8.8.8",
                            "is_manage": 1,
                            "is_image": 1
                        }
                    ]
                }
            ],
            "storages": [
                {
                    "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                    "path": "/opt/slow",
                    "used": 46161920,
                    "total": 27579797504,
                    "usage": "0.17",
                    "role": "1,2,3,4"
                }
            ],
            "TEMPLATE_SYS": {
                "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                "path": "/opt/slow",
                "used": 46161920,
                "total": 27579797504,
                "usage": "0.17",
                "role": "1,2,3,4"
            },
            "TEMPLATE_DATA": {
                "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                "path": "/opt/slow",
                "used": 46161920,
                "total": 27579797504,
                "usage": "0.17",
                "role": "1,2,3,4"
            },
            "INSTANCE_SYS": {
                "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                "path": "/opt/slow",
                "used": 46161920,
                "total": 27579797504,
                "usage": "0.17",
                "role": "1,2,3,4"
            },
            "INSTANCE_DATA": {
                "uuid": "e8b6c400-492d-4aec-86b8-e8a3e1e5a30c",
                "path": "/opt/slow",
                "used": 46161920,
                "total": 27579797504,
                "usage": "0.17",
                "role": "1,2,3,4"
            },
            "usage_sys": "0.17",
            "usage_data": "0.17",
            "total_sys": 55159595008,
            "used_sys": 92323840,
            "usage_mem": 0,
            "usage_vcpu": 0,
            "total_vm": 0,
            "running_vm": 0
        }
    }
    ```



## 数据网络 ##

### 1、数据网络基本信息列表 ###

* URL

  `/api/v1.0/resource_mgr/data_networks`

* Method

  **GET** 请求
  
* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | page_size | int |每页条数|
  | page| int| 页码|


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |count| int| 数据总条数|
  |results| object| 数据结果数组|
  |name| str| 数据网络名称 |
  |desc| str| 描述 |
  |uuid| str| 数据网络uuid|
  |subnet_count| int| 子网个数 |
  |switch_name|str|关联虚拟机名称|
  |switch_type| str|类型|
  |vlan_id| int|vlan id|
  |default|int|是否为默认网络 0-否，1-是|
  
  
  - 示例：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "subnet_count": 2,
                    "deleted_at": null,
                    "updated_at": null,
                    "created_at": "2020-02-26 03:04:53",
                    "deleted": 0,
                    "uuid": "834c7426-57be-11ea-85d5-562668d3ccea",
                    "name": "default1",
                    "switch_name": "default",
                    "vlan_id": null,
                    "switch_type": "flat",
                    "default": 1,
                    "switch": "ecbe2a6e-57bd-11ea-862d-562668d3ccea"
                }
            ]
        }
    }
    ```

### 2、数据网络新增 ###

* URL

  `/api/v1.0/resource_mgr/data_networks`
  
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
  | name(required)        | string | 子网名称                                         |
  | start_ip(required)    | string | 子网的开始IP                                     |
  | end_ip(required)      | string | 子网的结束IP                                     |
  | netmask(required)     | string | 子网掩码                                         |
  | gateway(required)     | string | 网关                                             |
  | dns1(required)        | string | 首选DNS                                          |
  | dns2                  | string | 备用DNS                                          |

  - 示例：

    ```json
    {
        "name": "test_network2",
        "switch_uuid" : "9c7050ba-5213-11ea-9d93-000c295dd728",
        "vlan_id" : 12,
        "subnet_info": {
                "name": "subnet1",
                "start_ip": "192.168.1.10",
                "end_ip": "192.168.1.20",
                "netmask": "255.255.255.0",
                "gateway": "192.168.1.0",
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

### 3、数据网络删除 ###

* URL

  `/api/v1.0/resource_mgr/data_networks`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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

### 4、数据网络修改 ###

* URL

  `/api/v1.0/resource_mgr/data_networks/<str:data_network_uuid>`

* Method

  **PUT** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | name | str |名称|
    | vlan_id| str| vlan ID|
    
    - 示例
    
    ```json
    {
        "vlan_id": 1,
        "name": "tt"
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

### 5、数据网络子网基本信息列表 ###

* URL

  `/api/v1.0/resource_mgr/data_networks/<str:data_network_uuid>/sub_networks`
  
* Method

  **GET** 请求

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | page_size | int |每页条数|
  | page| int| 页码|


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | count| int| 数据总条数|
  | results| object| 数据结果数组|
  | name| str| 数据网络名称 |
  | desc| str| 描述 |
  | uuid| str| 数据网络uuid|
  | subnet_count| int| 子网个数 |
  | switch_name|str|关联虚拟机名称|
  | switch_type| str|类型|
  | vlan_id| int|vlan id|
  | default|int|是否为默认网络 0-否，1-是|
  
  
  - 示例：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "deleted_at": null,
                    "updated_at": null,
                    "created_at": "2020-02-26 18:58:22",
                    "uuid": "b68f1e3a-5843-11ea-ad06-562668d3ccea",
                    "name": "子网1",
                    "netmask": "255.255.255.0",
                    "gateway": "172.16.1.0",
                    "cidr": "172.16.1.0/24",
                    "start_ip": "172.16.1.10",
                    "end_ip": "172.16.1.50",
                    "dns1": "8.8.8.8",
                    "dns2": "114.114.114.114",
                    "deleted": 0,
                    "network": "834c7426-57be-11ea-85d5-562668d3ccea"
                },
                {
                    "id": 2,
                    "deleted_at": null,
                    "updated_at": null,
                    "created_at": "2020-02-26 18:59:43",
                    "uuid": "e49b7d6c-5843-11ea-8bd1-562668d3ccea",
                    "name": "子网2",
                    "netmask": "255.255.255.0",
                    "gateway": "172.16.1.0",
                    "cidr": "172.16.1.0/24",
                    "start_ip": "172.16.1.51",
                    "end_ip": "172.16.1.100",
                    "dns1": "8.8.8.8",
                    "dns2": "114.114.114.114",
                    "deleted": 0,
                    "network": "834c7426-57be-11ea-85d5-562668d3ccea"
                }
            ]
        }
    }
    ```

### 6、数据网络子网修改 ###

* URL

  `/api/v1.0/resource_mgr/data_networks/<str:data_network_uuid>/sub_networks/<str:sub_network_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | name | str |子网名称|
  | start_ip| str| 起始IP|
  | end_ip| str| 结束IP|
  | netmask | str| 子网掩码 |
  | gateway | str| 网关|
  | dns1 | str| dns1|
  | dns2 | str| dns2|
  
- 示例：
  
    ```json
    {
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
        "msg": "success",
        "data": {
        }
    }
    ```

### 7、数据网络子网删除 ###

* URL

  `/api/v1.0/resource_mgr/data_networks/<str:data_network_uuid>/sub_networks`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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
        "msg": "success",
        "data": {
        }
    }
    ```

### 8、数据网络子网新增 ###

* URL

  `/api/v1.0/resource_mgr/data_networks/<str:data_network_uuid>/sub_networks`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description  |
  | ---------------------- | ------ | ------------ |
  | name(required)         | string | 子网名称     |
  | start_ip(required)     | string | 子网的开始IP |
  | end_ip(required)       | string | 子网的结束IP |
  | netmask(required)      | string | 子网掩码     |
  | gateway(required)      | string | 网关         |
  | dns1(required)         | string | 首选DNS      |
  | dns2                   | string | 备用DNS      |
  
- 示例：
  
    ```json
    {
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


## 分布式虚拟交换机 ##

### 1、分布式虚拟交换机基本信息列表 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Parameters  
  
  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  |page|int | 页面 |
  |page_size |str | 当前页条数|
  
* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | count | int | 数据总数 |
  | results | object | 结果数组 |
  | uuid | str | 虚拟交换机uuid |
  | name | str | 虚拟交换机名称 |
  | type | str | 类型， vlan/flat|
  | desc | str | 描述 |

  
  - 示例：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "uuid": "ecbe2a6e-57bd-11ea-862d-562668d3ccea",
                    "name": "default",
                    "type": "flat",
                    "desc": "默认分布式虚拟交换机",
                    "deleted_at": null,
                    "created_at": "2020-02-26 03:00:15",
                    "updated_at": null
                }
            ]
        }
    }
    ```

### 2、分布式虚拟交换机新增 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs`

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

### 3、分布式虚拟交换机删除 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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

### 4、分布式虚拟交换机修改 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs/<str:vswitch_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                                    |
  | ------------------- | ------ | ---------------------------------------------- |
  | name(required)      | string | 虚拟交换机名称                                 |
  | type(required)      | string | 虚拟交换机类型                                 |
  | desc                | string | 描述信息                                       |
  | uplinks(required)   | list   | 列表，绑定的网卡信息，每个包括如下字段         |
  | node_uuid(required) | string | 节点uuid                                       |
  | nic_uuid(required)  | string | 网卡uuid                                       |

  - 示例：

    ```json
    {
        "name": "test",
        "desc": "test",
        "type": "VLAN",
        "uplinks": [
            {
                "nic_name": "eth1",
                "node_name": "3c65082572.cloud.com",
                "nic_uuid": "6fac464c-2d8d-4d84-b58f-ea8d89d9862f",
                "node_uuid": "89362457-fdf5-464f-8e44-98e04fdb2052"
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

### 5、分布式虚拟交换机关联主机信息 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs/<str:vswitch_uuid>/node_map`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据数组 |
  |resource_pool_name| str| 资源池名称|
  | uuid | str | 链接uuid |
  | node_name | str|关联主机名称|
  | nic | str | 网卡名称 |
  | type | str | 类型， vlan/flat|
  | desc | str | 描述 |

  
  - 示例：

    ````json
    {
        "code": 0,
        "msg": "success",
        "name": "switch1",
        "type": "VLAN",
        "uplinks": [
            {
                "node_name": "xxxx",
                "node_uuid": "9c682016-5213-11ea-9d93-000c295dd728",
                "nic_name": "xxxx",
                "nic_uuid": "9c703c24-5213-11ea-9d93-000c295dd728"
            },
            {
                "node_name": "xxxx",
                "node_uuid": "9c682016-5213-11ea-9d93-000c295dd728",
                "nic_name": "xxxx",
                "nic_uuid": "9c703c24-5213-11ea-9d93-000c295dd728"
            }
        ]
    }
    ````

### 6、修改分布式虚拟交换机关联主机信息 ###

* URL

  `/api/v1.0/resource_mgr/vswitchs/<str:vswitch_uuid>/node_map`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                                    |
  | ------------------- | ------ | ---------------------------------------------- |
  | node_uuid(required) | string | 节点uuid                                       |
  | nic_uuid(required)  | string | 网卡uuid                                       |

  - 示例：

    ```json
    {
        "nic_name": "eth0",
        "node_name": "3c65082572.cloud.com",
        "nic_uuid": "95e61a91-18a7-4134-a957-ceda7b37b330",
        "node_uuid": "89362457-fdf5-464f-8e44-98e04fdb2052"
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


## 管理网络 ##

### 1、管理网络基本信息列表 ###

* URL

  `/api/v1.0/resource_mgr/manage_networks`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Parameters  
  
  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  |page|int | 页面 |
  |page_size |str | 当前页条数|

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据数组 |
  |count| int| 数据总数 |
  |hostname| str| 关联主机名 |
  | type | str | 类型，(1, '计算和主控一体'), (2, '计算和备控一体'), (3, '主控'), (4, '备控') , (5, '计算')|
  | manage_network | str | 管理网络 |
  | image_network | str | 管理网络|
  

  - 示例：

    ````json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "hostname": "3c65082572.cloud.com",
                    "type": 3,
                    "node_uuid": "89362457-fdf5-464f-8e44-98e04fdb2052",
                    "manage": {
                        "manage_network": "eth2/192.168.122.217",
                        "manage_network_uuid": "2297f53e-5586-422f-9d07-31cb3b8af369",
                        "manage_network_interface_uuid": "e58646a1-c758-4f82-834c-2bc82818a37a"
                    },
                    "image": {
                        "image_network": "eth0/172.16.1.59",
                        "image_network_uuid": "95e61a91-18a7-4134-a957-ceda7b37b330",
                        "image_network_interface_uuid": "1e529fc9-713c-40ac-9fb1-ea158407987b"
                    }
                }
            ]
        }
    }
    ````

### 2、修改管理网络关联主机信息 ###

* URL

  `/api/v1.0/resource_mgr/manage_networks/mn_node_map`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                                    |
  | ------------------- | ------ | ---------------------------------------------- |
  | node_uuid(required) | string | 节点uuid                                       |
  | nic_uuid(required)  | string | 网卡uuid                                       |
  | old_ip_uuid(required)  | string | 网卡附属ip uuid                                  |
  | new_ip_uuid(required)  | string | 网卡附属ip uuid                                  |

  - 示例：

    ```json
    {
        "uplinks": [
            {
                "old_ip_uuid": "1e529fc9-713c-40ac-9fb1-ea158407987b",
                "new_ip_uuid": "e58646a1-c758-4f82-834c-2bc82818a37a"
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

### 3、修改镜像网络关联主机信息 ###

* URL

  `/api/v1.0/resource_mgr/manage_networks/in_node_map`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                                    |
  | ------------------- | ------ | ---------------------------------------------- |
  | node_uuid(required) | string | 节点uuid                                       |
  | nic_uuid(required)  | string | 网卡uuid                                       |
  | ip_uuid(required)  | string | 网卡附属ip uuid                                       |

  - 示例：

    ````json
    {
        "uplinks": [
            {
                "old_ip_uuid": "1e529fc9-713c-40ac-9fb1-ea158407987b",
                "new_ip_uuid": "e58646a1-c758-4f82-834c-2bc82818a37a"
            }
        ]
    }
    ````
  
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


## ISO库 ##

### 1、ISO库基本信息列表 ###

* URL

  `/api/v1.0/resource_mgr/isos`

* Method

  **GET** 请求

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | name            | string | ISO文件名字模糊查询                     |
  | type            | string | ISO文件类型 1-软件包，2-工具包，3-系统包|
  | page_size | int |每页条数|
  | page| int| 页码|


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |count| int| 数据总条数|
  |results| object| 数据结果数组|
  |name| str| ISO文件名称|
  |desc| str|描述|
  |uuid| str||
  |path| str|ISO文件存储路径|
  |os_type|str|系统类型|
  |size| str|文件大小 单位：G|
  |status| int|状态|
  |type|int|ISO文件类型 1-软件包，2-工具包，3-系统包|
  
  
  - 示例：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 3,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "name": "win7",
                    "type": 1,
                    "uuid": "9b54b9b4-5847-11ea-8686-562668d3ccea",
                    "desc": "12",
                    "path": "/home/iso/cn_windows_7_professional_with_sp1_x64_dvd_u_677031.iso",
                    "os_type": "Windows7(64bit)",
                    "size": 3.0,
                    "status": 0,
                    "deleted": 0,
                    "deleted_at": null,
                    "created_at": "2020-01-20 03:23:26",
                    "updated_at": null
                }]
        }
    }
    ```

### 2、ISO库编辑 ###

* URL

  `/api/v1.0/resource_mgr/isos/<str:iso_uuid>`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | name | string | ISO文件类型 1-软件包，2-工具包，3-系统包 |
    | os_type | string  | 系统类型       |
    
  - 示例：

    ````json
    {
        "name": "test",
        "os_type": "xxx"
    }
    ````
  
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
        "msg": "success",
        "data": {
           }
    }
    ```

### 3、ISO库下载 ###

* URL

  `/api/v1.0/resource_mgr/isos/<str:iso_uuid>`

* Method

  **GET** 请求

### 4、ISO库删除 ###

* URL

  `/api/v1.0/resource_mgr/isos`

* Method

  **DELETE** 请求，**body** 无 **json** 格式
  
* Parameters

    | Name           | Type    | Description      |
    | -------------- | ------- | ---------------- |
    | uuids(required) | object  | uuid的数组       |
    
    - 示例
    
    ```json
        {
          "uuids" : ["5ea1aef4-3c26-11ea-b688-000c295dd728", "51a1aef4-3c26-11ea-b688-000c295dd728"]
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
        "msg": "success",
        "data": {
           }
    }
    ```

### 5、ISO库上传 ###

* URL

  `/api/v1.0/resource_mgr/isos`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters    
  
    from-data
    
    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | file              |  File   | ISO文件       |
    | iso_type | string | ISO文件类型 1-软件包，2-工具包，3-系统包 |
    | os_type | string  | 系统类型       |


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
        "msg": "success",
        "data": {
           }
    }
    ```


## 模板接口

教学模板和个人模板是一样的，都使用以下API

### 1、添加模板


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`create`
  - param - 创建模板的参数

  | Name                   | Type   | Description                          |
  | ---------------------- | ------ | ------------------------------------ |
  | name(required)         | string | 模板名称                             |
  | desc                   | string | 模板描述                             |
  | os_type(required)      | string | 模板的系统类型                       |
  | classify(required)     | int    | 模板分类：1、教学模板 2、个人模板    |
  | pool_uuid(required)    | string | 资源池uuid                           |
  | network_uuid(required) | string | 数据网络uuid                         |
  | subnet_uuid(required)  | string | 子网uuid                             |
  | bind_ip                | string | 模板分配的IP，如果没有则代表系统分配 |
  | vcpu(required)         | int    | 虚拟CPU数目                          |
  | ram(required)          | float  | 虚拟内存，单位为G                    |
  |                        |        |                                      |
  | system_disk            | dict   | 系统盘信息，具体如下：               |
  | image_id(required)     | string | 基础镜像uuid                         |
  | size(required)         | int    | 系统盘大小，单位为GB                 |
  |                        |        |                                      |
  | data_disks(required)   | list   | 数据盘信息，单个信息如下：           |
  | inx(required)          | int    | 启动顺序                             |
  | size(required)         | int    | 数据盘大小，单位为GB                 |
  
- 示例：
  
  ```json
    {
    	"action": "create",
    	"param": {
    		"name": "template1",
    	    "desc": "this is template1",
    	    "os_type": "win7",
    	    "classify": 1,
    	    "pool_uuid": "9c888a04-5213-11ea-9d93-000c295dd728",
    	    "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
    	    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
    	    "bind_ip": "172.16.11.21",
    		"vcpu": 2,
    		"ram": 2,
    		"system_disk": {
    			 "image_id": "4315aa82-3b76-11ea-930d-000c295dd728",
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

### 2、模板开机

开机需要支持批量操作


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`start`

  - param - 模板的相关信息

    | Name           | Type   | Description                                |
    | :------------- | :----- | :----------------------------------------- |
    | templates      | list   | 需要开机的模板列表，每条记录包含字段如下： |
  | name(required) | string | 模板名称                                   |
    | uuid(required) | string | 模板uuid                                   |

  - 示例：
  
    ```json
    {
    	"action": "start",
    	"param": {
    		"templates": [
    				{
    					"name": "template2",
    					"uuid": "f309f8a2-5c51-11ea-9b12-000c295dd728"
    				},
    				{
    					"name": "template1",
    					"uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
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

### 3、模板关机

关机需要支持批量操作


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`stop`

  - param - 模板信息

    | Name           | Type   | Description                                |
    | :------------- | :----- | :----------------------------------------- |
    | templates      | list   | 需要关机的模板列表，每条记录包含字段如下： |
  | name(required) | string | 模板名称                                   |
    | uuid(required) | string | 模板uuid                                   |

  - 示例：
  
    ```json
    {
    	"action": "stop",
    	"param": {
    		"templates": [
    				{
    					"name": "template2",
    					"uuid": "f309f8a2-5c51-11ea-9b12-000c295dd728"
    				},
    				{
    					"name": "template1",
    					"uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
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

### 4、模板强制关机、重启、强制重启和重置

同开关机的操作，只是`action`不同，分别是`hard_stop、reboot、hard_reboot和reset`。都支持批量操作，当个数大于1时，会返回成功和失败个数。而当个数为1时，成功会返回成功失败个数（成功1个，失败0个），否则会返回失败原因。

### 5、删除模板

删除模板，需要支持批量操作


* URL

  `/education/template/`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name           | Type   | Description                                |
  | -------------- | ------ | ------------------------------------------ |
  | templates      | list   | 需要删除的模板列表，每条记录包含字段如下： |
  | name(required) | string | 模板名称                                   |
| uuid(required) | string | 模板uuid                                   |
  
- 示例：
  
    ```json
    {
    	"templates": [
    			{
    				"name": "template2",
    				"uuid": "f309f8a2-5c51-11ea-9b12-000c295dd728"
    			},
    			{
    				"name": "template1",
    				"uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
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

### 6、编辑模板

在线编辑模板操作


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`edit`

  - param - 编辑模板的参数

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 模板名称    |
    | uuid(required) | string | 模板uuid    |

- 示例：

  ```json
  {
  	"action": "edit",
  	"param": {
          "name": "template1",
  		"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
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

### 7、更新模板

保存模板，即是更新模板操作


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`save`

  - param - 保存模板的参数

    | Name           | Type   | Description                                                  |
    | :------------- | :----- | :----------------------------------------------------------- |
    | name(required) | string | 模板名称                                                     |
    | uuid(required) | string | 模板uuid                                                     |
    | run_date       | string | 模板的定时更新时间，格式类似于`2020-4-19 15:48:15`。如果此参数不为空，则会定时更新模板，替换上一次未执行的任务 |
  
- 示例：
  
    ```json
    {
    	"action": "save",
    	"param": {
            "name": "template1",
    		"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
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

### 8、复制模板


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`copy`

  - param - 复制模板的参数

    | Name                    | Type   | Description                          |
    | ----------------------- | ------ | ------------------------------------ |
    | template_uuid(required) | string | 待复制的模板uuid                     |
    | name(required)          | string | 新模板的名字                         |
    | desc                    | string | 新模板描述                           |
    | pool_uuid(required)     | string | 新模板所属资源池uuid                 |
    | network_uuid(required)  | string | 数据网络uuid                         |
    | subnet_uuid(required)   | string | 子网uuid                             |
    | bind_ip                 | string | 新模板分配的IP，如果没有则是系统分配 |
  
- 示例：
  
    ```json
    {
        "action": "copy",
        "param": {
            "template_uuid": "9a327142-3b21-11ea-8339-000c295dd728",
            "name": "win7_template_copy",
            "desc": "this is win7 template copy",
            "pool_uuid": "e4a53850-26e9-11ea-a72d-562668d3ccea",
            "network_uuid": "1a870202-3732-11ea-8a2d-000c295dd728",
            "subnet_uuid": "b68bcc96-3732-11ea-b34d-000c295dd728",
            "bind_ip": "172.16.1.28"
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

### 9、下载模板


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`download`

  - param - 下载模板的参数

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 模板名称    |
  | uuid(required) | string | 模板uuid    |
  
- 示例：
  
    ```json
    {
    	"action": "download",
    	"param": {
            "name": "template1",
    		"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728"
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

### 10、加载资源和弹出资源


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`attach_source`和`detach_source`

  - param - 下载模板的参数

    | Name               | Type   | Description |
    | :----------------- | :----- | :---------- |
    | uuid(required)     | string | 模板uuid    |
    | name(required)     | string | 模板名称    |
    | iso_uuid(required) | string | ISO的uuid   |

  - 示例：

    ```json
    # 加载资源
    {
    	"action": "attach_source",
    	"param": {
    		"uuid": "92ff80a4-3c2a-11ea-87d5-000c295dd728",
            "name": "template1",
            "iso_uuid": "eee7d30b-940e-47b9-9531-95b0752687e1"
    	}
    }
    # 弹出加载的资源
    {
    	"action": "detach_source",
    	"param": {
    		"uuid": "6314500d-4ccf-4f50-b533-2541058718cf",
            "name": "template1"
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

### 11、发送ctrl+alt+del


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`send_key`

  - param - 下载模板的参数

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | uuid(required) | string | 模板uuid    |
    | name(required) | string | 模板名称    |

  - 示例：

    ```json
    {
    	"action": "send_key",
    	"param": {
    		"uuid": "6314500d-4ccf-4f50-b533-2541058718cf",
            "name": "template1"
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

### 12、模板属性修改 ###


* URL

  `/education/template`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                                                  |
  | --------------- | ------ | ------------------------------------------------------------ |
  | uuid(required)  | string | 模板uuid                                                     |
  | name(required)  | string | 模板名称                                                     |
  | value(required) | dict   | 更新的模板的属性，包含如下：                                 |
  | name            | string | 修改后的模板名称                                             |
  | desc            | string | 模板描述                                                     |
  | network_uuid    | string | 修改后的网络uuid                                             |
  | subnet_uuid     | string | 修改后的子网uuid                                             |
  | bind_ip         | string | 不管是系统分配还是固定IP，页面都可以填入IP作为模板的IP，如果选择系统分配，并且删除了原有IP，则bind_ip为空，server会自动分配 |
  | vcpu            | int    | 虚拟cpu个数                                                  |
  | ram             | float  | 虚拟内存，单位为G                                            |
  | devices         | list   | 模板最新的磁盘信息。如果磁盘只是修改了大小，则只修改查询出来的磁盘信息的`size`，只能扩容。如果添加了数据盘，则添加的格式为`{"inx": 0, "size": 50}` |

- 示例：

  ```json
  {
      "uuid": "27aef634-6daa-11ea-81c5-000c29e84b9c",
      "name": "win7模板",
      "value": {
          "name": "template",
          "desc": "",
          "network_uuid": "f5b30bce-6d9b-11ea-9565-000c29e84b9c",
          "subnet_uuid": "e1056f24-6da4-11ea-9565-000c29e84b9c",
          "bind_ip": "192.16.1.15",
          "ram": 2,
          "vcpu": 2,
          "devices": [
              {
                  "uuid": "27aef7ce-6daa-11ea-81c5-000c29e84b9c",
                  "type": "system",
                  "device_name": "vda",
                  "boot_index": 0,
                  "size": 150
              },
              # 下面是新增的盘
              {
                  "inx": 0,
                  "size": 50
              }
      ]
      }
  }
  ```


* aReturns

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

### 13、重传模板镜像 ###


* URL

  `/education/template`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`resync`

  - param - 下载模板的参数

    | Name               | Type   | Description                                       |
    | ------------------ | ------ | ------------------------------------------------- |
    | ipaddr(required)   | string | 需要重传的节点IP                                  |
    | role(required)     | string | 需要重传的模板镜像类型：1-系统盘镜像 2-数据盘镜像 |
    | image_id(required) | string | 镜像的uuid，对应模板的磁盘的uuid                  |
    | path(required)     | string | 镜像的存储位置，在初始化时配置的路径              |
    | version(required)  | int    | 模板的版本号                                      |

  - 示例

    ```json
    {
    	"action": "resync",
    	"param": {
    		"ipaddr": "172.16.1.15",
    		"role": 2,
    	    "path": "/opt/slow",
    	    "image_id": "c2133168-7aca-11ea-994b-000c29e84b9c",
    	    "version": 2
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

### 14、模板镜像管理查询 ###


* URL

  ` /education/template/image/?pool_uuid=7dcb05de-73f5-11ea-9ace-000c29e84b9c&template_uuid=b2fa70ae-741e-11ea-9791-000c29e84b9c `

* Method

  **GET** 请求

* Parameters

  | Name                    | Type   | Description                                  |
  | ----------------------- | ------ | -------------------------------------------- |
  | pool_uuid(required)     | string | 资源池uuid，用来找出所有在这个资源池下的节点 |
  | template_uuid(required) | string | 模板uuid，用来确定模板在每个节点下的镜像状态 |


* Returns

  | Name         | Type   | Description                          |
  | :----------- | :----- | :----------------------------------- |
  | name         | string | 节点名称                             |
  | uuid         | string | 节点uuid                             |
  | ip           | string | 节点IP                               |
  | storages     | list   | 镜像的状态信息，每一项字段信息如下： |
  | role         | int    | 镜像类型，1-系统盘镜像，2-数据盘镜像 |
  | path         | string | 镜像的存储位置                       |
  | bind_desktop | string | 是否有绑定桌面                       |
  | status       | int    | 0-正常 1-同传中 2-异常               |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "name": "controller",
                    "uuid": "7d99152e-73f5-11ea-9ace-000c29e84b9c",
                    "ip": "172.16.1.14",
                    "storages": [
                        {
                            "role": 1,
                            "path": "/opt/slow",
                            "image_id": "b2fa72de-741e-11ea-9791-000c29e84b9c",
                            "bind_desktop": false,
                            "status": 0
                        },
                        {
                            "role": 2,
                            "path": "/opt/slow",
                            "image_id": "b2fb1946-741e-11ea-9791-000c29e84b9c",
                            "bind_desktop": false,
                            "status": 0
                        }
                    ]
                },
                {
                    "name": "compute1",
                    "uuid": "bd94149c-7415-11ea-8c73-000c29e84b9c",
                    "ip": "172.16.1.15",
                    "storages": [
                        {
                            "role": 1,
                            "path": "/opt/slow",
                            "image_id": "b2fa72de-741e-11ea-9791-000c29e84b9c",
                            "bind_desktop": false,
                            "status": 0
                        },
                        {
                            "role": 2,
                            "path": "/opt/slow",
                            "image_id": "b2fb1946-741e-11ea-9791-000c29e84b9c",
                            "bind_desktop": false,
                            "status": 0
                        }
                    ]
                }
            ]
        }
    }
    ```

### 15、模板分页查询 ###


* URL

  ` /education/template/?searchtype=all&classify=1&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name       | Type   | Description                                |
  | ---------- | ------ | ------------------------------------------ |
  | searchtype | string | 查询类型，`all/contain/single`             |
  | classify   | int    | 1-教学模板 2-个人模板                      |
  | pool_uuid  | string | 当要查询属于某个资源池的模板时，加上此参数 |
  | page       | int    | 页数                                       |
  | page_size  | int    | 分页大小                                   |
  
  - 示例
  
    ```
    # 查询所有教学模板并分页
    /education/template/?searchtype=all&classify=1&page=1&page_size=10
    # 查询所有属于某个资源池的教学模板并分页
    /education/template/?searchtype=all&pool_uuid=6fd8bb14-6d70-11ea-9a33-0cc47a462da8&classify=1&page=1&page_size=10
    # 模糊匹配查询，根据教学模板名字匹配，同时支持分页
    /education/template/?searchtype=contain&classify=1&name=te&page=1&page_size=10
    ```
  
    
  
* Returns

  | Name            | Type   | Description                                                  |
  | :-------------- | :----- | :----------------------------------------------------------- |
  | name            | string | 模板名称                                                     |
  | uuid            | string | 模板uuid                                                     |
  | desc            | string | 模板的描述                                                   |
  | host_ip         | string | 模板所在节点的IP                                             |
  | host_name       | string | 模板所在节点的节点名                                         |
  | pool_name       | string | 资源池名称                                                   |
  | pool_uuid       | string | 资源池uuid                                                   |
  | network_name    | string | 数据网络名称                                                 |
  | network_uuid    | string | 数据网络uuid                                                 |
  | subnet_name     | string | 子网名称                                                     |
  | subnet_uuid     | string | 子网uuid                                                     |
  | subnet_start_ip | string | 子网开始IP                                                   |
  | subnet_end_ip   | string | 子网结束IP                                                   |
  | bind_ip         | string | 模板的IP                                                     |
  | vcpu            | int    | 虚拟CPU数量                                                  |
  | ram             | float  | 虚拟内存，单位为GB                                           |
  | os_type         | string | 系统类型，分别为`'Windows XP'、'Windows 7 bit 32'、'Windows 7 bit 64'、'Windows 10 bit 64'、'Linux': 'linux'` |
  | os_type_simple  | string | 系统类型简写，分别为`winxp/win7/win10/linux`                 |
  | owner           | string | 创建者                                                       |
  | desktop_count   | int    | 绑定的桌面组数量                                             |
  | instance_count  | int    | 绑定的桌面数量                                               |
  | status          | string | 模板状态，active-开机，inactive-关机，error-异常             |
  | updated_time    | string | 编辑模板后的更新时间                                         |
  | created_at      | string | 创建时间                                                     |
  | devices         | list   | 模板的磁盘信息，每个包含的字段信息如下：                     |
  | uuid            | string | 磁盘的uuid                                                   |
  | type            | string | 磁盘类型，system-系统盘，data-数据盘                         |
  | device_name     | string | 磁盘盘符名称                                                 |
  | boot_index      | int    | 磁盘启动顺序                                                 |
  | size            | int    | 磁盘大小，单位为GB                                           |
| used            | float  | 模板的某个磁盘已使用大小，单位为GB                           |
  
- 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null
            "previous": null,
            "results": [
                {
                    "uuid": "8f8c325a-6d7b-11ea-af95-0cc47a462da8",
                    "name": "win7模板",
                    "desc": "this is win7 template",
                    "host_ip": "172.16.1.27",
                    "host_name": "localhost.localdomain",
                    "network_name": "default",
                    "subnet_name": "subnet1",
                    "bind_ip": "192.16.1.15",
                    "vcpu": 2,
                    "ram": 2.0,
                    "os_type": "Windows7  bit 64",
                    "subnet_start_ip": "192.16.1.10",
                    "subnet_end_ip": "192.16.1.100",
                    "devices": [
                        {
                            "uuid": "8f8c3494-6d7b-11ea-af95-0cc47a462da8",
                            "type": "system",
                            "device_name": "vda",
                            "boot_index": 0,
                            "size": 50,
            				"used": 9.89
                        }
                    ],
                    "owner": "admin",
                    "desktop_count": 7,
                    "instance_count": 32,
                    "updated_time": "2020-03-30 10:08:44",
                    "status": "active",
                    "os_type_simple": "win7",
                    "created_at": "2020-03-24 11:00:04",
                    "pool_uuid": "6fd8bb14-6d70-11ea-9a33-0cc47a462da8",
                    "pool_name": "default",
                    "network_uuid": "6fb0caaa-6d70-11ea-9a33-0cc47a462da8",
                    "subnet_uuid": "738eaf34-6d7a-11ea-af95-0cc47a462da8"
                }
            ]
        }
    }
    ```



## 教学分组接口

### 1、添加教学分组


* URL

  `/education/group`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description    |
  | ---------------------- | ------ | -------------- |
  | name(required)         | string | 教学分组名称   |
  | group_type(required)   | int    | 教学分组为`1`  |
  | desc                   | string | 教学分组描述   |
  | network_uuid(required) | string | 数据网络uuid   |
  | subnet_uuid(required)  | string | 子网uuid       |
  | start_ip(required)     | string | 预设终端开始IP |
| end_ip(required)       | string | 预设终端结束IP |
  
- 示例：
  
    ```json
    {
        "name": "group5",
        "group_type": 1,
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

### 2、删除教学分组 ###

删除需要支持批量操作


* URL

  `/education/group/`

* Method

  **DELETE** 请求，**body** 使用 **json** 格式

* Parameters

  | Name           | Type   | Description                          |
  | -------------- | ------ | ------------------------------------ |
  | groups         | list   | 教学分组的列表，每个项包含如下字段： |
| name(required) | string | 分组名称                             |
  | uuid(required) | string | 分组uuid                             |

  - 示例：
  
    ```json
    {
    	"groups": [
    			{
    				"uuid": "f38c048e-59fc-11ea-84fd-000c295dd728",
    				"name": "group1"
    			},
    			{
    				"uuid": "52850290-5d1f-11ea-8fdf-000c295dd728",
    				"name": "group4"
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

### 3、修改教学分组 ###


* URL

  `/education/group`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 分组uuid                       |
  | name(required)  | string | 分组名称                       |
  | value(required) | dict   | 需要修改的分组新的属性，如下： |
  | name(required)  | string | 修改后的分组名称               |
  | desc            | string | 分组描述                       |
  | network_uuid    | string | 网络uuid                       |
  | subnet_uuid     | string | 子网uuid                       |
  | start_ip        | string | 预设终端开始IP                 |
| end_ip          | string | 预设终端结束IP                 |
  
- 示例：
  
    ```json
    {
    	"uuid": "02063e92-52ca-11ea-ba2e-000c295dd728",
        "name": "group1",
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

### 4、教学分组分页查询 ###


* URL

  ` /education/group/?searchtype=all&group_type=1&page=1&page_size=1 `

* Method

  **GET** 请求

* Parameters

  | Name                 | Type   | Description                     |
  | -------------------- | ------ | ------------------------------- |
  | group_type(required) | string | 分组类型，1-教学分组 2-用户分组 |
  | page                 | int    | 页数                            |
  | page_size            | int    | 分页大小                        |


* Returns

  | Name            | Type   | Description    |
  | :-------------- | :----- | :------------- |
  | uuid            | string | 分组的uuid     |
  | name            | string | 分组名称       |
  | desc            | string | 分组描述       |
  | network         | string | 网络的uuid     |
  | network_name    | string | 网络名称       |
  | subnet          | string | 子网uuid       |
  | subnet_name     | string | 子网名称       |
  | subnet_start_ip | string | 子网开始IP     |
  | subnet_end_ip   | string | 子网结束IP     |
  | start_ip        | string | 终端预设开始IP |
  | end_ip          | string | 终端预设结束IP |
| terminal_count  | int    | 终端数量       |
  | desktop_count   | int    | 桌面组的数量   |
| instance_count  | int    | 桌面数量       |
  
  - 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "d466a092-6f0e-11ea-be76-0cc47a462da8",
                    "name": "das",
                    "desc": "dsadas",
                    "network": "6fb0caaa-6d70-11ea-9a33-0cc47a462da8",
                    "network_name": "default",
                    "subnet": "738eaf34-6d7a-11ea-af95-0cc47a462da8",
                    "subnet_name": "subnet1",
                    "subnet_start_ip": "192.16.1.10",
                    "subnet_end_ip": "192.16.1.100",
                    "start_ip": "255.255.255.55",
                    "end_ip": "255.255.255.96",
                    "terminal_count": 0,
                    "instance_count": 29
                }
            ]
        }
    }
    ```



## 教学桌面组

### 1、添加教学桌面组


* URL

  `/education/desktop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`create`

  - param - 创建桌面组的参数，如下：

    | Name                    | Type   | Description                                                |
    | ----------------------- | ------ | ---------------------------------------------------------- |
    | name(required)          | string | 桌面组名称                                                 |
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
    	"action": "create",
    	"param": {
    		"name": "desktop2",
    	    "group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
    	    "template_uuid": "6f1006c0-56d1-11ea-aec0-000c295dd728",
    	    "pool_uuid": "9c888a04-5213-11ea-9d93-000c295dd728",
    	    "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
    	    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
    	    "vcpu": 1,
    	    "ram": 1,
    	    "sys_restore": 1,
    	    "data_restore": 1,
    	    "instance_num": 1,
    	    "prefix": "pc",
    	    "postfix": 3,
            "postfix_start": 5,
    	    "create_info": {
    	    	"192.168.1.11": 1
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

### 2、教学桌面组开机

开机需要支持批量操作


* URL

  `/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`start`

  - param - 开机的桌面组列表

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要开机的桌面组列表，其中每个项包含字段如下： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "start",
    	"param": {
    		"desktops": [
    				{
    					"name": "desktop1",
    					"uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 3、教学桌面组关机

关机需要支持批量操作


* URL

  `/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`stop`

  - param - 关机的桌面组列表

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要关机的桌面组列表，其中每个项包含字段如下： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "stop",
    	"param": {
    		"desktops": [
    				{
    					"name": "desktop1",
    					"uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 4、删除教学桌面组 ###

删除需要支持批量操作


* URL

  `/education/desktop/

* Method

  **DELETE** 请求，**body** 使用 **json** 格式

* Parameters

  | Name           | Type   | Description                                    |
  | -------------- | ------ | ---------------------------------------------- |
  | desktops       | list   | 需要删除的桌面组列表，其中每个项包含字段如下： |
| name(required) | string | 桌面组名称                                     |
  | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"desktops": [
    			{
    				"name": "desktop1",
    				"uuid": "500b75fc-5d20-11ea-9d96-000c295dd728"
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

### 5、激活教学桌面组

激活需要支持批量操作


* URL

  `/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`active`

  - param - 桌面组列表

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要激活的桌面组列表，其中每个项包含以下字段： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "active",
    	"param": {
    		"desktops": [
    				{
    					"name": "desktop1",
    					"uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 6、教学桌面组未激活

未激活需要支持批量操作


* URL

  `/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`inactive`

  - param - 桌面组列表

    | Name           | Type   | Description                                  |
    | :------------- | :----- | :------------------------------------------- |
    | desktops       | list   | 需要未激活的桌面组列表，每个项包含如下字段： |
  | name(required) | string | 桌面组名称                                   |
    | uuid(required) | string | 桌面组uuid                                   |

  - 示例：
  
    ```json
    {
    	"action": "inactive",
    	"param": {
    		"desktops": [
    				{
    					"name": "desktop1",
    					"uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 7、修改桌面组信息 ###


* URL

  `/education/desktop`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                      |
  | --------------- | ------ | -------------------------------- |
  | uuid(required)  | string | 桌面组uuid                       |
  | name(required)  | string | 桌面组名称                       |
  | value(required) | dict   | 更新的桌面组的属性，包含如下：   |
| name            | string | 修改后的桌面组名称               |
  | sys_restore     | int    | 系统盘是否还原，0-不还原，1-还原 |
  | data_restore    | int    | 数据盘是否还原，0-不还原，1-还原 |
  | order_num       | int    | 排序号                           |
  
- 示例：
  
    ```json
    {
    	"uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
        "name": "desktop1",
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

### 8、教学桌面组重启

重启需要支持批量操作


* URL

  `/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`reboot`

  - param - 桌面组列表

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要重启的桌面组列表，其中每个项包含如下字段： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "reboot",
    	"param": {
    		"desktops": [
    				{
    					"name": "desktop1",
    					"uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 9、教学桌面组分页查询 ###


* URL

  ` /education/desktop/?searchtype=all&&page=1&page_size=1`

* Method

  **GET** 请求

* Parameters

  | Name       | Type   | Description |
  | ---------- | ------ | ----------- |
  | searchtype | string | 查询分类    |
  | page       | int    | 页数        |
  | page_size  | int    | 分页大小    |
  
  - 示例
  
    ```
    # 分页查询所有教学桌面组
    /education/desktop/?searchtype=all&&page=1&page_size=1
    # 根据教学分组查询教学桌面组
    /education/desktop/?searchtype=all&group=d4d02b14-6f24-11ea-bdc0-0cc47a462da8&page=1&page_size=1
    # 教学分组下的教学桌面组模糊查询
    /education/desktop/?searchtype=all&group=d4d02b14-6f24-11ea-bdc0-0cc47a462da8&name=te&page=1&page_size=1
    ```
  
* Returns

  | Name            | Type    | Description                                            |
  | :-------------- | :------ | :----------------------------------------------------- |
  | uuid            | string  | 桌面的uuid                                             |
  | name            | string  | 桌面名称                                               |
  | owner           | string  | 创建者                                                 |
  | group           | string  | 分组uuid                                               |
  | group_name      | string  | 分组名称                                               |
  | template        | string  | 模板uuid                                               |
  | template_name   | string  | 模板名称                                               |
  | template_status | string  | 模板状态，当为"updating"时，会禁用掉该桌面组的所有操作 |
  | pool            | string  | 资源池uuid                                             |
  | pool_name       | string  | 资源池名称                                             |
  | sys_restore     | int     | 系统盘是否还原                                         |
  | data_restore    | int     | 数据盘是否还原                                         |
  | instance_num    | int     | 桌面总数量                                             |
  | inactive_count  | int     | 桌面未开机的数量                                       |
  | active_count    | int     | 桌面开机的数量                                         |
  | active          | boolean | 桌面组是否激活                                         |
  | vcpu            | int     | 虚拟CPU个数                                            |
  | ram             | float   | 虚拟内存，大小为G                                      |
  | os_type         | string  | 系统类型                                               |
  | prefix          | string  | 桌面名称的前缀                                         |
  | postfix         | int     | 桌面名称后缀数字个数                                   |
  | order_num       | int     | 排序号                                                 |
  | created_at      | string  | 创建时间                                               |
  | devices         | list    | 磁盘信息，单个字段信息如下：                           |
  | type            | string  | 磁盘类型，system-系统盘  data-数据盘                   |
  | boot_index      | int     | 磁盘启动顺序                                           |
  | size            | int     | 磁盘的大小，单位为GB                                   |


- 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "d3250bd2-6fcd-11ea-b8ce-0cc47a462da8",
                    "name": "dasd",
                    "template": "8f8c325a-6d7b-11ea-af95-0cc47a462da8",
                    "template_name": "win7模板",
                    "pool": "6fd8bb14-6d70-11ea-9a33-0cc47a462da8",
                    "pool_name": "default",
                    "sys_restore": 1,
                    "data_restore": 1,
                    "instance_num": 1,
                    "inactive_count": 1,
                    "active": false,
                    "group": "c2013f50-6f24-11ea-9a16-0cc47a462da8",
                    "group_name": "wlij",
                    "vcpu": 2,
                    "ram": 2.0,
                    "os_type": "Windows7  bit 64",
                    "created_at": "2020-03-27 09:53:58",
                    "active_count": 0,
                    "owner": "admin",
                    "network": "6fb0caaa-6d70-11ea-9a33-0cc47a462da8",
                    "network_name": "default",
                    "order_num": 1,
                    "devices": [
                        {
                            "type": "system",
                            "boot_index": 0,
                            "size": 50
                        }
                    ],
                    "prefix": "PC",
                    "postfix": 1,
                    "template_status": "active"
                }
            ]
        }
    }
    ```



## 教学桌面

### 1、教学桌面开机

需要支持一次多个桌面开机操作


* URL

  `/education/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`start`

  - param - 开机的桌面相关参数，如下：

    | Name                   | Type   | Description                        |
    | :--------------------- | :----- | :--------------------------------- |
    | desktop_uuid(required) | string | 需要开机的桌面所属桌面组uuid       |
    | desktop_name(required) | string | 需要开机的桌面所属桌面组名称       |
    | desktop_type(required) | int    | 教学桌面是`1`                      |
    | instances(required)    | list   | 桌面列表，其中每个项包含如下字段： |
    | name(required)         | string | 桌面名称                           |
    | uuid(required)         | string | 桌面uuid                           |
  
- 示例：
  
    ```json
    {
    	"action": "start",
    	"param": {
    		"desktop_uuid": "29407836-5d21-11ea-aa57-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 1,
    		"instances": [
    				{
    					"uuid": "6863d156-5d22-11ea-9bde-000c295dd728",
    					"name": "pc06"
    				},
    				{
    					"uuid": "6863de08-5d22-11ea-9bde-000c295dd728",
    					"name": "pc07"
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

### 2、教学桌面关机

需要支持一次多个桌面关机


* URL

  `/education/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`stop`

  - param - 关机的桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要关机的桌面所属桌面组uuid           |
    | desktop_name(required) | string | 需要关机的桌面所属桌面组名称           |
    | desktop_type(required) | int    | 教学桌面是`1`                          |
    | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
    | name(required)         | string | 桌面名称                               |
    | uuid(required)         | string | 桌面uuid                               |
  
- 示例：
  
    ```json
    {
    	"action": "stop",
    	"param": {
    		"desktop_uuid": "29407836-5d21-11ea-aa57-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 1,
    		"instances": [
    				{
    					"uuid": "6863d156-5d22-11ea-9bde-000c295dd728",
    					"name": "pc06"
    				},
    				{
    					"uuid": "6863de08-5d22-11ea-9bde-000c295dd728",
    					"name": "pc07"
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

### 3、添加教学桌面

桌面组中添加桌面


* URL

  `/education/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`action`

  - param - 增加的桌面相关参数，如下：

    | Name                   | Type   | Description                                                |
    | :--------------------- | :----- | :--------------------------------------------------------- |
    | desktop_uuid(required) | string | 添加的桌面所属桌面组uuid                                   |
    | desktop_name(required) | string | 添加的桌面所属桌面组名称                                   |
    | desktop_type(required) | int    | 教学桌面是`1`                                              |
    | instance_num(required) | int    | 增加的桌面数                                               |
    | create_info(required)  | dict   | 桌面在各个节点的分配信息，`key`值是节点IP，`value`则是数目 |
  
- 示例：
  
    ```json
    {
    	"action": "create",
    	"param": {
            "desktop_uuid": "29407836-5d21-11ea-aa57-000c295dd728",
            "desktop_name": "desktop2",
            "desktop_type": 1,
            "instance_num": 2,
            "create_info": {
                "172.16.1.11": 2
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

### 4、删除教学桌面


* URL

  `/education/instance/`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                            |
  | :--------------------- | :----- | :------------------------------------- |
  | desktop_uuid(required) | string | 需要删除的桌面所属桌面组uuid           |
  | desktop_name(required) | string | 需要删除的桌面所属桌面组名称           |
  | desktop_type(required) | int    | 个人桌面是`2`                          |
  | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
  | name(required)         | string | 桌面名称                               |
  | uuid(required)         | string | 桌面uuid                               |

  - 示例：

    ```json
    {
        "desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
        "desktop_name": "desktop2",
        "desktop_type": 2,
        "instances": [
            {
                "uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
                "name": "pc05"
            },
            {
                "uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
                "name": "pc06"
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

### 5、教学桌面重启

需要支持一次多个桌面重启


* URL

  `/education/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`reboot`

  - param - 重启的桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要重启的桌面所属桌面组uuid           |
    | desktop_name(required) | string | 需要重启的桌面所属桌面组名称           |
    | desktop_type(required) | int    | 教学桌面是`1`                          |
    | instances(required)    | list   | 桌面列表，其中每个桌面项包含以下字段： |
    | name(required)         | string | 桌面名称                               |
    | uuid(required)         | string | 桌面uuid                               |
  
- 示例：
  
    ```json
    {
    	"action": "reboot",
    	"param": {
    		"desktop_uuid": "29407836-5d21-11ea-aa57-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 1,
    		"instances": [
    				{
    					"uuid": "6863d156-5d22-11ea-9bde-000c295dd728",
    					"name": "pc06"
    				},
    				{
    					"uuid": "6863de08-5d22-11ea-9bde-000c295dd728",
    					"name": "pc07"
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

### 6、教学桌面获取控制台


* URL

  `/education/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`get_console`

  - param - 重启的桌面相关参数，如下：

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 桌面名称    |
    | uuid(required) | string | 桌面uuid    |

- 示例：

  ```json
  {
  	"action": "get_console",
  	"param": {
  		"uuid": "516fdca0-795c-11ea-8205-000c29e84b9c",
  		"name": "pc01"
  	}
  }
  ```


* Returns

  | Name           | Type   | Description          |
  | :------------- | :----- | :------------------- |
  | code           | int    | 返回码               |
  | msg            | str    | 请求返回的具体信息   |
  | data           | object | 根据需求返回相应数据 |
  | websockify_url | string | 桌面的连接ws地址     |

  - 示例：

    ```json
    {
        "code": 0,
        "data": {
            "websockify_url": "ws://172.16.1.14:6080/websockify/?token=516fdca0-795c-11ea-8205-000c29e84b9c"
        },
        "msg": "成功"
    }
    ```

### 7、教学桌面分页查询 ###


* URL

  ` /education/instance/?searchtype=all&desktop_uuid=c1e492e8-6fcd-11ea-b8ce-0cc47a462da8&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name                   | Type   | Description |
  | ---------------------- | ------ | ----------- |
  | desktop_uuid(required) | string | 桌面组uuid  |
  | page                   | int    | 页数        |
  | page_size              | int    | 分页大小    |
  
  - 示例
  
    ```
    # 属于某个教学桌面组下的桌面分页查询
    /education/instance/?searchtype=all&desktop_uuid=c1e492e8-6fcd-11ea-b8ce-0cc47a462da8&page=1&page_size=10
    ```
  
    
  
* Returns

  | Name        | Type   | Description                       |
  | :---------- | :----- | :-------------------------------- |
  | uuid        | string | 桌面uuid                          |
  | name        | string | 桌面名称                          |
  | ipaddr      | string | 桌面分配的IP                      |
  | hostname    | string | 桌面所在的节点名称                |
  | status      | string | 桌面状态，`active/inactive/error` |
  | up_time     | string | 桌面开机时间                      |
  | active_time | string | 桌面开机时长                      |
  | message     | string | 桌面信息                          |
  | user_name   | string | 桌面绑定的用户                    |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "c1e74ee8-6fcd-11ea-b8ce-0cc47a462da8",
                    "name": "PC1",
                    "ipaddr": "192.16.1.11",
                    "host_name": "localhost.localdomain",
                    "status": "inactive",
                    "up_time": "2020-03-27 09:53:30",
                    "active_time": 0,
                    "message": "",
                    "user_name": ""
                }
            ]
        }
    }
    ```



## 用户分组管理

### 1、添加用户分组

为了区分效果，这里的用户分组名称和教学分组的名称不能相同


* URL

  `/personal/group`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type   | Description   |
  | -------------------- | ------ | ------------- |
  | name(required)       | string | 分组名称      |
  | group_type(required) | int    | 用户分组为`2` |
  | desc                 | string | 分组描述      |
  
  - 示例：

    ```json
  {
        "name": "group2",
        "group_type": 2,
        "desc": "this is group2"
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

### 2、删除用户分组 ###

删除需要支持批量操作


* URL

  `/personal/group/

* Method

  **DELETE** 请求，**body** 使用 **json** 格式

* Parameters

  | Name           | Type   | Description                                  |
  | -------------- | ------ | -------------------------------------------- |
  | groups         | list   | 用户分组的列表，其中每个分组包含的字段如下： |
| name(required) | string | 用户分组的名称                               |
  | uuid(required) | string | 用户分组的uuid                               |

  - 示例：
  
    ```json
    {
    	"groups": [
    			{
    				"uuid": "9866933c-5d33-11ea-ab54-000c295dd728",
    				"name": "group4"
    			},
    			{
    				"uuid": "0c2746f2-59fd-11ea-b19c-000c295dd728",
    				"name": "group2"
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

### 3、修改分组 ###


* URL

  `/personal/group`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                    |
  | --------------- | ------ | ------------------------------ |
  | uuid(required)  | string | 分组uuid                       |
  | name(required)  | string | 分组名称                       |
  | value(required) | dict   | 需要修改的分组新的属性，如下： |
  | name(required)  | string | 修改后的分组名称               |
  | desc            | string | 分组描述                       |
  
- 示例：
  
    ```json
    {
    	"uuid": "02063e92-52ca-11ea-ba2e-000c295dd728",
        "name": "group1",
        "value": {
            "name": "group2",
            "desc": "this is group2"
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

### 4、用户分组分页查询 ###


* URL

  ` /personal/group/?searchtype=all&group_type=2&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name                 | Type   | Description                      |
  | -------------------- | ------ | -------------------------------- |
  | group_type(required) | string | 分组类型，1-教学分组，2-用户分组 |
  | page                 | int    | 页数                             |
  | page_size            | int    | 分页大小                         |


* Returns

  | Name         | Type    | Description                                          |
  | :----------- | :------ | :--------------------------------------------------- |
  | uuid         | string  | 用户分组uuid                                         |
  | name         | string  | 用户分组名称                                         |
  | desc         | string  | 用户分组描述                                         |
  | user_num     | int     | 分组包含的用户数量                                   |
  | enable_num   | int     | 分组中用户启用的数量                                 |
  | disable_num  | int     | 分组中用户禁用的数量                                 |
  | users        | list    | 分组中的用户详细信息列表，每个用户信息包含如下字段： |
  | uuid         | string  | 用户uuid                                             |
  | user_name    | string  | 用户名称                                             |
  | passwd       | string  | 用户密码，md5编码后的值                              |
  | name         | string  | 用户姓名                                             |
  | phone        | string  | 用户手机号                                           |
  | email        | string  | 用户邮箱                                             |
  | enabled      | boolean | 用户是否启用                                         |
  | group        | string  | 用户所属的用户组uuid                                 |
  | name_with_num| string  | 分组的统计信息                                       |


  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "b17ca27c-7547-11ea-97b1-000c29e84b9c",
                    "name": "group1",
                    "desc": "this is group3",
                    "user_num": 5,
                    "enable_num": 4,
                    "disable_num": 1,
                    "users": [
                        {
                            "uuid": "cd3b76c4-7550-11ea-9815-000c29e84b9c",
                            "user_name": "ctt01",
                            "passwd": "827ccb0eea8a706c4c34a16891f84e7b",
                            "name": "",
                            "phone": "",
                            "email": "",
                            "enabled": true,
                            "group": "b17ca27c-7547-11ea-97b1-000c29e84b9c",
                        },
                        {
                            "uuid": "cd3ca666-7550-11ea-9815-000c29e84b9c",
                            "user_name": "ctt02",
                            "passwd": "827ccb0eea8a706c4c34a16891f84e7b",
                            "name": "",
                            "phone": "",
                            "email": "",
                            "enabled": true,
                            "group": "b17ca27c-7547-11ea-97b1-000c29e84b9c"
                        },
                        {
                            "uuid": "cd3d59ee-7550-11ea-9815-000c29e84b9c",
                            "user_name": "ctt03",
                            "passwd": "827ccb0eea8a706c4c34a16891f84e7b",
                            "name": "",
                            "phone": "",
                            "email": "",
                            "enabled": false,
                            "group": "b17ca27c-7547-11ea-97b1-000c29e84b9c"
                        },
                        {
                            "uuid": "cd3dfe3a-7550-11ea-9815-000c29e84b9c",
                            "user_name": "ctt04",
                            "passwd": "827ccb0eea8a706c4c34a16891f84e7b",
                            "name": "",
                            "phone": "",
                            "email": "",
                            "enabled": true,
                            "group": "b17ca27c-7547-11ea-97b1-000c29e84b9c"
                        },
                        {
                            "uuid": "cd3ea7ea-7550-11ea-9815-000c29e84b9c",
                            "user_name": "ctt05",
                            "passwd": "827ccb0eea8a706c4c34a16891f84e7b",
                            "name": "",
                            "phone": "",
                            "email": "",
                            "enabled": true,
                            "group": "b17ca27c-7547-11ea-97b1-000c29e84b9c"
                        }
                    ]
                }
            ]
        }
    }
    ```



## 用户管理

### 1、单用户添加 ###

添加单用户到分组


* URL

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`single_create`

  - param - 单用户添加需要的参数，如下：

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
    	"action": "single_create",
    	"param": {
    		"group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
    		"user_name": "user2",
            "passwd": "password",
            "name": "john",
            "phone": "13144556677",
            "email": "345673456@qq.com",
            "enabled": 1
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

### 2、批量用户添加 ###

批量添加用户到分组中


* URL

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`multi_create`

  - param - 批量用户添加需要的参数，如下：

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
    	"action": "multi_create",
    	"param": {
    		"group_uuid": "d02cd368-5396-11ea-ad80-000c295dd728",
    		"prefix": "ctx",
            "postfix": 2,
            "postfix_start": 1,
            "user_num": 5,
            "passwd": "12345",
            "enabled": 1
    	}
    }
    ```


* Returns

  | Name        | Type | Description                          |
  | :---------- | :--- | :----------------------------------- |
  | code        | int  | 返回码                               |
  | msg         | str  | 请求返回的具体信息                   |
  | data        | dict | 根据需求返回相应数据，包括以下字段： |
| success_num | int  | 添加成功的用户数                     |
  | failed_num  | int  | 添加失败的用户数                     |

  - 示例：
  
    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "success_num": 5,
            "failed_num": 0
        }
    }
    ```

### 3、删除用户 ###

删除操作支持批量操作


* URL

  `/personal/user/`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                | Type   | Description                            |
  | ------------------- | ------ | -------------------------------------- |
  | users(required)     | list   | 用户列表，其中每个用户项包含字段如下： |
| user_name(required) | string | 用户名                                 |
  | uuid(required)      | string | 用户uuid                               |

  - 示例：
  
    ```json
    {
    	"users": [
    			{
                    "uuid": "3119dc92-5d34-11ea-a8a2-000c295dd728",
                    "user_name": "ctx01"
                },
                {
                    "uuid": "311af6c2-5d34-11ea-a8a2-000c295dd728",
                    "user_name": "ctx02"
                }
    		]
    }
    ```


* Returns

  | Name        | Type | Description          |
  | :---------- | :--- | :------------------- |
  | code        | int  | 返回码               |
  | msg         | str  | 请求返回的具体信息   |
  | data        | dict | 根据需求返回相应数据 |
| success_num | int  | 添加成功的用户数     |
  | failed_num  | int  | 添加失败的用户数     |

  - 示例：
  
    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "success_num": 5,
            "failed_num": 0
        }
    }
    ```

### 4、更新用户信息 ###


* URL

  `/personal/user/`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type    | Description                    |
  | -------------------- | ------- | ------------------------------ |
  | uuid(required)       | string  | 用户uuid                       |
  | user_name(required)  | string  | 用户名                         |
  | value(required)      | dict    | 更新的桌面组的属性，包含如下： |
  | group_uuid(required) | string  | 用户所属的分组uuid             |
  | user_name(required)  | string  | 更新后的用户名                 |
  | passwd(required)     | string  | 用户密码                       |
  | name                 | string  | 用户姓名                       |
  | phone                | string  | 电话号码                       |
  | email                | string  | 邮箱                           |
| enabled              | boolean | 启用或者禁用状态，默认启用     |
  
- 示例：
  
    ```json
    {
    	"uuid": "ba63d8d0-579f-11ea-b1ca-000c295dd728",
        "user_name": "ctx02",
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

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`enable`

  - param - 用户相关的参数，如下：

    | Name                | Type   | Description                            |
    | ------------------- | ------ | -------------------------------------- |
    | users(required)     | list   | 用户列表，其中每个用户项包含如下字段： |
  | user_name(required) | string | 用户名                                 |
    | uuid(required)      | string | 用户uuid                               |

  - 示例：
  
    ```json
    {
    	"action": "enable",
    	"param": {
    		"users": [
    				{
    	                "uuid": "3119dc92-5d34-11ea-a8a2-000c295dd728",
    	                "user_name": "ctx01"
    	            },
    	            {
    	                "uuid": "311af6c2-5d34-11ea-a8a2-000c295dd728",
    	                "user_name": "ctx02"
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

### 6、用户禁用 ###

设置用户状态为禁用


* URL

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`disable`
  - param - 用户相关的参数，如下：

    | Name                | Type   | Description                            |
    | ------------------- | ------ | -------------------------------------- |
    | users(required)     | list   | 用户列表，其中每个用户项包含如下字段： |
  | user_name(required) | string | 用户名                                 |
    | uuid(required)      | string | 用户uuid                               |

  - 示例：
  
    ```json
    {
    	"action": "disable",
    	"param": {
    		"users": [
    				{
    	                "uuid": "3119dc92-5d34-11ea-a8a2-000c295dd728",
    	                "user_name": "ctx01"
    	            },
    	            {
    	                "uuid": "311af6c2-5d34-11ea-a8a2-000c295dd728",
    	                "user_name": "ctx02"
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

### 7、移动用户 ###

移动用户到其他用户分组


* URL

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`move`

  - param - 用户相关的参数，如下：

    | Name                 | Type   | Description                            |
    | -------------------- | ------ | -------------------------------------- |
    | group_uuid(required) | string | 移动到的分组uuid                       |
    | group_name(required) | string | 移动到的分组名称                       |
    | users(required)      | list   | 用户列表，其中每个用户项包含如下字段： |
    | user_name(required)  | string | 用户名                                 |
    | uuid(required)       | string | 用户uuid                               |

  - 示例：

    ```json
    {
    	"action": "move",
    	"param": {
    		"group_uuid": "f6fe4ffc-5d33-11ea-a8a2-000c295dd728",
            "group_name": "group2",
            "users": [
                {
                    "uuid": "3119dc92-5d34-11ea-a8a2-000c295dd728",
                    "user_name": "ctx01"
                },
                {
                    "uuid": "311af6c2-5d34-11ea-a8a2-000c295dd728",
                    "user_name": "ctx02"
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

### 8、导出用户 ###

移动用户到其他用户分组


* URL

  `/personal/user/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 表示执行的具体操作，这里是`export`

  - param - 用户相关的参数，如下：

    | Name                | Type   | Description                            |
    | ------------------- | ------ | -------------------------------------- |
    | filename(required)  | string | 导出的文件名                           |
    | users(required)     | list   | 需要导出的用户列表，每个包含如下字段： |
    | user_name(required) | string | 用户名                                 |
    | uuid(required)      | string | 用户uuid                               |

  - 示例：

    ```json
    {
    	"action": "export",
    	"param": {
    		"filename": "user",
    		"users": [
    				{
    	                "uuid": "72b1c4f2-74b4-11ea-ab2d-000c29e84b9c",
    	                "user_name": "ctx01"
    	            },
    	            {
    	                "uuid": "72b2da40-74b4-11ea-ab2d-000c29e84b9c",
    	                "user_name": "ctx02"
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
        "data": {
            "url": "http://172.16.1.14:50000/api/v1/group/user/download?path=/root/user.xlsx"
        },
        "msg": "成功"
    }
    ```

### 9、导入用户 ###

移动用户到其他用户分组


* URL

  `/personal/user/upload`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  文件本身，另外还有`enable`参数，代表导入的用户是否启用


* Returns

  | Name        | Type   | Description                        |
  | :---------- | :----- | :--------------------------------- |
  | code        | int    | 返回码                             |
  | msg         | str    | 请求返回的具体信息                 |
  | data        | object | 根据需求返回相应数据，包含如下数据 |
  | failed_num  | int    | 导入失败的用户数                   |
  | success_num | int    | 导入成功的用户数                   |

  - 示例：

    ```json
    {
        "code": 0,
        "data": {
            "failed_num": 4,
            "success_num": 1
        },
        "msg": "成功"
    }
    ```

### 10、用户分组分页查询 ###


* URL

  ` /personal/user/?searchtype=all&&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name      | Type   | Description                                      |
  | --------- | ------ | ------------------------------------------------ |
  | group     | string | 查询某个分组下的用户时提供该参数，表示用户组uuid |
  | page      | int    | 页数                                             |
  | page_size | int    | 分页大小                                         |


* Returns

  | Name      | Type    | Description             |
  | :-------- | :------ | :---------------------- |
  | uuid      | string  | 用户uuid                |
  | user_name | string  | 用户名称                |
  | passwd    | string  | 用户密码，md5编码后的值 |
  | name      | string  | 用户姓名                |
  | phone     | string  | 用户手机号              |
  | email     | string  | 用户邮箱                |
  | enabled   | boolean | 用户是否启用            |
  | group     | string  | 用户所属的用户组uuid    |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "cf6b28a4-726c-11ea-92bd-0cc47a462da8",
                    "user_name": "sss",
                    "passwd": "123456",
                    "name": "",
                    "phone": "",
                    "email": "",
                    "enabled": false,
                    "group": "2ffca946-7258-11ea-a126-0cc47a462da8"
                }
            ]
        }
    }
    ```



## 个人桌面组

### 1、添加个人桌面组


* URL

  `/personal/desktop`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`create`

  - param - 创建桌面组的参数，如下：

    | Name                    | Type   | Description                                                  |
    | ----------------------- | ------ | ------------------------------------------------------------ |
    | name(required)          | string | 桌面组名称                                                   |
    | template_uuid(required) | string | 桌面组使用的模板uuid                                         |
    | pool_uuid(required)     | string | 资源池uuid                                                   |
    | network_uuid            | string | 数据网络uuid，可选                                           |
    | subnet_uuid             | string | 子网uuid，可选                                               |
    | allocate_type(required) | int    | IP分配类型，`1-系统分配 2-固定分配`，当没有网络选择并且是`1-系统分配`时，由环境中DHCP负责IP分配 |
    | allocate_start          | string | 当选择了网络，并且分配类型为`2-固定分配`时，需要提供此参数，表示起始IP |
    | vcpu(required)          | int    | 虚拟CPU数目                                                  |
    | ram(required)           | float  | 虚拟内存，单位为GB                                           |
    | sys_restore(required)   | int    | 系统盘是否重启还原                                           |
    | data_restore(required)  | int    | 数据盘是否重启还原                                           |
    | desktop_type(required)  | int    | 桌面类型，`1-随机桌面 2-静态桌面`                            |
    | groups                  | list   | 当桌面类型为`1-随机桌面`时，需要提供此参数，表示个人桌面组关联的用户分组uuid列表 |
    | allocates               | list   | 当桌面类型为`2-静态桌面`时，可以提供此参数，表示桌面与具体用户的对应关系（只能对应一个用户分组中的用户），其中的每个元素包括(user_uuid, name)两个`key`以及对应的值，分别表示用户和桌面。 |
    | group_uuid              | str    | 当桌面类型为`2-静态桌面`时，可以提供此参数，表示绑定的用户组uuid |
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
    	    "allocation": [
    	    		{
    	    			"user_uuid": "01d0e1b8-593f-11ea-9d4b-000c295dd728",
    	    			"name": "pc03"
    	    		},
    	    		{
    	    			"user_uuid": "01d1c902-593f-11ea-9d4b-000c295dd728",
    	    			"name": "pc04"
    	    		},
    	    		{
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

  `/personal/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`start`

  - param - 桌面相关参数

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要开机的桌面组列表，其中每个项包含如下字段： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "start",
    	"param": {
    		"desktops": [
    				{
    					"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    					"name": "desktop2"
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

### 3、个人桌面组关机

关机需要支持批量操作


* URL

  `/personal/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`stop`

  - param - 桌面相关参数

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要关机的桌面组列表，其中每个项包含如下字段： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "stop",
    	"param": {
    		"desktops": [
    				{
    					"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    					"name": "desktop2"
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

### 4、删除个人桌面组 ###

删除需要支持批量操作


* URL

  `/personal/desktop/

* Method

  **DELETE** 请求，**body** 使用 **json** 格式

* Parameters

  | Name           | Type   | Description                          |
  | -------------- | ------ | ------------------------------------ |
  | desktops       | list   | 桌面组列表，其中每个项包含如下字段： |
| name(required) | string | 桌面组名称                           |
  | uuid(required) | string | 桌面组uuid                           |

  - 示例：
  
    ```json
    {
    	"desktops": [
    			{
    				"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    				"name": "desktop2"
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

### 5、修改桌面组信息 ###


* URL

  `/personal/desktop/`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name            | Type   | Description                      |
  | --------------- | ------ | -------------------------------- |
  | uuid(required)  | string | 桌面组uuid                       |
  | name(required)  | string | 桌面组名称                       |
  | value(required) | dict   | 更新的桌面组的属性，包含如下：   |
| name            | string | 修改后的桌面组名称               |
  | sys_restore     | int    | 系统盘是否还原，0-不还原，1-还原 |
  | data_restore    | int    | 数据盘是否还原，0-不还原，1-还原 |
  | order_num       | int    | 排序号                           |
  
- 示例：
  
    ```json
    {
    	"uuid": "acdbfa10-56e8-11ea-8e10-000c295dd728",
        "name": "desktop1",
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

  `/personal/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`reboot`

  - param - 桌面组相关参数

    | Name           | Type   | Description                                    |
    | :------------- | :----- | :--------------------------------------------- |
    | desktops       | list   | 需要重启的桌面组列表，其中每个项包含如下字段： |
  | name(required) | string | 桌面组名称                                     |
    | uuid(required) | string | 桌面组uuid                                     |

  - 示例：
  
    ```json
    {
    	"action": "reboot",
    	"param": {
    		"desktops": [
    				{
    					"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    					"name": "desktop2"
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

### 7、个人桌面组开启维护模式


* URL

  `/personal/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`enter_maintenance`

  - param - 桌面组相关参数

    | Name           | Type   | Description                          |
    | :------------- | :----- | :----------------------------------- |
    | desktops       | list   | 桌面组列表，其中每个项包含如下字段： |
    | name(required) | string | 桌面组名称                           |
    | uuid(required) | string | 桌面组uuid                           |

  - 示例：

    ```json
    {
    	"action": "enter_maintenance",
    	"param": {
    		"desktops": [
    				{
    					"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    					"name": "desktop2"
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

### 8、个人桌面组关闭维护模式

重启需要支持批量操作


* URL

  `/personal/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`exit_maintenance`

  - param - 桌面组相关参数

    | Name           | Type   | Description                          |
    | :------------- | :----- | :----------------------------------- |
    | desktops       | list   | 桌面组列表，其中每个项包含如下字段： |
    | name(required) | string | 桌面组名称                           |
    | uuid(required) | string | 桌面组uuid                           |

  - 示例：

    ```json
    {
    	"action": "exit_maintenance",
    	"param": {
    		"desktops": [
    				{
    					"uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    					"name": "desktop2"
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

### 9、个人桌面组分页查询


* URL

  `/personal/desktop/?searchtype=all&page=1&page_size=10`

* Method

  **GET** 请求

* Parameters

  | Name       | Type   | Description                    |
  | :--------- | :----- | :----------------------------- |
  | searchtype | string | 查询类型，`all/contain/single` |
  | page       | string | 页数                           |
  | page_size  | list   | 分页大小                       |


* Returns

  results里面单条记录的字段信息如下：

  | Name            | Type   | Description                                                  |
  | :-------------- | :----- | :----------------------------------------------------------- |
  | uuid            | string | 桌面组uuid                                                   |
  | name            | string | 桌面组名称                                                   |
  | template        | string | 模板uuid                                                     |
  | template_name   | string | 模板名称                                                     |
  | template_status | string | 模板状态，当为"updating"时，会禁用掉该桌面组的所有操作       |
  | pool            | string | 资源池uuid                                                   |
  | pool_name       | string | 资源池名称                                                   |
  | sys_restore     | int    | 系统盘是否还原，0-不还原 1-还原                              |
  | data_restore    | int    | 数据盘是否还原，0-不还原 1-还原                              |
  | instance_num    | int    | 桌面组包含的桌面总数                                         |
  | active_count    | int    | 桌面处于开机状态的数量                                       |
  | inactive_count  | int    | 桌面处于关机状态的数量                                       |
  | vcpu            | int    | 虚拟cpu数量                                                  |
  | ram             | float  | 虚拟内存，单位为GB                                           |
  | os_type         | string | 系统类型，分别为`'Windows XP'、'Windows 7 bit 32'、'Windows 7 bit 64'、'Windows 10 bit 64'、'Linux': 'linux'` |
  | network         | string | 数据网络uuid                                                 |
  | network_name    | string | 数据网络名称                                                 |
  | owner           | string | 创建者                                                       |
  | order_num       | int    | 排序号                                                       |
  | maintenance     | int    | 维护模式，0-否 1-是                                          |
  | prefix          | string | 桌面组中桌面命名的前缀                                       |
  | postfix         | int    | 桌面组中桌面命名的后缀数字个数                               |
  | desktop_type    | int    | 1-随机桌面，2-静态桌面                                       |
  | group_uuid      | string | 当为静态桌面时，绑定的用户组uuid                             |
  | created_at      | string | 创建时间                                                     |
  | devices         | list   | 桌面组的磁盘信息，跟模板的磁盘属性一致，单个信息如下：       |
  | type            | string | 磁盘类型，system-系统盘  data-数据盘                         |
  | boot_index      | int    | 磁盘启动顺序                                                 |
| size            | int    | 磁盘的大小，单位为GB                                         |
  
- 示例：
  
    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "58502b06-74bb-11ea-8d41-000c29e84b9c",
                    "name": "desktop1",
                    "template": "4d2388d8-74b9-11ea-b870-000c29e84b9c",
                    "template_name": "win1",
                    "pool": "7dcb05de-73f5-11ea-9ace-000c29e84b9c",
                    "pool_name": "default",
                    "sys_restore": 0,
                    "data_restore": 0,
                    "instance_num": 3,
                    "inactive_count": 3,
                    "vcpu": 1,
                    "ram": 2,
                    "os_type": "Windows7  bit 64",
                    "active_count": 0,
                    "network_name": "default",
                    "network": "7dabcee4-73f5-11ea-9ace-000c29e84b9c",
                    "created_at": "2020-04-02 16:24:20",
                    "owner": "admin",
                    "order_num": 99,
                    "maintenance": 1,
                    "devices": [
                        {
                            "type": "system",
                            "boot_index": 0,
                            "size": 50
                        },
                        {
                            "type": "data",
                            "boot_index": 1,
                            "size": 50
                        }
                    ],
                    "prefix": "pc",
                    "postfix": 2,
                    "desktop_type": 2,
                    "group_uuid": "60e4a0f0-74b4-11ea-928e-000c29e84b9c"
                }
            ]
        }
    }
    ```



## 个人桌面组的随机桌面

### 1、添加绑定用户组

将用户组绑定到个人桌面组


* URL

  `/personal/desktop/random/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 具体操作，这里是`add_group`

  - param - 相关参数

    | Name                   | Type   | Description                                    |
    | :--------------------- | :----- | :--------------------------------------------- |
    | desktop_uuid(required) | string | 需要重启的桌面组列表，其中每个项包含如下字段： |
    | desktop_name(required) | string | 桌面组名称                                     |
    | group                  | list   | 需要添加的用户组信息，单个字段信息如下：       |
    | group_uuid             | string | 用户组uuid                                     |
    | group_name             | string | 用户组名称                                     |

  - 示例：

    ```json
    {
    	"action": "add_group",
    	"param": 
    		{
    	    "desktop_uuid": "8e178a90-7547-11ea-97b1-000c29e84b9c",
    	    "desktop_name": "desktop2",
    	    "groups": [
    	            {
    	                "group_uuid": "b17ca27c-7547-11ea-97b1-000c29e84b9c",
    	                "group_name": "group1"
    	            },
    	            {
    	                "group_uuid": "b3da54ba-7547-11ea-97b1-000c29e84b9c",
    	                "group_name": "group2"
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

### 2、移除绑定用户组

移除用户组与桌面组的绑定关系


* URL

  `/personal/desktop/random/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 具体操作，这里是`delete_group`

  - param - 相关参数

    | Name                   | Type   | Description                                |
    | :--------------------- | :----- | :----------------------------------------- |
    | desktop_uuid(required) | string |                                            |
    | desktop_name(required) | string | 桌面组名称                                 |
    | group                  | list   | 需要移除的绑定关系信息，单个字段信息如下： |
    | uuid                   | string | 用户组与桌面组绑定关系的uuid               |
    | group_name             | string | 用户组名称                                 |

  - 示例：

    ```json
    {
    	"action": "delete_group",
    	"param": 
    		{
    	    "desktop_uuid": "8e178a90-7547-11ea-97b1-000c29e84b9c",
    	    "desktop_name": "desktop2",
    	    "groups": [
    	            {
    	            	"uuid": "8e178d2e-7547-11ea-97b1-000c29e84b9c",
    	                "group_name": "group1"
    	            },
    	            {
    	                "uuid": "247f8c64-754b-11ea-9934-000c29e84b9c",
    	                "group_name": "group2"
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

### 3、查询随机桌面绑定关系


* URL

  `/personal/desktop/random/?desktop=8e178a90-7547-11ea-97b1-000c29e84b9c&page=1&page_size=10`

* Method

  **GET** 请求

* Parameters

  | Name              | Type   | Description      |
  | :---------------- | :----- | :--------------- |
  | desktop(required) | string | 个人桌面组的uuid |
  | page              | string | 页数             |
  | page_size         | list   | 分页大小         |


* Returns

  results里面单条记录的字段信息如下：

  | Name        | Type | Description                  |
  | :---------- | :--- | :--------------------------- |
  | uuid        | str  | 绑定关系的uuid               |
  | group_uuid  | str  | 绑定的用户组uuid             |
  | group_name  | str  | 绑定的用户组名称             |
  | user_num    | int  | 绑定的用户组中用户的数量     |
  | disable_num | int  | 绑定的用户组中禁用用户的数量 |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "49d7ea34-754f-11ea-947b-000c29e84b9c",
                    "group_uuid": "b17ca27c-7547-11ea-97b1-000c29e84b9c",
                    "group_name": "group1",
                    "user_num": 5,
                    "disable_num": 1
                },
                {
                    "uuid": "49d7ec32-754f-11ea-947b-000c29e84b9c",
                    "group_uuid": "b3da54ba-7547-11ea-97b1-000c29e84b9c",
                    "group_name": "group2",
                    "user_num": 5,
                    "disable_num": 0
                }
            ]
        }
    }
    ```

## 个人桌面组的静态桌面

### 1、修改用户绑定关系

移除用户与具体桌面的绑定关系


* URL

  `/personal/desktop/static/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 具体操作，这里是`change_bind`

  - param - 相关参数

    | Name                    | Type   | Description    |
    | :---------------------- | :----- | :------------- |
    | instance_uuid(required) | string | 绑定关系的uuid |
    | instance_name(required) | string | 绑定的桌面名   |
    | user_uuid(required)     | string | 绑定的用户uuid |
    | user_name(required)     | string | 绑定的用户名   |

  - 示例：

    ```json
    {
    	"action": "change_bind",
    	"param": 
    		{
                "user_uuid": "72b1c4f2-74b4-11ea-ab2d-000c29e84b9c",
                "user_name": "ctx01",
                "instance_uuid": "3c1c2fe9-5ae2-4ed0-8c98-174cbab231ea",
                "instance_name": "pc01"
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

### 2、修改静态桌面绑定的用户组

修改静态桌面绑定的用户组。点击自动匹配时调用该接口，会在后台确定一个默认匹配关系


* URL

  `/personal/desktop/static/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 具体操作，这里是`change_group`

  - param - 相关参数

    | Name                   | Type   | Description        |
    | :--------------------- | :----- | :----------------- |
    | desktop_uuid(required) | string | 桌面组uuid         |
    | desktop_name(required) | string | 桌面组名称         |
    | group_uuid             | string | 新绑定的用户组uuid |
    | group_name             | string | 新绑定的用户组名称 |

  - 示例：

    ```json
    {
    	"action": "change_group",
    	"param": {
    		"desktop_uuid": "58502b06-74bb-11ea-8d41-000c29e84b9c",
    		"desktop_name": "desktop1",
    		"group_uuid": "b3da54ba-7547-11ea-97b1-000c29e84b9c",
    		"group_name": "group2"
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

### 3、查询静态桌面绑定关系


* URL

  `/personal/desktop/static/?desktop_uuid=58502b06-74bb-11ea-8d41-000c29e84b9c&page=1&page_size=10`

* Method

  **GET** 请求

* Parameters

  | Name                   | Type   | Description      |
  | :--------------------- | :----- | :--------------- |
  | desktop_uuid(required) | string | 个人桌面组的uuid |
  | page                   | string | 页数             |
  | page_size              | list   | 分页大小         |


* Returns

  results里面单条记录的字段信息如下：

  | Name          | Type   | Description                                                  |
  | :------------ | :----- | :----------------------------------------------------------- |
  | bind_uuid     | string | 绑定关系的uuid，如果为空，则表示这个桌面没有绑定             |
  | user_uuid     | string | 绑定的用户uuid                                               |
  | user_name     | string | 绑定的用户名称                                               |
  | instance_uuid | string | 桌面uuid，返回是以桌面作为基准的，有多少个桌面，就会有多少条记录返回 |
  | instance_name | string | 桌面名称                                                     |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 3,
            "next": null,
            "previous": null,
            "results": [
                {
                    "user_uuid": "",
                    "user_name": "",
                    "instance_uuid": "5851a5d0-74bb-11ea-8d41-000c29e84b9c",
                    "instance_name": "pc01",
                    "bind_uuid": ""
                },
                {
                    "user_uuid": "72b2da40-74b4-11ea-ab2d-000c29e84b9c",
                    "user_name": "",
                    "instance_uuid": "5851af58-74bb-11ea-8d41-000c29e84b9c",
                    "instance_name": "pc02",
                    "bind_uuid": "26703130-74d4-11ea-b50b-000c29e84b9c"
                },
                {
                    "user_uuid": "72b38648-74b4-11ea-ab2d-000c29e84b9c",
                    "user_name": "",
                    "instance_uuid": "5851b656-74bb-11ea-8d41-000c29e84b9c",
                    "instance_name": "pc03",
                    "bind_uuid": "2bde6f7e-74d4-11ea-b50b-000c29e84b9c"
                }
            ]
        }
    }
    ```



## 个人桌面

### 1、个人桌面开机

需要支持一次多个桌面开机操作


* URL

  `/personal/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`start`

  - param - 桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要开机的桌面所属桌面组uuid           |
    | desktop_name(required) | string | 需要开机的桌面所属桌面组名称           |
    | desktop_type(required) | int    | 个人桌面是`2`                          |
  | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
    | name(required)         | string | 桌面名称                               |
  | uuid(required)         | string | 桌面uuid                               |
  
  - 示例：
  
    ```json
    {
    	"action": "start",
    	"param": {
    		"desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 2,
    		"instances": [
    				{
    					"uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
    					"name": "pc05"
    				},
    				{
    					"uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
    					"name": "pc06"
    				},
    				{
    					"uuid": "c48083ec-5d3d-11ea-b9c7-000c295dd728",
    					"name": "pc07"
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

### 2、个人桌面关机

需要支持一次多个桌面关机


* URL

  `/personal/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`stop`

  - param - 桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要关机的桌面所属桌面组uuid           |
    | desktop_name(required) | string | 需要关机的桌面所属桌面组名称           |
    | desktop_type(required) | int    | 个人桌面是`2`                          |
  | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
    | name(required)         | string | 桌面名称                               |
  | uuid(required)         | string | 桌面uuid                               |
  
  - 示例：
  
    ```json
    {
    	"action": "stop",
    	"param": {
    		"desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 2,
    		"instances": [
    				{
    					"uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
    					"name": "pc05"
    				},
    				{
    					"uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
    					"name": "pc06"
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

### 2、个人桌面强制关机

需要支持一次多个桌面强制关机


* URL

  `/personal/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`hard_stop`

  - param - 桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要强制关机的桌面所属桌面组uuid       |
    | desktop_name(required) | string | 需要强制关机的桌面所属桌面组名称       |
    | desktop_type(required) | int    | 个人桌面是`2`                          |
    | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
    | name(required)         | string | 桌面名称                               |
    | uuid(required)         | string | 桌面uuid                               |

  - 示例：

    ```json
    {
    	"action": "hard_stop",
    	"param": {
    		"desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 2,
    		"instances": [
    				{
    					"uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
    					"name": "pc05"
    				},
    				{
    					"uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
    					"name": "pc06"
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



### 3、添加个人桌面

桌面组中添加桌面


* URL

  `/personal/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`create`

  - param - 增加的桌面相关参数，如下：

    | Name                   | Type   | Description                                                |
    | :--------------------- | :----- | :--------------------------------------------------------- |
    | desktop_uuid(required) | string | 添加的桌面所属桌面组uuid                                   |
    | dekstop_name(required) | string | 添加的桌面所属桌面组名称                                   |
    | desktop_type(required) | int    | 个人桌面是`2`                                              |
    | instance_num(required) | int    | 增加的桌面数                                               |
    | prefix                 | string | 桌面的前缀                                                 |
    | create_info(required)  | dict   | 桌面在各个节点的分配信息，`key`值是节点IP，`value`则是数目 |
  
- 示例：
  
    ```json
    {
    	"action": "create",
    	"param": {
            "desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
            "desktop_name": "desktop2",
            "desktop_type": 2,
            "instance_num": 2,
            "create_info": {
                "172.16.1.11": 2
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

### 4、删除个人桌面


* URL

  `/personal/instance/`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description                            |
  | :--------------------- | :----- | :------------------------------------- |
  | desktop_uuid(required) | string | 需要删除的桌面所属桌面组uuid           |
  | desktop_name(required) | string | 需要删除的桌面所属桌面组名称           |
  | desktop_type(required) | int    | 个人桌面是`2`                          |
  | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
  | name(required)         | string | 桌面名称                               |
  | uuid(required)         | string | 桌面uuid                               |

  - 示例：

    ```json
    {
        "desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
        "desktop_name": "desktop2",
        "desktop_type": 2,
        "instances": [
            {
                "uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
                "name": "pc05"
            },
            {
                "uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
                "name": "pc06"
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

### 5、个人桌面重启

需要支持一次多个桌面重启


* URL

  `/personal/instance/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面的具体操作，这里是`reboot`

  - param - 重启的桌面相关参数，如下：

    | Name                   | Type   | Description                            |
    | :--------------------- | :----- | :------------------------------------- |
    | desktop_uuid(required) | string | 需要重启的桌面所属桌面组uuid           |
    | desktop_name(required) | string | 需要重启的桌面所属桌面组名称           |
    | desktop_type(required) | int    | 个人桌面是`2`                          |
  | instances(required)    | list   | 桌面列表，其中每个桌面项包含如下字段： |
    | name(required)         | string | 桌面名称                               |
  | uuid(required)         | string | 桌面uuid                               |
  
  - 示例：
  
    ```json
    {
    	"action": "reboot",
    	"param": {
    		"desktop_uuid": "c2387e1c-5d3a-11ea-a93e-000c295dd728",
    		"desktop_name": "desktop2",
    		"desktop_type": 2,
    		"instances": [
    				{
    					"uuid": "c239e2b6-5d3a-11ea-a93e-000c295dd728",
    					"name": "pc05"
    				},
    				{
    					"uuid": "c4807c44-5d3d-11ea-b9c7-000c295dd728",
    					"name": "pc06"
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

### 6、个人桌面分页查询 ###


* URL

  ` /personal/instance/?searchtype=all&desktop_uuid=c1e492e8-6fcd-11ea-b8ce-0cc47a462da8&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name                   | Type   | Description |
  | ---------------------- | ------ | ----------- |
  | desktop_uuid(required) | string | 桌面组uuid  |
  | page                   | int    | 页数        |
  | page_size              | int    | 分页大小    |


* Returns

  | Name        | Type   | Description                       |
  | :---------- | :----- | :-------------------------------- |
  | uuid        | string | 桌面uuid                          |
  | name        | string | 桌面名称                          |
  | ipaddr      | string | 桌面分配的IP                      |
  | hostname    | string | 桌面所在的节点名称                |
  | status      | string | 桌面状态，`active/inactive/error` |
  | up_time     | string | 桌面开机时间                      |
  | active_time | string | 桌面开机时长                      |
  | message     | string | 桌面信息                          |
  | user_name   | string | 桌面绑定的用户                    |

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 2,
            "next": "null,
            "previous": null,
            "results": [
                {
                    "uuid": "990b118a-7491-11ea-9c62-0cc47a462da8",
                    "name": "PC1",
                    "ipaddr": "",
                    "host_name": "localhost.localdomain",
                    "status": "active",
                    "up_time": "2020-04-02 17:17:05",
                    "active_time": 95335.0,
                    "message": "",
                    "user_name": "sss"
                },
                {
                    "uuid": "990b1c34-7491-11ea-9c62-0cc47a462da8",
                    "name": "PC2",
                    "ipaddr": "",
                    "host_name": "localhost.localdomain",
                    "status": "active",
                    "up_time": "2020-04-02 11:25:27",
                    "active_time": 116433.0,
                    "message": "",
                    "user_name": "aaa"
                }
            ]
        }
    }
    ```



## 通用查询方法

### 1、信息查询

目前查询支持三种方式，分别是查询所有，模糊查询和根据具体字段查询，后续可根据情况进行扩展。


* URL

  所有接口方式一致，例如：

  `/education/group/?searchtype=all&name=group1`

* Method

  **GET** 请求

* Parameters

  | Name                 | Description                                                  |
  | :------------------- | :----------------------------------------------------------- |
  | searchtype(required) | 目前支持三个取值：`all`、`contain`、`single`，默认为`all`。当取值为`all`时，表示查询所有相关的记录，当取值为`contain`时，表示`%value%`模糊查询，当取值为`single`，表示精确查询，且只返回一条记录。 |
  | key-value            | 键值对，`key`是数据库表中的字段名，`value`则是字段对应的值，用作查询条件。当searchtype为`all`时，如果再加上键值对，则会根据条件进行过滤（过滤方法为=），然后返回符合条件的所有记录。当searchtype为`contain`时，必须提供键值对，否则报错。键值对的过滤方法为`%value%`，返回满足条件的所有记录。当searchtype为`single`时，必须提供键值对，过滤方法为`=`，只会返回第一条匹配的数据。**NOTES**：由于支持分页查询，所以参数中会有`page`参数，如果数据库表中有此字段，则这个字段相关的条件会被忽略。 |



* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |

  - 示例：

    ```json
    # searchtype为 all、contain时的返回
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 4,
                    "deleted_at": null,
                    "updated_at": "2020-03-04 01:38:20",
                    "created_at": "2020-03-03 23:16:19",
                    "deleted": 0,
                    "uuid": "e0fcf0a6-5d1e-11ea-9db4-000c295dd728",
                    "name": "group1",
                    "group_type": 1,
                    "desc": "this is group2",
                    "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
                    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
                    "start_ip": "172.16.1.40",
                    "end_ip": "172.16.1.60"
                }
            ]
        }
    }
    # searchtype为 single 时的返回
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": 4,
            "deleted_at": null,
            "updated_at": "2020-03-04 01:38:20",
            "created_at": "2020-03-03 23:16:19",
            "deleted": 0,
            "uuid": "e0fcf0a6-5d1e-11ea-9db4-000c295dd728",
            "name": "group1",
            "group_type": 1,
            "desc": "this is group2",
            "network_uuid": "9c705b6e-5213-11ea-9d93-000c295dd728",
            "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
            "start_ip": "172.16.1.40",
            "end_ip": "172.16.1.60"
        }
    }
    ```
    

## 监控管理 ##

### 1、服务节点列表 ###

* URL

	`/api/v1.0/monitor_mgr/nodes/`

* Method

	**GET** 请求，**body** 参数使用 **json** 格式
	
	- 示例
	
	```
	    http://172.16.1.34:50004/api/v1.0/monitor_mgr/nodes/
	```

* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |uuid| str| 节点uuid |
  |name| str| 节点name |
  |type|int| 节点类型：1-计算和主控一体, 2-计算和备控一体, 3-主控, 4-备控,5-计算|
  |ip |str| 节点ip|
  
  - 示例：

    ```json
	{
		"code": 0,
		"msg": "成功",
		"data": {
			"count": 1,
			"next": null,
			"previous": null,
			"results": [{
				"name": "localhost.localdomain",
				"uuid": "bf251c2a-d4c8-40b5-ac4a-227273078170",
				"hostname": "localhost.localdomain",
				"ip": "172.16.1.34",
				"status": "error",
				"type": 1,
				"created_at": "2020-06-27 07:55:52"
			}]
		}
	}
    ```
### 2、获取节点当前信息

* URL

	`/api/v1.0/monitor_mgr/node/current_perf/`

* Method

	**POST** 请求
	
	- 示例
	
	```
	    http://172.16.1.34:50004/api/v1.0/monitor_mgr/node/current_perf/
		{
			"statis_period": 5,
			"node_uuid": "bf251c2a-d4c8-40b5-ac4a-227273078170",
			"is_all_nodes": true
		}
	```
	
	

* Parameters 

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | statis_period    | int  | 统计周期(多少秒)       |
    | node_uuid        | string  | 服务器节点uuid       |
    | is_all_nodes     | bool    | 查询类型，ture -全部节点 , false -单个节点   |
    


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code           | int   | 返回码 |
  |msg            | str   | 请求返回的具体信息 |
  |data           | array| 根据需求返回相应数据 |
  |node_name      | str | 节点名称 |
  |node_uuid      | str | 节点UUID |
  |time           | array | 统计时间轴数据 |
  |cpu_util       | float | 节点cpu使用率，是保留两位小数的float |
  |memory_util    | object | 节点内存信息|
  |percent        | float | 节点内存使用率，是保留两位小数的float|
  |used           | int   | 节点内存使用大小，字节数|
  |disk_io_util   | object| 节点磁盘IO数据|
  |nic_util       | object| 节点网卡IO数据 |
  |read_bytes_avg | int | 在统计周期内读取设备的平均字节数，如果是网卡，读取表示接收数据，也即下行数据，或者下载数据 |
  |write_bytes_avg| int |在统计周期内写入设备的平均字节数，如果是网卡，写入表示发送数据，也即上行数据，或者上传数据 |
  |process_list| array | 节点的进程信息 |
  | pid | int | 进程id|
  | user| str | 进程运行的用户名称|
  | cpu | float | 进程占用cpu的百分比，是保留两位小数的float| 
  | mem | float | 进程占用内存的百分比，是保留两位小数的float|
  | time| str | 进程启动时间 | 
  | command| str|进程名称 |
  
  - 示例：

    ```json
	{
		"code": 0,
		"msg": "成功",
		"data": [{
			"cpu_util": 3.56,
			"disk_io_util": {
				"sda": {
					"read_bytes_avg": 0,
					"write_bytes_avg": 40960
				},
				"sdb": {
					"read_bytes_avg": 0,
					"write_bytes_avg": 0
				}
			},
			"memory_util":{
				"percent":15.00,
				"used":554514841
			},
			"nic_util": {
				"eth0": {
					"ip": "172.16.1.34",
					"read_bytes_avg": 2455,
					"write_bytes_avg": 3152
				},
				"eth1": {
					"ip": "",
					"read_bytes_avg": 353,
					"write_bytes_avg": 0
				}
			},
			"node_name": "localhost.localdomain",
			"node_uuid": "bf251c2a-d4c8-40b5-ac4a-227273078170",
			"process_list": [{
				"command": "systemd",
				"cpu": 0.0,
				"mem": 0.07,
				"pid": 1,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "kthreadd",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 2,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "kworker/0:0H",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 4,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "ksoftirqd/0",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 6,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "migration/0",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 7,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "rcu_bh",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 8,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "rcu_sched",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 9,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "lru-add-drain",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 10,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "watchdog/0",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 11,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}, {
				"command": "watchdog/1",
				"cpu": 0.0,
				"mem": 0.0,
				"pid": 12,
				"time": "2020-07-27 02:03:07",
				"user": "root"
			}],
			"server_time": "2020-07-29 09:48:13"
		}]
	}
    ```
    
### 3、获取节点历史数据

* URL

	`/api/v1.0/monitor_mgr/node/history/`

* Method

	**GET** 请求
	
	- 示例
	
	```
	     http://172.16.1.34:50004/api/v1.0/monitor_mgr/node/history_perf/
		 {
			"statis_hours": 1,
			"step_minutes": 1,
			"node_uuid": "bf251c2a-d4c8-40b5-ac4a-227273078170"
		}
	```
	
	

* Parameters 

    | Name              | Type    | Description      |
    | ----------------- | ------- | ---------------- |
    | node_uuid        | string  | 服务器节点uuid       |
    | statis_hours    | int  | 统计周期(多少小时)       |
    | step_minutes    | int  | 统计时间轴间隔步长(多少分钟)       |
    


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code           | int   | 返回码 |
  |msg            | str   | 请求返回的具体信息 |
  |data           | object| 根据需求返回相应数据 |
  |time           | array | 统计时间轴数据 |
  |cpu_util       | array | 节点cpu使用率，是百分数 |
  |memory_util    | object | 节点内存使用率，是百分数|
  |percent        | array | 节点内存使用率，是百分数|
  |used           | array | 节点内存大小，字节数|	
  |disk_io_util   | object| 节点磁盘IO数据|
  |nic_util       | object| 节点网卡IO数据 |
  |read_bytes_avg | array | 在统计周期内读取设备的平均字节数，如果是网卡，读取表示接收数据，也即下行数据，或者下载数据 |
  |write_bytes_avg| array |在统计周期内写入设备的平均字节数，如果是网卡，写入表示发送数据，也即上行数据，或者上传数据 |


  - 示例：

    ```json
	{
		"code": 0,
		"msg": "成功",
		"data": {
			"cpu_util": [2.92, 2.13, 4.17, 4.5, 2.52, 6.92, 3.99, 3.19, 2.34, 2.42, 6.21, 4.7, 3.55, 7.3, 2.33, 6.27, 4.22, 3.1, 4.67, 4.96, 3.33, 2.88, 2.24, 5.19, 5.44, 8.24],
			"disk_io_util": {
				"sda": {
					"read_bytes_avg": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 141, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					"write_bytes_avg": [165040, 162639, 168500, 156777, 139122, 167229, 214051, 188062, 197949, 204446, 214827, 208048, 205717, 313767, 223161, 226833, 228951, 170407, 213980, 218712, 201692, 209178, 182342, 233824, 180082, 333611]
				},
				"sdb": {
					"read_bytes_avg": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					"write_bytes_avg": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
				}
			},
			"memory_util": {
				"percent": [41.0, 41.0, 41.0, 41.0, 41.0, 41.0, 38.5, 39.0, 40.0, 40.0, 40.0, 40.0, 41.0, 40.5, 39.5, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0],
				"used": [3470503184, 3471520358, 3475352371, 3488648806, 3488381542, 3462369962, 3230376959, 3307686843, 3327516125, 3361171728, 3386184362, 3412164471, 3445491916, 3394738516, 3322831462, 3348263867, 3388396816, 3395048447, 3396021589, 3396524031, 3410380458, 3410481561, 3410631133, 3416733900, 3420731255, 3406981597]
			},
			"nic_util": {
				"eth0": {
					"read_bytes_avg": [1828, 2681, 5636, 7409, 2035, 2671, 4201, 4203, 3601, 4072, 4510, 8034, 5344, 6545, 3617, 3836, 3954, 3837, 3418, 4806, 4446, 4502, 4891, 4618, 8498, 7087],
					"write_bytes_avg": [5078, 6826, 61008, 99782, 5118, 15833, 7756, 8387, 7160, 7553, 7572, 75726, 33268, 46317, 5616, 6021, 6464, 6186, 5548, 33025, 7629, 6714, 8403, 6698, 77435, 22403]
				},
				"eth1": {
					"read_bytes_avg": [84, 136, 168, 120, 105, 106, 98, 140, 105, 96, 350, 139, 92, 109, 136, 179, 170, 230, 152, 210, 160, 158, 157, 165, 99, 89],
					"write_bytes_avg": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
				}
			},
			"node_uuid": "bf251c2a-d4c8-40b5-ac4a-227273078170",
			"time": ["2020-08-06 02:24:00", "2020-08-06 02:25:00", "2020-08-06 02:26:00", "2020-08-06 02:27:00", "2020-08-06 02:28:00", "2020-08-06 02:29:00", "2020-08-06 02:30:00", "2020-08-06 02:31:00", "2020-08-06 02:32:00", "2020-08-06 02:33:00", "2020-08-06 02:34:00", "2020-08-06 02:35:00", "2020-08-06 02:36:00", "2020-08-06 02:37:00", "2020-08-06 02:38:00", "2020-08-06 02:39:00", "2020-08-06 02:40:00", "2020-08-06 02:41:00", "2020-08-06 02:42:00", "2020-08-06 02:43:00", "2020-08-06 02:44:00", "2020-08-06 02:45:00", "2020-08-06 02:46:00", "2020-08-06 02:47:00", "2020-08-06 02:48:00", "2020-08-06 02:49:00"]
		}
	}
    ```



