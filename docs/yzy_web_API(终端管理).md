[TOC]

# Web接口文档 #

web端的接口`endpoint`为`http://127.0.0.1:50004/api/v1.0/`

## 终端管理

### 1、终端分组列表接口 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_groups/`

* Method

	**GET** 请求，**body** 无 **json** 格式
  
    - 示例
  
    ```
     http://172.16.1.49:8000/api/v1.0/terminal_mgr/terminal_groups/?type=0
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

  `/api/v1.0/terminal_mgr/terminals/`

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
     http://172.16.1.49:8000/api/v1.0/terminal_mgr/terminal_groups/?page=1&page_size=10&uuid=xxxxx&type=1
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
  |open_num|int| 开机数|
  |close_num|int|关机数|
  ||||
  | results | object|当前页的数据数组|
  | name | str |终端名称|
  | terminal_id | int|终端序号|
  | mac | str|终端mac地址|
  | ip | str |终端ip|
  | mask | str |终端子网掩码|
  | platform | str |终端硬件类型|
  |username|str|接入用户名，个人终端才有|
  | soft_version | str |软件版本信息|
  | soft_version | str |软件版本信息|
  | instance | str |桌面名称|
  |status| int| 终端状态，0-离线，1-在线|
  | connect_time | str |接入时间|
  | connect_length | str |接入时长|
  | connect_length | str |接入时长|
  | resolution | str |分辨率|
  


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
           		"open_num": 10,
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
                      "instance": "PC101",
                      "status": 0,
                      "username":"user01",                      							  "connect_time": "2020-04-08 13:51:00",
                      "connect_length":"1小时20分钟",
                      "resolution": "1920*1680"
              },
              {
                      "name": "yzy-02",
                      "terminal_id": 2,
                      "mac":"52:54:00:e1:58:15",
                      "ip":"172.16.1.55",
                      "mask":"255.255.255.0",
                      "platform":"ARM",
                      "soft_version":"2.2.2.0",
                      "instance": "PC103",
                      "status": 1,
                      "username":"user02",
                      "connect_time": "2020-04-08 13:51:00",
                      "connect_length":"1小时20分钟",
                      "resolution": "1920*1680"
               }
          ]
       }
    }
    ```


### 3、关闭终端操作 ###


* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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

### 4、重启终端操作 ###


* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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


### 5、设置终端配置接口 ###
* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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

### 6、设置终端配置 ###


* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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
  |close_desktop_strategy|bool|关闭桌面策略是 true-关闭桌面同时关闭终端|
  |close_terminal_strategy|bool|关闭终端策略是 true-关闭终端同时关闭桌面
  |open_strategy			|bool	|开机策略， true-通电自启动， false - 未开启|
  |program					|object	| 程序tab配置项|
  |server_ip				|str	|服务器ip|
  |current_screen_info		|str	|设置分辨率|
  |show_modify_user_passwd	|bool	|密码修改显示， true/false|
  |terminal_setup_passwd	|str	|终端设置项密码|
  |windows					|object	| windows配置项栏|
  |window_mode				| int	| windows运行模式 1-全屏， 2-全屏可退出 3-全屏不可退出|
  |disconnect_setup			|object	| 断链的配置|
  |goto_local_desktop		|int	| 与服务器断开链接退回本地桌面, -1表示不启用 >=0 表示启用，并且表示响应多少秒进入本地桌面|
  |goto_local_auth			|bool| 断链退回本地桌面验证密码 true/false|
  |show 					|object		| 界面显示设置|
  |show_local_button		|bool		|展示本地桌面按钮, true/false|
  |goto_local_passwd		|str		|切换系统使用切换的密码|
  
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
                    "auto_desktop":0,
                    "close_strategy":0,
                    "open_strategy":true
                },
                "program":{
                    "server_ip":"172.16.1.33",
                    "current_screen_info": "1920*1270",
                    "show_modify_user_passwd":true,
                    "terminal_setup_passwd":"222222"
                },
                "windows":{
                    "window_mode":2,
                    "disconnect_setup":{
                        "goto_local_desktop":5,
                        "goto_local_auth": true
                    },
                    "show":{
                        "show_local_button":true,
                        "goto_local_passwd":"123456"
                    }
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

### 7、修改终端名称 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               		| string | 命令参数：update_name|
  | data               		|object||
  |	terminals				| object| 勾选终端数组|
  |	mac						| str 	|终端MAC地址|
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
    

### 8、删除终端 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

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


### 9、修改编号开始排序 ###


* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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



### 10、停止排序 ###


* URL

  `/api/v1.0/terminal_mgr/terminal_operate/`

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

### 11、按序重排IP ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

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
  |group_uuid				|str|终端组UUID|  
  
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

### 12、移动终端 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

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
    
### 13、导出终端日志 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：export_log|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						| str |终端mac|
  |name						| str	|终端名称|
  |group_name				|str	|组名称|
  |group_uuid				|str	|移动到组uuid|

  
  - 示例：

    ```json
    {
        "cmd": "export_log",
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
    	"msg": "成功",
        "data": {
        }
    }
    ```
    
    
### 14、轮询终端日志结果 ###


* URL

	`/api/v1.0/terminal_mgr/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                   | Type   | Description        |
  | ---------------------- | ------ | ------------------ |
  | cmd               | string | 命令参数：poll_log|
  | data               |object||
  |terminals				| object| 勾选终端数组|
  |mac						| str |终端mac|
  |name						| str	|终端名称|

  
  - 示例：

    ```json
    {
        "cmd": "poll_log",
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
  |down_url| str| 日志下载url|

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
        	"down_url": "http://172.12.3.11/adxxxxxx"
        }
    }
    ```

### 15、移动终端分组列表接口 ###


* URL

	`/api/v1.0/terminal_mgr/uedu_group/list/`

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

### 16、终端升级包接口 ###


* URL

	`/api/v1.0/terminal_mgr/terminal/upgrade_pag/`

* Method

  **GET** 请求，**body** 参数使用 **json** 格式

* Parameters



* Returns

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | code | int    | 返回码               |
  | msg  | str    | 请求返回的具体信息   |
  | data | object | 根据需求返回相应数据 |
  |name  | str    | 文件包名称 |
  |uuid  | str 	  | 文件包uuid |
  |platform| str|  cpu平台|
  |os | str |系统类型 linux, windows|
  |version | str | 版本|
  |path| str | 升级包路经|
  |count| str | 升级数|
  |upload_at| str| 上传时间|
  

  - 示例：

    ```json
    {
        "code": 0,
        "msg": "成功",
        "data": [
                    {
                        "id": 1,
                        "deleted_at": null,
                        "updated_at": "2020-04-17 18:13:19",
                        "created_at": "2020-04-17 18:13:22",
                        "count": 0,
                        "deleted": 0,
                        "uuid": "e2dfad28-8050-11ea-a129-562668d3ccea",
                        "name": "ARM端",
                        "platform": "ARM",
                        "os": "linux",
                        "version": "",
                        "size": 0.0,
                        "path": "",
                        "upload_at": null
                    },
                    {
                        "id": 2,
                        "deleted_at": null,
                        "updated_at": "2020-04-17 18:15:41",
                        "created_at": "2020-04-17 18:15:21",
                        "count": 0,
                        "deleted": 0,
                        "uuid": "2d5842fe-8051-11ea-aa53-562668d3ccea",
                        "name": "Linux端",
                        "platform": "x86",
                        "os": "linux",
                        "version": "",
                        "size": 0.0,
                        "path": "",
                        "upload_at": null
                    },
                    {
                        "id": 3,
                        "deleted_at": null,
                        "updated_at": "2020-04-17 18:17:11",
                        "created_at": "2020-04-17 18:17:09",
                        "count": 0,
                        "deleted": 0,
                        "uuid": "785298fe-8051-11ea-9f01-562668d3ccea",
                        "name": "Windows端",
                        "platform": "x86",
                        "os": "windows",
                        "version": "v1.0.0",
                        "size": 0.0,
                        "path": "/opt/terminal/upgrade/x86_windows_v1.0.0.zip",
                        "upload_at": null
                    }
                ]
    }
    ```

### 17、终端升级包上传 ###


* URL

	`/api/v1.0/terminal_mgr/terminal/upgrade_pag/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

  

* Parameters
	
  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | upgrade_uuid | str    | 升级包uuid               |
  | file  | object    | 上传包文件对象   |
  
  
  
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
    

### 18、点击终端升级操作 ###


* URL

	`/api/v1.0/terminal_mgr/terminal/terminal_operate/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name | Type   | Description          |
  | :--- | :----- | :------------------- |
  | cmd               | string | 命令参数：upgrade|
  | data               |object| |
  | all | bool    | 是否全部升级 true/false|
  | terminals  | object    |  选择终端列表  |
  |	mac 	| str | 终端mac |
  |name		| str	| 终端名称|
  |group_uuid| str	| 选择组uuid|
  |upgrade_uuid| str| 升级包的uuid|

- 示例：

    ```json
    {
        "cmd": "upgrade",
        "data": {
          "all": false,
          "terminals": [
          	  {"mac":  1, "name":  "yzy-01"},
              {"mac":  2, "name":  "yzy-02"},
              {"mac":  3, "name":  "yzy-03"}
          ],
          "group_uuid": "xxxxx-xxxxx-xxxxxx",
          "upgrade_uuid": "xxxxx-xxxxx-xxxxxx"
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

### 19、排序终端列表接口 ###


* URL

	`/api/v1.0/terminal_mgr/terminals/sort/`

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
  |status| str| 终端状态，‘0’-开机，‘1’-关机|
  |group_info | object| 终端组信息|
  |name|str| 终端组名称|
  |uuid|str| 终端组uuid|
  |open_num|int| 开机数|
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
            "open_num": 0,
            "close_num": 2
        }
    }
}
    ```


​    
