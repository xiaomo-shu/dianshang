[TOC]

# Web接口文档 #

web端的接口`endpoint`为`http://127.0.0.1:50004/api/v1.0/`

## 系统管理

### 1、添加系统桌面


* URL

  `/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`create`

  - param - 创建模板的参数

    | Name                   | Type    | Description                                |
    | ---------------------- | ------- | ------------------------------------------ |
    | name(required)         | string  | 模板名称                                   |
    | desc                   | string  | 模板描述                                   |
    | owner_id(required)     | string  | 模板所属用户uuid                           |
    | os_type(required)      | string  | 模板的系统类型，和基础镜像那里保持一致     |
    | classify(required)     | int     | 模板分类：1-教学模板 2-个人模板 3-系统桌面 |
    | pool_uuid(required)    | string  | 资源池uuid                                 |
    | network_uuid(required) | string  | 数据网络uuid                               |
    | subnet_uuid(required)  | string  | 子网uuid                                   |
    | bind_ip                | string  | 模板分配的IP，如果没有则代表系统分配       |
    | vcpu(required)         | int     | 虚拟CPU数目                                |
    | ram(required)          | float   | 虚拟内存，单位为GB                         |
    | iso(required)          | string  | 系统ISO的路径                              |
    | power_on               | string  | 创建后是否开机                             |
    | template               | boolean | 标识是否是模板                             |
    | autostart              | boolean | 是否随节点开机启动                         |
    |                        |         |                                            |
    | system_disk            | dict    | 系统盘信息，具体如下：                     |
    | bus                    | string  | 磁盘驱动类型，目前使用ide                  |
    | size(required)         | int     | 系统盘大小，单位为GB                       |

- 示例：

  ```json
  {
  	"action": "create",
  	"param": {
  		"name": "win10",
  	    "desc": "this is system desktop",
  	    "os_type": "windows_7_x64",
  	    "classify": 3,
  	    "pool_uuid": "64edbc3d-3caf-4ccb-8a84-fb531c25ffca",
  	    "network_uuid": "1c79096b-f498-45c4-8e5b-167fa0aef253",
  	    "subnet_uuid": "b37e167c-e4f6-4baf-b9b2-b9b232b503bf",
  		"vcpu": 4,
  		"ram": 4,
  		"system_disk": {
  			"image_id": "",
  			"bus": "ide",
  	        "size": 100
  		},
  		"iso":  "/root/cn_windows_10_consumer_editions_version_1909_x86_dvd_08dd0d3c.iso",
  		"power_on": true,
  		"template": false,
  		"autostart": false
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

### 2、数据库手动备份


* URL

  `/system/database/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  无


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

### 3、数据库备份删除

一次删除一个


* URL

  `/system/database/`

* Method

  **DELETE** 请求，**body** 参数使用 **json** 格式

* Parameters

  - | Name           | Type   | Description        |
    | :------------- | :----- | :----------------- |
    | id(required)   | int    | 备份记录的数据库id |
    | name(required) | string | 备份的名称         |

  - 示例：

    ```json
    {
    	"id": 3,
    	"name": "20200420194947.bak"
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

### 4、数据库备份设置

设置数据库备份的规则，永远只有一条，新设置的覆盖之前的


* URL

  `/system/crontab/task/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 定时任务的类型，这里是`database`

  - param - 定时任务相关参数，如下：

    | Name                | Type   | Description                                              |
    | :------------------ | :----- | :------------------------------------------------------- |
    | count(required)     | int    | 数据库备份的保留数量                                     |
    | node_uuid(required) | string | 备份保留位置的节点uuid，目前默认固定在主节点             |
    | status(required)    | int    | 0-未启用 1-启用                                          |
    | cron                | dict   | 备份周期相关的设置，只有status为1时才需要，包括以下字段  |
    | type(required)      | string | 包括`day`、`week`、`month`，分别表示按天、按周、按月备份 |
    | values              | list   | 按周备份时，选择在哪几天进行备份，星期一为0，以此类推    |
    | hour                | int    | 表示执行的具体小时                                       |
    | minute              | int    | 表示执行的具体分钟                                       |

  - 示例：

    ```json
    # 按天备份
    {
    	"action": "database",
    	"param": {
    		"count": 8,
            "node_uuid": "6fc1ee80-ae0d-4bfb-aca8-08d3ca34304e",
            "status": 1,
            "cron": {
                "type": "day",
                "hour": 11,
                "minute": 5
            }
    	}
    }
    # 按周备份，表示每周一11:55分执行
    {
    	"action": "database",
    	"param": {
    		"count": 8,
            "node_uuid": "6fc1ee80-ae0d-4bfb-aca8-08d3ca34304e",
            "status": 1,
            "cron": {
                "type": "week",
                "values":[0],
                "hour": 11,
                "minute": 55
            }
    	}
    }
    # 按月备份，默认是每个月的28号执行
    {
    	"action": "database",
    	"param": {
    		"count": 8,
            "node_uuid": "6fc1ee80-ae0d-4bfb-aca8-08d3ca34304e",
            "status": 1,
            "cron": {
                "type": "month",
                "hour": 13,
                "minute": 43
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

### 5、数据库备份下载

一次下载一个


* URL

  `/system/database/download/`

* Method

  **GET** 请求

* Parameters

  - id- 数据库备份的ID

  - 示例：

    ```json
    http://172.16.1.14:50004/api/v1.0/system/database/download/?id=4
    ```


* Returns

  文件对象

### 6、数据库备份分页查询 ###


* URL

  ` /system/database/?page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | page      | int  | 页数        |
  | page_size | int  | 分页大小    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | id         | string | 数据库备份的ID                         |
  | status     | int    | 备份成功与否，0-成功，1-失败           |
  | ipaddr     | string | 数据库备份的名称                       |
  | node_uuid  | string | 数据库备份所在节点的uuid               |
  | path       | string | 数据库备份在服务器上的地址             |
  | size       | float  | 数据库备份的大小，单位为MB             |
  | type       | int    | 数据库备份类型，0-手动备份，1-自动备份 |
  | created_at | string | 数据库备份的时间                       |

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
                    "id": 4,
                    "deleted_at": null,
                    "updated_at": "2020-04-20 19:53:02",
                    "created_at": "2020-04-20 19:53:02",
                    "status": 0,
                    "deleted": 0,
                    "name": "20200420195302.bak",
                    "node_uuid": "6fc1ee80-ae0d-4bfb-aca8-08d3ca34304e",
                    "path": "/opt/db_back/20200420195302.bak",
                    "size": 0.06,
                    "type": 0
                }
            ]
        }
    }
    ```

### 7、桌面定时任务添加

添加桌面定时开关机任务


* URL

  `/system/crontab/task/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 定时任务类型，这里是`desktop`

  - param - 定时任务相关参数，如下：

    | Name             | Type   | Description                                                 |
    | :--------------- | :----- | :---------------------------------------------------------- |
    | name(required)   | string | 定时任务名称                                                |
    | desc             | string | 定时任务的描述                                              |
    | status(required) | int    | 0-未启用，1-启用                                            |
    |                  |        |                                                             |
    | cron(required)   | list   | 备份周期相关的设置，只有status为1时才需要，每项包括以下字段 |
    | cmd(required)    | string | 命令，on-开机，off-关机                                     |
    | type(required)   | string | 桌面定时任务只有按周，所以为`week`                          |
    | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                   |
    | hour(required)   | int    | 执行的具体时辰                                              |
    | minute(required) | int    | 执行的具体分钟                                              |
    |                  |        |                                                             |
    | data             | list   | 表示需要操作的桌面，只包括教学桌面，每一项包含字段如下：    |
    | desktop_uuid     | string | 桌面组uuid                                                  |
  | instances        | list   | 桌面的列表，每一个桌面又包含如下字段：                      |
    | uuid             | string | 桌面uuid                                                    |
  | name             | string | 桌面名称                                                    |
  
  - 示例：
  
    ```json
    {
    	"action": "desktop",
    	"param": {
    		"name": "定时关机2",
    		"desc": "hhh",
    	    "status": 1,
    	    "cron": [
    	    		{
    	    			"cmd": "on",
    			        "type": "week",
    			        "values": [0,1,2],
    			        "hour": 8,
    			        "minute": 58
    			    },
    			    {
    			    	"cmd": "off",
    			        "type": "week",
    			        "values": [0,1,2],
    			        "hour": 20,
    			        "minute": 58
    			    }
    	    	],
    	    "data": [
    	    		{
    	    			"desktop_uuid": "a086ca8e-0a6b-4c93-817c-2a31178bda91",
    	    			"instances": [
    	    					{
    	    						"uuid": "ad4376dc-9433-429a-93d8-c7ecf417957e",
    	    						"name": "PC1"
    	    					}
    	    				]
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

### 8、定时任务修改 ###


* URL

  `/system/crontab/task/`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name             | Type   | Description                                                  |
  | :--------------- | :----- | :----------------------------------------------------------- |
  | uuid(required)   | string | 定时任务uuid                                                 |
  | name(required)   | string | 原来的定时任务名称                                           |
  |                  |        |                                                              |
  | value(required)  | dict   | 修改后的定时任务相关的信息，包括如下字段：                   |
  | name(required)   | string | 修改后的定时任务名称                                         |
  | desc             | string | 修改后的描述                                                 |
  | status(required) | int    | 0-未启用，1-启用                                             |
  |                  |        |                                                              |
  | cron(required)   | list   | 列表，只有status为1时才需要，表示修改后包括的定时任务情况。每项包括以下字段 |
  | uuid             | string | 如果是修改了已有的某一项任务，则需要提供原先任务的uuid。如果没有uuid值，表示该任务是新加的 |
  | cmd(required)    | string | 命令，on-开机，off-关机                                      |
  | type(required)   | string | 桌面定时任务只有按周，所以为`week`                           |
  | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                    |
  | hour(required)   | int    | 执行的具体时辰                                               |
  | minute(required) | int    | 执行的具体分钟                                               |
  |                  |        |                                                              |
  | data             | list   | 只有status为1时才需要。表示需要操作的桌面，只包括教学桌面，每一项包含字段如下： |
  | desktop_uuid     | string | 桌面组uuid                                                   |
  | instances        | list   | 桌面的列表，每一个桌面又包含如下字段：                       |
  | uuid             | string | 桌面uuid                                                     |
  | name             | string | 桌面名称                                                     |

- 示例：

  ```json
  {
  	"uuid": "e21438cf-2df3-48cf-82b3-318e4e36c801",
  	"name": "定时关机2",
  	"value": {
  		"name": "定时关机1",
  		"desc": "ttt",
  	    "status": 1,
  	    "cron": [
  	    		{
  	    			"uuid": "d03e19fa-de3a-43fb-a960-eae51fade279",
  	    			"cmd": "off",
  			        "type": "week",
  			        "values": [0,2],
  			        "hour": 9,
  			        "minute": 58
  			    },
  			    {
  			    	"cmd": "on",
  			        "type": "week",
  			        "values": [0,1],
  			        "hour": 21,
  			        "minute": 58
  			    }
  	    	],
  	    "data": [
  	    		{
  	    			"desktop_uuid": "a086ca8e-0a6b-4c93-817c-2a31178bda91",
  	    			"instances": [
  	    					{
  	    						"uuid": "ad4376dc-9433-429a-93d8-c7ecf417957e",
  	    						"name": "PC1"
  	    					}
  	    				]
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

### 9、定时任务分页查询 ###


* URL

  ` /system/crontab/task/?cron_type=0&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name                | Type | Description                                                  |
  | ------------------- | ---- | ------------------------------------------------------------ |
  | cron_type(required) | int  | 定时任务的分类，0-数据库定时任务，1-桌面定时任务，2-主机定时任务，3-终端定时任务 |
  | page                | int  | 页数                                                         |
  | page_size           | int  | 分页大小                                                     |


* Returns

  | Name      | Type   | Description                            |
  | :-------- | :----- | :------------------------------------- |
  | uuid      | string | 定时任务的uuid                         |
  | status    | int    | 定时任务是否启用，0-未启用，1-启用     |
  | name      | string | 定时任务的名称                         |
  | desc      | string | 定时任务的描述                         |
  |           |        |                                        |
  | detail    | dict   | 关于定时任务的具体信息                 |
  | count     | int    | 数据库备份特有的，保存数量             |
  | host_uuid | string | 备份所在的节点                         |
  | hour      | int    | 备份执行的具体时辰                     |
  | minute    | int    | 备份执行的具体分钟                     |
  | cycle     | string | 定时任务的类型，`day`、`week`、`month` |
| values    | list   | 如果是按周执行，则这里包括一周的哪几天 |
  
- 示例：
  
    ```json
    # http://172.16.1.14:50004/api/v1.0/system/crontab/task/?cron_type=0
    # 以下是获取数据库定时任务的返回值
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "03c6d826-432e-4db1-aef7-43d98382b141",
                    "name": "db_back_task:20200424155631",
                    "desc": "",
                    "details": {
                        "count": 8,
                        "host_uuid": "6fc1ee80-ae0d-4bfb-aca8-08d3ca34304e",
                        "hour": 12,
                        "minute": 5,
                        "cycle": "week",
                        "values": [
                            1
                        ]
                    },
                    "status": 1
                }
            ]
        }
    }
    # http://172.16.1.14:50004/api/v1.0/system/crontab/task/?cron_type=1
    # 以下是获取的桌面定时任务信息
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 1,
            "next": null,
            "previous": null,
            "results": [
                {
                    "uuid": "c7e3fd85-832c-42ab-ada5-1af24ade2f0e",
                    "name": "定时关机2",
                    "desc": "hhh",
                    "details": [
                        {
                            "uuid": "d5b9e33f-4063-4011-b88f-7f98705f3136",
                            "cmd": "on",
                            "data": [
                                {
                                    "desktop_uuid": "84481bfc-5506-4b4a-ad66-88e9e74bfc04",
                                    "instances": [
                                        {
                                            "uuid": "a2dd9450-dc55-417d-b7cb-55d5fbe4b66d",
                                            "name": "PC1"
                                        }
                                    ]
                                }
                            ],
                            "hour": 8,
                            "minute": 58,
                            "cycle": "week",
                            "values": [
                                0,
                                1,
                                2
                            ]
                        },
                        {
                            "uuid": "2d316f4d-a364-48cd-aaaf-89a4961c13f4",
                            "cmd": "off",
                            "data": [
                                {
                                    "desktop_uuid": "84481bfc-5506-4b4a-ad66-88e9e74bfc04",
                                    "instances": [
                                        {
                                            "uuid": "a2dd9450-dc55-417d-b7cb-55d5fbe4b66d",
                                            "name": "PC1"
                                        }
                                    ]
                                }
                            ],
                            "hour": 20,
                            "minute": 58,
                            "cycle": "week",
                            "values": [
                                0,
                                1,
                                2
                            ]
                        }
                    ],
                    "status": 1
                }
            ]
        }
    }
    ```

### 7、系统管理员分页查询 ###


* URL

  ` /api/v1.0/admin_users/?page=1&page_size=10&username=&role= `

* Method

  **GET** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | page      | int  | 页数        |
  | page_size | int  | 分页大小    |
  | username | str  | 用户名查询，可选    |
  | role | int  | 角色筛选，可选    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | id         | string | 管理员账号ID                         |
  | username     | int    |账号名称           |
  | real_name     | string | 真实姓名                       |
  | email  | string | 邮箱               |
  | last_login       | string | 最近一定登录时间             |
  | is_superuser       | float  | 是否为超级管理员，0-否，1-是           |
  | is_active       | int    | 是否激活，0-否，1-是 |
  | desc | string | 描述                       |
  | role | int | 角色ID                       |
  | role_name | string |角色名称                       |

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
                    "username": "admin",
                    "real_name": "123",
                    "email": "11@qq.com",
                    "last_login": "2020-05-06 09:19:24",
                    "login_ip": "172.16.1.47",
                    "is_superuser": 0,
                    "is_active": 0,
                    "desc": null,
                    "role": 1,
                    "role_name": null,
                    "created_at": "2020-03-07 23:49:53",
                    "updated_at": null,
                    "deleted_at": null
                }
            ]
        }
    }
    ```

### 8、添加系统管理员 ###


* URL

  ` /api/v1.0/admin_users/`

* Method

  **POST** 请求
  ```json
      {
          "username": "admin12",
          "real_name": "1233",
          "email": "11@qq.com",
          "desc": "测试",
          "role": 1
      }
  ```
```

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | username      | int  | 账号      |
  | real_name | int  | 真实名称    |
  |password| str|密码|
  | email | str  | 邮箱地址    |
  | role | int  | 角色id    |
  | desc | str  | 描述    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | id         | string | 管理员账号ID                         |
  | username     | int    |账号名称           |
  | real_name     | string | 真实姓名                       |
  | email  | string | 邮箱               |
  | last_login       | string | 最近一定登录时间             |
  | is_superuser       | float  | 是否为超级管理员，0-否，1-是           |
  | is_active       | int    | 是否激活，0-否，1-是 |
  | desc | string | 描述                       |
  | role | int | 角色ID                       |
  | role_name | string |角色名称                       |

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
                    "username": "admin",
                    "real_name": "123",
                    "email": "11@qq.com",
                    "last_login": "2020-05-06 09:19:24",
                    "login_ip": "172.16.1.47",
                    "is_superuser": 0,
                    "is_active": 0,
                    "desc": null,
                    "role": 1,
                    "role_name": null,
                    "created_at": "2020-03-07 23:49:53",
                    "updated_at": null,
                    "deleted_at": null
                }
            ]
        }
    }
```


### 9、角色查询接口  ###


* URL

  ` /api/v1.0/roles/?page=1&page_size=10`

* Method

  **GET** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | page      | int  | 页数        |
  | page_size | int  | 分页大小    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | id         | string | 管理员账号ID                         |
  | user_count     | int    |成员数量           |
  | role     | string | 角色名称                       |
  | desc  | string | 描述               |
  | enable       | int | 是否启用，0-否，1-是             |
  | created_at       | str  | 添加时间           |

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
                    "user_count": 1,
                    "deleted_at": null,
                    "updated_at": "2020-05-06 19:41:15",
                    "created_at": "2020-05-06 19:41:17",
                    "deleted": 0,
                    "role": "超级管理员",
                    "enable": 1,
                    "desc": "超级管理员默认角色",
                    "menus": []
                }
            ]
        }
    }
    ```


### 10、管理员名称查询  ###


* URL

  ` /api/v1.0/admin_user/name_check/?`
  
* Method

  **POST** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | username      | int  | 账户名称        |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | code         | int | 返回码                        |
  | msg     | str    |   返回信息  |


  - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功"
    }
    ```


### 11、管理员编辑  ###


* URL

  ` /api/v1.0/admin_users/`
  
* Method

  **PUT** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  |user_id| int| 用户id|
  | username      | int  | 账号      |
  | real_name | int  | 真实名称    |
  |password| str|密码|
  | email | str  | 邮箱地址    |
  | role | int  | 角色id    |
  | desc | str  | 描述    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  | code         | int | 返回码                        |
  | msg     | str    |   返回信息  |


  - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功"
    }
    ```

### 12、操作日志列表查询接口  ###


* URL

  ` http://172.16.1.29:50004/api/v1.0/system/logs/operation/?page=1&page_size=3&user_id=1&date=2020-05-05`

* Method

  **GET** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | page      | int  | 页数        |
  | page_size | int  | 分页大小    |
  | user_id | int| 操作人员id|
  | date  | str| 日期，如：2020-05-05|


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  |id				|int 	| 	编号	|
  | user_id         | string | 管理员账号ID                         |
  | user_name     | int     |	账号名称           |
  | user_ip     | string 	| 	IP地址                       |
  | content  | string 		| 操作记录               |


  - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 28,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 2,
                    "deleted_at": null,
                    "updated_at": "2020-05-05 09:37:03",
                    "created_at": "2020-05-05 09:37:03",
                    "deleted": 0,
                    "user_id": 1,
                    "user_name": "admin",
                    "user_ip": "172.16.1.56",
                    "content": "用户：admin 在ip: 172.16.1.56 处登录",
                    "result": "成功",
                    "module": "default"
                }
            ]
        }
    }
    ```
    
### 13、操作日志列表删除接口  ###


* URL

  ` http://172.16.1.29:50004/api/v1.0/system/logs/operation/`

