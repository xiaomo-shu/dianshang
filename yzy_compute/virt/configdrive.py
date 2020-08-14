# Copyright 2012 Michael Still and Canonical Inc
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Config Drive v2 helper."""

import os
import shutil
import six
import logging
from yzy_compute import utils
from common import jsonutils
from common import constants
from common import cmdutils
from yzy_compute import exception


# Config drives are 64mb, if we can't size to the exact size of the data
CONFIGDRIVESIZE_BYTES = 64 * constants.Mi
MD_JSON_NAME = "meta_data.json"
VD_JSON_NAME = "vendor_data.json"
VD2_JSON_NAME = "vendor_data2.json"
NW_JSON_NAME = "network_data.json"


class ConfigDriveBuilder(object):
    """Build config drives, optionally as a context manager."""

    def __init__(self, instance=None, network_info=None):
        self.mdfiles = []
        self.instance = instance
        self.route_configuration = None
        self.network_info = network_info
        # self.network_metadata = self.get_network_metadata(network_info)
        # self.add_instance_metadata()

    def __enter__(self):
        return self

    def __exit__(self, exctype, excval, exctb):
        if exctype is not None:
            # NOTE(mikal): this means we're being cleaned up because an
            # exception was thrown. All bets are off now, and we should not
            # swallow the exception
            return False

    def get_network_metadata(self, network_info):
        """Gets a more complete representation of the instance network information.

        This data is exposed as network_data.json in the metadata service and
        the config drive.
        """
        if not network_info:
            return

        # IPv4 or IPv6 networks
        nets = []
        # VIFs, physical NICs, or VLANs. Physical NICs will have type 'phy'.
        links = []
        # Non-network bound services, such as DNS
        services = []

        for vif in network_info:
            vif_id = "tap%s" % (vif['port_id'][:constants.RESOURCE_ID_LENGTH])
            link = {
                'ethernet_mac_adress': vif['mac_addr'],
                'mtu': 1500,
                'type': vif.get('type', 'bridge'),
                'id': vif_id,
                'vif_id': vif['port_id']
            }
            links.append(link)
            for server in vif.get('dns_server', []):
                service = {
                    'type': 'dns',
                    'address': server
                }
                services.append(service)
            network = {
                'link': vif_id,
                'type': 'ipv4',
                'ip_address': vif['fixed_ip'],
                'netmask': vif.get('netmask', '')
            }
            nets.append(network)

        return {
            "links": links,
            "networks": nets,
            "services": services
        }

    def get_ec2_metadata(self, ips):
        """
        :param version:
        :param instance:
        :param network_info:
            {
                "fixed_ips": ["203.0.113.203"]
            }
        :return:
        """
        fixed_ip = ips and ips[0] or ''

        meta_data = {
            'ami-manifest-path': 'FIXME',
            'hostname': self.instance['name'],
            'local-hostname': self.instance['name'],
            'public-hostname': self.instance['name'],
            'instance-action': 'none',
            'local-ipv4': fixed_ip or None,
        }

        data = {'meta-data': meta_data}
        return data

    def _metadata_as_json(self):
        metadata = dict()
        metadata['uuid'] = self.instance['uuid']
        metadata['hostname'] = self.instance['name']
        metadata['name'] = self.instance['name']
        metadata['network_config'] = self.network_metadata
        return jsonutils.dump_as_bytes(metadata)

    def _network_data(self):
        if self.network_metadata is None:
            return jsonutils.dump_as_bytes({})
        return jsonutils.dump_as_bytes(self.network_metadata)

    def _route_configuration(self):
        if self.route_configuration:
            return self.route_configuration

        path_handlers = {
            MD_JSON_NAME: self._metadata_as_json,
            NW_JSON_NAME: self._network_data
        }

        self.route_configuration = RouteConfiguration(path_handlers)
        return self.route_configuration

    def lookup(self, path):
        if path == "" or path[0] != "/":
            path = utils.normpath("/" + path)
        else:
            path = utils.normpath(path)
        path_tokens = path.split('/')[1:]
        try:
            if path_tokens[0] == "openstack":
                data = self._route_configuration().handle_path(path_tokens[1:])
        except Exception as e:
            logging.error("lookup path failed:%s", e)
            raise e

        return data

    def metadata_for_config_drive(self):
        """Yields (path, value) tuples for metadata elements."""
        version = 'latest'
        # ec2
        # data = self.get_ec2_metadata(ips)
        # filepath = os.path.join('ec2', version, 'meta-data.json')
        # yield (filepath, jsonutils.dump_as_bytes(data['meta-data']))

        # openstack
        path = 'openstack/%s/%s' % (version, MD_JSON_NAME)
        yield (path, self.lookup(path))

        # path = 'openstack/%s/%s' % (version, VD_JSON_NAME)
        # yield (path, self.lookup(path))

        path = 'openstack/%s/%s' % (version, NW_JSON_NAME)
        yield (path, self.lookup(path))

        # path = 'openstack/%s/%s' % (version, VD2_JSON_NAME)
        # yield (path, self.lookup(path))

    def _add_file(self, basedir, path, data):
        filepath = os.path.join(basedir, path)
        dirname = os.path.dirname(filepath)
        utils.ensure_tree(dirname)
        with open(filepath, 'wb') as f:
            # the given data can be either text or bytes. we can only write
            # bytes into files.
            if isinstance(data, six.text_type):
                data = data.encode('utf-8')
            f.write(data)

    def add_instance_metadata(self):
        for (path, data) in self.metadata_for_config_drive():
            self.mdfiles.append((path, data))

    # def _write_md_files(self, basedir):
    #     for data in self.mdfiles:
    #         self._add_file(basedir, data[0], data[1])

    def _write_md_files(self, basedir):
        try:
            if not self.network_info:
                return
            ip_info = self.network_info[0]
            if not ip_info.get('fixed_ip', None):
                return

            logging.info("set the network info to ip file")
            ip_file = os.path.join(basedir, 'ipinfo/ip.ini')
            dirname = os.path.dirname(ip_file)
            utils.ensure_tree(dirname)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "iptype", "FIX", run_as_root=True)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "complete", "NO", run_as_root=True)
            # cmdutils.execute('crudini', '--set', ip_file, "setting", "os", self.instance['os_type'],
            #                  run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "computer", self.instance['name'],
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "mac_number", 1,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "mac_1", ip_info.get('mac_addr'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "dhcp_1", 0,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_number_1", 1,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_type_1", 0,
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "ip_1_1", ip_info.get('fixed_ip'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "netmask_1_1", ip_info.get('netmask'),
                             run_as_root=True)
            cmdutils.execute('crudini', '--set', ip_file, "setting", "gateway_1_1", ip_info.get('gateway'),
                             run_as_root=True)
            dns_server = ip_info.get('dns_server', [])
            if dns_server:
                cmdutils.execute('crudini', '--set', ip_file, "setting", "dns_number_1", len(dns_server),
                                 run_as_root=True)
                for index, dns in enumerate(dns_server):
                    key = 'dns_1_%s' % (index + 1)
                    cmdutils.execute('crudini', '--set', ip_file, "setting", key, dns, run_as_root=True)
        except Exception as e:
            message = 'instance_uuid[%s] set ip info error:%s' % (self.instance['uuid'], e)
            logging.error(message)
            raise exception.SetIPAddressException(message)

    def _make_iso9660(self, path, tmpdir):
        publisher = "%(product)s %(version)s" % {
            'product': 'yzy_kvm',
            'version': '1.0.0'
            }

        cmdutils.execute('mkisofs',
                         '-o', path,
                         '-ldots',
                         '-allow-lowercase',
                         '-allow-multidot',
                         '-l',
                         '-input-charset',
                         'utf8',
                         '-output-charset',
                         'utf8',
                         '-publisher',
                         publisher,
                         '-hidden',
                         'ipinfo',
                         '-quiet',
                         '-J',
                         '-r',
                         # '-V', 'config-2',
                         tmpdir,
                         attempts=1,
                         run_as_root=False)

    def make_drive(self, path):
        """Make the config drive.

        :param path: the path to place the config drive image at

        :raises ProcessExecuteError if a helper process has failed.
        """
        with utils.tempdir() as tmpdir:
            self._write_md_files(tmpdir)

            self._make_iso9660(path, tmpdir)

    def __repr__(self):
        return "<ConfigDriveBuilder: " + str(self.mdfiles) + ">"


class RouteConfiguration(object):
    """Routes metadata paths to request handlers."""

    def __init__(self, path_handler):
        self.path_handlers = path_handler

    def handle_path(self, path_tokens):
        path = '/'.join(path_tokens[1:])

        path_handler = self.path_handlers[path]

        if path_handler is None:
            raise KeyError(path)

        return path_handler()
