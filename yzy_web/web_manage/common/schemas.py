"""
负责API接口参数的校验，使用jsonschema
"""
import inspect
import logging
import json
from functools import wraps
from jsonschema import validate, draft7_format_checker
from jsonschema.exceptions import ValidationError
from django.http import JsonResponse
from web_manage.common.errcode import get_error_result


logger = logging.getLogger(__name__)


def check_input(module, action='', need_action=False):
    """
    目前的参数校验只实现了基本类型的判断，后续可以针对每个字段做更详细的限制
    :param module: 模板标识，用来获取对应的json schema
    :param action: 用来获取对应操作的json shema，如果need_action为假，则需要提供此参数
    :param need_action: 标识参数里面需要提供 action 字段
    :return:
    """

    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            arg_dict = inspect.getcallargs(func, *args, **kwargs)
            try:
                data = json.loads(arg_dict['request'].body)
            except:
                data = dict()
            module_action = data.get('action')
            if need_action and not module_action:
                return JsonResponse(get_error_result("ParamError"), json_dumps_params={'ensure_ascii': False})
            if module_action:
                schema_name = module_action + '_' + module
            else:
                schema_name = action + '_' + module
            schema = schemas_all.get(schema_name)
            if schema:
                try:
                    validate(data, schema, format_checker=draft7_format_checker)
                except ValidationError as e:
                    logger.error("validate data error:%s", e.message)
                    ret = get_error_result("ParamError")
                    error = "%s" % (' --> '.join([i for i in e.path]))
                    ret['msg'] = ret['msg'] + ":" + error
                    return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})
            ret = func(*args, **kwargs)
            return ret
        return wrapper
    return decorated


# template schemas
create_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "os_type": {
                    "type": "string"
                },
                "classify": {
                    "type": "integer"
                },
                "pool_uuid": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "bind_ip": {
                    "type": "string"
                },
                "vcpu": {
                    "type": "integer"
                },
                "ram": {
                    "type": "number"
                },
                "system_disk": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string"
                        },
                        "size": {
                            "type": "integer"
                        }
                    },
                    "required": [
                        "image_id",
                        "size"
                    ]
                },
                "data_disks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "inx": {
                                "type": "integer"
                            },
                            "size": {
                                "type": "integer"
                            }
                        },
                        "required": [
                            "inx",
                            "size"
                        ]
                    }
                }
            },
            "required": [
                "name",
                "os_type",
                "classify",
                "pool_uuid",
                "network_uuid",
                "vcpu",
                "ram",
                "system_disk"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
start_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "templates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "templates"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
delete_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "templates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
            "templates"
        ]
}
save_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                },
                "run_date": {
                    "type": "string",
                    "format": "date-time"
                }
            },
            "required": [
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
copy_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "template_uuid": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "pool_uuid": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "bind_ip": {
                    "type": "string"
                }
            },
            "required": [
                "template_uuid",
                "name",
                "pool_uuid",
                "network_uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
change_device_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                },
                "iso_uuid": {
                    "type": "string"
                }
            },
            "required": [
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
send_key_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                }
            },
            "required": [
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
resync_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "ipaddr": {
                    "type": "string"
                },
                "image_id": {
                    "type": "string"
                },
                "role": {
                    "type": "integer"
                },
                "path": {
                    "type": "string"
                },
                "version": {
                    "type": "integer"
                }
            },
            "required": [
                "ipaddr",
                "image_id",
                "role",
                "path",
                "version"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}

# group schemas
create_edu_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "group_type": {
            "type": "integer"
        },
        "desc": {
            "type": "string"
        },
        "network_uuid": {
            "type": "string"
        },
        "subnet_uuid": {
            "type": "string"
        },
        "start_ip": {
            "type": "string"
        },
        "end_ip": {
            "type": "string"
        }
    },
    "required": [
        "name",
        "group_type",
        "network_uuid",
        "subnet_uuid",
        "start_ip",
        "end_ip"
    ]
}
delete_edu_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
        "groups"
    ]
}
update_edu_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "value": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "start_ip": {
                    "type": "string"
                },
                "end_ip": {
                    "type": "string"
                },
            },
            "required": [
                "name"
            ]
        }
    },
    "required": [
        "name",
        "uuid",
        "value"
    ]
}

