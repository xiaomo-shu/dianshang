service_code_name = {
    2000: "start_bt",
    2001: "stop_bt",
    2002: "set_tracker",
    2003: "add_task",
    2004: "del_task", 
    2005: "make_torrent",
    2006: "get_task_state",

    8000: "task_end",

}

name_service_code = {v: k for k, v in service_code_name.items()}
