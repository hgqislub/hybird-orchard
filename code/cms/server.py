import sys

from cms import config
from cms.common import log as logging
from cms import service

def main(servername):
    config.parse_args(sys.argv)
    logging.setup("cms")
     

    launcher = service.process_launcher()
    server = service.WSGIService(servername, use_ssl=False,
                                         max_url_len=16384)
    launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()
    