* Method

  **DELETE** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | ids      | array  | 操作id数组        |
  | del_range | str  | 删除时间范围，"week"-一周前，"month"-一月前，"three_month"-三月前，"half_year"-半年前，"year"-一年前    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  |code|int|返回码|
  |msg| str| 返回信息|


  - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功"
    }
    ```
    
    

### 14.系统日志导出


* URL

  `http:172.16.1.29:50004/api/v1.0/system/logs/export/`
  
 * Method

   **POST** 请求,**body** 参数使用 **json** 格式
   
* Parameters

  | Name                   | Type   | Description |
  | ---------------------- | ------ | ----------- |
  | start_date             | string | 开始时间     |
  | end_date               | string | 结束时间     |

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
         "message": "success",
         "data": {
             "down_url": "http://172.16.1.40:50004/api/v1.0/system/logs/export/?file=/var/log/yzy_kvm/log_down/2020-06-23.tar.gz"
        }
    }
    ```
    
    

### 15.警告日志列表查询接口


* URL

  `http://172.16.1.29:50004/api/v1.0/system/logs/warn/?page=1&page_size=10&option=1&date=2020-06-24`
  
* Method
  **GET** 请求
  
* Parameters
  
  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | page                | int    | 页码         |
  | page_size           | int    | 分页大小     |
  | option              | int    | 警告项       |
  | date                | string | 操作日期     |
  
