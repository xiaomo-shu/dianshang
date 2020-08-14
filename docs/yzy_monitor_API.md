[toc]

# KVM管理平台yzy_monitor模块接口文档

### 一、接口文档说明
#### 1、通用报文:

#### 2、返回码表：

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
#### 3、修改记录:
    20191219
    1、初始版本

****

### 二、节点资源信息查询 ###
##

#### 1、CPU监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/cpu

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/cpu
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "numbers": 4,
            "utc": 1576751520,
            "utilization": 8.1
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |numbers|节点CPU总逻辑核心数| int| data| |
    |utc| 查询时间的UTC值| int| data|linux上使用命令查看: date --date @1576751520 |
    |utilization| 节点CPU的总使用率| float| data| |
    

#### 2、查询CPU是否支持虚拟化 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/cpuvt

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/cpuvt
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "cpuvt": false,
            "hostname": "hostname"
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |cpuvt| 是否支持虚拟化| bool| data| |


#### 3、Memory监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/memory

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/memory
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "available": 4569825280,
            "total": 7144345600,
            "utc": 1576751520,
            "utilization": 8.1
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |available|节点memory可用容量| int| data|单位是Byte|
    |total|节点memory总容量| int| data|单位是Byte|
    |utc| 查询时间的UTC值| int| data| |
    |utilization| 节点内存的总使用率| float| data| |
    

#### 4、存储监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/disk

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/disk
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "utc": 1576753011,
            "/": {
                "type": 2,
                "total": 14371782656,
                "used": 11800793088,
                "free": 793088,
                "utilization": 82.1
            },
            "/boot": {
                "type": 1,
                "total": 1063256064,
                "used": 246792192,
                "free": 1793088,
                "utilization": 23.2
            }
    
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |type|磁盘类型| int| 挂载目录|0-rata 1-other|
    |used|此挂载点已使用容量| int| 挂载目录|单位是Byte|
    |free|此挂载点用容量| int| 挂载目录|单位是Byte|
    |total|此挂载点总容量| int| 挂载目录|单位是Byte|
    |utc| 查询时间的UTC值| int| data| |
    |utilization| 此挂载点容量的使用率| float| data| |