# education desktop group
create_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "group_uuid": {
                    "type": "string"
                },
                "template_uuid": {
                    "type": "string"
                },
                "pool_uuid": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "vcpu": {
                    "type": "integer"
                },
                "ram": {
                    "type": "number"
                },
                "sys_restore": {
                    "type": "integer"
                },
                "data_restore": {
                    "type": "integer"
                },
                "instance_num": {
                    "type": "integer"
                },
                "prefix": {
                    "type": "string"
                },
                "postfix": {
                    "type": "integer"
                },
                "postfix_start": {
                    "type": "integer"
                },
                "create_info": {
                    "type": "object"
                }
            },
            "required": [
                "name",
                "group_uuid",
                "template_uuid",
                "pool_uuid",
                "network_uuid",
                "subnet_uuid",
                "vcpu",
                "ram",
                "sys_restore",
                "data_restore",
                "instance_num",
                "prefix",
                "postfix",
                "create_info"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
start_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "desktops"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
delete_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "desktops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
            "desktops"
        ]
}
update_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "value": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "name"
            ]
        }
    },
    "required": [
        "name",
        "uuid",
        "value"
    ]
}

# education instance
create_edu_instance = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktop_uuid": {
                    "type": "string"
                },
                "desktop_name": {
                    "type": "string"
                },
                "desktop_type": {
                    "type": "integer"
                },
                "instance_num": {
                    "type": "integer"
                },
                "create_info": {
                    "type": "object"
                }
            },
            "required": [
                "desktop_uuid",
                "desktop_name",
                "desktop_type",
                "instance_num",
                "create_info"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
start_edu_instance = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktop_uuid": {
                    "type": "string"
                },
                "desktop_name": {
                    "type": "string"
                },
                "desktop_type": {
                    "type": "integer"
                },
                "instances": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "desktop_uuid",
                "desktop_name",
                "desktop_type",
                "instances"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
delete_edu_instance = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "desktop_uuid": {
            "type": "string"
        },
        "desktop_name": {
            "type": "string"
        },
        "desktop_type": {
            "type": "integer"
        },
        "instances": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
            "desktop_uuid",
            "desktop_name",
            "desktop_type",
            "instances"
        ]
}
get_console_edu_instance = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "uuid": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "uuid",
                "name"
            ]
        }
    },
    "required": [
        "action",
        "param"
    ]
}

# user group schemas
create_person_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "group_type": {
            "type": "integer"
        },
        "desc": {
            "type": "string"
        },
        "start_ip": {
            "type": "string"
        },
        "end_ip": {
            "type": "string"
        }
    },
    "required": [
        "name",
        "group_type"
    ]
}

# group user schemas
single_create_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "group_uuid": {
                    "type": "string"
                },
                "user_name": {
                    "type": "string"
                },
                "passwd": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "phone": {
                    "type": "string"
                },
                "email": {
                    "type": "string"
                },
                "enabled": {
                    "type": "integer"
                }
            },
            "required": [
                "group_uuid",
                "user_name",
                "passwd"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
multi_create_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "group_uuid": {
                    "type": "string"
                },
                "prefix": {
                    "type": "string"
                },
                "postfix": {
                    "type": "integer"
                },
                "postfix_start": {
                    "type": "integer"
                },
                "user_num": {
                    "type": "integer"
                },
                "passwd": {
                    "type": "string"
                },
                "enabled": {
                    "type": "integer"
                }
            },
            "required": [
                "group_uuid",
                "prefix",
                "postfix",
                "postfix_start",
                "user_num",
                "passwd"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
delete_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "users": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "user_name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
        "users"
    ]
}
update_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "user_name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "value": {
            "type": "object",
            "properties": {
                "user_name": {
                    "type": "string"
                },
                "group_uuid": {
                    "type": "string"
                },
                "passwd": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "phone": {
                    "type": "string"
                },
                "email": {
                    "type": "string"
                },
                "enabled": {
                    "type": "integer"
                }
            },
            "required": [
                "user_name",
                "group_uuid"
            ]
        }
    },
    "required": [
        "user_name",
        "uuid",
        "value"
    ]
}
enable_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "user_name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "user_name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "users"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
move_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "group_uuid": {
                    "type": "string"
                },
                "group_name": {
                    "type": "string"
                },
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "user_name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "user_name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "group_uuid",
                "group_name",
                "users"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