* Returns

  | Name                   | Type   | Description |
  | ---------------------- | ------ | ----------- |
  | number_id              | int    | 编号         |
  | warning_items          | int    | 警告项       |
  | operation_date         | string | 操作日期      |
  | ip_address             | string | ip地址       |
  | warning_content        | string | 警告内容      |
  
    - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功",
        "data": {
            "count": 28,
            "next": null,
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "deleted_at": null,
                    "operation_date": "2020-05-05 09:37:03",
                    "created_at": "2020-05-05 09:37:03",
                    "deleted": 0,
                    "number_id": 1,
                    "warning_items": "CPU利用率",
                    "ip_address": "172.16.1.56",
                    "warning_content": "CPU利用率过高: XenServer01",
                    "is_clear": 0
                }
            ]
        }
    }
    ```
  
  
  
### 16.警告日志清除接口


* URL

  ` http://172.16.1.29:50004/api/v1.0/system/logs/warn/`

* Method

  **DELETE** 请求

* Parameters

  | Name      | Type | Description |
  | --------- | ---- | ----------- |
  | ids      | array  | 操作id数组   |
  | del_range | str  | 删除时间范围，"week"-一周前，"month"-一月前，"three_month"-三月前，"half_year"-半年前，"year"-一年前    |


* Returns

  | Name       | Type   | Description                            |
  | :--------- | :----- | :------------------------------------- |
  |code|int|返回码|
  |msg| str| 返回信息|


  - 示例：

    ```json
      {
        "code": 0,
        "msg": "成功"
    }
    ```


 ### 17.获取VOI终端离线密码


