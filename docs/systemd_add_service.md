# Systemd添加自定义服务

## 一、自定义服务的配置
### 1、添加服务启动配置文件
	在/usr/lib/systemd/system/目录下新增服务配置文件，命名格式XXX.service
	例如新增配置文件：/usr/lib/systemd/system/yzy-monitor.service，配置文件内容参考如下：
	[Unit]
	Description=yzy-monitor server daemon
	After=network.target
	
	[Service]
	Type=simple
	ExecStart=/usr/local/python3.7/bin/python3 manager.py run
	ExecReload=/bin/kill -HUP $MAINPID
	KillMode=process
	Restart=on-failure
	RestartSec=30s
	WorkingDirectory=/opt/yzy_kvmprojects/yzy_monitor
	
	[Install]
	WantedBy=multi-user.target

### 2、修改配置文件内容
	配置分为三个部分：Unit、Service、Install
	Unit: 启动顺序与依赖关系
		Description 服务的简单描述
		After 依赖服务，表示需要对应服务启动后才能启动本服务
	Service: 启动行为
		ExecStart 启动程序的命令
		RestartSec 程序失败退出后多少秒会自动重启服务
		WorkingDirectory 启动程序的主工作目录
	Install: 类似centos里面操作系统启动的级别（单用户、多用户、界面等等）
		WantedBy=multi-user.target 表示多用户模式
	
	一般普通应用服务化，上述配置示例只需要修改下面三个参数：
		Unit下的Description
		Service下的ExecStart、RestartSec和WorkingDirectory

### 3、加载服务配置并设置自启动
	systemctl daemon-reload       # 重载systemd的配置
	systemctl enable yzy-monitor  # 设置yzy-monitor服务自启动
    systemctl start yzy-monitor   # 启动yzy-monitor服务

### 4、查看启动服务的日志
	journalctl -xef -u yzy-monitor # -x 输出日志内容丰富 -e 表示跳转到日志最后 -f 查看最新日志 -u 指定服务名称

## 二、systemd管理的服务的常用控制命令
	systemctl enable yzy-monitor  # 设置开机启动
	systemctl disable yzy-monitor # 关闭开机启动
	systemctl start yzy-monitor   # 启动服务
	systemctl stop yzy-monitor    # 停止服务
	systemctl restart yzy-monitor # 重启服务
	systemctl status yzy-monitor  # 查看服务状态
