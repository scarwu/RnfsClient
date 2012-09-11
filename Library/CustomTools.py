# -*- coding: utf-8 -*-

import os
import hashlib

class LocalManage():
    def __init__(self):
        pass

    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    def getLocalList(self, path = ''):
        local_list = {}
        current_path = self.config['root'] + path
        for dirname in os.listdir(current_path):
            if os.path.isdir(current_path + '/' + dirname):
                local_list[path + '/' + dirname] = {
                    'type': 'dir'
                }
                local_list.update(self.getLocalList(path + '/' + dirname))
            else:
                local_list[path + '/' + dirname] = {
                    'type': 'file',
                    'hash': self.md5Checksum(current_path + '/' + dirname),
                    'size': os.path.getsize(current_path + '/' + dirname)
                }
        return local_list
    
    def fileInfo(self, path):
        if not os.path.exists(path):
            return None
        else:
            return {
                'hash': self.md5Checksum(self.config['root'] + '/' + path),
                'size': os.path.getsize(self.config['root'] + '/' + path)
            }
    