#### 5、磁盘IO监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/diskio

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/diskio
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功"
        "data": {
            "sda": {
                "read_bytes": 1221801984,
                "write_bytes": 4739875840
            },
            "sda1": {
                "read_bytes": 26844672,
                "write_bytes": 2118144
            },
            "sda2": {
                "read_bytes": 1193376256,
                "write_bytes": 4737757696
            },
            "utc": 1577183389
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |read_bytes|读取字节数| int| 挂载目录|单位是Byte|
    |write_bytes|写字节数| int| 挂载目录|单位是Byte|
    |utc| 查询时间的UTC值| int| data| |


#### 6、网络监控信息 ####
直接采用URL的POST方法请求，不需要body信息
已经过滤了虚拟网络设备
* URL

    ### http://host:port/api/v1/monitor/network

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/network
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "utc": 1576753658,
            "ens192": {
                "ip": "172.16.1.33",
                "mac": "00:0c:29:b1:24:74",
                "mask": "255.255.255.0",
                "gateway": "172.16.1.1",
                "dns1": "114.114.114.114",
                "dns2": "8.8.8.8",
                "speed": 10000,
                "stat": true
            },
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |ip|网卡IP地址V4版本| str| 网卡名称||
    |mac|网卡MAC地址| str| 网卡名称||
    |mask|IP地址对应的mask掩码| str| 网卡名称||
    |gateway|网关| str| 网卡名称||
    |dns1|域名解析服务器1| str| 网卡名称||
    |dns2|域名解析服务器2| str| 网卡名称||
    |speed|网卡的带宽| int| 网卡名称|单位是MB|
    |stat|网卡的对应网线的连接状态| bool| 网卡名称|true表示网线连接正常，false表示网线连接异常|
    |utc| 查询时间的UTC值| int| data| |



#### 7、网络IO监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/networkio

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/networkio
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "utc": 1577183665,
            "ens192": {
                "bytes_recv": 73173297,
                "bytes_send": 239217622
            },
            "lo": {
                "bytes_recv": 263823412,
                "bytes_send": 263823412
            }
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |bytes_recv|网卡发送字节数| str| 网卡名称||
    |bytes_send|网卡收取字节数| str| 网卡名称||
    |utc| 查询时间的UTC值| int| data| |


#### 8、虚拟机启动数监控信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/vm

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/vm
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "numbers": 0,
            "utc": 1576754877
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |numbers|虚拟机启动数| int| data||
    |utc| 查询时间的UTC值| int| data| |


#### 9、节点硬件信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/hardware

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/hardware
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "utc": 1576755546,
            "server_version": "YI Server 5.0",
            "cpu": {
                "Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GH": 4
            },
            "disk": {
                "VMware Virtual dis": 1
            },
            "gfxcard": {
                "VMware VMWARE040": 1
            },
            "memory": {
                "Main Memor": 1
            }
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |utc| 查询时间的UTC值| int| data| |
    |server_version|服务器自定义版本信息| str| data| /etc/os-release VARIANT字段配置信息 |
    |cpu|cpu信息| dict| data| cpu的型号: 个数|
    |disk|disk信息| dict| data| 存储磁盘的型号: 个数|
    |gfxcard|显卡信息| dict| data| 显卡的型号: 个数|
    |memory|内存信息| dict| data| 内存的型号: 个数|


#### 10、节点应用服务状态信息 ####
直接采用URL的POST方法请求，不需要body信息

* URL

    ### http://host:port/api/v1/monitor/service

* Method

    ###  **POST** 请求，**body** 无

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/service
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "utc": 1576755889,
            "libvirtd": "running",
            "yzy-monitor": "running"
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| |
    |utc| 查询时间的UTC值| int| data| |


#### 11、spice客户端正常连接状态查询 ####
* URL

    ### http://host:port/api/v1/monitor/port_status
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/port_status
    {
        "ports": "55460,5905"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "5905": true,
            "55460": false
        }
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object|  |
    
    返回数据是端口号对应的连接状态的bool值，正常情况下是有4条TCP连接都是ESTABLISHED才返回true


#### 12、网卡配置文件的新增 ####
* URL

    ### http://host:port/api/v1/monitor/add_ip
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/add_ip
    {
        "name": "eth0:0",
        "ip": "172.16.1.34",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "name": "eth0:0"
        }
    }
    ```
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |name| 子ip配置名称 | |int | 格式限制:以冒号分割 例如"ens192:2" |
    |ip | ip地址 | |str |  |
    |netmask | 子网掩码 | | str|  |
    |gateway | 网关地址 | |str |  |
    |dns1 | 域名解析服务器地址1 | | str|  |
    |dns2 | 域名解析服务器地址2 | |str | 可以没有 |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| 成功情况下返回ip配置设备名称|
    
#### 13、网卡配置文件的修改 ####
* URL

    ### http://host:port/api/v1/monitor/update_ip
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/update_ip
    {
        "name": "eth0:0",
        "ip": "172.16.1.34",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "name": "eth0:0"
        }
    }
    ```
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |name| 子ip配置名称 | |int | 格式限制:以冒号分割 例如"ens192:2" |
    |ip | ip地址 | |str |  |
    |netmask | 子网掩码 | | str|  |
    |gateway | 网关地址 | |str |  |
    |dns1 | 域名解析服务器地址1 | | str|  |
    |dns2 | 域名解析服务器地址2 | |str | 可以没有 |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    |data | 返回业务数据 | | object| 成功情况下返回ip配置设备名称| 
    
    
