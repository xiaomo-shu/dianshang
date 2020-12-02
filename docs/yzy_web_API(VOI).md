[TOC]

# Web接口文档 #

web端的接口`endpoint`为`http://127.0.0.1:50004/api/v1.0/`


## 模板接口

### 1、添加模板


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`create`
  - param - 创建模板的参数

    | Name                   | Type   | Description                                                  |
    | ---------------------- | ------ | ------------------------------------------------------------ |
    | name(required)         | string | 模板名称                                                     |
    | desc                   | string | 模板描述                                                     |
    | os_type(required)      | string | 模板的系统类型，由模板安装方式决定。如果由基础镜像安装，则类型获取基础镜像类型，如果由iso安装，则由创建者手动指定 |
    | classify(required)     | int    | 模板分类：1、教学模板 ，默认为教学模板。预留字段，后续用来区分个人模板 |
    | network_uuid(required) | string | 网络uuid                                                     |
    | subnet_uuid            | string | 子网uuid，为空或者没有代表DHCP分配                           |
    | bind_ip(required)      | string | 给虚拟机分配的IP，DHCP分配时为空                             |
    | vcpu(required)         | int    | 虚拟CPU数目                                                  |
    | ram(required)          | float  | 虚拟内存，单位为G                                            |
    | groups(required)       | list   | 表示绑定的教学分组的uuid，如果是所有教学分组，则为空列表     |
    | iso                    | string | 如果是基于ISO全新安装，则需要提供ISO的路径                   |
    |                        |        |                                                              |
    | system_disk            | dict   | 系统盘信息，具体如下：                                       |
    | image_id(required)     | string | 基础镜像uuid                                                 |
    | size(required)         | int    | 系统盘大小，单位为GB                                         |
    |                        |        |                                                              |
    | data_disks(required)   | list   | 数据盘信息，单个信息如下：                                   |
    | inx(required)          | int    | 启动顺序，从0开始                                            |
    | size(required)         | int    | 数据盘大小，单位为GB                                         |
- 示例：
  
  ```json
  # 基于基础镜像添加  
  {
    	"action": "create",
    	"param": {	
    		"name": "template1",
    	    "desc": "this is template1",
    	    "os_type": "windows_7_x64",
    	    "classify": 1,
          "network_uuid": "9c87ff12-5213-11ea-9d93-000c295dd729",
    	    "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
          "bind_ip": "192.168.2.2",
    		"vcpu": 2,
    		"ram": 2,
          "groups": [
              "9c87ff12-5213-11ea-9d93-000c295dd729"
          ],
    		"system_disk": {
    			 "image_id": "4315aa82-3b76-11ea-930d-000c295dd728",
    	         "size": 50
    		},
    	    "data_disks": [
    	  		{
    	  			"inx": 0,
    	  			"size": 50
    	  		}
    	  	]
    	}
    }
  # 全新安装
  {
  	"action": "create",
  	"param": {
  		"name": "win7",
  	    "desc": "this is system desktop",
  	    "os_type": "windows_7_x64",
  	    "classify": 1,
  	    "network_uuid": "83425121-8d85-4975-9105-c3b5aae9ea0c",
          "subnet_uuid": "9c87ff12-5213-11ea-9d93-000c295dd728",
          "bind_ip": "192.168.2.2",
  		"vcpu": 4,
  		"ram": 4,
  		"system_disk": {
  			"image_id": "",
  	        "size": 100
  		},
  		"data_disks": [
  				{
  					"inx": 0,
  					"size": 50
  				}
  			],
  		"iso": "/opt/iso/cn_windows_7_ultimate_with_sp1_x86_dvd_u_677486.iso"
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

开机按钮是在在线编辑界面中，支持批量操作。当个数大于1时，会返回成功和失败个数。而当个数为1时，成功会返回成功失败个数（成功1个，失败0个），否则会返回失败原因。


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`start`

  - param - 模板信息

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

  | Name        | Type   | Description          |
  | :---------- | :----- | :------------------- |
  | code        | int    | 返回码               |
  | msg         | str    | 请求返回的具体信息   |
  | data        | object | 根据需求返回相应数据 |
  | success_num | int    | 开机成功的个数       |
  | failed_num  | int    | 开机失败的个数       |

  - 示例：

    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "success_num": 2,
            "failed_num": 0
        }
    }
    ```

