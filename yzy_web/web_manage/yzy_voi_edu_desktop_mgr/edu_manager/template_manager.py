import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.common import utils
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post
from web_manage.common import constants
from web_manage.yzy_voi_edu_desktop_mgr import models as voi_education_model
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common import db_api


logger = logging.getLogger(__name__)


class VoiTemplateManager(object):

    @operation_record("创建模板'{param[name]}'", module="voi_template")
    def create_check(self, param, log_user=None):
        logger.info("create voi template, classify:%s", param['classify'])
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if voi_education_model.YzyVoiTemplate.objects.filter(name=param['name'], classify=param['classify']):
            logger.error("create voi template error, the name is exists")
            return get_error_result("TemplateAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/create", param)
        logger.info("create voi template end, ret:%s", ret)
        return ret

    def start_templates(self, templates):
        if len(templates) == 1:
            return self.start_template(templates[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.start_template, template)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def stop_templates(self, templates):
        if len(templates) == 1:
            return self.stop_template(templates[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.stop_template, template)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def hard_stop_templates(self, templates):
        if len(templates) == 1:
            return self.stop_template(templates[0], action="hard_stop")
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.stop_template, template, "hard_stop")
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def reboot_templates(self, templates):
        if len(templates) == 1:
            return self.reboot_template(templates[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.reboot_template, template)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def hard_reboot_templates(self, templates):
        if len(templates) == 1:
            return self.reboot_template(templates[0], "hard_reboot")
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.reboot_template, template, "hard_reboot")
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def reset_templates(self, templates):
        if len(templates) == 1:
            return self.reset_template(templates[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.reset_template, template)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def delete_templates(self, templates):
        if len(templates) == 1:
            return self.delete_template(templates[0])
        success_num = 0
        failed_num = 0
        all_task = list()
        with ThreadPoolExecutor(max_workers=constants.MAX_THREADS) as executor:
            for template in templates:
                future = executor.submit(self.delete_template, template)
                all_task.append(future)
            for future in as_completed(all_task):
                result = future.result()
                if result.get('code') != 0:
                    failed_num += 1
                else:
                    success_num += 1
        return get_error_result("Success", {"success_num": success_num, "failed_num": failed_num})

    def start_template(self, template):
        logger.info("start voi template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("start voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/voi/template/start", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("start voi template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("start voi template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def stop_template(self, template, action='stop'):
        logger.info("%s voi template, name:%s, uuid:%s", action, template['name'], template['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("stop voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/voi/template/%s" % action, {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("%s voi template failed:%s", action, ret['msg'])
            return ret
        else:
            logger.info("%s voi template success, name:%s, uuid:%s", action, template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def reboot_template(self, template, action="reboot"):
        logger.info("%s voi template, name:%s, uuid:%s", action, template['name'], template['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("%s voi template error, it is not exists", action)
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/voi/template/%s" % action, {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("%s voi template failed:%s", action, ret['msg'])
            return ret
        else:
            logger.info("%s voi template success, name:%s, uuid:%s", action, template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def reset_template(self, template):
        logger.info("reset voi template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("reset voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/voi/template/reset", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("reset voi template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("reset voi template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def delete_template(self, template):
        logger.info("delete voi template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("delete voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/voi/template/delete", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("delete voi template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("delete voi template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def start_check(self, param, log_user=None):
        """
        :param param:
            {
                "templates": [
                    {
                        "name": "template1",
                        "uuid": ""
                    },
                    ...
                ]
            }
        :return:
        """
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.start_templates(templates)
        msg = "模板'%s'开机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    def stop_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.stop_templates(templates)
        msg = "模板'%s'关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    def hard_stop_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.hard_stop_templates(templates)
        msg = "模板'%s'强制关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    def reboot_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.reboot_templates(templates)
        msg = "模板'%s'重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    def hard_reboot_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.hard_reboot_templates(templates)
        msg = "模板'%s'强制重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    def reset_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.reset_templates(templates)
        msg = "模板'%s'重置" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="voi_template")
        return ret

    @operation_record("更新模板'{param[name]}'", module="voi_template")
    def save_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("save template")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("save voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/save", param)
        logger.info("save voi template end:%s", ret)
        return ret

    @operation_record("保存模板'{param[name]}'", module="voi_template")
    def iso_save_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("iso save template")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("save voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/iso_save", param)
        logger.info("iso save voi template end:%s", ret)
        return ret

    @operation_record("模板'{param[name]}'版本回退", module="voi_template")
    def rollback_check(self, param, log_user=None):
        """
        :param param:
            {
                "rollback_version": 5,
                "cur_version": 6,
                "name": "",
                "uuid": ""
            }
        :return:
        """
        logger.info("voi template %s rollback", param['name'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=param['uuid'], deleted=False):
            logger.info("voi template rollback error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/rollback", param)
        logger.info("voi rollback template end:%s", ret)
        return ret

    @operation_record("下载模板'{param[name]}'", module="voi_template")
    def download_check(self, param, log_user=None):
        logger.info("download voi template")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("download voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/download", param, timeout=3600)
        logger.info("download voi template end, ret:%s", ret)
        return ret

    def edit_check(self, param, log_user=None):
        """

        :param param:
        {
            "name": "template1",
            "uuid": ""
        }
        :return:
        """
        logger.info("edit voi template %s begin", param)
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("edit voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/edit", param)
        logger.info("edit voi template url end:%s", ret)
        return ret

    @operation_record("复制模板'{param[name]}'", module="voi_template")
    def copy_check(self, param, log_user=None):
        logger.info("copy voi template")
        uuid = param.get('template_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.error("copy voi template error, it is not exists")
            return get_error_result("TemplateNotExist", name='')
        if voi_education_model.YzyVoiTemplate.objects.filter(name=param['name'], deleted=False):
            logger.error("copy voi template error, the template name already exists")
            return get_error_result("TemplateAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/copy", param)
        logger.info("copy voi template end:%s", ret)
        return ret

    @operation_record("模板'{param[name]}'加载资源'{param[iso_uuid]}'", module="voi_template")
    def attach_source_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728",
                "iso_uuid": ""
            }
        :return:
        """
        logger.info("voi template attach_source")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("voi template attach_source error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/attach_source", param)
        logger.info("voi template attach_source end")
        return ret

    @operation_record("模板'{param[name]}'弹出资源", module="voi_template")
    def detach_source_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("voi template detach_source")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("voi template detach_source error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/detach_source", param)
        logger.info("voi template detach_source end:%s", ret)
        return ret

    def get_console_check(self, param, log_user=None):
        """
        :param param:
            {
                "uuid": "",
                "name": ""
            }
        :return:
        """
        ret = server_post("/api/v1/voi/template/console", param)
        logger.info("get template %s console end, ret:%s", param['uuid'], ret)
        return ret

    @operation_record("更新模板'{data[name]}'属性", module="voi_template")
    def update_template(self, data, log_user=None):
        logger.info("update voi template, name:%s, uuid:%s", data['name'], data['uuid'])
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update voi template, it is not exists")
            return get_error_result("TemplateNotExist", name=data['name'])
        ret = server_post("/api/v1/voi/template/update", data)
        if ret.get('code') != 0:
            logger.info("update voi template failed:%s", ret['msg'])
        else:
            logger.info("update voi template success, name:%s", data['name'])
        return ret

    def allocate_ipaddr(self, subnet_uuid):
        subnet = resource_model.YzySubnets.objects.filter(uuid=subnet_uuid, deleted=False).first()
        if not subnet:
            return get_error_result("SubnetNotExist")
        all_ips = utils.find_ips(subnet.start_ip, subnet.end_ip)
        # 选择子网并且系统分配，模板IP从后往前取值
        ipaddr = ""
        all_ip_reverse = all_ips[::-1]
        used_ips = db_api.get_personal_used_ipaddr(subnet_uuid)
        for ip in all_ip_reverse:
            if ip not in used_ips:
                ipaddr = ip
                break
        return {"ipaddr": ipaddr}

    @operation_record("模板'{param[name]}'取消上传", module="voi_template")
    def cancel_upload_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("voi template cancel upload")
        uuid = param.get('uuid')
        if not voi_education_model.YzyVoiTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("voi template cancel_upload error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/voi/template/cancel_upload", param)
        logger.info("voi template cancel_upload end:%s", ret)
        return ret