#### 14、网卡配置文件的删除 ####
* URL

    ### http://host:port/api/v1/monitor/delete_ip
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/delete_ip
    {
        "name": "eth0:0",
        "ip": "172.16.1.34",
        "netmask": "255.255.255.0",
        "gateway": "172.16.1.254",
        "dns1": "8.8.8.8",
        "dns2": "114.114.114.114"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "name": "eth0:0"
        }
    }
    ```
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |name| 子ip配置名称 | |int | 格式限制:以冒号分割 例如"ens192:2" |
    |ip | ip地址 | |str |  |
    |netmask | 子网掩码 | | str|  |
    |gateway | 网关地址 | |str |  |
    |dns1 | 域名解析服务器地址1 | | str|  |
    |dns2 | 域名解析服务器地址2 | |str | 可以没有 |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    
    
#### 14、网卡配置文件的交换 ####
* URL

    ### http://host:port/api/v1/monitor/exchange_ip
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/exchange_ip
    {
        "name1": "eth0",
        "name2": "eth0:0"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "name1": "eth0:0"，
            "name2": "eth0"
        }
    }
    ```
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |name1| ip配置名称 | |int | 格式限制:如果是自网卡 以冒号分割 例如"ens192:2" |
    |name2| ip配置名称 | |int | 格式限制:如果是自网卡 以冒号分割 例如"ens192:2" |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    
    
#### 15、验证操作系统密码 ####
* URL

    ### http://host:port/api/v1/monitor/verify_password
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/verify_password
    {
        "user": "root",
        "password": "123456"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功"
    }
    ```
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |user| 操作系统用户名 | |str |  |
    |password| 用户密码明文 | |str | |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |
    
    
#### 16、系统资源使用率统计信息 ####
* URL

    ### http://host:port/api/v1/monitor/resource_statis
    

* Method

    ###  **POST** 请求，**body** 有数据

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/resource_statis
    {
        "statis_period": 15
    }
    ```

    * 返回
    
    ```
	{
	  "code": 0,
	  "data": {
		"cpu_util": "18.15",
		"disk_util": {
		  "/": {
			"rate": "19.90",
			"total": 78582382592,
			"used": 15640133632
		  },
		  "/boot": {
			"rate": "23.20",
			"total": 1063256064,
			"used": 246841344
		  }
		},
		"memory_util": "39.15",
		"nic_util": {
		  "ens192": {
			"ip": "172.16.1.33",
			"read_bytes_avg": 402,
			"read_bytes_max": 402,
			"write_bytes_avg": 354,
			"write_bytes_max": 354
		  },
		  "ens224": {
			"ip": "",
			"read_bytes_avg": 0,
			"read_bytes_max": 0,
			"write_bytes_avg": 0,
			"write_bytes_max": 0
		  }
		},
		"utc": 1588671209
	  },
	  "msg": "成功"
	}

    ```
    
    * 请求描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |statis_period| 统计周期 | |int | 限定60秒内的统计 |
    
    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  | 
    |data| 业务数据 |是| | object| |
    |utc |UTC时间 |否|data|str ||
    |cpu_util |CPU在请求时间周期内的平均使用率 |否|data|str |2位小数位的百分比|
    |memory_util |内存在请求时间周期内的平均使用率 |否|data|str |2位小数位的百分比|
    |disk_util |磁盘各分区在请求时间的使用率 |是|data|object |2位小数位的百分比|
    |nic_util |网卡使用率 |是|data|object |字节/秒|
    |ip |网卡IP地址 |否|nic_util|str ||
    |read_bytes_avg |网卡在请求时间周期内的平均每秒读取字节数 |否|nic_util|int |字节数/秒|
    |read_bytes_max |网卡在请求时间周期内的最大每秒读取字节数 |否|nic_util|int |字节数/秒|
    |write_bytes_avg |网卡在请求时间周期内的平均每秒写入字节数 |否|nic_util|int |字节数/秒|
    |write_bytes_max |网卡在请求时间周期内的最大每秒写入字节数 |否|nic_util|int |字节数/秒|

### 三、节点控制类请求

