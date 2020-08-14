service_code_name = {
    1000: "wakeup",
    1001: "shutdown",
    1002: "restart",
    1003: "delete",
    1004: "update_name",
    1005: "update_config",
    1006: "enter_maintenance_mode",
    1007: "clear_all_desktop",
    1008: "download_desktop",
    1009: "cancel_download_desktop",
    1010: "add_data_disk",
    1011: "order",
    1012: "update_ip",
    1013: "update_difference_disk",
    1014: "pxe_start",
    1015: "send_torrent",
    1016: "upload_desktop",
    1017: "send_desktop",
    1018: "push_task_result",  # 任务结果 {"torrent_id": "xxxxx", "msg": "Success","result": 0 }
                               # 任务结果 {"torrent_id": "xxxxx", "msg": "Fail","result": 1 }

    1019: "enter_maintain", # 进入维护模式
    1020: "upload_disk",

    1021: "bt_task_complete",  # bt任务完成通知
    1022: "watermark_switch",   # 水印开关通知
    1023: "ssh_upload_desktop", 
    1024: "update_desktop_group_info",
    1025: "cancel_send_desktop",

    9000: "heartbeat",
    9001: "terminal_login",
    9002: "terminal_logout",
    9003: "get_date_time",
    9004: "get_config_version_id",
    9005: "get_config_info",
    9006: "update_config_info",
    9007: "get_desktop_group_list",
    9008: "verify_admin_user",
    9009: "order_confirm",
    9010: "order_query",
    9011: "sync_desktop_info",
    9012: "get_desktop_info",
    9013: "desktop_upload",
    9014: "torrent_upload",
    9015: "task_result",    # 上报任务结果
    9016: "operate_auth",
    9017: "init_desktop",   # 初始化桌面
    9018: "check_upload_state", # 校验
    9019: "bt_tracker",         # bt tracker地址
    9020: "p_to_v_start",          # p2v
    9021: "p_to_v_state",

    # 9030: "win_login"           # window终端登录

    9022: "diff_disk_upload",       # 差分盘上传磁盘
    9023: "diff_disk_download",
    9024: "desktop_login",  # 上报桌面下载
}

name_service_code = {v: k for k, v in service_code_name.items()}
