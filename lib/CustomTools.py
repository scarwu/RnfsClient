# -*- coding: utf-8 -*-

import os
import hashlib

class FileHandler():
    def __init__(self, root):
        self.root = root
        
        # Check root directory
        if not os.path.exists(self.root):
            os.mkdir(self.root)
    
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
        current_path = self.root + path
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
    
    def removeDir(self, dirname):
        for path in (os.path.join(dirname, filename) for filename in os.listdir(self.root + '/' + dirname)):
            if os.path.isdir(path):
                self.removeDir(path)
            elif os.path.exists(path):
                    os.unlink(path)
                    
        if os.path.exists(dirname):
            os.rmdir(dirname)
    
    def fileInfo(self, path):
        if not os.path.exists(path):
            return None
        else:
            return {
                'hash': self.md5Checksum(self.root + '/' + path),
                'size': os.path.getsize(self.root + '/' + path)
            }