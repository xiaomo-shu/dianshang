# BT 服务接口文档

## 1.通用报文:

## 2.返回码表
    | 返回码| 含义    |
    |:---  |: --    |
    |0		|success|
    |20001	| bt 服务启动失败未设置track ip port |
    |20002 	| track port bind 失败|
    |20003	| 文件不存在	|
    |20004	| 种子文件损坏|
    |20005	| 下载超时	|
    |-1		| 未知异常	|


* server code
```

   {
   		2000:	"start_bt"
   		2001:	"stop_bt"
   		2002:	"set_tracker"
   		2003:	"add_task"   
   		2004:	“del_task” 
   		2005:	"make_torrent"
   		2006:	"get_task_state"
   		
   		8000:	"task_end"			//下载完成或者异常结束
   }
```
* start_bt 请求/返回 启动bt服务
```
{
	"time_out": 1000  		//可以设置超时时间
	"track_ip": 127.0.0.1
	"track_port": 1337
}

{
	"code"
	"msg": "Success"
}
```
*  stop_bt 请求/返回 停止bt服务
```
{
	""
}

{
	"code"
	"msg": "Success"
}
```
*  set_tracker 请求/返回 设置tracker 信息
```
{
	"ip": 127.0.0.1
	"port": 1337
}

{
	"code"
	"msg": "Success"
}
```
*  add_task 请求/返回 添加一个任务
```
{
	"torrent":  "/data/uuid.torrent"
	"save_path": "/mnt/"
	# 在save_path 存在源文件则为上传否则为下载
}

{
	"code": 0
	"msg": "Success"
	"torrent_id" 12121
}
```
*  del_task 请求/返回 删除一个任务
```
{
	"torrent_id": 12121
}

{
	"code": 0
	"msg": "Success"
}
```
*  make_torrent 请求/返回 生成一个种子文件
```
{
	"file_path": "/mnt/win7.qcow2"
	"torrent_path": "/mnt/win7.torrent"
}

{
	"code": 0
	"msg": "Success"
}
```
*  get_task_state 请求/返回 生成一个种子文件
```
{
	"torrent_id": 12121
}

{
	"code": 0
	"msg": "Success"
	"state" "checking" "downloading" "finished" "seeding" 
	"progress" : 0.9
	"total_download" : 100 //kb  当前下载总数
	"download_rate": 100 //kb	下载速度
	"total_size":		//文件总大小
}

```
