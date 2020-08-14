import sys
import pickle
import hashlib
import time
import traceback
import logging
import datetime as dt
from functools import wraps
from flask import current_app
from yzy_terminal.thrift_protocols.terminal import ConnectService
from yzy_terminal.thrift_protocols.terminal.ttypes import *
from yzy_terminal.database import api as db_api


def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        logging.debug("@timefn:" + fn.__name__ + " took " + str(t2 - t1) + " seconds")
        return result
    return measure_time


class ConnectServiceHandler:
    def __init__(self, token_client, mac_token, token_status):
        self.token_client = token_client
        self.mac_token = mac_token
        self.token_status = token_status
        self.token_client_tmp = {}

    def get_md5(self, input_str):
        md5 = hashlib.md5()
        md5.update(input_str.encode('utf8'))
        md5_value = md5.hexdigest()
        return md5_value

    def client_connected(self, oprot):
        try:
            client = ConnectService.Client(oprot)
            client_md5 = self.get_md5(str(oprot))
            self.token_client_tmp[client_md5] = oprot
            if oprot.trans.isOpen():
                client.TokenId(client_md5)
                logging.debug('Client.token_id called {}'.format(client_md5))
        except TTransport.TTransportException as tx:
            logging.error("client_connected Error TTransport.TTransportException == {}".format(tx))
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))

    def client_closed(self, oprot, app):
        client_md5 = self.get_md5(str(oprot))
        self.token_client_tmp.pop(client_md5)
        if client_md5 in self.token_client.keys():
            self.token_client.pop(client_md5)
            logging.debug('pop token_client mac {}'.format(client_md5))
            token_mac = {v: k for k, v in self.mac_token.items()}
            logging.debug('mac_token = {}, token_mac = {}'.format(self.mac_token, token_mac))
            if client_md5 in token_mac.keys():
                mac = token_mac[client_md5]
                self.mac_token.pop(mac)
                logging.debug('pop mac_token mac {}'.format(mac))
                if client_md5 in self.token_status.keys():
                    self.token_status.pop(client_md5)
                    logging.debug('pop token_status token {}'.format(client_md5))
                # set terminal status to offline
                user_name = None
                try:
                    with app.app_context():
                        table_api = db_api.YzyTerminalTableCtrl(current_app.db)
                        table_api.update_terminal_by_mac(**{'mac': mac, 'status': '0'})
                        logging.debug('set yzy_terminal offline {}'.format(mac))
                except Exception as err:
                    logging.error('delete user desktop records err mac: {}, user: {}'.format(mac, user_name))
                    logging.error(err)
                    logging.error(''.join(traceback.format_exc()))

    def Command(self, msg):
        logging.debug('Get client Command == {}'.format(msg.cmdstr))

    def TokenId(self, token_id):
        if token_id in self.token_client_tmp.keys():
            self.token_client[token_id] = self.token_client_tmp[token_id]
            logging.info('Add Client = {}'.format(token_id))

    def Ping(self, token_id, time):
        try:
            logging.debug('Get client token_id [{}] time [{}].........................'.format(token_id, time))
            if token_id in self.token_client.keys():
                self.token_status[token_id] = True
                if self.token_client[token_id].trans.isOpen():
                    client = ConnectService.Client(self.token_client[token_id])
                    int_time = int(dt.datetime.now().timestamp() - dt.datetime.utcfromtimestamp(0).timestamp())
                    client.Ping(token_id, int_time)
        except TTransport.TTransportException as tx:
            logging.error("Ping Error TTransport.TTransportException == {}".format(tx))
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
