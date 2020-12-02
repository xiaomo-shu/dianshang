import six
import sys
import logging
import traceback


class save_and_reraise_exception(object):
    """Save current exception, run some code and then re-raise.

    In some cases the exception context can be cleared, resulting in None
    being attempted to be re-raised after an exception handler is run. This
    can happen when eventlet switches greenthreads or when running an
    exception handler, code raises and catches an exception. In both
    cases the exception context will be cleared.

    To work around this, we save the exception state, run handler code, and
    then re-raise the original exception. If another exception occurs, the
    saved exception is logged and the new exception is re-raised.

    In some cases the caller may not want to re-raise the exception, and
    for those circumstances this context provides a reraise flag that
    can be used to suppress the exception.  For example::

      except Exception:
          with save_and_reraise_exception() as ctxt:
              decide_if_need_reraise()
              if not should_be_reraised:
                  ctxt.reraise = False

    If another exception occurs and reraise flag is False,
    the saved exception will not be logged.

    If the caller wants to raise new exception during exception handling
    he/she sets reraise to False initially with an ability to set it back to
    True if needed::

      except Exception:
          with save_and_reraise_exception(reraise=False) as ctxt:
              [if statements to determine whether to raise a new exception]
              # Not raising a new exception, so reraise
              ctxt.reraise = True

    .. versionchanged:: 1.4
       Added *logger* optional parameter.
    """
    def __init__(self, reraise=True, logger=None):
        self.reraise = reraise
        if logger is None:
            logger = logging.getLogger()
        self.logger = logger
        self.type_, self.value, self.tb = (None, None, None)

    def force_reraise(self):
        if self.type_ is None and self.value is None:
            raise RuntimeError("There is no (currently) captured exception"
                               " to force the reraising of")
        six.reraise(self.type_, self.value, self.tb)

    def capture(self, check=True):
        (type_, value, tb) = sys.exc_info()
        if check and type_ is None and value is None:
            raise RuntimeError("There is no active exception to capture")
        self.type_, self.value, self.tb = (type_, value, tb)
        return self

    def __enter__(self):
        # TODO(harlowja): perhaps someday in the future turn check here
        # to true, because that is likely the desired intention, and doing
        # so ensures that people are actually using this correctly.
        return self.capture(check=False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.reraise:
                self.logger.error('Original exception being dropped: %s',
                                  traceback.format_exception(self.type_,
                                                             self.value,
                                                             self.tb))
            return False
        if self.reraise:
            self.force_reraise()


class BaseException(Exception):
    """Base Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        try:
            if not message:
                message = self.msg_fmt % kwargs
            else:
                message = six.text_type(message)
        except Exception:
            # NOTE(melwitt): This is done in a separate method so it can be
            # monkey-patched during testing to make it a hard failure.
            self._log_exception()
            message = self.msg_fmt

        self.message = message
        super(BaseException, self).__init__(message)

    def _log_exception(self):
        # kwargs doesn't match a variable in the message
        # log the issue and the kwargs
        logging.exception('Exception in string format operation')
        for name, value in self.kwargs.items():
            logging.error("%s: %s" % (name, value))  # noqa

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full NovaException message, (see __init__)
        return self.args[0]

    def __repr__(self):
        dict_repr = self.__dict__
        dict_repr['class'] = self.__class__.__name__
        return str(dict_repr)


class UndefinedNetworkType(BaseException):
    code = 30001
    msg_fmt = "The network type %{type}s is undefined"


class NetworkNamespaceNotFound(BaseException):
    code = 30002
    msg_fmt = "Network namespace %(netns_name)s could not be found."


class NetworkInterfaceNotFound(BaseException):
    code = 30003
    msg_fmt = "Network interface %(device)s not found in namespace %(namespace)s."


class InterfaceOperationNotSupported(BaseException):
    code = 30004
    msg_fmt = "Operation not supported on interface %(device)s, namespace %(namespace)s."


class InterfaceNameTooLong(BaseException):
    code = 30005
    msg_fmt = "Interface %(interface)s name is too long."


class InvalidArgument(BaseException):
    code = 30006
    msg_fmt = "Invalid value %(value)s for parameter %(parameter)s provided."


class InstanceNotFound(BaseException):
    code = 30007
    msg_fmt = "Instance %(instance_id)s could not be found."


class InstancePowerOffFailure(BaseException):
    code = 300008
    msg_fmt = "Failed to power off instance: %(reason)s"


class HypervisorUnavailable(BaseException):
    code = 30009
    msg_fmt = "Connection to the hypervisor is broken on host: %(host)s"


class NBDConnectException(BaseException):
    code = 30010


class NBDDisconnectException(BaseException):
    code = 30011


class ModifyComputeNameException(BaseException):
    code = 30012


class SetIPAddressException(BaseException):
    code = 300013

#############################################################
class ImageNotFound(BaseException):
    code = 300014
    msg_fmt = "Image %(image)s not found"


class ImageVersionError(BaseException):
    code = 300015
    msg_fmt = "THE image version %(version)s is not correct, please check it"


class ImageCopyIOError(BaseException):
    code = 300016
    msg_fmt = "Copy image %(image)s raise IOError"


class CdromNotExist(BaseException):
    code = 300017
    msg_fmt = "There is no cdrom device in domain %(domain)s"


class ChangeCdromPathError(BaseException):
    code = 300018
    msg_fmt = "Change the domain %(domain)s cdrom path error:%(error)s"


class ImageResizeError(BaseException):
    code = 300019
    msg_fmt = "Resize image %(image)s Error:%(error)s"


class ImageCommitError(BaseException):
    code = 300020
    msg_fmt = "Commit image %(image)s Error:%(error)s"


class InstanceAutostartError(BaseException):
    code = 300021
    msg_fmt = "set instance %(instance)s autostart Error"


class ImageDeleteIOError(BaseException):
    code = 300022
    msg_fmt = "delete image %(image)s raise IOError"


class ImageRebaseError(BaseException):
    code = 300023
    msg_fmt = "rebase image %(image)s raise IOError"

#############################################################


class BondException(BaseException):
    code = 300023
    msg_fmt = "Bond Error: %(error)s !"


class UnBondException(BaseException):
    code = 300024
    msg_fmt = "UnBond Error: %(error)s !"


class EnableHaException(BaseException):
    code = 300025
    msg_fmt = "Enable HA Error: %(error)s !"


class DisableHaException(BaseException):
    code = 300026
    msg_fmt = "Disable HA Error: %(error)s !"


class SwitchHaMasterException(BaseException):
    code = 300027
    msg_fmt = "Switch HA Master Error: %(error)s !"


class VGNotExists(BaseException):
    code = 300028
    msg_fmt = "卷组'%(vg)s'不存在"


class PVCreateError(BaseException):
    code = 300029
    msg_fmt = "创建物理卷'%(pv)s'失败: %(error)s"


class VGExtendError(BaseException):
    code = 300031
    msg_fmt = "卷组'%(vg)s'扩容失败: %(error)s"


class LVNotExists(BaseException):
    code = 300032
    msg_fmt = "逻辑卷'%(lv)s'不存在"


class LVExtendError(BaseException):
    code = 300033
    msg_fmt = "逻辑卷'%(lv)s'扩容失败：%(error)s"


class UnSupportFileFormat(BaseException):
    code = 300034
    msg_fmt = "不支持的文件系统类型：%(fstype)s"


class LVFormatGetFailed(BaseException):
    code = 300035
    msg_fmt = "获取逻辑卷'%(lv)s'文件系统格式失败，请先格式化"


class LVSyncFormatFailed(BaseException):
    code = 300036
    msg_fmt = "逻辑卷'%(lv)s'同步文件系统失败"


class VGNoEnoughSize(BaseException):
    code = 300037
    msg_fmt = "卷组'%(vg)s'可用空间不足"


class LVAlreadyExists(BaseException):
    code = 300038
    msg_fmt = "逻辑卷'%(lv)s'已存在"


class LVCreateError(BaseException):
    code = 300039
    msg_fmt = "逻辑卷'%(lv)s'创建失败：%(error)s"


class LVMountError(BaseException):
    code = 300040
    msg_fmt = "挂载'%(lv)s'到'%(mount_point)s'失败：%(error)s"


class LVRemoveError(BaseException):
    code = 300041
    msg_fmt = "逻辑卷'%(lv)s'删除失败：%(error)s"