export_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string"
                },
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "user_name": {
                                "type": "string"
                            },
                            "uuid": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "user_name",
                            "uuid"
                        ]
                    }
                }
            },
            "required": [
                "filename",
                "users"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
import_group_user = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string"
                }
            },
            "required": [
                "filepath"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}

# personal desktop group
create_personal_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "template_uuid": {
                    "type": "string"
                },
                "pool_uuid": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "allocate_type": {
                    "type": "integer"
                },
                "allocate_start": {
                    "type": "string"
                },
                "vcpu": {
                    "type": "integer"
                },
                "ram": {
                    "type": "number"
                },
                "sys_restore": {
                    "type": "integer"
                },
                "data_restore": {
                    "type": "integer"
                },
                "desktop_type": {
                    "type": "integer"
                },
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "group_uuid": {
                    "type": "string"
                },
                "allocation": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "group_uuid": {
                                "type": "string"
                            },
                            "user_uuid": {
                                "type": "string"
                            },
                            "name": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "user_uuid",
                            "name"
                        ]
                    }
                },
                "instance_num": {
                    "type": "integer"
                },
                "prefix": {
                    "type": "string"
                },
                "postfix": {
                    "type": "integer"
                },
                "postfix_start": {
                    "type": "integer"
                },
                "create_info": {
                    "type": "object"
                }
            },
            "required": [
                "name",
                "template_uuid",
                "pool_uuid",
                "allocate_type",
                "vcpu",
                "ram",
                "sys_restore",
                "data_restore",
                "instance_num",
                "prefix",
                "postfix",
                "create_info"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}

# desktop user
add_group_desktop_random = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktop_uuid": {
                    "type": "string"
                },
                "desktop_name": {
                    "type": "string"
                },
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "group_uuid": {
                                "type": "string"
                            },
                            "group_name": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "group_uuid",
                            "group_name"
                        ]
                    }
                }
            },
            "required": [
                "desktop_uuid",
                "desktop_name",
                "groups"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
delete_group_desktop_random = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktop_uuid": {
                    "type": "string"
                },
                "desktop_name": {
                    "type": "string"
                },
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "uuid": {
                                "type": "string"
                            },
                            "group_name": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "uuid",
                            "group_name"
                        ]
                    }
                }
            },
            "required": [
                "desktop_uuid",
                "desktop_name",
                "groups"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}

# static desktop
change_bind_desktop_static = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "instance_uuid": {
                    "type": "string"
                },
                "instance_name": {
                    "type": "string"
                },
                "user_uuid": {
                    "type": "string"
                },
                "user_name": {
                    "type": "string"
                },
            },
            "required": [
                "instance_uuid",
                "instance_name",
                "user_uuid",
                "user_name"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
change_group_desktop_static = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "desktop_uuid": {
                    "type": "string"
                },
                "desktop_name": {
                    "type": "string"
                },
                "group_uuid": {
                    "type": "string"
                },
                "group_name": {
                    "type": "string"
                }
            },
            "required": [
                "desktop_uuid",
                "desktop_name",
                "group_uuid",
                "group_name"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}

