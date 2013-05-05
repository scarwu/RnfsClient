# -*- coding: utf-8 -*-
'''
File Transfer Model

@package     RESTful Network File System
@author      ScarWu
@copyright   Copyright (c) 2012-2013, ScarWu (http://scar.simcz.tw/)
@license     https://github.com/scarwu/RnfsClient/blob/master/LICENSE
@link        https://github.com/scarwu/RnfsClient
'''

import os
from threading import Thread
from collections import deque

class Manager():
    def __init__(self, target, api, db):
        self.target = target
        self.api = api
        self.db = db
        
        # Initialize All Handler
        self.ul_handler = UploadHandler(self.target, self.api, self.db)
        self.dl_handler = DownloadHandler(self.target, self.api, self.db)
    
    # Start Upload Thread
    def upload(self, file_list):
        if not self.ul_handler.isAlive():
            self.ul_handler = UploadHandler(self.target, self.api, self.db)
            self.ul_handler.file_list = deque(file_list)
            self.ul_handler.start()
        else:
            for file_info in file_list:
                if file_info not in self.ul_handler.file_list:
                    self.ul_handler.file_list.append(file_info)
    
    # Start Download Thread
    def download(self, file_list):
        if not self.dl_handler.isAlive():
            self.dl_handler = DownloadHandler(self.target, self.api, self.db)
            self.dl_handler.file_list = deque(file_list)
            self.dl_handler.start()
        else:
            for file_info in file_list:
                if file_info not in self.dl_handler.file_list:
                    self.dl_handler.file_list.append(file_info)

    # Wait All Thread Finished
    def wait(self):
        if self.ul_handler.isAlive():
            self.ul_handler.join()
            
        if self.dl_handler.isAlive():
            self.dl_handler.join()

'''
File Upload Handler
'''
class UploadHandler(Thread):
    def __init__(self, target, api, db):
        Thread.__init__(self)
        
        self.target = target
        self.api = api
        self.db = db
        self.file_list = deque([])
    
    def run(self):
        if self.file_list:
            self.handler()
    
    def handler(self):
        while self.file_list:
            info = self.file_list.popleft()
            
            # Server Create Dir
            if info['type'] == 'dir':
                print "<<< Create Dir: %s" % info['path']
                self.db.add({
                    'path': info['path'],
                    'type': 'dir'
                })
                self.api.uploadFile(info['path'])
            
            # Upload File
            else:
                if info['update']:
                    print "<<< Update File: %s" % info['path']
                    if not self.api.updateFile(info['path'], self.target + info['path']):
                        self.db.delete(info['path'])
                        print '<<< Update File: Fail %s' % self.api.getStatus()
                        print self.api.getResult()
                else:
                    print "<<< Upload File: %s" % info['path']
                    self.db.add({
                        'path': info['path'],
                        'type': 'file'
                    })
                    if not self.api.uploadFile(info['path'], self.target + info['path']):
                        self.db.delete(info['path'])
                        print '<<< Upload File: Fail %s' % self.api.getStatus()
                        print self.api.getResult()

'''
File Download Handler
'''
class DownloadHandler(Thread):
    def __init__(self, target, api, db):
        Thread.__init__(self)
        
        self.target = target
        self.api = api
        self.db = db
        self.file_list = deque([])
        
    def run(self):
        if self.file_list:
            self.handler()
    
    def handler(self):
        while self.file_list:
            info = self.file_list.popleft()
            
            # Local Create Dir
            if info['type'] == 'dir':
                print ">>> Create Dir: %s" % info['path']
                self.db.add({
                    'path': info['path'],
                    'type': 'dir'
                })
                os.mkdir(self.target + info['path'])
                
            # Download File
            else:
                print ">>> Download File: %s" % info['path']
                self.db.add({
                    'path': info['path'],
                    'type': 'file'
                })
                if not self.api.downloadFile(info['path'], self.target + info['path']):
                    self.db.delete(info['path'])
                    print '>>> Download File: Fail %s' % self.api.getStatus()
                    print self.api.getResult()
