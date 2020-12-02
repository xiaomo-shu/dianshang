[TOC]

# Web接口文档 #

web端的接口`endpoint`为`http://127.0.0.1:50004/api/v1.0/`

## 终端管理

### 1、终端分组列表接口 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_groups/`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
    - 示例
  
    ```
     http://172.16.1.49:8000/api/v1.0/voi/terminal_mgr/terminal_groups/?type=0
    ```

* Parameters
  | Name |Type|Description|
  | :------- | :----| :-----|
  |type|int |终端组类型，0-未分组，1-教学分组，2-个人分组, 不传获取所有类型|


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  |name| str| 终端组名称|
  |uuid| str|未分组终端为空 |
  |type| int| 终端组类型，0-未分组，1-教学分组，2-个人分组|
  |count|str|终端组终端数量|


  - 示例：

    ```json
    {
        "code": 0,
        "msg": "success",
        "data": [
          {"name":  "503教室", "uuid": "1", "type":  1, "count":  10},
          {"name":  "503办公室","uuid": "2", "type":  2, "count":  5},
          {"name":  "未分组", "uuid": "", "type":  0, "count":  10}
      ]
    }
    ```

### 2、终端列表接口 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminals/`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式
  
* Parameters
  | Name |Type|Description|
  | :------- | :----| :-----|
  |uuid| str|终端组uuid|
  |type| int|终端组类型，0-未分组，1-教学分组，2-个人分组|
  |filter| str|搜索输入框|
  |page |int | 页面 |
  |page_size |str | 当前页条数|

- 示例
  
    ```
     http://172.16.1.49:8000/api/v1.0/voi/terminal_mgr/terminals/?page=1&page_size=10&uuid=xxxxx&type=1
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | count | int |数据总数|
  | group_info| object | 终端组基本信息|
  |name|str|终端组名称|
  |uuid|str| 终端组uuid |
  |uefi_num|int| uefi开机数|
  |windows_num|int| windows开机数|
  |linux_num|int| 维护模式开机数|
  |u_linux_num|int| 部署模式开机数|
  |close_num|int|关机数|
  ||||
  | results | object|当前页的数据数组|
  | name | str |终端名称|
  | terminal_id | int|终端序号|
  | mac | str|终端mac地址|
  | ip | str |终端ip|
  | mask | str |终端子网掩码|
  | platform | str |终端硬件类型|
  | soft_version | str |软件版本信息|
  |status| int| 终端状态，0-离线，1-UEFI, 2-LINUX(维护模式), 3-WINDOWS, 5-U-LINUX(部署模式)|
  |disk_residue | str |剩余磁盘容量 单位:G |
  |destop_group_cnt | int |桌面组数量|
  |download_status | int | 桌面下发状态：0-无下发 1-下发中|
  |download_percent | int | 百分比值: 0 5 100|


  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功",
	    "data": {
            "count": 2,
            "next": null,
            "previous": null,
            "group_info": {
            	"name": "xxxx",
           		"uuid": "xxxxx-xxxx",
           		"uefi_num": 10,
				"windows_num": 10,
				"linux_num": 10,
				"u_linux_num": 11,
           		"close_num": 11
            },
            "results": [
                {
                      "name": "yzy-01",
                      "terminal_id": 1,
                      "mac":"52:54:00:e1:58:14",
                      "ip":"172.16.1.54",
                      "mask":"255.255.255.0",
                      "platform":"ARM",
                      "soft_version":"2.2.2.0",
                      "status": 0,
					  "disk_residue": "15.30",
					  "destop_group_cnt": 3,
					  "download_status": 1,
					  "download_percent": 22
              },
              {
                      "name": "yzy-02",
                      "terminal_id": 2,
                      "mac":"52:54:00:e1:58:15",
                      "ip":"172.16.1.55",
                      "mask":"255.255.255.0",
                      "platform":"ARM",
                      "soft_version":"2.2.2.0",
                      "status": 1,
					  "disk_residue": "15.30",
					  "destop_group_cnt": 3,
					  "download_status": 0,
					  "download_percent": 0
               }
          ]
       }
    }
    ```