# system
scheduler_database = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer"
                },
                "node_uuid": {
                    "type": "string"
                },
                "status": {
                    "type": "integer"
                },
                "cron": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string"
                        },
                        "values": {
                            "type": "array"
                        },
                        "day": {
                            "type": "integer"
                        },
                        "hour": {
                            "type": "integer"
                        },
                        "minute": {
                            "type": "integer"
                        },
                    },
                    "required": [
                        "type",
                        "hour",
                        "minute"
                    ]
                },
            },
            "required": [
                "count",
                "node_uuid",
                "status"
            ]
        }
    },
    "required": [
        "action",
        "param"
    ]
}
desktop_crontab_task = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "status": {
                    "type": "integer"
                },
                "cron": {
                    "type": "array",
                    "item": {
                        "type": "object",
                        "properties": {
                            "cmd": {
                                "type": "string"
                            },
                            "type": {
                                "type": "string"
                            },
                            "values": {
                                "type": "array"
                            },
                            "day": {
                                "type": "integer"
                            },
                            "hour": {
                                "type": "integer"
                            },
                            "minute": {
                                "type": "integer"
                            },
                        },
                        "required": [
                            "cmd",
                            "type",
                            "hour",
                            "minute"
                        ]
                    }

                },
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "desktop_uuid": {
                                "type": "string"
                            },
                            "instances": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "uuid": {
                                            "type": "string"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                    },
                                    "required": [
                                        "uuid"
                                    ]
                                }
                            }
                        },
                        "required": [
                            "desktop_uuid",
                            "instances"
                        ]
                    }
                }
            },
            "required": [
                    "name"
                ]
        }
    },
    "required": [
        "action",
        "param"
    ]
}
delete_crontab_task = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "desktops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "uuid": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "uuid"
                ]
            }
        }
    },
    "required": [
            "tasks"
        ]
}

