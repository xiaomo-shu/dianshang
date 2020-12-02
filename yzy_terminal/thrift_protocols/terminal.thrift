/**
 * The first thing to know about are types. The available types in Thrift are:
 *
 *  bool    Boolean, one byte
 *  i8 (byte)   Signed 8-bit integer
 *  i16     Signed 16-bit integer
 *  i32     Signed 32-bit integer
 *  i64     Signed 64-bit integer
 *  double      64-bit floating point value
 *  string      String
 *  binary      Blob (byte array)
 *  map<t1,t2>  Map from one type to another
 *  list<t1>    Ordered list of one type
 *  set<t1>     Set of unique elements of one type
 *
 * Did you also notice that Thrift supports C style comments?
 *
 * version V2.1
 */

namespace cpp Thrift

struct UserInfo {
    1:string user_name;
    2:string user_passwd;
}

/**
 *IP信息
 */
struct IPInfo{
    1: i32 IsDhcp
    2: string Ip
    3: string Subnet
    4: string Gateway
    5: string Mac
    6: string DNS1
    7: string DNS2
}

struct DesktopGroupInfo {
    1:string group_name; // 桌面组名称
    2:i32    group_id; // 桌面组序号
    3:string group_desc; // 桌面组的描述
    4:string group_uuid; // 桌面组UUID
    5:string os_type; // windows_7_x64/windows_7/windows_10_x64/Other
}

struct DesktopInfo {
    1:string ip;
    2:i32 port;
    3:string desktop_name;
    4:string token; // 服务器开启虚拟机动态生成的md5值
    5:string dsk_type; // 是指基于思捷、kvm等不同底层虚拟的桌面
    6:DesktopGroupInfo group;
    7:i32 status; // 0-关闭 1-运行
    8:string os_type; // 桌面操作系统类型
    9:UserInfo dsk_user; // 桌面操作系统用户名和密码
    10:string dsk_uuid; // 桌面的唯一ID  
}

struct RespDesktopInfo {
    1:string code; // "0000" 表示正常返回, "0001" 表示被其他终端占用
    2:string msg;
    3:string description;
    4:DesktopInfo dsk_info;
}

// 教学桌面专用
struct TerminalDesktopInfo {
    1:i32 terminal_id;
    2:string terminal_mac;
    3:string terminal_ip;
    4:string desktop_ip;
}

/**
 *服务器配置信息

 */
struct YunServerInfo{
    1: string ServerUrl
    2: string ServerUrl1
    3: string UserName
    4: string UserPass
    5: string Domain
    6: i64 TimeOut
}

/**
 *屏幕分辨率
 */
struct ScreenInfo{
    1: i32 Width
    2: i32 Height
}

/**
 *硬件信息
 */
struct HardwareInfo{
    1: string CpuID
    2: string HardDiskID
    3: string MacAddress
    4: string YunId
}

/**
 *教室信息
 */
struct RoomInfo{
    1: string RoomId
    2: string Name
    3: string Des
    4: double OrderId
    5: i32 SeatNum
    6: string Group
}

/**
 *RDP远程桌面信息
 */
struct RemoteDesktopInfo{
    1:string MachineName
    2:string Domain
    3:string Uername
    4:string Pwd
    5:string DesktopName,
    6:string SoftwareInfo
    7:string Domain0
    8:string Uername0
    9:string Pwd0
}

/*
*服务器信息
*/
struct ServiceInfo
{
    1:string Ip
    2:i32 Port
}

/*
*屏幕广播参数
*/
struct ScreenBroadCastInfo
{
    1:string CastServicename
    2:string ScrCastChannel
    3:string ScrCastIp
    4:i32 ScrCastPort
    5:i32 ScrCastQuality
    6:i32 ScrCastRecvWinStyle
    7:i32 ScrCastAllowRecord
    8:i32 ScrCastSvrScreenRecord
}

/*
*版本信息
*/
struct VersionInfo
{
    1:string ConfVersion
    2:string Version
}

/******************************************************
 *多系统切换 add by rock
 */