### 3、启动终端操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：start|
  | data             |object||
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "start",
        "data": {
          "terminals": [
              {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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

### 4、关闭终端操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：shutdown|
  | data             |object||
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "shutdown",
        "data": {
          "terminals": [
              {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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

### 5、重启终端操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              	| string | 命令参数：reboot|
  | data             	|object||
  | terminals			|array| 选中终端数组|
  | mac           		|str| 终端mac |
  | name             	|string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "shutdown",
        "data": {
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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


### 6、设置终端配置接口 ###
* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：get_setup|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						| str |终端mac|
  |name						| str|终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "get_setup",
        "data": {
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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

### 7、设置终端配置 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              		|string| 命令参数：update_setup|
  | data             		|object	|               |
  |terminals	    		|array	|修选终端数组|
  |mac						|mac	| 终端mac|
  |name						|str	|终端名称|
  |||
  |setup_info				|object	| 设置的配置信息|
  |mode						|object	|模式栏的相关配置|
  |show_desktop_type		|int	|默认登录桌面: 0-教学桌面 1-个人桌面 2-混合桌面|
  |auto_desktop				|int	|自动进入桌面: 0-不自动打开 >0表示进入第几个|
  |program					|object	| 程序tab配置项|
  |server_ip				|str	|服务器ip|

  
  - 示例：

    ```json
    {
        "cmd": "update_setup",
        "data": {
        	"terminals": [
                {"mac":  1, "name":  "yzy-01"},
                {"mac":  2, "name":  "yzy-02"},
                {"mac":  3, "name":  "yzy-03"}
            ],
        	"setup_info":{
                "mode":{
                    "show_desktop_type":1,
                    "auto_desktop":0
                },
                "program":{
                    "server_ip":"172.16.1.33"
                },
                "teach_config": {
                    "room_num": 1,
                    "teach_pc_ip": "192.168.2.23",
                    "top_server_ip": "172.16.1.33",
                    "channel_num": 10
                }
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

### 8、修改终端名称 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               		| string | 命令参数：update_name|
  | data               		|object|			|
  |	terminals				| object| 勾选终端数组|
  | mac 					|str  |  终端mac地址|
  |	id						| int 	|终端序号|
  |	name					| str	|终端名称|
  |prefix					|str 	|终端名称的前缀|
  |postfix					|int	|终端名称后缀是几位数字, 1,2,3|
  |postfix_start			|int	|终端名称后缀的起始数字，默认为1, 可选参数，如果不存在则引用序号|
  |use_terminal_id			|bool	|true-使用终端序号作为文件名后缀|
  
  - 示例：

    ```json
    {
        "cmd": "update_name",
        "data": {
          "terminals": [
          	  {"mac":  "66:7F:A8:85:49:A3", "name":  "yzy-01", "terminal_id": 3},
              {"mac":  "66:7F:A8:85:49:A4", "name":  "yzy-02", "terminal_id": 1},
              {"mac":  "66:7F:A8:85:49:A5", "name":  "yzy-03", "terminal_id": 33}
          ],
		  "use_terminal_id": true,
          "prefix": "yzy",
          "postfix": 1,
          "postfix_start": 1
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
    

### 9、删除终端 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：delete|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						| str |终端mac|
  |name						| str|终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "delete",
        "data": {
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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


### 10、修改编号开始排序 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               		| string | 命令参数：start_sort|
  | data               		|object||
  |group_uuid				|str| 终端分组uuid|
  |index_start				|int| 起始序号|
  
  - 示例：

    ```json
    {
        "cmd": "start_sort",
        "data": {
          "group_uuid": "xxxxx-xxxxx-xxxxx",
          "index_start": 10
       }
    }
    ```


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |batch_num| int  | 排序任务id			|
  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
        	"batch_num": 6
        }
    }
    ```



### 11、停止排序 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：end_sort|
  | data               |object||
  |	batch_num				| int| 排序任务id|
  
  - 示例：

    ```json
    {
        "cmd": "end_sort",
        "data": {
			"group_uuid": "xxxxx-xxxxx-xxxxx",
         	"batch_num": 6
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

### 12、按序重排IP ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：modify_ip|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						|mac |终端mac|
  |name						| str|终端名称|
  |start_ip					|str| 起始ip地址|
  |netmask					|str|子网掩码|
  |gateway					|str|网关|
  |dns1						|str|dns1|
  |dns2						|str|dns2|
  
  - 示例：

    ```json
    {
        "cmd": "modify_ip",
        "data": {
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
          ],
          "start_ip": "172.16.1.20",
          "netmask": "255.255.255.0",
          "gateway": "172.16.1.254",
          "dns1": "8.8.8.8",
          "dns2": "114.114.114.114",
		  "group_uuid": "23423423423kkl242kl34234l23kl",
		  "modify_ip_method": "dhcp"
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
        "data": {
        }
    }
    ```

### 13、移动终端 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：move|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						| str |终端mac|
  |name						| str	|终端名称|
  |group_name				|str	|组名称|
  |group_uuid				|str	|移动到组uuid|

  
  - 示例：

    ```json
    {
        "cmd": "move",
        "data": {
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
          ],
          "group_name": "503办公室",
          "group_uuid": "xxxx-xxx-xxx"
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
  	 		"data": {
  	 		}
    }
    ```

### 14、移动终端分组列表接口 ###


* URL

	`/api/v1.0/voi/terminal_mgr/group/list/`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Parameters



* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |uuid  | str    | 分组uuid|
  |name  | str    | 分组name|

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": [
            {
                "uuid": "a5ad57dd-8428-46fe-beff-ea3812e68394",
                "name": "个人分组"
            },
            {
                "uuid": "",
                "name": "未分组"
            }
        ]
    }
    ```


### 15、排序终端列表接口 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminals/sort/`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Parameters
  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | group_uuid | str    | 终端组uuid|
  


* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |results|array| 终端列表|
  |id| int| 终端id|
  |terminal_id| int | 终端序号|
  |mac|str| 终端mac|
  |ip | str| 终端ip|
  |name| str| 终端name|
  |status| int| 终端状态，0-离线，1-UEFI, 2-LINUX(维护模式), 3-WINDOWS, 5-U-LINUX(部署模式)|
  |group_info | object| 终端组信息|
  |name|str| 终端组名称|
  |uuid|str| 终端组uuid|
  |uefi_num|int| uefi开机数|
  |windows_num|int| windows开机数|
  |linux_num|int| 维护模式开机数|
  |u_linux_num|int| 部署模式开机数|
  |close_num| int| 关机数|
  

  - 示例：

    ```json
    {
    "code": 0,
    "msg": "成功",
    "data": {
        "results": [
            {
                "id": 1496,
                "terminal_id": 2,
                "mac": "AA:BB:CC:01:02",
                "ip": "192.168.1.2",
                "name": "云之翼503教室的终端-02",
                "status": "0"
            },
            {
                "id": 1497,
                "terminal_id": 3,
                "mac": "AA:BB:CC:01:03",
                "ip": "192.168.1.3",
                "name": "云之翼503教室的终端-03",
                "status": "0"
            }
        ],
        "group_info": {
            "name": "教学分组1",
            "uuid": "9d1ad859-c43f-486c-9f3c-d8784371a79f",
			"uefi_num": 10,
			"windows_num": 10,
			"linux_num": 10,
			"u_linux_num": 11,
            "close_num": 2
        }
    }
}
    ```


​    

### 16、终端进入维护模式操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：enter_maintenance_mode|
  | data             |object||
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "enter_maintenance_mode",
        "data": {
          "terminals": [
              {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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
	
### 17、清空终端所有桌面操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：clear_all_desktop|
  | data             |object||
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "clear_all_desktop",
        "data": {
          "terminals": [
              {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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
	
### 18、终端下发桌面操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：send_desktop |
  | data             |object||
  | desktop_groups	 |array| 下发桌面组的uuid列表|
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
    	"cmd": "send_desktop",
    	"data": {
				"terminals": [
    			{"mac": "11111-11111", "name": "yzy-01"}
    		],
    		"desktop_uuid": "7f7344ff-acbe-48f5-86da-506f0c07be77",
    		"desktop_name": "name"
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
	
### 19、取消下发桌面操作 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              | string | 命令参数：cancel_download_desktop|
  | data             |object||
  | terminals		|array| 选中终端数组|
  | mac             |str| 终端mac |
  | name             |string| 终端名称|
  
  - 示例：

    ```json
    {
        "cmd": "cancel_send_desktop",
        "data": {
          "terminals": [
              {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
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
	

### 20、获取终端组数据盘配置接口 ###
* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：get_data_disk_setup|
  | data               |object||
  |group_uuid	    		|str	|终端组UUID|
  
  - 示例：

    ```json
    {
        "cmd": "get_setup",
        "data": {
          "group_uuid": "23214232322323"
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

### 21、设置终端组数据盘配置 ###


* URL

  `/api/v1.0/voi/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd              		|string| 命令参数：update_data_disk_setup|
  | data             		|object	|               |
  |group_uuid	    		|str	|终端组UUID|
  |setup_info				|object	| 设置的配置信息|
  |enable					|int	|是否启用标识：0-不启用， 1-启用|
  |restore					|int	|是否还原标识：0-不还原， 1-还原|
  |size					    |int	|数据盘大小 单位G|
  |desktop_groups	        |array  |共享桌面组UUID列表|

  
  - 示例：

    ```json
    {
        "cmd": "update_data_disk_setup",
        "data": {
        	"group_uuid": "23214232322323",
        	"setup_info":{
                "enable": 1,
				"restore": 1,
				"size": 8,
				"desktop_groups": ["123423421341242341", "22223322222222222"]
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
    
    
 ### 22、VOI终端列表拉取接口 ###


* URL

	`api/v1.0/voi/terminal_mgr/terminal_upgrade/`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
    - 示例
  
    ```
     http://172.16.1.6:50004/api/v1.0/voi/terminal_mgr/terminal_upgrade/
    ``
    ```


* Returns

  | Name |Type|Description|
  | :------- | :----| :-----|
  |code|int | 返回码 |
  |msg |str | 请求返回的具体信息 |
  |data | object| 根据需求返回相应数据 |
  | name | str | 文件包名称|
  |uuid| str|文件包uuid |
  |platform| str| 平台 |
  |os |str|系统类型linux,windows|
  |version|str|版本|
  |count|str|升级数|
  |upload_at|str|上传时间|
  | path | str| 升级包路径|
  


  - 示例：

    ```json
    
    {
        "code": 0,
        "msg": "成功",
        "data": [
            {
                "id": 4,
                "deleted_at": null,
                "updated_at": "2020-08-19 09:30:22",
                "created_at": "2020-08-18 09:30:18",
                "count": 0,
                "terminal_count": 0,
                "upload_at": "2020-08-19 09:30:07",
                "deleted": 0,
                "uuid": "816dcaa1-3e06-4ce5-b5a0-a1b079990f97",
                "name": "windows端",
                "platform": "VOI",
                "os": "windows",
                "version": "",
                "size": 0.0,
                "path": ""
            },
            {
                "id": 9,
                "deleted_at": null,
                "updated_at": "2020-08-20 09:15:00",
                "created_at": "2020-08-20 09:11:23",
                "count": 0,
                "terminal_count": 0,
                "upload_at": "2020-08-20 09:15:00",
                "deleted": 0,
                "uuid": "2d6819c9-6e10-4629-b33a-9eef2e48a341",
                "name": "VOI_os_2.0.0.rar",
                "platform": "VOI",
                "os": "os",
                "version": "2.0.0",
                "size": 6.1,
                "path": "/opt/terminal/soft/VOI_os_2.0.0.rar"
            }
        ]
    }
    ```
    
    
### 23、VOI终端升级包上传 ###


* URL

	`/api/v1.0/voi/terminal_mgr/terminal_upgrade/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

  

* Parameters
	
  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | file  | object    | 上传包文件对象 (文件名：VOI_操作系统_版本.zip)  |
  
  
  
* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  | name | str | 文件包名称|
  |uuid| str|文件包uuid |
  |platform| str| 平台 |
  |os |str|系统类型linux,windows|
  |version|str|版本|
  |count|str|升级数|
  |upload_at|str|上传时间|
  | path | str| 升级包路径|

  - 示例：

    ```json
  {
    "code": 0,
    "msg": "成功",
    "data": {
        "id": 10,
        "uuid": "cfc7ee64-04b2-418e-948d-0bd476214ec6",
        "name": "VOI_OS_2.0.0.1.zip",
        "platform": "VOI",
        "os": "OS",
        "version": "2.0.0.1",
        "path": "/opt/terminal/soft/VOI_OS_2.0.0.1.zip",
        "size": 0.0,
        "upload_at": "2020-08-21T01:46:54.407261+08:00",
        "deleted": 0,
        "deleted_at": null,
        "created_at": "2020-08-21 01:46:54",
        "updated_at": null
    }
}
    ```