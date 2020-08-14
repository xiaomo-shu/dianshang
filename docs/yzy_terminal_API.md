# KVM管理平台yzy_terminal模块接口文档

### 一、接口文档说明
#### 1、通用报文:

#### 2、返回码表：

    | 返回码 | 含义 |
    | :--- | :--- |
    |0     | 成功|
    |10001 | 登录失败|
    |10002 | 用户名错误|
    |-1    | 未知异常|


​       
#### 3、修改记录:
    20200210
    1、初始版本

****


### 二、提供给管理平台控制终端的接口

#### 1、终端关机/重启/删除/终端用户注销 请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：shutdown/restart/delete/user_logout            |
    | handler     | 处理headler             | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                   |
    | data        | 业务数据                | 是   |      | object   |  |
    | mac_list    | 终端MAC地址列表         | 是   | data | str      |     |


* 示例：

    * shutdown 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "shutdown",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```


    * restart 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "restart",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
        }
    }
    
    {
      "code": 0,
      "msg": "成功"
    }
    ```
    
    * delete 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "delete",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
        }
    }
    
    {
      "code": 0,
      "msg": "成功"
    }
    ```

    * user_logout 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "user_logout",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
        }
    }
    
    {
      "code": 0,
      "msg": "成功"
    }
    ```



#### 2、终端计算机名称请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：modify_terminal_name                        |
    | handler     | 处理headler          | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据             | 是   |      | object   |  | mac为键名，终端需要修改的名称为键值

* 示例：

    * modify_terminal_name 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "modify_terminal_name",
        "data": {
            "00-50-56-C0-00-08": "PC01",
            "00-50-56-C0-00-07": "PC02"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 3、终端 排序/排序撤销 请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：terminal_order, cancel_terminal_order          |
    | handler     | 处理headler             | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                   |
    | data        | 业务数据                | 是   |      | object   |  |
    | group_uuid  | 终端管理分组uuid        | 是   | data | str      |     |
    | start_num   | 终端编号开始值          | 是   | data | int      |                              |
    | batch_num   | 批次号                  | 是   | data | int      |  管理平台发送排序指令的批次号，用于取消排序用             |
    


* 示例：

    * terminal_order 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "terminal_order",
        "data": {
            "group_uuid": "00234242342342342322",
            "start_num": 5
        }
    }

    {
      "code": 0,
      "msg": "成功",
	  "data": {
	      "batch_num": 1
	  }
    }
    ```
    
    * cancel_terminal_order 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "cancel_terminal_order",
        "data": {
            "group_uuid": "00234242342342342322",
            "batch_num": 1
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 4、终端IP地址修改请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型      | 是   |      | str         | 操作命令：modify_ip                         |
    | handler     | 处理headler  | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据      | 是   |      | object   |  |
    | terminal_ids| 终端id列表    | 是   | data | str      |   |
    | mac_list    | 终端MAC地址列表         | 是   | data | str      |     |
    | start_ip    | 终端ip开始值  | 是   | data | str      |                              |
    | mask        | 终端ip掩码    | 是   | data | str      |                              |
    | gateway     | 网关地址      | 是   | data | str      |                              |
    | dns1        | DNS1         | 是   | data | str      |                              |
    | dns2        | DNS2         | 是   | data | str      |                              |

* 示例：

    * modify_ip 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "modify_ip",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
            "to_ip_list": "192.168.1.101,192.168.1.102,192.168.1.103",
            "mask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "dns1": "8.8.8.8",
            "dns2": "114.114.114.114"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 5、获取终端日志文件请求 ####
采用URL的POST方法请求
获取日志存放固定路径，前端导出的时候直接去读取，读取完后直接删除，
文件名规范：“00-50-56-C0-00-08_2020-12-01.zip”,一个终端一个压缩包"mac+开始日期.zip"
确定文件已经完整上传到服务器结束，检查同名的ok文件是否已经存在 "mac+开始日期.ok"
* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：get_log_file                         |
    | handler     | 处理headler             | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据                | 是   |      | object   |  |
    | terminal_ids   | 终端id列表           | 是   | data | str      |   |


* 示例：

    * get_log_file 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "get_log_file",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
            "start_date": "2020-12-01",
            "end_data": "2020-12-03"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```



#### 6、升级终端程序请求 ####  ----------
采用URL的POST方法请求
升级程序有严格文件格式，终端CPU架构_操作系统类型_版本号.文件类型后缀：”x86_windows_v2.2.2.2.zip”
* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：update_program                        |
    | handler     | 处理headler             | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据                | 是   |      | object   |  |
    | mac_list    | 终端MAC地址列表         | 是   | data | str      |     |
    | program_file_name  | 终端程序文件名      | 是   | data | string      |                |


