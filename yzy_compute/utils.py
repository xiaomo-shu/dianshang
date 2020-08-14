import contextlib
import os
import sys
import logging
import stat
import errno
import netaddr
import socket
import tempfile
import shutil
from common import constants
from common.config import SERVER_CONF as CONF


_IS_IPV6_ENABLED = None
_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


def get_instance_path(instance, relative=False):
    """Determine the correct path for instance storage.

    This method determines the directory name for instance storage.

    :param instance: the instance we want a path for
    :param relative: if True, just the relative path is returned

    :returns: a path to store information about that instance
    """
    if relative:
        return instance['uuid']
    # return os.path.join("/var/lib/nova/instances/", instance.uuid)
    return os.path.join(CONF.libvirt.instances_path, instance['uuid'])


def get_instance_data_path(instance, relative=False):
    """Determine the correct path for instance data disk.

    :returns: a path to data disk information about that instance
    """
    if relative:
        return instance['uuid']
    # return os.path.join("/var/lib/nova/instances/", instance.uuid)
    return os.path.join(CONF.libvirt.data_path, instance['uuid'])

def ensure_tree(path, mode=_DEFAULT_MODE):
    """Create a directory (and any ancestor directories required)

    :param path: Directory to create
    :param mode: Directory creation permissions
    """
    try:
        logging.info("ensure the path:%s", path)
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
        else:
            raise


def canonicalize():
    """Canonicalize the architecture name
    :returns: a canonical architecture name
    """
    name = os.uname()[4]
    if name is None:
        return None

    newname = name.lower()

    if newname in ("i386", "i486", "i586"):
        newname = constants.I686

    # Xen mistake from Icehouse or earlier
    if newname in ("x86_32", "x86_32p"):
        newname = constants.I686

    if newname == "amd64":
        newname = constants.X86_64

    return newname


def import_module(import_str):
    """Import a module dynamic
    """
    __import__(import_str)
    return sys.modules[import_str]


def get_default_machine_type():
    arch = canonicalize()
    if arch in [constants.X86_64, constants.I686]:
        # 默认会返回当前系统，但是使用大于7.2.0同时使用virtio磁盘启动系统，会grub loading
        # https://ask.openstack.org/en/question/101928/instance-get-stuck-when-booting-grub/
        # 根据上述说明，是因为运行在esxi上的原因？
        return constants.DEFAULT_MACH_TYPE
    default_mtypes = {
        # constants.ARMV7: "virt",
        # constants.AARCH64: "virt",
        # constants.S390: "s390-ccw-virtio",
        # constants.S390X: "s390-ccw-virtio",
        constants.I686: "pc",
        constants.X86_64: "pc",
    }
    return default_mtypes.get(arch)


def ip_to_cidr(ip, prefix=None):
    """Convert an ip with no prefix to cidr notation

    :param ip: An ipv4 or ipv6 address.  Convertable to netaddr.IPNetwork.
    :param prefix: Optional prefix.  If None, the default 32 will be used for
        ipv4 and 128 for ipv6.
    """
    net = netaddr.IPNetwork(ip)
    if prefix is not None:
        # Can't pass ip and prefix separately.  Must concatenate strings.
        net = netaddr.IPNetwork(str(net.ip) + '/' + str(prefix))
    return str(net)


def is_netmask(ip):
    ip_addr = netaddr.IPAddress(ip)
    return ip_addr.is_netmask(), ip_addr.netmask_bits()


def cidr_to_ip(ip_cidr):
    """Strip the cidr notation from an ip cidr or ip

    :param ip_cidr: An ipv4 or ipv6 address, with or without cidr notation
    """
    net = netaddr.IPNetwork(ip_cidr)
    return str(net.ip)

def is_cidr_host(cidr):
    """Determines if the cidr passed in represents a single host network

    :param cidr: Either an ipv4 or ipv6 cidr.
    :returns: True if the cidr is /32 for ipv4 or /128 for ipv6.
    :raises ValueError: raises if cidr does not contain a '/'.  This disallows
        plain IP addresses specifically to avoid ambiguity.
    """
    if '/' not in str(cidr):
        raise ValueError("cidr doesn't contain a '/'")
    net = netaddr.IPNetwork(cidr)
    if net.version == 4:
        return net.prefixlen == constants.IPv4_BITS
    return net.prefixlen == constants.IPv6_BITS


def cidr_mask_length(cidr):
    """Returns the mask length of a cidr

    :param cidr: (string) either an ipv4 or ipv6 cidr or a host IP.
    :returns: (int) mask length of a cidr; in case of host IP, the mask length
              will be 32 (IPv4) or 128 (IPv6)
    """
    return netaddr.IPNetwork(cidr).netmask.netmask_bits()


def get_socket_address_family(ip_version):
    """Returns the address family depending on the IP version"""
    return (int(socket.AF_INET if ip_version == constants.IP_VERSION_4
                else socket.AF_INET6))


