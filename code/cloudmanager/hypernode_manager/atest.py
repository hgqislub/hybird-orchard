import json
def read_conf(file_path):
    fd = None
    try:
        fd = open(file_path, 'r+')
        tmp = fd.read()
        print tmp
        return json.loads(tmp)
    finally:
        if fd:
            fd.close()

read_conf("E:\\test.txt")