### 3、模板关机

关机支持批量操作，当个数大于1时，会返回成功和失败个数。而当个数为1时，成功会返回成功失败个数（成功1个，失败0个），否则会返回失败原因。


* URL

  `/voi/education/template/`

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

  | Name        | Type   | Description          |
  | :---------- | :----- | :------------------- |
  | code        | int    | 返回码               |
  | msg         | str    | 请求返回的具体信息   |
  | data        | object | 根据需求返回相应数据 |
| success_num | int    | 关机成功的个数       |
  | failed_num  | int    | 关机失败的个数       |

  - 示例：
  
    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "success_num": 2,
            "failed_num": 0
        }
    }
    ```

### 4、模板强制关机、重启、强制重启和重置

同开关机的操作，只是`action`不同，分别是`hard_stop、reboot、hard_reboot和reset`。都支持批量操作，当个数大于1时，会返回成功和失败个数。而当个数为1时，成功会返回成功失败个数（成功1个，失败0个），否则会返回失败原因。

### 5、删除模板

删除模板，需要支持批量操作


* URL

  `/voi/education/template/`

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

  | Name        | Type   | Description          |
  | :---------- | :----- | :------------------- |
  | code        | int    | 返回码               |
  | msg         | str    | 请求返回的具体信息   |
  | data        | object | 根据需求返回相应数据 |
| success_num | int    | 删除成功的个数       |
  | failed_num  | int    | 删除失败的个数       |

  - 示例：
  
    ```json
    {
    	"code": 0,
    	"msg": "成功",
        "data": {
            "success_num": 2,
            "failed_num": 0
        }
    }
    ```

### 6、编辑模板

在线编辑模板操作


* URL

  `/voi/education/template/`

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

### 7、加载资源和弹出资源


* URL

  `/voi/education/template/`

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

### 8、保存模板

当使用ISO全新安装创建模板时，需要进行保存模板才能达到和基于基础镜像创建时的状态


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`iso_save`

  - param - 保存模板的参数

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 模板名称    |
    | uuid(required) | string | 模板uuid    |

- 示例：

  ```json
  {
  	"action": "iso_save",
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

### 9、更新模板

在线编辑后进行更新模板操作


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`save`

  - param - 保存模板的参数

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 模板名称    |
    | uuid(required) | string | 模板uuid    |
    | desc           | string | 更新的描述  |
  
- 示例：
  
    ```json
    {
    	"action": "save",
    	"param": {
            "name": "template1",
    		"uuid": "710620d8-56cf-11ea-b5f9-000c295dd728",
            "desc": "添加QQ"
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

### 10、版本回退


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`rollback`

  - param - 保存模板的参数

    | Name             | Type   | Description                                       |
    | :--------------- | :----- | :------------------------------------------------ |
    | name(required)   | string | 模板名称                                          |
    | uuid(required)   | string | 模板uuid                                          |
    | rollback_version | string | 回退到的那个版本，如果当前版本只有一个，则取值为0 |
    | cur_version      | string | 当前版本                                          |

- 示例：

  ```json
  {
  	"action": "rollback",
  	"param": {
  		"name": "template1",
  		"uuid": "5652a1d5-7544-42d0-8dad-f6c0858c8871",
  		"rollback_version": 3,
  		"cur_version": 4
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

### 11、复制模板


* URL

  `/voi/education/template/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 模板的具体操作，这里是`copy`

  - param - 复制模板的参数

    | Name                    | Type   | Description                                              |
    | ----------------------- | ------ | -------------------------------------------------------- |
    | template_uuid(required) | string | 待复制的模板uuid                                         |
    | name(required)          | string | 新模板的名字                                             |
    | desc                    | string | 新模板描述                                               |
    | network_uuid(required)  | string | 所属网络uuid                                             |
    | subnet_uuid             | string | 子网uuid                                                 |
    | bind_ip                 | string | 分配的IP。如果是DHCP分配，则subnet_uuid和bind_ip都为空   |
    | groups(required)        | list   | 表示绑定的教学分组的uuid，如果是所有教学分组，则为空列表 |
  
- 示例：
  
    ```json
    {
        "action": "copy",
        "param": {
            "template_uuid": "9a327142-3b21-11ea-8339-000c295dd728",
            "name": "win7_template_copy",
            "desc": "this is win7 template copy",
            "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
            "subnet_uuid": "b68bcc96-3732-11ea-b34d-000c295dd728",
            "bind_ip": "192.168.2.150",
            "groups": []
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

### 12、下载模板


* URL

  `/voi/education/template/`

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
    	"msg": "成功",
        "data": {
            "url": "http://172.16.1.27:50000/api/v1/template/download?path=/opt/slow/instances/_base/1111_20200522164908_c2_r2.0_d100"
        }
    }
    ```

### 13、模板属性修改 ###


* URL

  `/voi/education/template`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name             | Type   | Description                                                  |
  | ---------------- | ------ | ------------------------------------------------------------ |
  | uuid(required)   | string | 模板uuid                                                     |
  | name(required)   | string | 模板名称                                                     |
  | value(required)  | dict   | 更新的模板的属性，包含如下：                                 |
  | name             | string | 修改后的模板名称                                             |
  | desc             | string | 模板描述                                                     |
  | network_uuid     | string | 数据网络uuid                                                 |
  | subnet_uuid      | string | 修改后的子网uuid                                             |
  | bind_ip          | string | 分配的IP信息                                                 |
  | vcpu             | int    | 虚拟cpu个数                                                  |
  | ram              | float  | 虚拟内存，单位为G                                            |
  | devices          | list   | 模板最新的磁盘信息。如果磁盘只是修改了大小，则只修改查询出来的磁盘信息的`size`，只能扩容。如果添加了数据盘，则添加的格式为`{"inx": 0, "size": 50}` |
  | groups(required) | list   | 表示绑定的教学分组的uuid，如果是所有教学分组，则为空列表     |

- 示例：

  ```json
  {
      "uuid": "27aef634-6daa-11ea-81c5-000c29e84b9c",
      "name": "win7模板",
      "value": {
          "name": "template",
          "desc": "",
          "network_uuid": "570ddad8-27b5-11ea-a53d-562668d3ccea",
          "subnet_uuid": "e1056f24-6da4-11ea-9565-000c29e84b9c",
          "bind_ip": "192.168.2.2",
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
      	],
      	"groups": []
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

### 14、模板分页查询 ###


* URL

  ` /voi/education/template/?searchtype=all&classify=1&page=1&page_size=10 `

* Method

  **GET** 请求

* Parameters

  | Name       | Type   | Description                    |
  | ---------- | ------ | ------------------------------ |
  | searchtype | string | 查询类型，`all/contain/single` |
  | classify   | int    | 1-教学模板                     |
  | page       | int    | 页数                           |
  | page_size  | int    | 分页大小                       |
  
  - 示例
  
    ```
    # 查询所有教学模板并分页
    /voi/template/?searchtype=all&classify=1&page=1&page_size=10
    # 模糊匹配查询，根据教学模板名字匹配，同时支持分页
    /voi/template/?searchtype=contain&classify=1&name=te&page=1&page_size=10
    ```
    
    
  
* Returns

  | Name            | Type    | Description                                                  |
  | :-------------- | :------ | :----------------------------------------------------------- |
  | name            | string  | 模板名称                                                     |
  | uuid            | string  | 模板uuid                                                     |
  | desc            | string  | 模板的描述                                                   |
  | network_name    | string  | 数据网络名称                                                 |
  | network_uuid    | string  | 数据网络uuid                                                 |
  | subnet_name     | string  | 子网名称                                                     |
  | subnet_uuid     | string  | 子网uuid                                                     |
  | subnet_start_ip | string  | 子网开始IP                                                   |
  | subnet_end_ip   | string  | 子网结束IP                                                   |
  | bind_ip         | string  | 模板的IP                                                     |
  | vcpu            | int     | 虚拟CPU数量                                                  |
  | ram             | float   | 虚拟内存，单位为GB                                           |
  | os_type         | string  | 系统类型                                                     |
  | owner           | string  | 创建者                                                       |
  | desktop_count   | int     | 绑定的桌面组数量                                             |
  | terminal_count  | int     | 桌面数量                                                     |
  | all_group       | boolean | 是否绑定了所有的教学分组                                     |
  | groups          | list    | 绑定的所有教学分组                                           |
  | attach          | string  | 模板加载的ISO的uuid                                          |
  | version         | int     | 模板当前版本                                                 |
  | status          | string  | 模板状态，active-开机，inactive-关机，error-异常，updating-更新中 |
  | updated_time    | string  | 编辑模板后的更新时间                                         |
  | devices         | list    | 模板的磁盘信息，每个包含的字段信息如下：                     |
  | uuid            | string  | 磁盘的uuid                                                   |
  | type            | string  | 磁盘类型，system-系统盘，data-数据盘                         |
  | device_name     | string  | 磁盘盘符名称                                                 |
  | boot_index      | int     | 磁盘启动顺序                                                 |
  | size            | int     | 磁盘大小，单位为GB                                           |
  | used            | float   | 模板的某个磁盘已使用大小，单位为GB                           |
  
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
                    "uuid": "f133bcc6-6f54-4527-9e2c-d12143b2ae1d",
                    "name": "1",
                    "bind_ip": "172.16.5.200",
                    "os_type": "windows_7",
                    "owner": "admin",
                    "updated_time": "2020-05-21 20:50:55",
                    "groups": [
                        {
                            "uuid": "5cc1eead-368b-405b-acad-ccb86b81f234",
                            "name": "df"
                        }
                    ],
                    "vcpu": 2,
                    "ram": 2.0,
                    "desc": "1",
                    "network_uuid": "d133c64c-6585-4dc2-8e26-2ac2d67e1948",
                    "network_name": "333",
                    "version": 1,
                    "status": "inactive",
                    "attach": null,
                    "all_group": false,
                    "desktop_count": 0,
                    "terminal_count": 0,
                    "devices": [
                        {
                            "uuid": "e551d730-ad18-422f-be1e-7da6acdce0fe",
                            "type": "system",
                            "device_name": "vda",
                            "boot_index": 0,
                            "size": 100,
                            "used": 11.73
                        },
                        {
                            "uuid": "26e431dd-1177-4f12-b530-403f39a7efa1",
                            "type": "data",
                            "device_name": "vdb",
                            "boot_index": 1,
                            "size": 50,
                            "used": 0.0
                        }
                    ],
                    "cpu_count": 40,
                    "total_ram": 125.7,
                    "subnet_uuid": "5506989e-d83b-4647-862f-9ef971c0f0f5",
                    "subnet_name": "子网1",
                    "subnet_start_ip": "172.16.5.161",
                    "subnet_end_ip": "172.16.5.200"
                }
            ]
        }
    }
    ```

### 15、根据教学分组查询模板 ###


* URL

  ` /voi/education/template/?searchtype=all&group=6fb0caaa-6d70-11ea-9a33-0cc47a462da8&page=1&page_size=1 `

* Method

  **GET** 请求

* Parameters

  | Name            | Type   | Description    |
  | --------------- | ------ | -------------- |
  | group(required) | string | 教学分组的uuid |
  | page            | int    | 页数           |
  | page_size       | int    | 分页大小       |


* Returns

  | Name            | Type    | Description                  |
  | :-------------- | :------ | :--------------------------- |
  | template        | string  | 模板uuid                     |
  | template_name   | string  | 模板名称                     |
| template_status | string  | 模板状态                     |
  | group           | string  | 分组uuid                     |
| group_name      | string  | 分组名称                     |
  | os_type         | string  | 模板系统类型                 |
  | owner           | string  | 模板创建者                   |
  | data_disk       | boolean | false-无数据盘 true-有数据盘 |
  | used            | boolean | 模板在该分组下是否已使用     |
  
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
                    "template": "f246956c-b1ce-4c70-aa40-4b3ac276a3df",
                    "template_name": "template1",
                    "template_status": "inactive",
                    "group": "02431a03-178c-41ee-a74d-492cc924933e",
                    "group_name": "group2",
                    "os_type": "windows_7_x64",
                    "owner": "admin",
                    "data_disk": false,
                    "used": false
                }
            ]
        }
    }
    ```

### 16、模板IP分配 ###


* URL

  ` /voi/education/template/ipaddr/?subnet_uuid=d466a092-6f0e-11ea-be76-0cc47a462da8 `

* Method

  **GET** 请求

* Parameters

  | Name                 | Type   | Description    |
  | -------------------- | ------ | -------------- |
  | subnet_uui(required) | string | IP地址段的uuid |


* Returns

  | Name   | Type   | Description  |
  | :----- | :----- | :----------- |
  | ipaddr | string | 返回分配的IP |
  
  - 示例
  
  ```json
  {
  	"ipaddr": "192.168.1.50"
  }
  ```
  

### 17、模板更新点信息查询 ###


* URL

  ` /voi/education/template/operate/?searchtype=all&exist=1&template=f246956c-b1ce-4c70-aa40-4b3ac276a3df `

* Method

  **GET** 请求

* Parameters

  | Name               | Type   | Description                                                 |
  | ------------------ | ------ | ----------------------------------------------------------- |
  | template(required) | string | 模板的uuid                                                  |
  | exist              | int    | 查询更新点信息时，exist=1，如果是查询所有，则可以去掉该条件 |


* Returns

  | Name     | Type   | Description           |
  | :------- | :----- | :-------------------- |
  | uuid     | string | 操作记录的uuid        |
  | template | string | 模板uuid              |
  | remark   | string | 操作的描述信息        |
  | exist    | string | 表示目前还存在的版本  |
  | version  | string | 模板的版本            |
  | op_type  | string | 1-模板更新 2-版本回退 |

  - 示例

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
                  "uuid": "1788a878-59ae-4fc0-b7bd-fb6421842ab4",
                  "template": "f133bcc6-6f54-4527-9e2c-d12143b2ae1d",
                  "remark": "1212",
                  "updated_at": "2020-05-21 20:50:55",
                  "exist": true,
                  "version": 1,
                  "op_type": 1
              }
          ]
      }
  }
  ```

  


## 教学分组接口

### 1、添加教学分组


* URL

  `/voi/education/group/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                 | Type   | Description                                           |
  | -------------------- | ------ | ----------------------------------------------------- |
  | name(required)       | string | 教学分组名称                                          |
  | group_type(required) | int    | 教学分组为`1`。预留字段，后续个人桌面管理部分还有分组 |
  | desc                 | string | 教学分组描述                                          |
  | start_ip(required)   | string | 预设终端开始IP                                        |
  | end_ip(required)     | string | 预设终端结束IP                                        |
  