# voi template
create_voi_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "os_type": {
                    "type": "string"
                },
                "classify": {
                    "type": "integer"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "bind_ip": {
                    "type": "string"
                },
                "vcpu": {
                    "type": "integer"
                },
                "ram": {
                    "type": "number"
                },
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "system_disk": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string"
                        },
                        "size": {
                            "type": "integer"
                        }
                    },
                    "required": [
                        "image_id",
                        "size"
                    ]
                },
                "data_disks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "inx": {
                                "type": "integer"
                            },
                            "size": {
                                "type": "integer"
                            }
                        },
                        "required": [
                            "inx",
                            "size"
                        ]
                    }
                }
            },
            "required": [
                "name",
                "os_type",
                "classify",
                "network_uuid",
                "vcpu",
                "ram",
                "system_disk"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
save_voi_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                },
                "run_date": {
                    "type": "string",
                    "format": "date-time"
                },
                "desc": {
                    "type": "string"
                }
            },
            "required": [
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
update_voi_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "bind_ip": {
                    "type": "string"
                },
                "vcpu": {
                    "type": "integer"
                },
                "ram": {
                    "type": "number"
                },
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "name",
                "network_uuid",
                "vcpu",
                "ram",
                "groups"
            ]
        }
    },
    "required": [
            "uuid",
            "name",
            "param"
        ]
}
# voi education group
create_voi_edu_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "group_type": {
            "type": "integer"
        },
        "desc": {
            "type": "string"
        },
        "start_ip": {
            "type": "string"
        },
        "end_ip": {
            "type": "string"
        }
    },
    "required": [
        "name",
        "start_ip",
        "end_ip"
    ]
}
update_voi_edu_group = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "value": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "start_ip": {
                    "type": "string"
                },
                "end_ip": {
                    "type": "string"
                },
            },
            "required": [
                "name",
                "start_ip",
                "end_ip"
            ]
        }
    },
    "required": [
        "name",
        "uuid",
        "value"
    ]
}
copy_voi_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "template_uuid": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "desc": {
                    "type": "string"
                },
                "groups": {
                    "type": "array",
                    "item": {
                        "type": "string"
                    }
                },
                "network_uuid": {
                    "type": "string"
                },
                "subnet_uuid": {
                    "type": "string"
                },
                "bind_ip": {
                    "type": "string"
                }
            },
            "required": [
                "template_uuid",
                "name",
                "network_uuid",
                "groups"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
rollback_voi_template = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "rollback_version": {
                    "type": "integer"
                },
                "cur_version": {
                    "type": "integer"
                },
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                }
            },
            "required": [
                "rollback_version",
                "cur_version",
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
# voi desktop
create_voi_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "group_uuid": {
                    "type": "string"
                },
                "template_uuid": {
                    "type": "string"
                },
                "sys_restore": {
                    "type": "integer"
                },
                "data_restore": {
                    "type": "integer"
                },
                "prefix": {
                    "type": "string"
                },
                "use_bottom_ip": {
                    "type": "boolean"
                },
                "ip_detail": {
                    "type": "object"
                },
                "show_info": {
                    "type": "boolean"
                },
                "auto_update": {
                    "type": "boolean"
                },
                "data_disk": {
                    "type": "boolean"
                },
                "data_disk_size": {
                    "type": "integer"
                },
                "data_disk_type": {
                    "type": "integer"
                }
            },
            "required": [
                "name",
                "group_uuid",
                "template_uuid",
                "sys_restore",
                "data_restore",
                "prefix",
                "auto_update",
                "use_bottom_ip"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
default_voi_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "uuid": {
                    "type": "string"
                }
            },
            "required": [
                "name",
                "uuid"
            ]
        }
    },
    "required": [
            "action",
            "param"
        ]
}
update_voi_edu_desktop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "uuid": {
            "type": "string"
        },
        "value": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "sys_restore": {
                    "type": "integer"
                },
                "data_restore": {
                    "type": "integer"
                },
                "use_bottom_ip": {
                    "type": "boolean"
                },
                "ip_detail": {
                    "type": "object",
                    "properties": {
                        "auto": {
                            "type": "boolean"
                        },
                        "start_ip": {
                            "type": "string"
                        },
                        "netmask": {
                            "type": "string"
                        },
                        "gateway": {
                            "type": "string"
                        },
                        "dns_master": {
                            "type": "string"
                        },
                        "dns_slave": {
                            "type": "string"
                        },
                    },
                },
                "show_info": {
                    "type": "boolean"
                },
                "auto_update": {
                    "type": "boolean"
                },
            },
            "required": [
                "name",
                "sys_restore",
                "data_restore",
                "show_info",
                "auto_update"
            ]
        }
    },
    "required": [
        "name",
        "uuid",
        "value"
    ]
}
operation_crontab_task = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer"
                },
                "cron": {
                    "type": "object",
                    "properties": {
                            "type": {
                                "type": "string"
                            },
                            "values": {
                                "type": "array"
                            },
                            "day": {
                                "type": "integer"
                            },
                            "hour": {
                                "type": "integer"
                            },
                            "minute": {
                                "type": "integer"
                            },
                        },
                    "required": [
                        "type",
                        "hour",
                        "minute"
                    ]
                }
            }
        }
    },
    "required": [
        "action",
        "param"
    ]
}
warning_crontab_task = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer"
                },
                "cron": {
                    "type": "object",
                    "properties": {
                            "type": {
                                "type": "string"
                            },
                            "values": {
                                "type": "array"
                            },
                            "day": {
                                "type": "integer"
                            },
                            "hour": {
                                "type": "integer"
                            },
                            "minute": {
                                "type": "integer"
                            },
                        },
                    "required": [
                        "type",
                        "hour",
                        "minute"
                    ]
                }
            }
        }
    },
    "required": [
        "action",
        "param"
    ]
}
create_warn_setup = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "data": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer"
                },
                "option": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "ratio": {
                            "type": "string"
                        },
                        "time": {
                            "type": "string"
                        },
                        "host_name": {
                            "type": "array",
                            "item": {
                                "type": "string"
                            }
                        }
                    },
                },
            }
        }
    },
    "required": [
        "status",
        "option",
    ]
}
update_warn_setup = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "data": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer"
                },
                "option": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "ratio": {
                            "type": "string"
                        },
                        "time": {
                            "type": "string"
                        },
                        "host_name": {
                            "type": "array",
                            "item": {
                                "type": "string"
                            }
                        }
                    }
                },
            }
        }
    },
    "required": [
        "status",
        "option",
    ]
}
update_crontab_task = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        },
        "param": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "integer"
                },
                "uuid": {
                    "type": "string"
                },
                "cron": {
                    "type": "object",
                    "properties": {
                            "type": {
                                "type": "string"
                            },
                            "values": {
                                "type": "array"
                            },
                            "day": {
                                "type": "integer"
                            },
                            "hour": {
                                "type": "integer"
                            },
                            "minute": {
                                "type": "integer"
                            },
                        },
                    "required": [
                        "type",
                        "hour",
                        "minute"
                    ]
                }
            }
        }
    },
    "required": [
        "action",
        "param"
    ]
}

