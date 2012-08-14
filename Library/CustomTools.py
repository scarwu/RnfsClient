# -*- coding: utf-8 -*-

import os
import json
import hashlib
import ConfigParser
from collections import deque

class LocalManage():
    def __init__(self):
        self.config_path = 'RNFileSystemClient.ini'
        if not os.path.exists(self.config_path):
            file(self.config_path, 'wb').write(file('RNFileSystemClient.sample.ini', 'rb').read())
        
        self.config_parser = ConfigParser.RawConfigParser()
        self.config_parser.read(self.config_path)
        self.config = {
            'config_path': self.config_path,
            'root': self.config_parser.get('local', 'root'),
            'cache_list': self.config_parser.get('local', 'cache_list'),
            'host': self.config_parser.get('server', 'host'),
            'port': self.config_parser.getint('server', 'port'),
            'ssl': self.config_parser.getboolean('server', 'ssl'),
            'sync_time': self.config_parser.getint('time', 'sync'),
            'polling_time': self.config_parser.getint('time', 'polling'),
            'username': self.config_parser.get('info', 'username'),
            'password': self.config_parser.get('info', 'password'),
            'token': self.config_parser.get('info', 'token')
        }
        
        # Check root directory
        if not os.path.exists(self.config['root']):
            os.mkdir(self.config['root'])
            
        # Check root directory
        if not os.path.exists(self.config['cache_list']):
            file(self.config['cache_list'], 'wb').write("{}")
            self.cache_list = {}
        else:
            self.cache_list = json.loads(file(self.config['cache_list'], 'rb').read())

        self.user_info = {}
        self.server_list = {}
        self.local_list = {}
        
        self.upload_index = deque([])
        self.download_index = deque([])
    
    def saveListCache(self):
        file(self.config['cache_list'], 'wb').write(json.dumps(self.local_list, separators=(',', ':')))

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
    
    def removeDir(self, dirname):
        for path in (os.path.join(dirname, filename) for filename in os.listdir(self.config['root'] + '/' + dirname)):
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
                'hash': self.md5Checksum(self.config['root'] + '/' + path),
                'size': os.path.getsize(self.config['root'] + '/' + path)
            }
    