* 示例：

    * update_program 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "update_program",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
            "program_file_name": "x86_windows_v2.2.2.2.zip"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 7、设置终端请求
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：set_terminal                         |
    | handler     | 处理headler             | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据                | 是   |      | object   |  |
    | mac_list    | 终端MAC地址列表         | 是   | data | str      |     |
    | show_desktop_type | 云桌面登录展示    | 是   | data | int      | 0-教学桌面 1-个人桌面 2-混合桌面               |
    | auto_desktop   | 自动打开云桌面    | 是   | data | int    |  0-不自动打开 >0表示进入第几个                     |
    | open_strategy| 开机策略    | 是   | data | bool      | true-通电自启动                  |
    | close_desktop_strategy| 关闭桌面策略    | 是   | data | bool      | true-关闭桌面同时关闭终端 |
    | close_terminal_strategy| 关闭终端策略    | 是   | data | bool      | true-关闭终端同时关闭桌面 |
	| screen_resolution | 屏幕分辨率    | 是   | data | str      | 1024*768                           |
    | server_ip| 服务器ip地址    | 是   | data | str      |                              |
    | show_modify_user_passwd| 终端显示修改用户密码    | 是   | data | bool      |  修改终端用户密码的按钮是否显示给用户                 |
    | terminal_setup_passwd| 终端设置项密码    | 是   | data | str      |                              |
	| window_mode  | 运行模式    | 是   | data | int      | 1-全屏， 2-全屏可退出 3-全屏不可退出                          |
    | goto_local_desktop  | 与服务器断开链接退回本地桌面    | 是   | data | int | -1表示不启用 >=0 表示启用，并且表示响应多少秒进入本地桌面 |
    | goto_local_auth | 断链退回本地桌面验证密码 | 是   | data | bool | true-验证密码 |
    | show_local_button | 展示本地桌面按钮  | 是   | data | bool      | true-显示 false-隐藏                   |
    | goto_local_passwd | 切换系统使用切换的密码    | 是   | data | str      |                     |
    
* 示例：

    * set_mode 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "set_terminal",
        "data": {
            "mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07,00-50-56-C0-00-06",
			"mode": {
				"show_desktop_type": 0,
				"auto_desktop": 1,
				"open_strategy": true,
				"close_desktop_strategy": false,
				"close_terminal_strategy": true
			},
            "program": {			
				"screen_resolution": "1024*768",
				"server_ip": "172.16.1.33",
				"show_modify_user_passwd": true,
				"terminal_setup_passwd": "111111"
			},
			"windows": {
				"window_mode": 2,
				"goto_local_desktop": 5,
				"goto_local_auth": true,
				"show_local_button": false,
				"goto_local_passwd": "123456"
			}
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 8、终端移动分组 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：change_group                        |
    | handler     | 处理headler          | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据             | 是   |      | object   |  | mac为键名，终端需要修改的名称为键值|
	| mac_list    | 终端MAC地址列表         | 是   | data | str      |     |
    | to_group_uuid | 移动到的分组UUID    | 是   | data | str      |                |


* 示例：

    * change_group 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "change_group",
        "data": {
			"mac_list": "00-50-56-C0-00-08,00-50-56-C0-00-07",
            "to_group_uuid": "2222222222222222222222222"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```

#### 9、删除分组 ####
采用URL的POST方法请求
前端删除教学分组/个人分组的时需要调用此接口同步更新终端分组group_uuid信息
* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：delete_group                        |
    | handler     | 处理headler          | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据             | 是   |      | object   |  | |
    | group_uuid  | 分组UUID    | 是   | data | str      |                |


* 示例：

    * delete_group 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "delete_group",
        "data": {
            "group_uuid": "2222222222222222222222222"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```
	
#### 10、云桌面关闭通知 ####
采用URL的POST方法请求
* URL

    ### http://host:port/api/v1/terminal/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数        | 描述                    | 必填 | 父级 | 数据类型 | 备注                                                     |
    | :---------- | :---------------------- | :--- | :--- | :------- | :------------------------------------------------------- |
    | command     | 命令类型、表示某种操作  | 是   |      | str      | 操作命令：desktop_close_notice                        |
    | handler     | 处理headler          | 是   |      | str      | Crontab的操作都是使用`TerminalHandler`                    |
    | data        | 业务数据             | 是   |      | object   |  | |
    | group       | 桌面组信息           | 是   | data | object      |                |
    | name        | 桌面组名称           | 是   | group | str      |                |
	| id          | 桌面组排序           | 是   | group | int      |                |
    | desc        | 桌面组描述           | 是   | group | str      |                |
    | uuid        | 桌面组UUID           | 是   | group | str      |                |
    | ip          | 云桌面spice连接IP地址| 是   | data | str      |                |
	| port        | 云桌面spice连接端口  | 是   | data | int      |                |
    | desktop_name| 云桌面名称           | 是   | data | str      |                |
    | token       | 云桌面spice连接令牌  | 是   | data | str      |                |
    | os_type     | 云桌面操作系统类型   | 否   | data | str      |                |
    | dsk_uuid    | 云桌面UUID           | 是   | data | str      |                |
    | terminal_mac| 终端mac地址          | 否   | data | str      |                |

* 示例：

    * desktop_close_notice 请求/返回
    
    ```
    {
        "handler": "WebTerminalHandler",
        "command": "desktop_close_notice",
        "data": {
			"group": {
				"name": "桌面组名称",
				"id": 11,
				"desc": "桌面组描述",
				"uuid": "23333333334444444444"
			},
            "ip": "172.16.1.33",
			"port": 5059,
			"instance_name": "VM01",
			"token": "5059234234SFASDFSFDAS",
			"os_type": "win10",
			"instance_uuid": "234safdasfasdf23234",
			"terminal_mac": "00:0c:29:b1:24:74"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```