struct SystemTableInfo {
    1:string DesktopId; ##桌面场景guid
    2:string SystemTabUid; ##系统切换的桌面UID
    3:string TabDeskName;##桌面名称
    4:i32 NeedNums; ##资源申请数量
    5:i32 ReadyNums; ##资源已就绪数量
    6:i32 LogonNums; ##已登录云桌面数量
    7:bool IsNeedSign; ##是否需点名
    8:bool AutoLogin; ##是否自动登录云桌面
    9:string TabDateTime; ##系统切换开始时间
    10:i64 AutoLoginDelaySecond; ##自动登录延时时间(从开始时间计)
    11:bool TabIsReady;##指定是否已分配已准备好的桌面给到当前客户端。非自动登录云桌面时生效
    12:string DeskDescription;//
    13:i32 RegisterCount;
    14:i32 UnRegisterCount;
    15:i32 OpenCount;//开机数量
    16:i32 CloseCount;//关机数量
    17:string Status;//桌面状态(1 开启 2 关闭 9 正在开机 10 正在关机)
    18:string StatusName;//状态名称
    19:bool Checked;
    20:bool IsClassing;
    21:bool IsReady;
}

struct EduClientInfo
{//教学客户端配置 暂未使用
    1: string RoomName
    2: string Group
    3: string ProtectPass
    4:ServiceInfo EduServiceInfo      //教学服务
    5:ServiceInfo EduTopServiceInfo       //教学顶层服务
    6:ServiceInfo ClientServiceInfo       //终端管理服务
    7:string SlientImagePath          //静默图片
    8:string FileReceivePath          //文件接收路径
    9:i32 DisEnableNet           //网络限制
    10:i32 Slient            //静默中
    11:i32 Casting               //广播中
    12:ScreenBroadCastInfo BroadCastInfo  //广播配置
    13:VersionInfo EduVersionInfo     //教学配置版本
    14:i32 UserType //3-教师终端-2-教师云桌面端 1-学生终端 0-学生云桌面端
    15:i32 PlatForm //0-x86  1-ARM
    16:i32 DemoModing               //演示中 add by rock
    17:i32 CutClassing              //切课中 add by rock
    18:SystemTableInfo SysTableInfo     //切换系统的状态
    19:i32 Montioring
}

 /**
 *座位信息
 */
struct SitInfo {
    1:i32 Row
    2:i32 Col
    3:double RowId //row.(col*0.01)  如5.03表示第5行第3列（最多到第99列）
    4:string Des
    5:string UserUuid
    6:string RoomId
}


/**
 *客户端配置信息
 */
struct ClientInfo {
    1: string Num//终端编号
    2: string HostName
    3: IPInfo IPinfo    //IP信息对应TerminalConf.IPinfo
    4: YunServerInfo Yuninfo
    6: ScreenInfo Screeninfo  //设置终端正在使用的屏幕信息
    7: i32 ShowLocalDesktop
    8: string  AutoOpen
    9: string  ConfigPass
    10: string MachineCode
    11: string ActivateCode
    12: string Activatestate
    13: string Ewfstate
    14: string version;
    15: string ConfVersion
    16: i64 ConfTime
    17: i64 OverTime
    18: HardwareInfo HardInfo
    19: i32 ShowLoginPage
    20: i32 ShowDesktopBootForm
    21: i32 ShowDesktopDesc
    22: RoomInfo roomoInfo
    23: string LocalPass
    24: i32 IdleTimeOut
    25: i32 CloseWhileExitYunDesk
    26: RemoteDesktopInfo remoteDesktopInfo
    27: i32 usertype //3-教师终端-2-教师云桌面端 1-学生终端 0-学生云桌面端
    28: i32 PlatForm //0-x86  1-ARM
    29: EduClientInfo EduInfo //教学客户端配置
    30: SitInfo ClientSitInfo
    31: TerminalConf TerminalConfInfo
}

/**
 *KVM 终端配置
 */

// 与服务器断开链接退回本地桌面设置
struct DisconnectSetup {
    // -1表示不启用 >=0 表示启用，并且表示响应多少秒进入本地桌面
    1:i32 goto_local_desktop;
    // true-进入本地桌面需要输入密码
    2:bool goto_local_auth;
}

struct DisplaySetup {
    1:bool show_local_button; // 显示本地桌面按钮 true-显示 false-隐藏
    2:string goto_local_passwd; // 进入本地桌面密码(注意:非本地操作系统密码)
}