schemas_all = {
    "create_template": create_template,
    "start_template": start_template,
    "stop_template": start_template,
    "hard_stop_template": start_template,
    "reboot_template": start_template,
    "hard_reboot_template": start_template,
    "reset_template": start_template,
    "delete_template": delete_template,
    "save_template": save_template,
    "copy_template": copy_template,
    "download_template": save_template,
    "attach_source_template": change_device_template,
    "detach_source_template": change_device_template,
    "send_key_template": send_key_template,
    "resync_template": resync_template,
    "create_edu_group": create_edu_group,
    "delete_edu_group": delete_edu_group,
    "update_edu_group": update_edu_group,
    "create_edu_desktop": create_edu_desktop,
    "start_edu_desktop": start_edu_desktop,
    "stop_edu_desktop": start_edu_desktop,
    "active_edu_desktop": start_edu_desktop,
    "inactive_edu_desktop": start_edu_desktop,
    "reboot_edu_desktop": start_edu_desktop,
    "delete_edu_desktop": delete_edu_desktop,
    "update_edu_desktop": update_edu_desktop,
    "create_edu_instance": create_edu_instance,
    "start_edu_instance": start_edu_instance,
    "stop_edu_instance": start_edu_instance,
    "reboot_edu_instance": start_edu_instance,
    "delete_edu_instance": delete_edu_instance,
    "get_console_edu_instance": get_console_edu_instance,
    "create_person_group": create_person_group,
    "delete_person_group": delete_edu_group,
    "update_person_group": update_edu_group,
    "single_create_group_user": single_create_group_user,
    "multi_create_group_user": multi_create_group_user,
    "delete_group_user": delete_group_user,
    "update_group_user": update_group_user,
    "enable_group_user": enable_group_user,
    "disable_group_user": enable_group_user,
    "move_group_user": move_group_user,
    "export_group_user": export_group_user,
    "import_group_user": import_group_user,
    "create_personal_desktop": create_personal_desktop,
    "start_personal_desktop": start_edu_desktop,
    "stop_personal_desktop": start_edu_desktop,
    "reboot_personal_desktop": start_edu_desktop,
    "enter_maintenance_personal_desktop": start_edu_desktop,
    "exit_maintenance_personal_desktop": start_edu_desktop,
    "delete_personal_desktop": delete_edu_desktop,
    "update_personal_desktop": update_edu_desktop,
    "create_personal_instance": create_edu_instance,
    "start_personal_instance": start_edu_instance,
    "stop_personal_instance": start_edu_instance,
    "hard_stop_personal_instance": start_edu_instance,
    "reboot_personal_instance": start_edu_instance,
    "delete_personal_instance": delete_edu_instance,
    "add_group_desktop_random": add_group_desktop_random,
    "delete_group_desktop_random": delete_group_desktop_random,
    "change_bind_desktop_static": change_bind_desktop_static,
    "change_group_desktop_static": change_group_desktop_static,
    "database_crontab_task": scheduler_database,
    "desktop_crontab_task": desktop_crontab_task,
    "delete_crontab_task": delete_crontab_task,
    "create_voi_template": create_voi_template,
    "delete_voi_template": delete_template,
    "update_voi_template": update_voi_template,
    "start_voi_template": start_template,
    "stop_voi_template": start_template,
    "reboot_voi_template": start_template,
    "hard_reboot_voi_template": start_template,
    "reset_voi_template": start_template,
    "copy_voi_template": copy_voi_template,
    "rollback_voi_template": rollback_voi_template,
    "create_voi_edu_group": create_voi_edu_group,
    "delete_voi_edu_group": delete_edu_group,
    "update_voi_edu_group": update_voi_edu_group,
    "create_voi_edu_desktop": create_voi_edu_desktop,
    "delete_voi_edu_desktop": delete_edu_desktop,
    "active_voi_edu_desktop": start_edu_desktop,
    "inactive_voi_edu_desktop": start_edu_desktop,
    "default_voi_edu_desktop": default_voi_edu_desktop,
    "update_voi_edu_desktop": update_voi_edu_desktop,
    "operation_crontab_task": operation_crontab_task,
    "warning_crontab_task": warning_crontab_task,
    "create_warn_setup": create_warn_setup,
    "update_warn_setup": update_warn_setup,
    "operation_update_crontab_task": update_crontab_task,
    "warning_update_crontab_task": update_crontab_task,
}