* URL

  `http:172.16.1.29:50004/api/v1.0/system/voi_setup/`
  
 * Method

   **GET** 请求,**body** 无

* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | offline_passwd | str | 终端离线密码 |
  
  - 示例：
  
    ```json
    {
         "code": 0,
         "message": "success",
         "data": {
             "offline_passwd": "234232"
        }
    }
    ```
    
    
    
### 18、日志定时清理任务

添加日志定时清理任务


* URL

  `/system/logs/setup/cron/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 定时任务类型，根据不同的数值创建不同的定时任务`warning` 警告日志定时任务清理
                                                    `operation` 操作日志定时任务清理

  - param - 定时任务相关参数，如下：

    | Name             | Type   | Description                                                 |
    | :--------------- | :----- | :---------------------------------------------------------- |
    | status(required) | int    | 0-未启用，1-启用                                            |                                                 |
    | cron(required)   | dict   | 备份周期相关的设置，只有status为1时才需要，每项包括以下字段 |
    | type(required)   | string | 定时任务周期，如：day, week, month                          |
    | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                   |
    | hour(required)   | int    | 执行的具体时辰                                              |
    | minute(required) | int    | 执行的具体分钟                                              |                                                 |
  
  - 示例：
  
    ```json
    {
    	"action": "operation",
    	"param": {
    	    "status": 1,
    	    "cron": 
    	    		{
    			        "type": "week",
    			        "values": [0,1,2],
    			        "hour": 8,
    			        "minute": 58
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
    
    
    
### 19、更新日志定时清理任务

更新日志定时清理任务


* URL

  `/system/logs/setup/cron/`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 定时任务类型，`warning` 更新警告日志定时清理任务
                         `operation` 更新操作日志定时任务
  - param - 定时任务相关参数，如下：

    | Name             | Type   | Description                                                 |
    | :--------------- | :----- | :---------------------------------------------------------- |
    | status(required) | int    | 0-未启用，1-启用                                            |                                                 |
    | uuid(required)   | str    | 定时任务详情uuid                                           |                                                 |
    | cron(required)   | dict   | 备份周期相关的设置，只有status为1时才需要，每项包括以下字段 |
    | type(required)   | string | 定时任务周期，如：day, week, month                          |
    | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                   |
    | hour(required)   | int    | 执行的具体时辰                                              |
    | minute(required) | int    | 执行的具体分钟                                              |                                                 |
  
  - 示例：
  
    ```json
    {
    	"action": "warning",
    	"param": {
    	    "status": 1,
            "uuid": "a84e2270-10b2-45e1-9c1c-4c6f530e14fa",
    	    "cron": 
    	    		{
    			        "type": "week",
    			        "values": [0,1,2],
    			        "hour": 8,
    			        "minute": 58
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
    
    
    
### 20、告警设置数据获取接口

* URL

  `/system/logs/warn/setup/`
  
* Method

  **GET** 请求
  
* Returns

  | Name       | Type   | Description |
  | -----------| ------ | ----------- |
  | code       | int    | 返回码         |
  | msg        | int    | 请求返回具体信息       |
  | data       | object | 根据需求返回相应的数据       |
  | control    | object | 主控名称及uuid       |
  | node_name  | array | 所有的资源池名称和计算节点名称和uuid       |
  
  - 示例：
  
    ```json
    {
      "code": 0,
      "msg": "成功",
      "data": null,
      "control": {
        "name": "mian_29ds1",
        "uuid": "26cb46d4-bea7-425d-bbf6-636f79570401"
      },
      "node_name": [
        {
          "name": "default",
          "node_name": [
            {
              "name": "mian_29",
              "uuid": "7e4d5027-7979-4ed2-ad25-2e88aa84c81e"
            },
            {
              "name": "main_29",
              "uuid": "ea13935a-1751-409f-a41a-c69bfc7ee7a1"
            }
          ]
        },
        {
          "name": "2",
          "node_name": [
            {
              "name": "mian_29",
              "uuid": "7e4d5027-7979-4ed2-ad25-2e88aa84c81e"
            },
            {
              "name": "main_29",
              "uuid": "ea13935a-1751-409f-a41a-c69bfc7ee7a1"
            }
          ]
        }
      ]
    }
    ```
    
    
    
### 21、创建告警设置选项接口

* URL
  `/system/logs/warn/setup/`
  
* Method
  
  **POST** 请求，**body** 参数使用 **json** 格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | status              | int    | 状态：0、未启用，1、启用         |
  | option              | object | 选择的告警项 格式："option": {"cpu": {"ratio": 95, "time": 10}, "memory": {"ratio": 90, "time": 5}}    |
  
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
    
    
    
### 22、更新告警设置选项接口

* URL
  `/system/logs/warn/setup/`
  
* Method
  
  **PUT** 请求，**body** 参数使用 **json** 格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | status              | int    | 状态：0、未启用，1、启用         |
  | option              | object | 选择的告警项     |
  | host                | str    | 选择的主机       |
  
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



### 23、获取定时任务设置详情接口

* URL

  `system/logs/setup/cron/?uuid=a84e2270-10b2-45e1-9c1c-4c6f530e14fa`

* Method

  **GET** 请求
  
* Returns

  | Name       | Type   | Description |
  | -----------| ------ | ----------- |
  | code       | int    | 返回码         |
  | msg        | int    | 请求返回具体信息       |
  | data       | object | 根据需求返回相应的数据       |
  
  - 示例：

    ```json
    {
      "code": 0,
      "msg": "成功",
      "data": {
        "task_uuid": "04e8234e-0f93-4765-8780-86039fe19513",
        "hour": 6,
        "minute": 30,
        "cycle": "week",
        "values": "6",
        "status": 0
      }
    }
    ```
    
    
    
### 24、终端定时任务添加

* URL
  `system/crontab/task/`
  
* Method
  **POST** 请求，**body** 参数使用 **json** 格式
  
* Parameter

  | Name             | Type   | Description                                                 |
  | :--------------- | :----- | :---------------------------------------------------------- |
  | name(required)   | string | 定时任务名称                                                |
  | desc             | string | 定时任务的描述                                              |
  | status(required) | int    | 0-未启用，1-启用                                            |
  | cron(required)   | list   | 备份周期相关的设置，只有status为1时才需要，每项包括以下字段 |
  | cmd(required)    | string | 命令，on-开机，off-关机                                     |
  | type(required)   | string | 终端定时任务只有按周，所以为`week`                          |
  | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                   |
  | hour(required)   | int    | 执行的具体时辰                                              |
  | minute(required) | int    | 执行的具体分钟                                              |
  |                  |        |                                                             |
  | mac              | string | 终端mac地址                                                 |
  | name             | string | 终端名称                                                    |
  
  - 示例：
  
    ```json
    {
        "action": "terminal",
        "param": {
            "name": "terminal_test1",
            "desc": "test",
            "cmd": "off",
            "status": 1,
            "cron": {
                "type": "week",
                "values": [0,1,2],
                "hour": 1,
                "minute": 10
            },
            "data": [
                {
                    "name": "YZY-134",
                    "mac": "00:0C:29:A1:FF:9A"
                }
            ]
        }
    }
    
  ```
  
    
    
### 25、编辑终端定时关机

* URL
  `/system/crontab/task/`
  
* Method
  **PUT** 请求，**body** 参数使用 **json**格式
  
* Parameter

  | Name             | Type   | Description                                                  |
  | :--------------- | :----- | :----------------------------------------------------------- |
  | uuid(required)   | string | 定时任务uuid                                                 |
  | name(required)   | string | 原来的定时任务名称                                           |
  | disposable       |string  |是否单次执行                                                |
  | value(required)  | dict   | 修改后的定时任务相关的信息，包括如下字段：                   |
  | name(required)   | string | 修改后的定时任务名称                                         |
  | desc             | string | 修改后的描述                                                 |
  | status(required) | int    | 0-未启用，1-启用                                             |
  |                  |        |                                                              |
  | cron(required)   | list   | 列表，只有status为1时才需要，表示修改后包括的定时任务情况。每项包括以下字段 |
  | uuid             | string | 如果是修改了已有的某一项任务，则需要提供原先任务的uuid。如果没有uuid值，表示该任务是新加的 |
  | cmd(required)    | string | 命令，on-开机，off-关机                                      |
  | type(required)   | string | 桌面定时任务只有按周，所以为`week`                           |
  | values(required) | list   | 每一周的哪几天执行，0表示星期一，以此类推                    |
  | hour(required)   | int    | 执行的具体时辰                                               |
  | minute(required) | int    | 执行的具体分钟                                               |
  |                  |        |                                                              |
  | data             | list   | 只有status为1时才需要。表示需要操作的终端，只包括教学终端，每一项包含字段如下： |
  | mac              | string | 终端mac地址                                                     |
  | name             | string | 终端名称                                                     |
  
  - 示例：
    ```json
    {
        "action": "terminal",
        "name": "terminal_test",
        "disposable": "disposable",
        "uuid": "b8e07768-d694-4e2b-8e8b-fc1416df944f",
        "value": {
            "name": "terminal_test",
            "desc": "test",
            "status": 1,
            "cron": [{
                "uuid": "d7c4d0da-19e0-42de-a5d9-64d5da95d4e3",
                "cmd": "off",
                "type": "week",
                "values": [0,2,3],
                "hour": 2,
                "minute": 38
            }],
            "data": [
                {
                    "mac": "00:0C:29:A1:FF:9A",
                    "name": "main_40"
                }
            ]
    }
    }
    ```
    
    
    
### 26、管理员删除功能

* URL

  `admin_users/`
  
* Method

  **DELETE** 请求，**body** 参数使用 **json**格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | id                  | int    |管理员id      |
  
  - 示例：
  ```json
  {
    "id": 1
    }
    ```



### 27、角色管理新建功能

* URL

  `roles/`
  
* Method

  **POST** 请求，**body** 参数使用 **json**格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | role                | string |角色名称      |
  | desc                | string |描述信息      |
  
  - 示例：
  ```json
  {
    "role": "user",
    "desc": "test"
    }
    ```
  
  
  
### 28、角色管理编辑功能

* URL

  `roles/`
  
* Method

  **PUT** 请求，**body** 参数使用 **json**格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  |id                   | int    |角色id       |
  | role                | string |角色名称      |
  | desc                | string |描述信息      |
  
  - 示例：
  ```json
  {
    "id": 1,
    "role": "user",
    "desc": "test"
    }
    ```
  
  
  
### 29、角色管理删除功能

* URL

  `roles/`
  
* Method

  **DELETE** 请求，**body** 参数使用 **json**格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | id                  | int    |角色id        |
  
  - 示例：
  ```json
  {
    "id": 1
    }
    ```
  
  
  
### 30、禁/启用功能

* URL

  `/admin_user/enable/`
  
* Method

  **POST** 请求，**body** 参数使用 **json**格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | id                  | int    |id信息        |
  | enable              | int    |是否启用：0-禁用，1-启用        |
  | option              | string |标志模块：admin_user-管理员模块，role-角色模块        |
  
  - 示例：
  ```json
  {
    "id": 1,
    "enable": 1,
    "option": "admin_user"
    }
    ```
  
  
### 31、任务信息记录查询

* URL

  `/system/task_info?search_type=all&status=running&time_frame=week`
  
* Method 
  
  **GET** 请求，**body** 参数使用 **json**格式
  
* Returns

  | Name       | Type   | Description |
  | -----------| ------ | ----------- |
  | code       | int    | 返回码         |
  | msg        | int    | 请求返回具体信息       |
  | data       | object | 根据需求返回相应的数据       |
  
  - 示例：
  ```json
      {
      "code": 0,
      "msg": "成功",
      "data": [
        {
          "name": "桌面组批量关机",
          "status": "complete",
          "created_at": "2020-10-16 14:47:00"
        },
        {
          "name": "桌面组批量开机",
          "status": "complete",
          "created_at": "2020-10-16 14:41:00"
        },
        {
          "name": "桌面定时开关机",
          "status": "queue",
          "created_at": "2020-10-16 14:39:56"
        },
        {
          "name": "桌面组批量关机",
          "status": "complete",
          "created_at": "2020-10-16 14:02:00"
        },
        {
          "name": "桌面定时开关机",
          "status": "complete",
          "created_at": "2020-10-16 14:00:29"
        }
      ]
    }
  ```
  


### 32 服务器时间修改

* URL
  `api/v1.0/system/strategy/system_time` 
  
* Method

  **POST** 请求 **body** 参数使用 **json** 格式
  
* Parameters

  | Name                | Type   | Description |
  | --------------------| ------ | ----------- |
  | date                | string |输入的日期时间 |
  | time_zone           | string |选择的时区        |
  | ntp_server          | string |需要同步的服务器地址|
  | check               | bool   |是否勾选|
  
    - 示例：
  ```json
  {
    "date": "2020-11-24 17:21:00",
    "time_zone": "Asia/Shanghai",
    "ntp_server": "cn.ntp.org.cn",
    "check": "True"
    }
    ```