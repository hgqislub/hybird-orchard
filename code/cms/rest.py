from oslo.config import cfg
import server
import sys

if __name__ == "__main__":
    sys.exit(server.main('rest'))
