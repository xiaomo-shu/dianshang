import json
import logging
from datetime import datetime, timedelta
from common import constants
from common.utils import create_uuid, create_md5
from common.errcode import get_error_result
from yzy_server.database import apis as db_api
from yzy_server.apis.v1.controllers.system_ctl import CrontabController



logger = logging.getLogger(__name__)
WEEKDAY_MAP = {
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
    "sun": 7
}


class TermController(object):

    def _check_course_num_map(self, data):
        """
        校验每节课的上下课时间
        :param
        data:
        {
            "1": "08:00-08:45",
            "2": "09:00-09:45",
            "3": "10:00-10:45",
            "4": "11:00-11:45",
            "5": "14:00-14:45",
            "6": "15:00-15:45",
            "7": "16:00-16:45",
            "8": "17:00-17:45",
            "9": "19:00-19:45",
            "10": "20:00-20:45"
        }
        """
        try:
            _d = dict()
            for k, v in data.items():
                _d[int(k)] = v

            nums = sorted(list(_d.keys()))
            if nums != list(range(1, len(nums) + 1)):
                return get_error_result("ParamError", data={"course_num_map_keys": nums})

            # 结束时间不得早于开始时间，如：第一节课的下课时间不能早于第一节课的上课时间，不得晚于第二节课的开始时间
            last_end_obj = datetime.strptime("2020/01/01 00:00", "%Y/%m/%d %H:%M")
            for num in range(1, len(nums) + 1):
                start, end = _d[num].split("-")
                start_obj = datetime.strptime("2020/01/01 %s" % start, "%Y/%m/%d %H:%M")
                end_obj = datetime.strptime("2020/01/01 %s" % end, "%Y/%m/%d %H:%M")
                if start_obj > end_obj and start_obj.hour <= 18:
                    return get_error_result("TermDetailError", detail_msg="上课时间不能晚于下课时间", data={
                        "course_num_map_start": start,
                        "course_num_map_end": end
                    })
                if start_obj < last_end_obj:
                    return get_error_result("TermDetailError", detail_msg="下课时间不能晚于下一节课的上课时间", data={
                        "course_num_map_start": start,
                        "course_num_map_last_end": last_end_obj.date().strftime("%Y/%m/%d")
                    })
                last_end_obj = end_obj

        except Exception as e:
            logger.exception("_check_course_num_map failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

        return None

    def _check_term_time_detail(self, data):
        """
        校验学期开始、结束日期、课堂时长、课间时长、上下午晚上开始时间
        :param data
           {
               "name": "2020年上学期",
               "start": "2020/09/01",
               "end": "2021/02/01",
               "duration": 45,
               "break_time": 10,
               "morning": "08:00",
               "afternoon": "14:00",
               "evening": "19:00",
               "morning_count": 4,
               "afternoon_count": 4,
               "evening_count": 2,
               "course_num_map": {
                   "1": "08:00-08:45",
                   "2": "09:00-09:45",
                   "3": "10:00-10:45",
                   "4": "11:00-11:45",
                   "5": "14:00-14:45",
                   "6": "15:00-15:45",
                   "7": "16:00-16:45",
                   "8": "17:00-17:45",
                   "9": "19:00-19:45",
                   "10": "20:00-20:45"
               }
            }
        """
        try:
            if list(data.keys()) != ["name", "start", "end", "duration", "break_time", "morning", "afternoon", "evening",
                                     "morning_count", "afternoon_count", "evening_count", "course_num_map"]:
                return get_error_result("ParamError", data={"keys": list(data.keys())})

            try:
                start = datetime.strptime(data["start"], '%Y/%m/%d').date()
                end = datetime.strptime(data["end"], '%Y/%m/%d').date()
            except Exception:
                return get_error_result("ParamError", data={"start": data["start"], "end": data["end"]})

            # 学期结束日期不能为过去时间
            if end < datetime.now().date():
                return get_error_result("TermEndPassedError")

            # 学期开始时间至学期结束时间为课程表存在的学期长度，开始时间不得晚于结束时间
            if start > end:
                return get_error_result("TermStartLaterThanEndError")

            for k in ["duration", "break_time"]:
                data[k] = int(data[k])
                if data[k] < 0:
                    return get_error_result("ParamError", data={k: data[k]})

            for k in ["morning_count", "afternoon_count", "evening_count"]:
                data[k] = int(data[k])
                if data[k] < 0:
                    return get_error_result("ParamError", data={k: data[k]})

            if data["duration"] == 0:
                logger.error('ParamError: duration = 0')
                return get_error_result("ParamError", data={"duration": data["duration"]})

            if data["morning_count"] + data["afternoon_count"] + data["evening_count"] == 0:
                return get_error_result("ParamError", data={
                    "morning_count": data["morning_count"],
                    "afternoon_count": data["afternoon_count"],
                    "evening_count": data["evening_count"]
                })

            if data["morning_count"] == 0:
                data["morning"] = ""
            else:
                # 上午开始时间不能低于12点
                data["morning"] = data["course_num_map"]["1"].split("-")[0]
                morning = datetime.strptime("%s %s" % (data["start"], data["morning"]), "%Y/%m/%d %H:%M")
                if morning > datetime.strptime("%s %s" % (data["start"], "12:00"), "%Y/%m/%d %H:%M"):
                    return get_error_result("TermDetailError", detail_msg="上午开始时间应在12点之前")

            if data["afternoon_count"] == 0:
                data["afternoon"] = ""
            else:
                # 下午开始时间应在12点至18点之间
                data["afternoon"] = data["course_num_map"][str(data["morning_count"] + 1)].split("-")[0]
                afternoon = datetime.strptime("%s %s" % (data["start"], data["afternoon"]), "%Y/%m/%d %H:%M")
                if afternoon < datetime.strptime("%s %s" % (data["start"], "12:00"), "%Y/%m/%d %H:%M") \
                        or afternoon > datetime.strptime("%s %s" % (data["start"], "18:00"), "%Y/%m/%d %H:%M"):
                    return get_error_result("TermDetailError", detail_msg="下午开始时间应在12点至18点之间")

            if data["evening_count"] == 0:
                data["evening"] = ""
            else:
                # 晚上开始时间应在18点之后
                data["evening"] = data["course_num_map"][str(data["morning_count"] + data["afternoon_count"] + 1)].split("-")[0]
                evening = datetime.strptime("%s %s" % (data["start"], data["evening"]), "%Y/%m/%d %H:%M")
                if evening < datetime.strptime("%s %s" % (data["start"], "18:00"), "%Y/%m/%d %H:%M"):
                    return get_error_result("TermDetailError", detail_msg="晚上开始时间应在18点之后")

            # interval = data["morning_count"] * data["duration"]
            # if morning + timedelta(minutes=interval) > afternoon:
            #     return get_error_result("TermDetailError", detail_msg="上午结束时间不能晚于下午开始时间")
            #
            # interval = data["afternoon_count"] * data["duration"]
            # if afternoon + timedelta(minutes=interval) > evening:
            #     return get_error_result("TermDetailError", detail_msg="下午结束时间不能晚于晚上开始时间")
            #
            # interval = data["evening_count"] * data["duration"]
            # if evening + timedelta(minutes=interval) > morning + timedelta(hours=24):
            #     return get_error_result("TermDetailError", detail_msg="晚上结束时间不能晚于次日上午开始时间")

            # interval = data["morning_count"] * data["duration"] + (data["morning_count"] - 1) * data["break_time"]
            # if morning + timedelta(minutes=interval) > afternoon:
            #     # logger.error('ParamError: morning + timedelta(minutes=interval) > afternoon')
            #     return get_error_result("ParamError", data={
            #         "morning": data["morning"],
            #         "morning_count": data["morning_count"],
            #         "duration": data["duration"],
            #         "break_time": data["break_time"],
            #         "afternoon": data["afternoon"]
            #     })
            # interval = data["afternoon_count"] * data["duration"] + (data["afternoon_count"] - 1) * data["break_time"]
            # if afternoon + timedelta(minutes=interval) > evening:
            #     # logger.error('ParamError: afternoon + timedelta(minutes=interval) > evening')
            #     return get_error_result("ParamError", data={
            #         "afternoon": data["afternoon"],
            #         "afternoon_count": data["afternoon_count"],
            #         "duration": data["duration"],
            #         "break_time": data["break_time"],
            #         "evening": data["evening"]
            #     })
            # interval = data["evening_count"] * data["duration"] + (data["evening_count"] - 1) * data["break_time"]
            # if evening + timedelta(minutes=interval) > morning + timedelta(hours=24):
            #     # logger.error('ParamError: evening + timedelta(minutes=interval) > morning + timedelta(hours=24)')
            #     return get_error_result("ParamError", data={
            #         "evening": data["evening"],
            #         "evening_count": data["evening_count"],
            #         "duration": data["duration"],
            #         "break_time": data["break_time"],
            #         "morning": data["morning"]
            #     })

        except Exception as e:
            logger.exception("_check_term_time_detail failed: %s" % str(e), exc_info=True)
            return get_error_result("ParamError", data=str(e))

        return None

    def _generate_weeks_num_map(self, start, end):
        """
        根据学期开始日期、结束日期，生成该学期的所有周
        :param start: "2020/09/01"
        :param end: "2021/02/01"
        :return
        {
            1: ["2020/08/31", "2020/09/06"],
            2: ["2020/09/07", "2020/09/13"],
            ...
        }
        """
        weeks_num_map = dict()
        # 首尾非整周自动补齐为整周
        week_start = datetime.strptime(start, '%Y/%m/%d').date()
        week_start = week_start - timedelta((week_start.isoweekday() - 1))
        end_date = datetime.strptime(end, '%Y/%m/%d').date()
        end_date = end_date + timedelta((7 - end_date.isoweekday()))
        i = 1
        while True:
            if week_start > end_date:
                break
            week_end = week_start + timedelta((7 - week_start.isoweekday()))
            if week_end > end_date:
                week_end = end_date
            weeks_num_map[i] = [week_start.strftime("%Y/%m/%d"), week_end.strftime("%Y/%m/%d")]
            week_start = week_end + timedelta(1)
            i += 1
        return weeks_num_map

    def _check_term_duplicate(self, start, end, exclued_uuid=""):
        """
        校验新学期期间是否与已有学期重叠
        :param start: "2020/09/01"
        :param end: "2021/02/01"
        :param exclued_uuid: 排除学期的uuid
        :return:
        """
        try:
            exsit_term_obj_list = db_api.get_term_with_all({})
            if exsit_term_obj_list:
                new_start = datetime.strptime(start, '%Y/%m/%d').date()
                new_end = datetime.strptime(end, '%Y/%m/%d').date()
                for exsit_term_obj in exsit_term_obj_list:
                    if exsit_term_obj.uuid != exclued_uuid:
                        exist_start = datetime.strptime(exsit_term_obj.start, '%Y/%m/%d').date()
                        exist_end = datetime.strptime(exsit_term_obj.end, '%Y/%m/%d').date()
                        if exist_start <= new_end and new_start <= exist_end:
                            return get_error_result("TermDuplicateError", name=exsit_term_obj.name)
            return None
        except Exception as e:
            logger.exception("_check_term_duplicate failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def create(self, data):
        """
        创建新学期
        :param data:
        {
           "name": "2020年上学期",
           "start": "2020/09/01",
           "end": "2021/02/01",
           "duration": 45,
           "break_time": 10,
           "morning": "08:00",
           "afternoon": "14:00",
           "evening": "19:00",
           "morning_count": 4,
           "afternoon_count": 4,
           "evening_count": 2,
           "course_num_map": {
               "1": "08:00-08:45",
               "2": "09:00-09:45",
               "3": "10:00-10:45",
               "4": "11:00-11:45",
               "5": "14:00-14:45",
               "6": "15:00-15:45",
               "7": "16:00-16:45",
               "8": "17:00-17:45",
               "9": "19:00-19:45",
               "10": "20:00-20:45"
           }
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)

            check_ret = self._check_course_num_map(data["course_num_map"])
            if check_ret:
                return check_ret

            check_ret = self._check_term_time_detail(data)
            if check_ret:
                return check_ret

            if db_api.get_term_with_first({"name": data["name"]}):
                return get_error_result("TermNameExist")

            # 校验新学期期间是否与已有学期重叠
            check_ret = self._check_term_duplicate(data["start"], data["end"])
            if check_ret:
                return check_ret

            data["uuid"] = create_uuid()
            data["weeks_num_map"] = self._generate_weeks_num_map(data["start"], data["end"])

            # 添加学期的定时任务
            task_uuid = self._add_crontab_task(
                term_uuid=data["uuid"],
                name=data["name"],
                start_date=data["start"],
                end_date=data["end"],
                course_num_map=data["course_num_map"],
                weeks_num_map=data["weeks_num_map"]
            )

            if task_uuid:
                data["crontab_task_uuid"] = task_uuid
                data["course_num_map"] = json.dumps(data["course_num_map"])
                data["weeks_num_map"] = json.dumps(data["weeks_num_map"])

                # 新创建学期时，所有教学分组的状态默认为已启用
                group_status_map = dict()
                group_obj_list = db_api.get_group_with_all({"group_type": constants.EDUCATION_GROUP})
                for group_obj in group_obj_list:
                    group_status_map[group_obj.uuid] = constants.COURSE_SCHEDULE_ENABLED
                data["group_status_map"] = json.dumps(group_status_map)

                db_api.create_term(data)
                logger.info("insert in yzy_term success: %s" % data)
                return get_error_result()
            else:
                logger.info("add course crontab task failed")
                return get_error_result("OtherError")

        except Exception as e:
            logger.exception("create term failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def update(self, data):
        """
        编辑指定学期
        :param data:
        {
           "uuid": "062d6d14-97c1-448d-a9fb-67367fdf843b",
           "name": "2020年上学期",
           "start": "2020/09/01",
           "end": "2021/02/01",
           "duration": 45,
           "break_time": 10,
           "morning": "08:00",
           "afternoon": "14:00",
           "evening": "19:00",
           "morning_count": 4,
           "afternoon_count": 4,
           "evening_count": 2,
           "course_num_map": {
               "1": "08:00-08:45",
               "2": "09:00-09:45",
               "3": "10:00-10:45",
               "4": "11:00-11:45",
               "5": "14:00-14:45",
               "6": "15:00-15:45",
               "7": "16:00-16:45",
               "8": "17:00-17:45",
               "9": "19:00-19:45",
               "10": "20:00-20:45"
           }
        :return:
        """
        try:
            logger.info("data: %s" % data)
            uuid = data.pop("uuid", None)
            if not uuid:
                return get_error_result("ParamError")

            term_obj = db_api.get_term_with_first({"uuid": uuid})
            if not term_obj:
                return get_error_result("TermNotExist")

            name_exist_obj = db_api.get_term_with_first({"name": data["name"]})
            # 如果学期下已有课表，只允许编辑学期名称
            if db_api.get_course_schedule_with_all({"term_uuid": uuid}):
                if list(data.keys()) != ["name"]:
                    return get_error_result("TermOccupiedError")

                if name_exist_obj and name_exist_obj.uuid != uuid:
                    return get_error_result("TermNameExist")

                term_obj.update({"name": data["name"]})
                crontab_task_obj = db_api.get_crontab_first({"uuid": term_obj.crontab_task_uuid})
                if crontab_task_obj:
                    crontab_task_obj.update({"desc": "%s_课表定时任务" % term_obj.name})
                logger.info("update in yzy_term success: {'name': %s}" % term_obj.name)
                return get_error_result()

            # 如果学期下没有课表，可以编辑所有项
            check_ret = self._check_course_num_map(data["course_num_map"])
            if check_ret:
                return check_ret

            check_ret = self._check_term_time_detail(data)
            if check_ret:
                return check_ret

            update_dict = dict()
            for k, v in data.items():
                if isinstance(v, dict):
                    data[k] = json.dumps(data[k])
                if data[k] != getattr(term_obj, k):
                    if k == "name" and name_exist_obj and name_exist_obj.uuid != uuid:
                        return get_error_result("TermNameExist")
                    update_dict[k] = data[k]

            # 如果修改了学期开始，则校验新学期期间是否与已有学期重叠
            if "start" in update_dict.keys() or "end" in update_dict.keys():
                check_ret = self._check_term_duplicate(data["start"], data["end"], exclued_uuid=uuid)
                if check_ret:
                    return check_ret
                update_dict["weeks_num_map"] = json.dumps(self._generate_weeks_num_map(data["start"], data["end"]))

            if update_dict:
                # 编辑学期时，删除原有定时任务，重新设置
                if not CrontabController().remove_course_crontab_job(term_obj.crontab_task_uuid):
                    return get_error_result("OtherError")

                task_uuid = self._add_crontab_task(
                    term_uuid=term_obj.uuid,
                    name=update_dict.get("name", term_obj.name),
                    start_date=update_dict.get("start", term_obj.start),
                    end_date=update_dict.get("end", term_obj.end),
                    course_num_map=json.loads(update_dict.get("course_num_map", term_obj.course_num_map)),
                    weeks_num_map=json.loads(update_dict.get("weeks_num_map", term_obj.weeks_num_map))
                )

                if task_uuid:
                    update_dict["crontab_task_uuid"] = task_uuid
                    term_obj.update(update_dict)
                    logger.info("update in yzy_term success: %s" % update_dict)
                    return get_error_result()
                else:
                    logger.info("add course crontab task failed")
                    return get_error_result("OtherError")

            return get_error_result()
        except Exception as e:
            logger.exception("update term failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def delete(self, data):
        """
        删除学期及其关联的所有课表
        :param data: {"uuid": "c9d3cda3-9977-44be-a758-b92c622be97e"}
        :return:
        """
        try:
            logger.info("data: %s" % data)
            term_uuid = data.get("uuid", None)
            if not term_uuid:
                return get_error_result("ParamError")

            term_obj = db_api.get_term_with_first({"uuid": term_uuid})
            if not term_obj:
                return get_error_result("TermNotExist")

            # 删除学期的定时任务
            if not CrontabController().remove_course_crontab_job(term_obj.crontab_task_uuid):
                return get_error_result("OtherError")

            # 找出该学期下所有课表的引用模板的uuid
            template_uuids = db_api.get_distinct_course_template_uuids_by_course_schedule({"term_uuid": term_uuid})
            template_uuids = [tuple_[0] for tuple_ in template_uuids]

            # 删除该学期下所有课表
            ds_ret = db_api.delete_course_schedule_many({"term_uuid": term_uuid})
            logger.info("delete many[%s] in yzy_course_schedule success where term_uuid[%s]" % (ds_ret, term_uuid))

            # 删除该学期下所有课表的引用模板
            dt_ret = db_api.delete_course_template_many_by_uuids(template_uuids)
            logger.info("delete many[%s] in yzy_course_template success where uuid in [%s]" % (dt_ret, template_uuids))

            # 删除该学期下所有课表的引用模板包含的课程
            dc_ret = db_api.delete_course_many_by_course_template_uuids(template_uuids)
            logger.info("delete many[%s] in yzy_course success where course_template_uuid in [%s]" % (dc_ret, template_uuids))

            # 删除学期
            term_obj.soft_delete()
            logger.info("delete uuid[%s] in yzy_term success" % term_uuid)
            return get_error_result()
        except Exception as e:
            logger.exception("delete term failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def _add_crontab_task(self, term_uuid, name, start_date, end_date, course_num_map, weeks_num_map):
        """
        {
            "1": "08:00-08:45",
            "2": "09:00-09:45",
            "3": "10:00-10:45",
            "4": "11:00-11:45",
            "5": "14:00-14:45",
            "6": "15:00-15:45",
            "7": "16:00-16:45",
            "8": "17:00-17:45",
            "9": "19:00-19:45",
            "10": "20:00-20:45"
        }
        """
        # 添加学期的定时任务
        crontab_time_list = list()
        for k, v in course_num_map.items():
            start, end = v.split("-")
            # 桌面组提前5分钟激活、开机
            b5_obj = datetime.strptime("2020/01/01 %s" % start, "%Y/%m/%d %H:%M") - timedelta(minutes=5)
            crontab_time_list.append({
                "course_num": k,
                "cmd": "active",
                "hour": b5_obj.hour,
                "minute": b5_obj.minute
            })
            end_hour, end_minute = end.split(":")
            crontab_time_list.append({
                "course_num": k,
                "cmd": "inactive",
                "hour": int(end_hour),
                "minute": int(end_minute)
            })

        _d = {
            "name": "course_schedule_cron",
            "desc": "%s_课表定时任务" % name,
            "start_date": start_date.replace("/", "-"),
            "end_date": end_date.replace("/", "-"),
            "cron": crontab_time_list,
            "status": 1,
            "term_uuid": term_uuid,
            "weeks_num_map": weeks_num_map
        }

        return CrontabController().add_course_schedule_crontab(_d)



class CourseScheduleController(object):

    def _check_course(self, course, group_uuid, course_num_map, course_ret_list, desktops):
        """
        :param course: 课程内容列表
        [
            {
                "course_num": 1,
                "mon": {
                          "name": "math_desktop",
                          "uuid": "f56036ca-e91d-440c-8e33-26a18c1f7220"
                },
                "tue": {
                          "name": "",
                          "uuid": ""
                },
                "wed": {
                          "name": "",
                          "uuid": ""
                },
                "thu": {
                          "name": "",
                          "uuid": ""
                },
                "fri": {
                          "name": "math_desktop",
                          "uuid": "f56036ca-e91d-440c-8e33-26a18c1f7220"
                },
                "sat": {
                          "name": "",
                          "uuid": ""
                },
                "sun": {
                          "name": "",
                          "uuid": ""
                }
            },
            ...
        ]
        :param group_uuid: 教学分组uuid
        :param course_num_map: 上课时间映射表
        {
           "1": "08:00-08:45",
           "2": "09:00-09:45",
           "3": "10:00-10:45",
           "4": "11:00-11:45",
           "5": "14:00-14:45",
           "6": "15:00-15:45",
           "7": "16:00-16:45",
           "8": "17:00-17:45",
           "9": "19:00-19:45",
           "10": "20:00-20:45"
        }
        :param course_ret_list: 空列表，用于保存有效的课程值
        :param desktops: 空字典，用于保存教学桌面组uuid与名称的映射关系
        :return:
        """
        try:
            course_num_list = [str(_d["course_num"]) for _d in course]
            if course_num_list != list(course_num_map.keys()):
                return get_error_result("ParamError", data={"course_num_list": course_num_list})

            # 提取出有效值（课表中非空的格子）
            for _d in course:
                for name, num in WEEKDAY_MAP.items():
                    desktop_dict = _d.get(name, dict())
                    if desktop_dict.get("uuid", ""):
                        course_ret_list.append(
                            {
                                "desktop_uuid": desktop_dict["uuid"],
                                "weekday": num,
                                "course_num": _d["course_num"],
                            }
                        )

            for _d in course_ret_list:
                desktop_obj = db_api.get_desktop_by_uuid(_d.get("desktop_uuid", ""))
                if not desktop_obj:
                    return get_error_result("EduDesktopNotExist")
                if desktop_obj.group_uuid != group_uuid:
                    return get_error_result("EduDesktopNotBelongGroup")
                if desktop_obj.uuid not in desktops.keys():
                    desktops[desktop_obj.uuid] = desktop_obj.name

            return None
        except Exception as e:
            logger.exception("_check_course failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def update(self, data):
        """
        创建、编辑、删除一个周的课表
        :param data:
        {
            "term_uuid": "5e5244f0-b269-4f2d-a8f8-38e946b07942",
            "group_uuid": "41b212d6-3ef4-49f1-851d-424cb4559261",
            "week_num": 1,
            "course": [
                {
                    "course_num": 1,
                    "mon": {
                              "name": "math_desktop",
                              "uuid": "f56036ca-e91d-440c-8e33-26a18c1f7220"
                    },
                    "tue": {
                              "name": "",
                              "uuid": ""
                    },
                    "wed": {
                              "name": "",
                              "uuid": ""
                    },
                    "thu": {
                              "name": "",
                              "uuid": ""
                    },
                    "fri": {
                              "name": "math_desktop",
                              "uuid": "f56036ca-e91d-440c-8e33-26a18c1f7220"
                    },
                    "sat": {
                              "name": "",
                              "uuid": ""
                    },
                    "sun": {
                              "name": "",
                              "uuid": ""
                    }
                },
                ...
            ]
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)

            # name = data.get("name", None)
            # term = data.get("term", None)
            # term_time_detail = data.get("term_time_detail", None)
            # course_num_map = data.get("course_num_map", None)

            term_uuid = data.get("term_uuid", None)
            group_uuid = data.get("group_uuid", None)
            week_num = data.get("week_num", None)
            course = data.get("course", None)
            if not all([term_uuid, week_num, group_uuid, course]):
                return get_error_result("ParamError", data={"keys": ["term_uuid", "week_num", "group_uuid", "course"]})

            # if not term in [0, 1]:
            #     logger.error('ParamError: term')
            #     return get_error_result("ParamError")
            #
            # if not self._check_term_time_detail(term_time_detail):
            #     return get_error_result("ParamError")
            #
            # weeks_num_map = self._generate_weeks_num_map(term_time_detail["start"], term_time_detail["end"])
            # if week_num not in weeks_num_map.keys():
            #     logger.error('ParamError: week_num')
            #     return get_error_result("ParamError")
            #
            # course_num_map = self._check_course_num_map(course_num_map)
            # if not course_num_map:
            #     logger.error('ParamError: course_num_map')
            #     return get_error_result("ParamError")
            #
            # if db_api.get_course_schedule_with_first({"name": name}):
            #     return get_error_result("CourseScheduleNameExist")

            term_obj = db_api.get_term_with_first({"uuid": term_uuid})
            if not term_obj:
                return get_error_result("TermNotExist")

            # 校验课表内容，并提取出有效值（课表中非空的格子）
            course_ret_list = list()
            desktops = dict()
            course_num_map = json.loads(term_obj.course_num_map)
            check_ret = self._check_course(course, group_uuid, course_num_map, course_ret_list, desktops)
            if check_ret:
                return check_ret

            # 用term_uuid、group_uuid、week_num三个字段代替uuid的作用，唯一确定一条yzy_course_schedule数据
            course_schedule_obj = db_api.get_course_schedule_with_first({
                "term_uuid": term_uuid,
                "group_uuid": group_uuid,
                "week_num": week_num})

            # 数据库中找不到，并且课表内容不为空，说明是要创建新课表
            if not course_schedule_obj and course_ret_list:
                self._create(term_uuid, group_uuid, week_num, course_ret_list, desktops)
            # 数据库中能找到，并且课表内容不为空，说明是要编辑此课表
            elif course_schedule_obj and course_ret_list:
                self._update(course_schedule_obj, course_ret_list, desktops)
            # 数据库中能找到，并且课表内容为空，说明是要删除此课表
            elif course_schedule_obj and not course_ret_list:
                self._delete(course_schedule_obj)
            # 数据库中找不到，并且课表内容为空，说明是传参错误
            else:
                return get_error_result()
                # return get_error_result("ParamError", data={"course": data["course"]})

            return get_error_result()

            # # 创建课表后默认启用课表
            # course_schedule_obj = db_api.get_course_schedule_with_first(course_schedule["uuid"])
            # ret = self.enable({"uuids": [course_schedule["uuid"]]})
            # if ret.get("code", -1) == 0:
            #     course_schedule_obj["status"] = 0
            #     course_schedule_obj.softupdate()
            #     return get_error_result()
            # else:
            #     # # 启用失败则删除课表
            #     # self._delete_course_template([course_schedule_obj.course_template_uuid])
            #     # course_schedule_obj.soft_delete()
            #     return get_error_result("AddCourseScheduleCrontabError")
        except Exception as e:
            logger.exception("update course_schedule failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def _create(self, term_uuid, group_uuid, week_num, course_ret_list, desktops):
        group_obj = db_api.get_group_with_first({"uuid": group_uuid})
        if not group_obj:
            return get_error_result("EduGroupNotExist")
        if group_obj.group_type != constants.EDUCATION_GROUP:
            return get_error_result("CourseNotEduGroup")

        course_template = {
            "uuid": create_uuid(),
            "desktops": json.dumps(desktops)
        }

        course_values_list = [{
            "uuid": create_uuid(),
            "course_template_uuid": course_template["uuid"],
            "desktop_uuid": _d["desktop_uuid"],
            "weekday": _d["weekday"],
            "course_num": _d["course_num"]
        } for _d in course_ret_list]

        # 课表创建后默认启用
        course_schedule = {
            "uuid": create_uuid(),
            "term_uuid": term_uuid,
            "group_uuid": group_uuid,
            "course_template_uuid": course_template["uuid"],
            "week_num": week_num,
            "course_md5": create_md5(json.dumps(course_ret_list)),
            "status": constants.COURSE_SCHEDULE_ENABLED
        }

        db_api.create_course_template(course_template)
        logger.info("insert in yzy_course_template success: %s" % course_template)
        db_api.create_course_many(course_values_list)
        logger.info("insert many[%d] in yzy_course success: course_template_uuid[%s]"
                    % (len(course_values_list), course_template["uuid"]))
        db_api.create_course_schedule_many([course_schedule])
        logger.info("insert in yzy_course_schedule success: %s" % course_schedule)

    def _update(self, course_schedule_obj, course_ret_list, desktops):
        course_md5 = create_md5(json.dumps(course_ret_list))
        if course_md5 != course_schedule_obj.course_md5:
            course_template = {
                "uuid": create_uuid(),
                "desktops": json.dumps(desktops)
            }

            course_values_list = [{
                "uuid": create_uuid(),
                "course_template_uuid": course_template["uuid"],
                "desktop_uuid": _d["desktop_uuid"],
                "weekday": _d["weekday"],
                "course_num": _d["course_num"]
            } for _d in course_ret_list]

            # 创建新模板和课程
            db_api.create_course_template(course_template)
            logger.info("insert in yzy_course_template success: %s" % course_template)
            db_api.create_course_many(course_values_list)
            logger.info("insert many[%d] in yzy_course success: course_template_uuid[%s]"
                        % (len(course_values_list), course_template["uuid"]))

            # 记录旧模板uuid
            old_tmplate_uuid = course_schedule_obj.course_template_uuid

            # 更新课表中的引用模板、课程md5
            update_dict = {
                "course_template_uuid": course_template["uuid"],
                "course_md5": course_md5
            }
            course_schedule_obj.update(update_dict)
            logger.info("update uuid[%s] in yzy_course_schedule success: %s" % (course_schedule_obj.uuid, update_dict))

            # 删除没有被任何课表所引用的旧模板及其包含的课程
            self._delete_course_template([old_tmplate_uuid])

    def _delete(self, course_schedule_obj):
        # 记录课表uuid，模板uuid
        uuid = course_schedule_obj.uuid
        course_template_uuid = course_schedule_obj.course_template_uuid

        # 删除课表
        course_schedule_obj.soft_delete()
        logger.info("delete uuid[%s] in yzy_course_schedule success" % uuid)

        # 删除没有被任何课表所引用的模板及其包含的课程
        self._delete_course_template([course_template_uuid])

    def delete(self, data):
        """
        删除指定学期、教学分组下的所有课表
        :param data:
        {
            "term_uuid": "062d6d14-97c1-448d-a9fb-67367fdf843b",
            "group_uuid": "41b212d6-3ef4-49f1-851d-424cb4559261"
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)
            term_uuid = data.get("term_uuid", None)
            group_uuid = data.get("group_uuid", None)
            if not term_uuid or not group_uuid:
                return get_error_result("ParamError")

            if not db_api.get_term_with_first({"uuid": term_uuid}):
                return get_error_result("TermNotExist")

            if not db_api.get_group_with_first({"uuid": group_uuid}):
                return get_error_result("EduGroupNotExist")

            template_uuids = db_api.get_distinct_course_template_uuids_by_course_schedule({
                "term_uuid": term_uuid,
                "group_uuid": group_uuid})
            template_uuids = [tuple_[0] for tuple_ in template_uuids]

            ds_ret = db_api.delete_course_schedule_many({
                "term_uuid": term_uuid,
                "group_uuid": group_uuid})
            logger.info("delete many[%s] in yzy_course_schedule success where term_uuid[%s] group_uuid[%s] "
                        % (ds_ret, term_uuid, group_uuid))

            dt_ret = db_api.delete_course_template_many_by_uuids(template_uuids)
            logger.info("delete many[%s] in yzy_course_template success where uuid in [%s]"
                        % (dt_ret, template_uuids))

            dc_ret = db_api.delete_course_many_by_course_template_uuids(template_uuids)
            logger.info("delete many[%s] in yzy_course success where course_template_uuid in [%s]"
                        % (dc_ret, template_uuids))

            return get_error_result()
        except Exception as e:
            logger.exception("delete course_schedule failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def apply(self, data):
        """
        将指定课表批量应用到多个周
        :param data:
        {
            "uuid": "886cc37d-121c-4f81-a933-f002b5d86094",
            "week_nums": [1, 3, 5, 7]
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)
            uuid = data.get("uuid", None)
            week_nums = data.get("week_nums", None)
            if not uuid or not week_nums or not isinstance(week_nums, list) or not all([isinstance(i, int) for i in week_nums]):
                return get_error_result("ParamError", data={"keys": ["uuid", "week_nums"]})

            target_cs_obj = db_api.get_course_schedule_with_first({"uuid": uuid})
            if not target_cs_obj:
                return get_error_result("CourseScheduleNotExist")

            # 校验批量应用的周是否合法
            term_obj = db_api.get_term_with_first({"uuid": target_cs_obj.term_uuid})
            weeks_num_map = json.loads(term_obj.weeks_num_map)
            week_nums = set([num for num in week_nums if num != target_cs_obj.week_num])
            for week_num in week_nums:
                if str(week_num) not in weeks_num_map.keys():
                    # logger.error("ParamError: week_nums %d" % week_num)
                    return get_error_result("ParamError", data={"week_nums": week_num})

            # 找出该学期、该教学分组下所有已有课表的周
            cs_list = db_api.get_course_schedule_with_all({
                "term_uuid": target_cs_obj.term_uuid,
                "group_uuid": target_cs_obj.group_uuid
            })
            occupied_weeks = dict()
            for cs_obj in cs_list:
                occupied_weeks[cs_obj.week_num] = cs_obj

            cs_values_list = list()
            for week_num in week_nums:
                # 如果批量应用的周已有课表，则覆盖，将其引用模板更新为target模板
                if week_num in occupied_weeks.keys():
                    occupied_weeks[week_num].update({"course_template_uuid": target_cs_obj.course_template_uuid})
                    logger.info("update uuid[%s] week_num[%s] in yzy_course_schedule success: {'course_template_uuid': %s}"
                                % (str(week_num), occupied_weeks[week_num].uuid, occupied_weeks[week_num].course_template_uuid))
                # 如果批量应用的周没有课表，则创建
                else:
                    cs_values_list.append(
                        {
                            "uuid": create_uuid(),
                            "term_uuid": target_cs_obj.term_uuid,
                            "group_uuid": target_cs_obj.group_uuid,
                            "course_template_uuid": target_cs_obj.course_template_uuid,
                            "week_num": week_num,
                            "course_md5": target_cs_obj.course_md5,
                            "status": 1
                        }
                    )

            db_api.create_course_schedule_many(cs_values_list)
            logger.info("insert many[%d] in yzy_course_schedule success: course_template_uuid[%s]"
                        % (len(cs_values_list), target_cs_obj.course_template_uuid))

            return get_error_result()
        except Exception as e:
            logger.exception("apply course_schedule failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def enable(self, data):
        """
        启用指定学期、教学分组下的所有课表
        :param data:
        {
            "term_uuid": "062d6d14-97c1-448d-a9fb-67367fdf843b",
            "group_uuid": "41b212d6-3ef4-49f1-851d-424cb4559261"
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)
            term_uuid = data.get("term_uuid", None)
            group_uuid = data.get("group_uuid", None)
            if not term_uuid or not group_uuid:
                return get_error_result("ParamError", data={"keys": ["term_uuid", "group_uuid"]})

            term_obj = db_api.get_term_with_first({"uuid": term_uuid})
            if not term_obj:
                return get_error_result("TermNotExist")

            if not db_api.get_group_with_first({"uuid": group_uuid}):
                return get_error_result("EduGroupNotExist")

            # 更新该学期的group_status_map字段（保存了教学桌面组的课表启用状态）
            group_status_map = json.loads(term_obj.group_status_map)
            if group_status_map.get(group_uuid, None) != constants.COURSE_SCHEDULE_ENABLED:
                group_status_map[group_uuid] = constants.COURSE_SCHEDULE_ENABLED
                term_obj.update({"group_status_map": json.dumps(group_status_map)})
                logger.info("update uuid[%s] in yzy_term success : {'group_status_map': {'%s': %s}}"
                    % (term_uuid, group_uuid, constants.COURSE_SCHEDULE_ENABLED))

            # 找出该学期、该教学分组下的所有课表，标记为启用
            ret = db_api.update_course_schedule_many(
                value_dict={"status": constants.COURSE_SCHEDULE_ENABLED},
                item={"term_uuid": term_uuid, "group_uuid": group_uuid}
            )

            logger.info("update many[%s] in yzy_course_schedule success where term_uuid[%s], group_uuid[%s]: {'status': %s}"
                        % (ret, term_uuid, group_uuid, constants.COURSE_SCHEDULE_ENABLED))

            return get_error_result()
        except Exception as e:
            logger.exception("enable course_schedule failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def disable(self, data):
        """
        禁用指定学期、教学分组下的所有课表
        :param data:
        {
            "term_uuid": "062d6d14-97c1-448d-a9fb-67367fdf843b",
            "group_uuid": "41b212d6-3ef4-49f1-851d-424cb4559261"
        }
        :return:
        """
        try:
            logger.info("data: %s" % data)
            term_uuid = data.get("term_uuid", None)
            group_uuid = data.get("group_uuid", None)
            if not term_uuid or not group_uuid:
                return get_error_result("ParamError", data={"keys": ["term_uuid", "group_uuid"]})

            term_obj = db_api.get_term_with_first({"uuid": term_uuid})
            if not term_obj:
                return get_error_result("TermNotExist")

            if not db_api.get_group_with_first({"uuid": group_uuid}):
                return get_error_result("EduGroupNotExist")

            # 更新该学期的group_status_map字段（保存了教学桌面组的课表启用状态）
            group_status_map = json.loads(term_obj.group_status_map)
            if group_status_map.get(group_uuid, None) != constants.COURSE_SCHEDULE_DISABLED:
                group_status_map[group_uuid] = constants.COURSE_SCHEDULE_DISABLED
                term_obj.update({"group_status_map": json.dumps(group_status_map)})
                logger.info("update uuid[%s] in yzy_term success : {'group_status_map': {'%s': %s}}"
                    % (term_uuid, group_uuid, constants.COURSE_SCHEDULE_DISABLED))

            # 找出该学期、该教学分组下的所有课表，标记为禁用
            ret = db_api.update_course_schedule_many(
                value_dict={"status": constants.COURSE_SCHEDULE_DISABLED},
                item={"term_uuid":term_uuid, "group_uuid": group_uuid}
            )

            logger.info("update many[%s] in yzy_course_schedule success where term_uuid[%s], group_uuid[%s]: {'status': %s}"
                        % (ret, term_uuid, group_uuid, constants.COURSE_SCHEDULE_DISABLED))

            return get_error_result()
        except Exception as e:
            logger.exception("disable course_schedule failed: %s" % str(e), exc_info=True)
            return get_error_result("OtherError")

    def _delete_course_template(self, uuids):
        """
        删除没有被任何课表所引用的模板及其包含的课程
        """
        template_uuids = list()
        for tmp_uuid in uuids:
            cs_objs = db_api.get_course_schedule_with_all({"course_template_uuid": tmp_uuid})
            if not cs_objs:
                template_uuids.append(tmp_uuid)

        dt_ret = db_api.delete_course_template_many_by_uuids(template_uuids)
        logger.info("delete many[%s] in yzy_course_template success where uuid in [%s]"
                    % (dt_ret, template_uuids))

        dc_ret = db_api.delete_course_many_by_course_template_uuids(template_uuids)
        logger.info("delete many[%s] in yzy_course success where course_template_uuid in [%s]"
                    % (dc_ret, template_uuids))