- 示例：
  
    ```json
    {
        "name": "group5",
        "group_type": 1,
        "desc": "this is group1",
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

  `/voi/education/group/`

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

  `/voi/education/group/`

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

  ` /voi/education/group/?searchtype=all&group_type=1&page=1&page_size=1 `

* Method

  **GET** 请求

* Parameters

  | Name                 | Type   | Description                     |
  | -------------------- | ------ | ------------------------------- |
  | group_type(required) | string | 分组类型，1-教学分组 2-用户分组 |
  | page                 | int    | 页数                            |
  | page_size            | int    | 分页大小                        |


* Returns

  | Name           | Type   | Description          |
  | :------------- | :----- | :------------------- |
  | uuid           | string | 分组的uuid           |
  | name           | string | 分组名称             |
  | desc           | string | 分组描述             |
  | start_ip       | string | 终端预设开始IP       |
  | end_ip         | string | 终端预设结束IP       |
  | terminal_count | int    | 终端数量             |
  | desktop_count  | int    | 分组包含的桌面组数量 |
  
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
                    "uuid": "e6b62e57-96f7-49c1-bd51-42a288dd6640",
                    "name": "group1",
                    "desc": "this is group1",
                    "start_ip": "192.168.1.11",
                    "end_ip": "192.168.1.100",
                    "enabled": true,
                    "terminal_count": 0,
                    "desktop_count": 1
                },
                {
                    "uuid": "02431a03-178c-41ee-a74d-492cc924933e",
                    "name": "group2",
                    "desc": "this is group1",
                    "start_ip": "192.169.1.11",
                    "end_ip": "192.169.1.100",
                    "enabled": true,
                    "terminal_count": 0,
                    "desktop_count": 0
                }
            ]
        }
    }
    ```



