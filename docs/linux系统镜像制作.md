# linux系统制作的几点注意事项

- 安装时，选择桌面版本进行安装，不需要安装任何开发工具包
- 系统使用中文
- 磁盘默认使用100G
- 默认root用户登录



# ubuntu16制作

首先使用ISO安装系统，安装完成后进行如下操作：

- ubuntu默认是以`guest`用户登录的，以下操作设置开机自动以`root`用户登录。

  - 设置root密码：`sudo passwd root`

  - `/usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf`加入如下配置：

    ```shell
    # 手工输入登录系统的用户名和密码
    greeter-show-manual-login = true
    # 不允许guest登录
    allow-guest = false
    # root用户自动登录
    autologin-user = root
    autologin-user-timeout = 0
    ```

  - 切换到root用户，修改`/root/.profile`，将`mesg n`替换成`tty -s && mesg n`

- 进行了以上操作后，重启以`root`用户登录系统，然后进行一下优化：

  - 删除安装系统时创建的用户：`userdel -rf user1`
  - 关闭ubuntu中的`关机/重启`确认，如果不关闭，会导致API调用关闭虚拟机时，系统提示是否要确认关机，导致一直无法关闭虚拟机：在`/etc/acpi/events/powerbtn`中，将`action`修改为`action=/sbin/shutdown -h now`
  - 在设置中，进行以下优化：
    - `软件和更新`关闭自动更新
    - `电源`中设置为`不要挂起`
    - `安全和隐私`中关闭发送错误报告
    - `亮度和锁屏`中关闭锁屏



# centos制作

安装提示安装完成后，进行以下操作：

- 第一个也是设置`root`用户自动登录，首先修改密码`sudo passwd root`，然后修改`/etc/gdm/custom.conf`中添加`AutomaticLoginEnabel=true`和`AutomaticLogin=root`
- 重启后进行如下设置：
  - 设置->privacy 中关闭锁屏
  - /etc/sysconfig/selinux 修改为`permissive`模式
  - 删除安装时创建的用户：`usedel -rf user1`
  
  
  
# ubuntu20制作

使用ISO安装系统，安装完成后进行以下操作：

- 设置root密码：`sudo passwd root`

- `/usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf`加入如下配置：
  - greeter-show-manual-login = true
  - allow-guest = false
  
- 修改gdm-autologin和gdm-password
  - 执行sudo vim /etc/pam.d/gdm-autologin 注释掉auth required pam_succeed_if.so user != root quiet_success这一行(第三行左右)
  - 执行sudo vim /etc/pam.d/gdm-password注释掉 auth required pam_succeed_if.so user != root quiet_success这一行(第三行左右)
  
- 修改/root/.profile文件
  - 执行sudo vim/root/.profile修改配置文件，
  - 文档最后一行前添加 tty -s && 改成 tty -s &&mesg n || true
  
- 修改/etc/gdm3/custom.conf
  - AutomaticLoginEnable = true
  - AutomaticLogin = root
  
- 重启会自动登录到root账户
  - 优化设置同上
  - 重启虚拟机
  


# 设置ip

- 设置ip
  - 在/usr/local/src/目录下创建ipset.sh文件
  ```shell
  #!/bin/bash
  
  python3 /usr/local/src/ipsetting.py  
  ```
  - 设置开机自启动
    - 如果是ubuntu20 则需要创建/etc/rc.local文件(ubuntu18 以后默认没有这个文件的。需要自己创建)
    ```shell
    #!/bin/sh
    
    bash /usr/local/src/ipset.sh
    exit 0
    ```
    - 给rc.local加上执行权限, sudo chmod +x /etc/rc.local
    - 在/etc/systemd/system目录下创建软连接 ln -s /lib/systemd/system/rc.local.service /etc/systemd/system
    
  - 上传ipsetting.py文件