__author__ = 'Administrator'

from urlparse import urljoin
import json
import time
from hwcloud import LOG

from hwcloud.java_gateway import HWSRestMethod

def retry(times, interval):

    def _wrapper(f):
        def __wrapper(*args, **kwargs):
            timer = 0
            while(True):
                response = f(*args, **kwargs)
                if not str(response['status']).startswith('20'):
                    if timer < times:
                        timer += 1
                        time.sleep(interval)
                        LOG.debug('retry time: %s' % timer)
                        continue
                    else:
                        return response
                else:
                    return response
        return __wrapper
    return _wrapper

RETRY_TIMES = 10

#interval seconds
RETRY_INTERVAL = 0.5

class HWSService(object):
    def __init__(self, ak, sk, service_name, region, protocol, host, port):
        self.ak = ak
        self.sk = sk
        self.service_name = service_name
        self.region = region
        self.protocol = protocol
        self.host = host
        self.port = port
        self.uri_prefix = self.get_url_prefix()

    def get_url_prefix(self):
        return ":".join(["://".join([self.protocol, self.host]), self.port])

    def composite_full_uri(self, api_uri):
        return urljoin(self.uri_prefix, api_uri)

    @retry(RETRY_TIMES, RETRY_INTERVAL)
    def get(self, uri):
        request_url = self.composite_full_uri(uri)
        return json.loads(HWSRestMethod.get(self.ak, self.sk, request_url, self.service_name, self.region))

    @retry(RETRY_TIMES, RETRY_INTERVAL)
    def post(self, uri, body):
        request_url = self.composite_full_uri(uri)
        return json.loads(HWSRestMethod.post(self.ak, self.sk, request_url, body, self.service_name, self.region))

    @retry(RETRY_TIMES, RETRY_INTERVAL)
    def delete(self, uri):
        request_url = self.composite_full_uri(uri)
        return json.loads(HWSRestMethod.delete(self.ak, self.sk, request_url, self.service_name, self.region))

    def convertDictOptsToString(self, opts):
        str_opts = ""
        for key, value in opts.items():
            this_opt = "=".join([key, value])
            if str_opts == "":
                str_opts = this_opt
            else:
                str_opts = "&".join([str_opts, this_opt])
        return str_opts

    def get_job_detail(self, project_id, job_id):
        uri = '/v1/%s/jobs/%s' % (project_id, job_id)

        return self.get(uri)