## 教学桌面组

### 1、添加教学桌面组


* URL

  `/voi/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`create`

  - param - 创建桌面组的参数，如下：

    | Name                    | Type    | Description                                                  |
    | ----------------------- | ------- | ------------------------------------------------------------ |
    | name(required)          | string  | 桌面组名称                                                   |
    | group_uuid(required)    | string  | 桌面组所属分组                                               |
    | template_uuid(required) | string  | 桌面组使用的模板uuid                                         |
    | sys_restore(required)   | int     | 系统盘是否重启还原                                           |
    | data_restore(required)  | int     | 数据盘是否重启还原。0-不还原，1-还原。如果没有数据盘，则传递2 |
    | prefix(required)        | string  | 桌面名称的前缀                                               |
    | use_bottom_ip(required) | boolean | 是否使用底层客户端IP作为桌面IP                               |
    | ip_detail               | dict    | 当`use_bottom_ip`为`false`时，需要提供此参数                 |
    | show_info(required)     | boolean | 是否显示桌面信息，false-不显示，true-显示                    |
    | auto_update(required)   | boolean | 是否自动更新桌面，false-否，true-是                          |
    
  - 示例：
  
    ```json
  {
  	"action": "create",
    	"param": {
    		"name": "desktop1",
    	    "group_uuid": "b8d57562-db59-4da1-8734-e31601d4220a",
    	    "template_uuid": "f246956c-b1ce-4c70-aa40-4b3ac276a3df",
    	    "sys_restore": 1,
    	    "data_restore": 1,
    	    "prefix": "pc",
    	    "use_bottom_ip": false,
            "ip_detail": {
                "auto": false,
                "start_ip":  "192.168.12.12",
                "netmask": "255.255.255.0",
                "gateway": "192.168.12.254",
                "dns_master": "8.8.8.8",
                "dns_slave": "114.114.114.114"
            },
            "show_info": true,
            "auto_update": true
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

删除需要支持批量操作


* URL

  `/voi/education/desktop/`

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

### 3、设为默认


* URL

  `/voi/education/desktop/`

* Method

  **POST** 请求，**body** 参数使用 **json** 格式

* Parameters

  - action - 桌面组的具体操作，这里是`default`

  - param - 桌面组列表

    | Name           | Type   | Description |
    | :------------- | :----- | :---------- |
    | name(required) | string | 桌面组名称  |
    | uuid(required) | string | 桌面组uuid  |

  - 示例：

    ```json
    {
    	"action": "default",
    	"param": {
            "name": "desktop1",
            "uuid": "29407836-5d21-11ea-aa57-000c295dd728"
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

### 4、激活教学桌面组

激活教学桌面组，支持批量


* URL

  `/voi/education/desktop/`

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

### 5、教学桌面组未激活

未激活，支持批量操作


* URL

  `/voi/education/desktop/`

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

### 6、修改桌面组信息 ###


* URL

  `/voi/education/desktop/`

* Method

  **PUT** 请求，**body** 参数使用 **json** 格式

* Parameters

  | Name                    | Type    | Description                                  |
  | ----------------------- | ------- | -------------------------------------------- |
  | uuid(required)          | string  | 桌面组uuid                                   |
  | name(required)          | string  | 桌面组名称                                   |
  | value(required)         | dict    | 更新的桌面组的属性，包含如下：               |
| name                    | string  | 修改后的桌面组名称                           |
  | sys_restore             | int     | 系统盘是否还原，0-不还原，1-还原             |
  | data_restore            | int     | 数据盘是否还原，0-不还原，1-还原，2-无数据盘 |
  | use_bottom_ip(required) | boolean | 是否使用底层客户端IP作为桌面IP               |
  | ip_detail               | dict    | 当`use_bottom_ip`为`false`时，需要提供此参数 |
  | show_info(required)     | boolean | 是否显示桌面信息，false-不显示，true-显示    |
  | auto_update(required)   | boolean | 是否自动更新桌面，false-否，true-是          |
  
- 示例：
  
    ```json
    {
    	"uuid": "88464c00-6cec-492c-8e98-748f73b2591c",
    	"name": "desktop1",
    	"value": {
    		"name": "desktop2",
    		"sys_restore": 0,
    		"data_restore": 0,
    		"show_info": 0,
    		"auto_update":0
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

### 7、教学桌面组分页查询 ###


* URL

  ` /voi/education/desktop/?searchtype=all&&page=1&page_size=1`

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
    /voi/education/desktop/?searchtype=all&&page=1&page_size=1
    # 根据教学分组查询教学桌面组
    /voi/education/desktop/?searchtype=all&group=d4d02b14-6f24-11ea-bdc0-0cc47a462da8&page=1&page_size=1
    # 教学分组下的教学桌面组模糊查询
    /voi/education/desktop/?searchtype=all&group=d4d02b14-6f24-11ea-bdc0-0cc47a462da8&name=te&page=1&page_size=1
    ```
  
* Returns

  | Name            | Type    | Description                                            |
  | :-------------- | :------ | :----------------------------------------------------- |
  | uuid            | string  | 桌面的uuid                                             |
  | name            | string  | 桌面名称                                               |
  | default         | string  | 是否为默认，0-否 1-是                                  |
  | owner           | string  | 创建者                                                 |
  | group           | string  | 分组uuid                                               |
  | group_name      | string  | 分组名称                                               |
  | template        | string  | 模板uuid                                               |
  | template_name   | string  | 模板名称                                               |
  | template_status | string  | 模板状态，当为"updating"时，会禁用掉该桌面组的所有操作 |
  | sys_restore     | int     | 系统盘是否还原                                         |
  | data_restore    | int     | 数据盘是否还原，如果为2则代表没有数据盘                |
  | inactive_count  | int     | 离线数                                                 |
  | active_count    | int     | 在线数                                                 |
  | total_count     | int     | 总数                                                   |
  | active          | boolean | 桌面组是否激活                                         |
  | os_type         | string  | 系统类型                                               |
  | prefix          | string  | 桌面名称的前缀                                         |
  | postfix         | int     | 桌面名称后缀数字个数                                   |
  | show_info       | boolean | 是否显示桌面信息，false-不显示，true-显示              |
  | auto_update     | boolean | 是否自动更新桌面，false否，true-是                     |
  | created_at      | string  | 创建时间                                               |


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
                    "uuid": "0f15fca7-e80b-49d4-b224-bc1f04d11428",
                    "name": "s",
                    "owner": "admin",
                    "template": "f246956c-b1ce-4c70-aa40-4b3ac276a3df",
                    "template_name": "template1",
                    "template_status": "inactive",
                    "group": "e6b62e57-96f7-49c1-bd51-42a288dd6640",
                    "group_name": "group1",
                    "sys_restore": 1,
                    "data_restore": 1,
                    "active": false,
                    "os_type": "windows_7_x64",
                    "created_at": "2020-05-13 08:22:53",
                    "inactive_count": 0,
                    "active_count": 0,
                    "default": true,
                    "show_info": false,
                    "auto_update": false,
                    "prefix": "PC",
                    "postfix": 1,
                    "total_count": 0
                }
            ]
        }
    }
    ```

### 8、教学桌面分页查询 ###


* URL

  ` http://172.16.1.34:50004/api/v1.0/voi/education/instance/?searchtype=all&desktop_group=691cbdf0-b85b-48bf-9387-fb367784e3d3&page=1&page_size=10 `

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
    voi/education/instance/?searchtype=all&desktop_group=691cbdf0-b85b-48bf-9387-fb367784e3d3&page=1&page_size=10
    ```
  
    
  
* Returns

  | Name        | Type   | Description                       |
  | :---------- | :----- | :-------------------------------- |
  | terminal_mac    | string | 终端MAC地址                          |
  | desktop_status  | int    | 桌面运行状态： 0-离线 1-在线         |
  | desktop_ip      | string | 桌面分配的IP                         |
  | start_datetime  | string | 桌面启动时间                         |
  | desktop_name    | string | 桌面名称                             |

  - 示例：

    ```json
	{
		"code":0,
		"msg":"成功",
		"data":{
			"count":3,
			"next":null,
			"previous":null,
			"results":[
				{
					"terminal_mac":"00:50:56:C0:00:13",
					"desktop_status":0,
					"desktop_ip":"192.168.33.1",
					"terminal_ip":"127.0.0.1",
					"start_datetime":"2020-07-10 08:23:11+00:00",
					"desktop_name":"PC-1"
				},
				{
					"terminal_mac":"2A:73:E1:53:03:6F",
					"desktop_status":0,
					"desktop_ip":"192.168.33.2",
					"terminal_ip":"172.16.1.42",
					"start_datetime":"2020-07-13 01:32:40+00:00",
					"desktop_name":"PC-12"
				},
				{
					"terminal_mac":"00:50:56:C0:22:22",
					"desktop_status":0,
					"desktop_ip":"192.168.33.3",
					"terminal_ip":"127.0.0.1",
					"start_datetime":"2020-07-14 00:37:24+00:00",
					"desktop_name":"PC-1"
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

  `/voi/education/group/?searchtype=all&name=group1`

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