struct TerminalConf {
    1:i32 terminal_id;//终端编号
    2:string mac;//物理地址
    3:IPInfo ip_info;// IP信息
    4:string terminal_name;//终端名称
    5:string platform; // ARM x86
    6:string soft_version;//终端程序版本
    7:i32 show_desktop_type; // 0-教学桌面、1-个人桌面、2-混合桌面
    8:i32 auto_desktop; // 0-不自动进入、>1 表示进入第几个桌面
    9:bool close_desktop_strategy; // true-关闭桌面同时关闭终端
    10:bool close_terminal_strategy; // true-关闭终端同时关闭桌面
    11:bool open_strategy; // true-通电启动终端
    12:ServiceInfo server_info;//终端管理服务IP地址和端口
    13:list<ScreenInfo> screen_info_list; // 终端所有可用分辨率
    14:ScreenInfo current_screen_info;//设置终端正在使用的屏幕信息
    15:bool show_modify_user_passwd; // true-显示修改密码(终端用户密码)
    16:string terminal_setup_passwd; // 终端设置项密码
    17:i64 conf_version; // 用于对终端配置信息的服务器端和终端进行同步更新
    18:i32 window_mode; // 1-全屏， 2-全屏可退出 3-全屏不可退出
    19:DisconnectSetup disconnect_setup;//断开服务器连接设置
    20:DisplaySetup show;//是否显示本地桌面按钮图标
    21:bool hide_tools; // true-隐藏工具条
    22:string top_level_service_ip;// 顶层服务ip
    23:string teacher_service_ip;// 教师服务ip
    24:i32 classroom_num;// 教室编号
    25:string multicast_ip;// 组播ip
    26:i32 multicast_port;// 组播port


}

// 文件类型决定了文件上传或者下载对应服务器上面存储的路径的配置
enum FileType {
    LOG = 1;
    SOFT = 2;
    PATCH = 3;
}

struct FileCtrlInfo {
    1:string file_name;
    2:FileType file_type;
    3:i64 total_size;
    4:i64 operate_offset;
    5:i32 operate_length;
}

// 路由信息
struct RouteInfo {
    1: string RouteId
    2: string RouteAddress
    3: IPInfo IPinfo
}

/**
*结果信息
*/
struct ResultInfo {
    1:string code
    2:string Message
    3:string Description
}

/**
 *云桌面运行软件信息
 */
 struct SoftInfo{
    1:string ProcessName
    2:string ClassName
    3:string DefaultTitle
    4:string ProcessPath
    5:string Username
    6:binary ImgData
}

/**
* 云客户端显示信息
*/
struct YunClientShowInfo{
    1:string ID,
    2:string ClientNum,
    3:i32 OnlineState,
    4:string ComputerName
    5:string ClientIPAddress
    6:string ClientMAC
    7:string LoginUser
    8:string LoginDomain
    9:string SafeState
    10:string ActivateCode
    11:double OrderID
    12:string Version
    13:string Note
    14:bool Checked
    15:string RoomID
    16:string Group
    17:string RemoteScreenConnectString
    18: i32 PlatForm //0-x86  1-ARM
    19:string PlatFormDesc //平台说明
    20:string ActivateState//激活状态
}

enum CommandBodyType {
    JSON = 1;
    XML = 2;
    TEXT = 3;
}

/**
 *服务器发送给客户端的命令
 */
struct  CommandMsg {
    1: i64 Num = 0
    2: string Body
    3: CommandBodyType BodyType
    4: string cmdstr
    5: string Version
    6: binary BodyBytes
    7: i64 TotalPackets
    8: string From//由谁发出
    9: string Tos//发送给谁
    10: bool IsNeedConfirm
    11: map<string,string> ArgsDic
    12: i64 batch_num = 0
}


// 实现双向通信，服务器和终端都需实现
service ConnectService {
    // 支持命令：终端关机、终端重启、更新配置、升级终端程序、上传日志、桌面关闭通知、更新IP、终端排序
    oneway void Command(1:CommandMsg msg);
    // 服务器调用此方法时，如果终端是需要双向通信的连接必须有回调此方法
    oneway void TokenId(1:string tokenId);
    oneway void RouteAddress(1: string routeAddress);
    oneway void Ping(1:string tokenId, 2:i64 Time); // 预留用于连接检测或者心跳
    oneway void RouteAddressInfo(1:string tokenId, 2:RouteInfo routeInfo);
}