# def wait_until_true(predicate, timeout=60, sleep=1, exception=None):
#     """Wait until callable predicate is evaluated as True
#
#     :param predicate: Callable deciding whether waiting should continue.
#     Best practice is to instantiate predicate with functools.partial()
#     :param timeout: Timeout in seconds how long should function wait.
#     :param sleep: Polling interval for results in seconds.
#     :param exception: Exception instance to raise on timeout. If None is passed
#                       (default) then WaitTimeout exception is raised.
#     """
#     try:
#         with eventlet.Timeout(timeout):
#             while not predicate():
#                 eventlet.sleep(sleep)
#     except eventlet.Timeout:
#         if exception is not None:
#             # pylint: disable=raising-bad-type
#             raise exception
#         raise WaitTimeout("Timed out after %d seconds" % timeout)


# def parse_mappings(mapping_list, unique_values=True, unique_keys=True):
#     """Parse a list of mapping strings into a dictionary.
#
#     :param mapping_list: A list of strings of the form '<key>:<value>'.
#     :param unique_values: Values must be unique if True.
#     :param unique_keys: Keys must be unique if True, else implies that keys
#         and values are not unique.
#     :returns: A dict mapping keys to values or to list of values.
#     :raises ValueError: Upon malformed data or duplicate keys.
#     """
#     mappings = {}
#     for mapping in mapping_list:
#         mapping = mapping.strip()
#         if not mapping:
#             continue
#         split_result = mapping.split(':')
#         if len(split_result) != 2:
#             raise ValueError("Invalid mapping: '%s'" % mapping)
#         key = split_result[0].strip()
#         if not key:
#             raise ValueError("Missing key in mapping: '%s'" % mapping)
#         value = split_result[1].strip()
#         if not value:
#             raise ValueError("Missing value in mapping: '%s'" % mapping)
#         if unique_keys:
#             if key in mappings:
#                 raise ValueError("Key %(key)s in mapping: '%(mapping)s' not "
#                                    "unique" % {'key': key,
#                                                 'mapping': mapping})
#             if unique_values and value in mappings.values():
#                 raise ValueError("Value %(value)s in mapping: '%(mapping)s' "
#                                    "not unique" % {'value': value,
#                                                     'mapping': mapping})
#             mappings[key] = value
#         else:
#             mappings.setdefault(key, [])
#             if value not in mappings[key]:
#                 mappings[key].append(value)
#     return mappings

def is_enabled_and_bind_by_default():
    """Check if host has the IPv6 support and is configured to bind IPv6
    address to new interfaces by default.
    """
    global _IS_IPV6_ENABLED

    if _IS_IPV6_ENABLED is None:
        disabled_ipv6_path = "/proc/sys/net/ipv6/conf/default/disable_ipv6"
        if os.path.exists(disabled_ipv6_path):
            with open(disabled_ipv6_path, 'r') as f:
                disabled = f.read().strip()
            _IS_IPV6_ENABLED = disabled == "0"
        else:
            _IS_IPV6_ENABLED = False
        if not _IS_IPV6_ENABLED:
            logging.info("IPv6 not present or configured not to bind to new "
                     "interfaces on this system. Please ensure IPv6 is "
                     "enabled and /proc/sys/net/ipv6/conf/default/"
                     "disable_ipv6 is set to 0 to enable IPv6.")
    return _IS_IPV6_ENABLED

@contextlib.contextmanager
def tempdir(**kwargs):
    argdict = kwargs.copy()
    # if 'dir' not in argdict:
    #     argdict['dir'] = CONF.tempdir
    tmpdir = tempfile.mkdtemp(**argdict)
    try:
        yield tmpdir
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            logging.error('Could not remove tmpdir: %s', e)

def normpath(path):
    """Normalize path, eliminating double slashes, etc."""
    path = os.fspath(path)
    if isinstance(path, bytes):
        sep = b'/'
        empty = b''
        dot = b'.'
        dotdot = b'..'
    else:
        sep = '/'
        empty = ''
        dot = '.'
        dotdot = '..'
    if path == empty:
        return dot
    initial_slashes = path.startswith(sep)
    # POSIX allows one or two initial slashes, but treats three or more
    # as single slash.
    if (initial_slashes and
        path.startswith(sep*2) and not path.startswith(sep*3)):
        initial_slashes = 2
    comps = path.split(sep)
    new_comps = []
    for comp in comps:
        if comp in (empty, dot):
            continue
        if (comp != dotdot or (not initial_slashes and not new_comps) or
             (new_comps and new_comps[-1] == dotdot)):
            new_comps.append(comp)
        elif new_comps:
            new_comps.pop()
    comps = new_comps
    path = sep.join(comps)
    if initial_slashes:
        path = sep*initial_slashes + path
    return path or dot


def get_backing_file(version, image_id, base_path):
    """
    :param version: the image version
    :param image_id: when the version is larger than 0,the image_id is the template system disk uuid
    :param base_path: the system or data path
    :return:
    """
    backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
    if not os.path.isdir(backing_dir):
        ensure_tree(backing_dir)
    if version > 0:
        backing_file_name = constants.IMAGE_FILE_PREFIX % str(version) + image_id
    else:
        backing_file_name = image_id
    file_path = os.path.join(backing_dir, backing_file_name)
    return file_path
