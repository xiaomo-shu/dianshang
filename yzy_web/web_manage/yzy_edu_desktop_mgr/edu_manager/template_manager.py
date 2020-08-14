import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from web_manage.yzy_resource_mgr import models as resource_model
from web_manage.common.log import operation_record, insert_operation_log
from web_manage.common.errcode import get_error_result
from web_manage.common.http import server_post, scheduler_post
from web_manage.common import constants
from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.common.utils import is_ip_addr


logger = logging.getLogger(__name__)


class TemplateManager(object):

    # def get_object_list(self, request, classify=1):
    #     try:
    #         page = YzyWebPagination()
    #         query_set = education_model.YzyInstanceTemplate.objects.filter(classify=classify,
    #                                                                        deleted=False)
    #         templates = page.paginate_queryset(queryset=query_set, request=request, view=self)
    #         ser = TemplateSerializer(instance=templates, many=True, context={'request': request})
    #         return page.get_paginated_response(ser.data)
    #     except Exception as e:
    #         logger.error("get templates list error:%s", e)
    #         raise e
    #
    # def get_object_contain(self, request, key, value, classify=1):
    #     try:
    #         item = {
    #             key + '__contains': value,
    #             'classify': classify,
    #             'deleted': False
    #         }
    #         page = YzyWebPagination()
    #         query_set = education_model.YzyInstanceTemplate.objects.filter(**item)
    #         templates = page.paginate_queryset(queryset=query_set, request=request, view=self)
    #         ser = TemplateSerializer(instance=templates, many=True, context={'request': request})
    #         return page.get_paginated_response(ser.data)
    #     except Exception as e:
    #         logger.error("get templates list error:%s", e)
    #         raise e
    #
    # def get_object(self, request, key, value, classify=1):
    #     try:
    #         ret = {
    #             'code': 0,
    #             "message": "success",
    #             "data": None
    #         }
    #         item = {
    #             key: value,
    #             'classify': classify,
    #             'deleted': False
    #         }
    #         query_set = education_model.YzyInstanceTemplate.objects.filter(**item).first()
    #         if query_set:
    #             ser = TemplateSerializer(query_set, context={'request': request})
    #             ret['data'] = ser.data
    #             return JsonResponse(ret)
    #         else:
    #             return JsonResponse(ret)
    #     except Exception as e:
    #         logger.error("get templates error:%s", e)
    #         raise e
    #
    # def get_education(self, request, *args, **kwargs):
    #     """
    #     :param request:
    #     :param args:
    #     :param kwargs:
    #         searchtype: 'all/single/contain'
    #         key: the search key, 'name' or 'uuid' is the most situation
    #         value: the value of the search key
    #     :return:
    #     """
    #     try:
    #         search_type = request.GET.get('searchtype', 'all')
    #         key = request.GET.get('key', 'uuid')
    #         value = request.GET.get('value')
    #         if search_type != 'all' and not value:
    #             return param_error("ParamError")
    #         if 'all' == search_type:
    #             return self.get_object_list(request, classify=constants.TEMPLATE_EDUCATION)
    #         elif 'contain' == search_type:
    #             return self.get_object_contain(request, key, value, classify=constants.TEMPLATE_EDUCATION)
    #         elif 'single' == search_type:
    #             return self.get_object(request, key, value, classify=constants.TEMPLATE_EDUCATION)
    #         else:
    #             return param_error("ParamError")
    #     except Exception as e:
    #         logger.error("template get request failed:%s", e)
    #         return param_error("SystemError")

    @operation_record("创建模板{param[name]}", module="template")
    def create_check(self, param, log_user=None):
        logger.info("create template, classify:%s", param['classify'])
        pool_uuid = param.get('pool_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not resource_model.YzyResourcePools.objects.filter(uuid=pool_uuid, deleted=False):
            logger.error("create template error, resource pool not exists")
            return get_error_result("ResourcePoolNotExist")
        if education_model.YzyInstanceTemplate.objects.filter(name=param['name'], classify=param['classify']):
            logger.error("create template error, the name is exists")
            return get_error_result("TemplateAlreadyExist", name=param['name'])
        ret = server_post("/api/v1/template/create", param)
        logger.info("create template end:%s", ret)
        return ret

    def complete_install_check(self, param, log_user=None):
        logger.info("complete template install, uuid:%s", param['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=param['uuid'], deleted=False):
            logger.error("complete template install error, the template not exists")
            return get_error_result("TemplateNotExist", name='')
        ret = server_post("/api/v1/template/complete_install", param)
        logger.info("complete template install:%s", ret)
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

    def start_template(self, template):
        logger.info("start template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("start template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/template/start", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("start template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("start template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

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

    def stop_template(self, template):
        logger.info("stop template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("stop template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/template/stop", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("stop template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("stop template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def hard_stop_templates(self, templates):
        for template in templates:
            logger.info("hard stop template, name:%s, uuid:%s", template['name'], template['uuid'])
            if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
                logger.info("hard stop template error, it is not exists")
                return get_error_result("TemplateNotExist", name=template['name'])
            ret = server_post("/api/v1/template/hard_stop", {"uuid": template['uuid']})
            if ret.get('code') != 0:
                logger.info("hard stop template failed:%s", ret['msg'])
                return ret
            else:
                logger.info("hard stop template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success")

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

    def reboot_template(self, template):
        logger.info("reboot template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("reboot template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/template/reboot", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("reboot template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("reboot template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success", {"success_num": 1, "failed_num": 0})

    def hard_reboot_templates(self, templates):
        for template in templates:
            logger.info("hard reboot template, name:%s, uuid:%s", template['name'], template['uuid'])
            if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
                logger.info("hard reboot template error, it is not exists")
                return get_error_result("TemplateNotExist", name=template['name'])
            ret = server_post("/api/v1/template/hard_reboot", {"uuid": template['uuid']})
            if ret.get('code') != 0:
                logger.info("hard reboot template failed:%s", ret['msg'])
                return ret
            else:
                logger.info("hard reboot template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success")

    def reset_templates(self, templates):
        for template in templates:
            logger.info("reset template, name:%s, uuid:%s", template['name'], template['uuid'])
            if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
                logger.info("reset template error, it is not exists")
                return get_error_result("TemplateNotExist", name=template['name'])
            ret = server_post("/api/v1/template/reset", {"uuid": template['uuid']})
            if ret.get('code') != 0:
                logger.info("reset template failed:%s", ret['msg'])
                return ret
            else:
                logger.info("reset template success, name:%s, uuid:%s", template['name'], template['uuid'])
        return get_error_result("Success")

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

    def delete_template(self, template):
        logger.info("delete template, name:%s, uuid:%s", template['name'], template['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=template['uuid'], deleted=False):
            logger.info("delete template error, it is not exists")
            return get_error_result("TemplateNotExist", name=template['name'])
        ret = server_post("/api/v1/template/delete", {"uuid": template['uuid']})
        if ret.get('code') != 0:
            logger.info("delete template failed:%s", ret['msg'])
            return ret
        else:
            logger.info("delete template success, name:%s, uuid:%s", template['name'], template['uuid'])
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
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    def stop_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.stop_templates(templates)
        msg = "模板'%s'关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    def hard_stop_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.hard_stop_templates(templates)
        msg = "模板'%s'强制关机" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    def reboot_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.reboot_templates(templates)
        msg = "模板'%s'重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    def hard_reboot_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.hard_reboot_templates(templates)
        msg = "模板'%s'强制重启" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    def reset_check(self, param, log_user=None):
        templates = param.get('templates', [])
        names = list()
        for template in templates:
            names.append(template['name'])
        ret = self.reset_templates(templates)
        msg = "模板'%s'重置" % ('/'.join(names))
        insert_operation_log(msg, ret['msg'], log_user, module="template")
        return ret

    # def delete_check(self, param):
    #     """
    #     需要支持批量删除
    #     :param param:
    #         {
    #             "templates": [
    #                 "",
    #                 ...
    #             ]
    #         }
    #     :return:
    #     """
    #     templates = param.get('templates', [])
    #     for template in templates:
    #         logger.info("delete template, uuid:%s", template)
    #         if not education_model.YzyInstanceTemplate.objects.filter(uuid=template, deleted=False):
    #             logger.info("delete template error, it is not exists")
    #             return get_error_result("TemplateNotExist")
    #         ret = server_post("/api/v1/template/delete", {"uuid": template})
    #         if ret.get('code') != 0:
    #             logger.info("delete template failed:%s", ret['msg'])
    #             return ret
    #         else:
    #             logger.info("delete template success, uuid:%s", template)
    #     return get_error_result("Success")

    @operation_record("更新模板'{param[name]}'", module="template")
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
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("save template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        run_date = param.get('run_date', None)
        if run_date:
            ret = scheduler_post("/api/v1/template/save", param)
        else:
            ret = server_post("/api/v1/template/save", param)
        logger.info("save template end:%s", ret)
        return ret

    @operation_record("重传模板镜像'{param[image_id]}'", module="template")
    def resync_check(self, param, log_user=None):
        """
        :param param:
            {
                "ipaddr": "172.16.1.15",
                "role": 2,
                "path": "/opt/slow",
                "image_id": "c2133168-7aca-11ea-994b-000c29e84b9c",
                "version": 2
            }
        :return:
        """
        logger.info("resync template image:%s", param['image_id'])
        image_id = param.get('image_id')
        if not education_model.YzyInstanceDeviceInfo.objects.filter(uuid=image_id, deleted=False):
            logger.info("resync template image error, it is not exists")
            return get_error_result("ImageNotFound")
        ret = server_post("/api/v1/template/resync", param)
        logger.info("resync template image end:%s", ret)
        return ret

    @operation_record("下载模板'{param[name]}'", module="template")
    def download_check(self, param, log_user=None):
        logger.info("download template")
        uuid = param.get('uuid')
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("download template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/template/download", param)
        logger.info("download template end:%s", ret)
        return ret

    @operation_record("编辑模板'{param[name]}'", module="template")
    def edit_check(self, param, log_user=None):
        """

        :param param:
        {
            "name": "template1",
            "uuid": ""
        }
        :return:
        """
        logger.info("edit template %s begin", param)
        uuid = param.get('uuid')
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("edit template error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/template/edit", param)
        logger.info("edit template url end:%s", ret)
        return ret

    @operation_record("复制模板'{param[name]}'", module="template")
    def copy_check(self, param, log_user=None):
        logger.info("copy template")
        uuid = param.get('template_uuid')
        if log_user:
            param['owner_id'] = log_user['id']
        else:
            param['owner_id'] = 1
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.error("copy template error, it is not exists")
            return get_error_result("TemplateNotExist", name='')
        if education_model.YzyInstanceTemplate.objects.filter(name=param['name'], deleted=False):
            logger.error("copy template error, the template name already exists")
            return get_error_result("TemplateAlreadyExist", name=param['name'])

        # 已选择IP类型为固定IP，校验bind_ip
        if param.get('IPtype', None) == "2":
            bind_ip = param.get('bind_ip', None)
            if not bind_ip:
                return get_error_result("StaticIPTypeWithoutIPAddress")
            if not is_ip_addr(bind_ip):
                return get_error_result("IpAddressError")

        ret = server_post("/api/v1/template/copy", param)
        logger.info("copy template end:%s", ret)
        return ret

    @operation_record("模板'{param[name]}'加载资源'{param[iso_uuid]}'", module="template")
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
        logger.info("template attach_source")
        uuid = param.get('uuid')
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("template attach_source error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/template/attach_source", param)
        logger.info("template attach_source end:%s", ret)
        return ret

    @operation_record("模板'{param[name]}'弹出资源", module="template")
    def detach_source_check(self, param, log_user=None):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("template detach_source")
        uuid = param.get('uuid')
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("template detach_source error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/template/detach_source", param)
        logger.info("template detach_source end:%s", ret)
        return ret

    def send_key_check(self, param):
        """
        :param param:
            {
                "name": "template1",
                "uuid": "655a1b9c-592a-11ea-b491-000c295dd728"
            }
        :return:
        """
        logger.info("template send_key, default is ctrl+alt+del")
        uuid = param.get('uuid')
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=uuid, deleted=False):
            logger.info("template send_key error, it is not exists")
            return get_error_result("TemplateNotExist", name=param['name'])
        ret = server_post("/api/v1/template/send_key", param)
        logger.info("template send_key end:%s", ret)
        return ret

    @operation_record("更新教学模板'{data[name]}'属性", module="template")
    def update_template(self, data, log_user=None):
        logger.info("update education template, name:%s, uuid:%s", data['name'], data['uuid'])
        if not education_model.YzyInstanceTemplate.objects.filter(uuid=data['uuid'], deleted=False):
            logger.info("update education template, it is not exists")
            return get_error_result("TemplateNotExist", name=data['name'])
        ret = server_post("/api/v1/template/update", data)
        if ret.get('code') != 0:
            logger.info("update education template failed:%s", ret['msg'])
        else:
            logger.info("update education template success, name:%s", data['name'])
        return ret