// 单向调用服务，用于管理终端
service ManageService {
    //思杰
    // 终端登录,终端MAC和通信链路建立绑定关系
    bool ClientLogin(1:string tokenId,2:HardwareInfo info);//登录方法 判断是否激活
    string GetServerConfVer(1:string tokenId);
    bool UpdateInfo(1:string tokenId,2:ClientInfo info);
    ClientInfo GetClientInfo(1:string tokenId);
    oneway void UpdateCopyDiskProgress(1:string tokenId,2:string message);
    string GetClientNum();
    string GetClientUser();
    string GetClientIp();
    string GetDateTime();
    bool ExistClientNum(1:string clientNum);
    ClientInfo ChangeClient(1:ClientInfo clientInfo);
    bool IsFirstLoginUpdatePwd(1:string username,2:string pwd);
    bool UpdateUserPwd(1:string username,2:string oldPwd,3:string pwd);
    ResultInfo OpenSoft(1:SoftInfo softInfo);
    ResultInfo AddSoftInfoList(1:list<SoftInfo> listSoft);
    list<SoftInfo> GetSoftInfoList();
    list<YunClientShowInfo> GetList(1:i32 pageIndex,2:i32 pageSize,3:string keyword,4:string roomId);
    /**获取用户是否可以修改密码*/
    bool CanModifyPassword(1:string userName);
    /**验证用户密码是否正确*/
    bool ValidateUserPassword(1:string userName,2:string password);

    //kvm
    // 终端用户登录认证,验证通过后返回用户会话ID直接放ResultInfo的Description里面，异常情况为空
    ResultInfo user_login(1:UserInfo user, 2:string mac);
    // 终端用户登录注销
    ResultInfo user_logout(1:string user_session_id);
    // 终端用户修改密码
    ResultInfo user_modify_passwd(1:UserInfo old_user, 2:UserInfo new_user);
    // 终端获取资源枚举列表信息(桌面组信息;教学桌面填写mac，个人桌面填写user_session_id)
    list<DesktopGroupInfo> get_dskgrop_info(1:string mac, 2:string user_session_id);
    // 获取所有终端和云桌面关联列表信息(电子教学软件用,只取教学桌面, 电子教学软件那边会每隔3秒取一次数据)
    list<TerminalDesktopInfo> get_desktop_info();
    // 终端请求打开云桌面系统
    RespDesktopInfo desktop_open(1:DesktopGroupInfo info, 2:string mac, 3:string user_session_id);
    // 终端请求关闭单个云桌面
    ResultInfo desktop_close(1:DesktopInfo info);
    // 终端请求关闭关联所有的云桌面(教学场景:只需要传参mac，user_session_id为空，个人场景: 两个参数都需要传)
    ResultInfo all_desktop_close(1:string mac, 2:string user_session_id);
    // 终端获取配置版本号, 如果没有终端配置，返回 -1
    i64 get_config_version(1:string mac);
    // 终端获取配置信息
    TerminalConf get_config(1:string mac);
    // 终端请求更新配置信息
    ResultInfo update_config(1:ClientInfo conf);
    // 终端排序查询
    CommandMsg order_query(1:string mac); // 返回值：terminal_id == -1表示非排序中 >=0 正在排序的号码
    // 终端响应服务端发起的命令的确认
    bool command_confirm(1:CommandMsg cmd_msg, 2:string mac);
}

// 单向调用服务，用于文件下载上传
service FileService {
    //思杰
    i64 GetFileSize(1:string fileName);
    binary ReadByte(1:string fileName,2:i64 offset,3:i32 length);

    //kvm
    // 获取文件大小
    i64 get_file_size(1:string file_name, 2:FileType file_type);
    // 下载文件
    binary read_bytes(1:FileCtrlInfo read_info);
    // 上传文件
    bool write_bytes(1:FileCtrlInfo write_info, 2:binary data);
}
