# -*- coding: utf-8 -*-

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
        self.up_handler = UpdateHandler(self.target, self.api, self.db)
    
    # Start Upload Thread
    def upload(self, file_list):
        if not self.ul_handler.isAlive():
            self.ul_handler = UploadHandler(self.target, self.api, self.db)
            self.ul_handler.file_list = deque(file_list)
            self.ul_handler.start()
        else:
            self.ul_handler.file_list += deque(file_list)
    
    # Start Download Thread
    def download(self, file_list):
        if not self.dl_handler.isAlive():
            self.dl_handler = DownloadHandler(self.target, self.api, self.db)
            self.dl_handler.file_list = deque(file_list)
            self.dl_handler.start()
        else:
            self.dl_handler.file_list += deque(file_list)
    
    # Start Update Thread
    def update(self, file_list):
        if not self.up_handler.isAlive():
            self.up_handler = UpdateHandler(self.target, self.api, self.db)
            self.up_handler.file_list = deque(file_list)
            self.up_handler.start()
        else:
            self.up_handler.file_list += deque(file_list)

    # Wait All Thread Finished
    def wait(self):
        if self.ul_handler.isAlive():
            self.ul_handler.join()
            
        if self.dl_handler.isAlive():
            self.dl_handler.join()
            
        if self.up_handler.isAlive():
            self.up_handler.join()

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

'''
File Update Handler
'''
class UpdateHandler(Thread):
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
            
            # Upload File
            if info['to'] == 'server':
                print "<<< Update File: %s" % info['path']
                if not self.api.updateFile(info['path'], self.target + info['path']):
                    self.db.delete(info['path'])
                    print '<<< Update File: Fail %s' % self.api.getStatus()
                    print self.api.getResult()
            
            # Download File
            else:
                print ">>> Update File: %s" % info['path']
                
                if not self.db.isExists(info['path']):
                    self.db.add({
                        'path': info['path'],
                        'type': 'file'
                    })

                if not self.api.downloadFile(info['path'], self.target + info['path']):
                    self.db.delete(info['path'])
                    print '>>> Update File: Fail %s' % self.api.getStatus()
                    print self.api.getResult()
                    