#### 1、节点定时开关机设置请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/monitor/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数 |描述|必填|父级|数据类型|备注|
    | :--- | :--- | :--- | :--- | :--- | :--- |
    |command | 命令类型、表示某种操作 |是||str | 操作命令：setup_shutdown/delete_shutdown/select_shutdown/modify_shutdown |
    |handler | 处理headler |是| |str | Crontab的操作都是使用`CrontabHandler` |
    |data     | 业务数据 |是| | object| 除了setup_shutdown/modify_shutdown命令，其他都不需要data |
    |task_name |定时任务名称 |是|data|str |需要请求端保证唯一性，否则会出现错乱,只能包含数字和字母|
    |exec_time|执行时间（小时,分钟）|是|data|str|注意先后顺序，使用逗号隔开|
    |exec_weekly |每周几执行（0表示周日）|是|data|str|数字无先后顺序，使用逗号隔开|


* 示例：

    * setup_shutdown 请求/返回
    
    ```
    {
        "handler": "CrontabHandler",
        "command": "setup_shutdown",
        "data": {
            "task_name": "shutdown3",
            "exec_minute": "55",
            "exec_hour": "3",
            "exec_weekly": "1,2"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }

    ```

    * delete_shutdown 请求/返回
    
    ```
    {
        "handler": "CrontabHandler",
        "command": "delete_shutdown",
        "data": {
            "task_name": "shutdown3"
        }
    }

    {
      "code": 0,
      "msg": "成功"
    }
    ```


    * modify_shutdown 请求/返回
    
    ```
    {
        "handler": "CrontabHandler",
        "command": "modify_shutdown",
        "data": {
            "task_name": "shutdown3",
            "exec_minute": "5",
            "exec_hour": "22",
            "exec_weekly": "1,2,5,6,7"
        }
    }
    
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "exec_hour": "3",
            "exec_minute": "55",
            "exec_weekly": "1,2"
        }
    }
    ```


    * select_shutdown 请求/返回
    
    ```
    {
        "handler": "CrontabHandler",
        "command": "select_shutdown",
        "data": {
            "task_name": "shutdown3"
        }
    }
    
    {
        "code": 0,
        "msg": "成功",
        "data": {
            "exec_hour": "3",
            "exec_minute": "55",
            "exec_weekly": "1,2"
        }
    }
    ```



#### 2、节点服务器重启/关机请求 ####
采用URL的POST方法请求，只要收到消息就返回成功

* URL

    ### http://host:port/api/v1/monitor/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数 |描述|必填|父级|数据类型|备注|
    | :--- | :--- | :--- | :--- | :--- | :--- |
    |command | 命令类型、表示某种操作 |是||str | 目前支持两种操作命令：shutdown/reboot |
    |handler | 处理headler |是| |str | 填写固定值“OsHandler” |


