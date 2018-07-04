import logging

from celery_tasks.main import celery_app
from .yuntongxun.sms import CCP

SMS_CODE_TEMP_ID = 1

# 获取日志器
logger = logging.getLogger('django')


# 定义任务函数
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code, expires):
    """发送短信验证码"""
    print('发送短信任务函数被调用。。。')
    # try:
    #     res = CCP().send_template_sms(mobile, [sms_code, expires], SMS_CODE_TEMP_ID)
    # except Exception as e:
    #     logger.error('发送短信异常: mobile: %s sms_code: %s' % (mobile, sms_code))
    # else:
    #     if res != 0:
    #         # 发送短信失败
    #         logger.error('发送短信失败: mobile: %s sms_code: %s' % (mobile, sms_code))
