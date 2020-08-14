import logging
from flask import current_app
import threading
import traceback
import time


class AsyncCleanTask(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app

    def _cleanTempVm(self):
        with self.app.app_context():
            try:
                l = list_ImageTemparyInstance()
                for o in l:
                    last_connect_time = o.last_connect_time
                    utc_now_ts = timeutils.utcnow_ts()
                    LOG.info('no connection time long:%s' % (utc_now_ts - last_connect_time))

                    if utc_now_ts - last_connect_time > 30 and o.status is None:
                        stdout, stderr = cmdutils.Popen('', '',
                                                        'ps -ef |grep -v grep | grep qemu-kvm |grep 127.0.0.1 |grep %s' % o.proc_id)
                        if len(stdout) == 0:
                            LOG.info('process[%s] is not exists.' % o.proc_id)
                            cmdutils.Popen('', '', 'rm -rf %s' % o.file_name)
                            db_api.delete_ImageTemparyInstance(o.id)
                            db_api.update_image(o.image_id, {'status': 'ACTIVE', 'fault': '%s$$$$ error:%s' % (
                            'OS_EDIT', 'Abnormal shutdown-1')})
                        else:
                            LOG.info('do clean tempary instance start')
                            cmdutils.Popen('', '', 'rm -f /dev/shm/spice.%s' % o.proc_id)
                            cmdutils.Popen('', '', 'kill -9 %s' % o.proc_id)
                            cmdutils.Popen('', '', 'rm -rf %s' % o.file_name)

                            db_api.delete_ImageTemparyInstance(o.id)
                            db_api.update_image(o.image_id, {'status': 'ACTIVE', 'fault': '%s$$$$ error:%s' % (
                            'OS_EDIT', 'Abnormal shutdown-2')})
                            LOG.info('do clean tempary instance end')

                        LOG.info('exec cleanTempVm.....:%s' % ('end'))
            except:
                logging.error("cleanTempVm error:%s" % traceback.format_exc())

    # def resetImageState(self, ):
    #     db_images = db_api.list_image()
    #     syncImages = []
    #     for o in db_images:
    #         if o.status in ('SYNC_TO_CLUSTER', 'SYNC', 'SYNC_NEW'):
    #             syncImages.append({'image_id': o.image_id, 'name': o.name, 'status': o.status});
    #     if len(syncImages) > 0:
    #         # check cluster-client status:
    #         stdout, stderr = cmdutils.Popen('', '', 'service cluster-client status')
    #         if stdout[0].find('running') >= 0:
    #             pass
    #         else:
    #             LOG.info('cluster-client service is not running,reset sync,sync_new,sync_to_cluster')
    #             for o in syncImages:
    #                 if o['status'] == 'SYNC':
    #                     db_api.update_image(o['image_id'], {'status': 'ACTIVE', 'fault': '%s$$$$ error:%s' % (
    #                     'SYNC', 'cluster-client service not running ,auto canceld!')})
    #                 elif o['status'] == 'SYNC_NEW':
    #                     db_api.update_image(o['image_id'], {'status': 'ERROR', 'fault': '%s$$$$ error:%s' % (
    #                     'SYNC_NEW', 'cluster-client service not running ,auto canceld!')})
    #                 elif o['status'] == 'SYNC_TO_CLUSTER':
    #                     db_api.update_image(o['image_id'], {'status': 'ACTIVE', 'fault': '%s$$$$ error:%s' % (
    #                     'SYNC_TO_CLUSTER', 'cluster-client service not running ,auto canceld!')})
    #
    # def checkComputeNodeState(self, ):
    #     try:
    #         GLOBAL_threading_lock.acquire()
    #         cur_time = timeutils.utcnow_ts()
    #         db_sqls = []
    #         for ip in GLOBAL_compute_nodes.keys():
    #             compute_node = GLOBAL_compute_nodes[ip]
    #             if cur_time - compute_node['heartbeat'] > 30:
    #                 del GLOBAL_compute_nodes[ip]
    #                 node_instances = db_api.list_instances_by_node(ip)
    #                 for instance in node_instances:
    #                     if instance.task_state is not None:
    #                         db_sqls.append(
    #                             "update vec.vec_instances set task_state=NULL where uuid='%s';" % (instance.uuid))
    #
    #         if len(db_sqls) > 0:
    #             db_api.exec_sql("".join(db_sqls))
    #
    #     except:
    #         LOG.info('checkComputeNodeState err:%s.' % (traceback.format_exc()))
    #     finally:
    #         GLOBAL_threading_lock.release()

    def run(self):
        with self.app.app_context():
            while True:
                try:
                    print("async start")
                    self._cleanTempVm()
                    # self.resetImageState()
                    # self.checkComputeNodeState()
                    # LOG.info('end clean')
                except Exception as e:
                    logging.error("AsyncCleanTaskHandler error:%s" % traceback.format_exc())
                time.sleep(30)
