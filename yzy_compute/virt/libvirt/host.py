"""
Manages information about the host OS and hypervisor.

This class encapsulates a connection to the libvirt
daemon and provides certain higher level APIs around
the raw libvirt API. These APIs are then used by all
the other libvirt related classes
"""

import six
import threading
import logging
from common import encodeutils
from common.config import SERVER_CONF as CONF
from yzy_compute.virt.libvirt import guest as libvirt_guest
from yzy_compute import exception
from yzy_compute import utils


libvirt = None


class Host(object):

    def __init__(self, uri, read_only=False):

        global libvirt
        if libvirt is None:
            libvirt = utils.import_module('libvirt')

        self._uri = uri
        self._read_only = read_only
        self._hostname = None

        self._wrapped_conn = None
        self._wrapped_conn_lock = threading.Lock()

    @staticmethod
    def _connect_auth_cb(creds, opaque):
        if len(creds) == 0:
            return 0
        raise Exception("Can not handle authentication request for %d credentials" % len(creds))

    def _connect(self, uri, read_only):
        auth = [[libvirt.VIR_CRED_AUTHNAME,
                 libvirt.VIR_CRED_ECHOPROMPT,
                 libvirt.VIR_CRED_REALM,
                 libvirt.VIR_CRED_PASSPHRASE,
                 libvirt.VIR_CRED_NOECHOPROMPT,
                 libvirt.VIR_CRED_EXTERNAL],
                Host._connect_auth_cb,
                None]

        flags = 0
        if read_only:
            flags = libvirt.VIR_CONNECT_RO
        return libvirt.openAuth(uri, auth, flags)

    def _get_new_connection(self):
        # call with _wrapped_conn_lock held
        logging.debug('Connecting to libvirt: %s', self._uri)

        # This will raise an exception on failure
        wrapped_conn = self._connect(self._uri, self._read_only)
        return wrapped_conn

    @staticmethod
    def _test_connection(conn):
        try:
            conn.getLibVersion()
            return True
        except libvirt.libvirtError as e:
            if (e.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                       libvirt.VIR_ERR_INTERNAL_ERROR) and
                e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                         libvirt.VIR_FROM_RPC)):
                logging.debug('Connection to libvirt broke')
                return False
            raise

    def _get_connection(self):
        # multiple concurrent connections are protected by _wrapped_conn_lock
        with self._wrapped_conn_lock:
            # Drop the existing connection if it is not usable
            if (self._wrapped_conn is not None and
                    not self._test_connection(self._wrapped_conn)):
                self._wrapped_conn = None

            if self._wrapped_conn is None:
                try:
                    # This will raise if it fails to get a connection
                    self._wrapped_conn = self._get_new_connection()
                except Exception as ex:
                    logging.error('Failed to connect to libvirt: %(msg)s', ex)

        return self._wrapped_conn

    def get_connection(self):
        """Returns a connection to the hypervisor

        This method should be used to create and return a well
        configured connection to the hypervisor.

        :returns: a libvirt.virConnect object
        """
        try:
            conn = self._get_connection()
        except libvirt.libvirtError as ex:
            logging.exception("Connection to libvirt failed: %s", ex)
            raise exception.HypervisorUnavailable(host=CONF.default.host)
        return conn

    def write_instance_config(self, xml):
        """Defines a domain, but does not start it.

        :param xml: XML domain definition of the guest.

        :returns: an instance of Guest
        """
        if six.PY2:
            xml = encodeutils.safe_encode(xml)
        domain = self.get_connection().defineXML(xml)
        return libvirt_guest.Guest(domain)

    def list_guests(self, only_running=True, only_guests=True):
        """Get a list of Guest objects for instances

        :param only_running: True to only return running instances
        :param only_guests: True to filter out any host domain (eg Dom-0)

        See method "list_instance_domains" for more information.

        :returns: list of Guest objects
        """
        return [libvirt_guest.Guest(dom) for dom in self.list_instance_domains(
            only_running=only_running, only_guests=only_guests)]

    def list_instance_domains(self, only_running=True, only_guests=True):
        """Get a list of libvirt.Domain objects for instances

        :param only_running: True to only return running instances
        :param only_guests: True to filter out any host domain (eg Dom-0)

        Query libvirt to a get a list of all libvirt.Domain objects
        that correspond to instances. If the only_running parameter
        is true this list will only include active domains, otherwise
        inactive domains will be included too. If the only_guests parameter
        is true the list will have any "host" domain (aka Xen Domain-0)
        filtered out.

        :returns: list of libvirt.Domain objects
        """
        flags = libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE
        if not only_running:
            flags = flags | libvirt.VIR_CONNECT_LIST_DOMAINS_INACTIVE

        doms = []
        for dom in self.get_connection().listAllDomains(flags):
            if only_guests and dom.ID() == 0:
                continue
            doms.append(dom)

        return doms

    def get_guest(self, instance):
        """Retrieve libvirt guest object for an instance.

        All libvirt error handling should be handled in this method and
        relevant nova exceptions should be raised in response.

        :param instance: a nova.objects.Instance object

        :returns: a nova.virt.libvirt.Guest object
        :raises exception.InstanceNotFound: The domain was not found
        :raises exception.InternalError: A libvirt error occurred
        """
        return libvirt_guest.Guest(self._get_domain(instance))

    def _get_domain(self, instance):
        """Retrieve libvirt domain object for an instance.

        All libvirt error handling should be handled in this method and
        relevant nova exceptions should be raised in response.

        :param instance: a nova.objects.Instance object

        :returns: a libvirt.Domain object
        :raises exception.InstanceNotFound: The domain was not found
        :raises exception.InternalError: A libvirt error occurred
        """
        try:
            conn = self.get_connection()
            return conn.lookupByUUIDString(instance['uuid'])
        except libvirt.libvirtError as ex:
            error_code = ex.get_error_code()
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise exception.InstanceNotFound(instance_id=instance['uuid'])

            msg = ('Error from libvirt while looking up %(instance_name)s: '
                     '[Error Code %(error_code)s] %(ex)s' %
                   {'instance_name': instance['name'],
                    'error_code': error_code,
                    'ex': ex})
            raise Exception(msg)

    def get_storage_by_name(self, pool_name):
        conn = self.get_connection()
        try:
            ret = conn.storagePoolLookupByName(pool_name)
            return ret
        except libvirt.libvirtError:
            return False

    def create_storage(self, xml):
        conn = self.get_connection()
        flags = libvirt.VIR_STORAGE_POOL_CREATE_WITH_BUILD
        logging.info("create storage, flags:%s", flags)
        try:
            pool = conn.storagePoolDefineXML(xml)
            pool.create(flags)
            pool.setAutostart(1)
        except Exception as e:
            logging.error('Error create storage with XML: %s', e)
            raise
