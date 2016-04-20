import sys

from oslo.config import cfg
import webob.exc

from cms.i18n import _
from cms.common import excutils
from cms.common import log as logging

LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Make exception message format errors fatal'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


def _cleanse_dict(original):
    """Strip all admin_password, new_pass, rescue_pass keys from a dict."""
    return dict((k, v) for k, v in original.iteritems() if "_pass" not in k)


class CMSException(Exception):
    """Base CMS Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False
    title = ''

    def __init__(self, message=None, code=500, title='', **kwargs):
        self.kwargs = kwargs
        self.code = code
        self.title = title

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))    # noqa

                if CONF.fatal_exception_format_errors:
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(CMSException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full CMSException message, (see __init__)
        return self.args[0]

        
class ValidationError(CMSException):
    msg_fmt = _("Expecting to find %(attribute)s in %(target)s -"
                       " the server could not comply with the request"
                       " since it is either malformed or otherwise"
                       " incorrect. The client is assumed to be in error.")
    code = 400
    title = 'Bad Request'

class Invalid(CMSException):
    msg_fmt = _("Unacceptable parameters.")
    code = 400

class Forbidden(CMSException):
    msg_fmt = _("Not authorized.")
    code = 403

class UnexpectedError(CMSException):
    msg_fmt = _("Unexpected Error.")
    code = 500

class AdminRequired(Forbidden):
    msg_fmt = _("Cloud does not have admin privileges")

class InvalidInput(Invalid):
    msg_fmt = _("Invalid input received: %(reason)s")

class InvalidContentType(Invalid):
    msg_fmt = _("Invalid content type %(content_type)s.")

class InvalidID(Invalid):
    title = "Invalid Id"
    msg_fmt = _("Invalid ID received %(id)s.")

class NotFound(CMSException):
    title = "Not Found"
    msg_fmt = _("Resource could not be found.")
    code = 404

class ConfigNotFound(CMSException):
    msg_fmt = _("Could not find config at %(path)s")

class PasteAppNotFound(CMSException):
    msg_fmt = _("Could not load paste app '%(name)s' from %(path)s")

class MalformedRequestBody(CMSException):
    msg_fmt = _("Malformed message body: %(reason)s")

class OrphanedObjectError(CMSException):
    msg_fmt = _('Cannot call %(method)s on orphaned %(objtype)s object')


class ObjectActionError(CMSException):
    msg_fmt = _('Object action %(action)s failed because: %(reason)s')

class DataExists(CMSException):
    title = "Data Already Exists"
    code = 409
    msg_fmt = _("data already exists.")

class CloudExists(DataExists):
    title = "Cloud Already Exists"
    msg_fmt = _("Cloud name <%(name)s> already exists in region <%(region)s>.")

class UserExists(DataExists):
    title = "User Already Exists"
    msg_fmt = _("User name <%(name)s> already exists in region <%(region)s>.")

class AssociationExists(DataExists):
    title = "Association Already Exists"
    msg_fmt = _("%(obj)s <%(name)s> association already exists in region <%(region)s>.")

class CloudNotFound(NotFound):
    title = "Cloud Not Found"
    msg_fmt = _("Cloud not found for id <%(id)s>.")

class UserNotFound(NotFound):
    title = "User Not Found"
    msg_fmt = _("User not found for id <%(id)s>.")

class AssociationNotFound(NotFound):
    title = "Association Not Found"
    msg_fmt = _("%(obj)s association not found for id <%(id)s>.")

class CloudCreateFailed(CMSException):
    msg_fmt = _("Unable to create cloud")

class UserCreateFailed(CMSException):
    msg_fmt = _("Unable to create cloud")

class AssociationCreateFailed(CMSException):
    msg_fmt = _("Unable to create association")

class IntegrityException(CMSException):
    code = 409
    title = 'Integrity Exception'
    msg_fmt = _("%(msg)s.")

# class CloudIntegrityException(IntegrityException):
    # title = 'Integrity Exception'
    # msg_fmt = 'Cloud integrity Exception' 

# class AssociationIntegrityException(IntegrityException):
    # title = 'Association Integrity Error'
    # msg_fmt = _("association failed: %(msg)s.")

class CloudInUse(CMSException):
    title = "Cloud IN USE"
    code = 409
    msg_fmt = _("Cloud %(id)s is still in use.")

class UserInUse(CMSException):
    title = "User IN USE"
    code = 409
    msg_fmt = _("User %(id)s is still in use.")

class CloudUnSupportedType(CMSException):
    title = "Bad Request"
    code = 400
    msg_fmt = _("Cloud Unsupported cloud type %(type)s.")