* 示例：

    * 请求
    
    ```
    http://172.16.1.33:6666/api/v1/monitor/task
    {
        "handler": "OsHandler",
        "command": "shutdown"
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功"
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |


#### 3、应用服务的控制请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/monitor/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数 |描述|必填|父级|数据类型|备注|
    | :--- | :--- | :--- | :--- | :--- | :--- |
    |command | 命令类型、表示某种操作 |是||str | 目前支持两种操作命令：start/stop/restart/enable/disable|
    |handler | 处理headler |是| |str | 填写固定值“ServiceHandler”  |
    |service | 应用服务名称 |是| | str/array| 除了查询状态，其他操作都可以使用array的格式多个输入 |


* 示例：

    * 请求
    
    ```
    {
        "handler": "ServiceHandler",
        "command": "stop",
        "data": {
            "service": "libvirtd"
        }
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功"
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |


#### 4、定时监控任务控制请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/monitor/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数 |描述|必填|父级|数据类型|备注|
    | :--- | :--- | :--- | :--- | :--- | :--- |
    |command | 命令类型、表示某种操作 |是||str | 目前支持两种操作命令：update/pause/resume，只有update有data|
    |handler | 处理headler |是| |str | 填写固定值“TimerHandler”  |
    |addr | 应用服务名称 |是|data| str|只有update操作才需要修改上报地址，否则按照默认设置addr上报 |
    |node_uuid | 计算节点的UUID |是|data| str| |


* 示例：

    * 请求
    
    ```
    {
        "handler": "TimerHandler",
        "command": "update",
        "data": {
            "addr": "http://172.16.1.33:3333",
            "node_uuid": "123142342342342342343"
        }
    }
    ```

    * 返回
    
    ```
    {
        "code": 0,
        "msg": "成功"
    }
    ```

    * 返回描述

    | 参数    |描述    |父级    | 数据类型|备注|
    |:------ |:-----| :-----| :---| :----|
    |code| 返回码 | |int | 对应code含义见返回码表 |
    |msg | 返回信息 | |str |  |


### 四、节点主动上报类请求
##

#### 1、节点资源监控信息 ####
直接采用URL的POST方法请求

* URL

    ### http://host:port/

* Method

    ###  **POST** 请求，**body** json格式

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    {
        "hostname": "zhouli33",
        "ip": "172.16.1.33",
        "utc": 1577179877,
        "type": "resource",
        "node_uuid": "123142342342342342343",
        "data": {
            "cpu": {
                "numbers": 4,
                "utilization": 20.6
            },
            "memory": {
                "available": 4958343168,
                "total": 7144353792,
                "utilization": 30.6
            },
            "disk": {
                "/": {
                    "type": 2,
                    "total": 14371782656,
                    "used": 11806334976,
                    "utilization": 82.1
                },
                "/boot": {
                    "type": 1,
                    "total": 1063256064,
                    "used": 246792192,
                    "utilization": 23.2
                }
            },
            "diskio": {
                "sda": {
                    "read_bytes": 1217431552,
                    "write_bytes": 4599874560
                },
                "sda1": {
                    "read_bytes": 26844672,
                    "write_bytes": 2118144
                },
                "sda2": {
                    "read_bytes": 1189005824,
                    "write_bytes": 4597756416
                }

            },
            "networkio": {
                "ens192": {
                    "bytes_recv": 70831805,
                    "bytes_send": 229473046
                },
                "lo": {
                    "bytes_recv": 252337044,
                    "bytes_send": 252337044
                }
            }
        }
    }
    ```

    * 请求描述
    返回数据说明请参考查询接口



#### 2、节点应用服务状态上报接口 ####
直接采用URL的POST方法请求

* URL

    ### http://host:port/

* Method

    ###  **POST** 请求，**body** json格式

* Parameters
    
    ### 无


* 示例：

    * 请求
    
    ```
    {
        "hostname": "zhouli33",
        "ip": "172.16.1.33",
        "utc": 1577183023,
        "type": "service",
        "node_uuid": "123142342342342342343",
        "data": {
            "httpd": "not found",
            "libvirtd": "running",
            "mysqld": "not found",
            "redis": "running",
            "yzy-client": "not found",
            "yzy-compute": "not found",
            "yzy-monitor": "not found"
        }
    }
    ```

    * 请求描述
        服务的状态只有"running"才是正常的，其他都是异常
    

### 五、节点文件或目录操作请求

#### 1、节点目录删除请求 ####
采用URL的POST方法请求

* URL

    ### http://host:port/api/v1/monitor/task

* Method

    ###  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters
    | 参数 |描述|必填|父级|数据类型|备注|
    | :--- | :--- | :--- | :--- | :--- | :--- |
    |command | 命令类型、表示某种操作 |是||str | 操作命令：delete_file |
    |handler | 处理headler |是| |str | 文件的操作都是使用`FileHandler` |
    |data     | 业务数据 |是| | object| 除了setup_shutdown/modify_shutdown命令，其他都不需要data |
    |file_name |文件或目录绝对路径 |是|data|str |需要绝对路径|



* 示例：

    * delete_file 请求/返回
    
    ```
    {
		"handler": "FileHandler",
		"command": "delete_file",
		"data": {
			"file_name": "/tmp/test"
		}
    }

    {
      "code": 0,
      "msg": "成功"
    }

    ```