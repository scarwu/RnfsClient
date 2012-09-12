# -*- coding: utf-8 -*-

import os
from threading import Thread
from collections import deque

class Manager():
    def __init__(self, root, api, db):
        self.ul_handler = None
        self.dl_handler = None
        self.up_handler = None
        
        self.root = root
        self.api = api
        self.db = db
    
    def upload(self, index):
        self.ul_handler.index += deque([index])
        if not self.ul_handler.index and not self.ul_handler.isAlive():
            self.ul_handler = UploadHandler(self.root, self.api, self.db)
            self.ul_handler.start()

    def download(self, index):
        self.dl_handler.index += deque([index])
        if not self.dl_handler.index and not self.dl_handler.isAlive():
            self.dl_handler = DownloadHandler(self.root, self.api, self.db)
            self.dl_handler.start()
    
    def update(self, index):
        self.up_handler.index += deque([index])
        if not self.up_handler.index and not self.up_handler.isAlive():
            self.up_handler = UpdateHandler(self.root, self.api, self.db)
            self.up_handler.start()

    def wait(self):
        if self.ul_handler.isAlive():
            self.ul_handler.join()
            
        if self.dl_handler.isAlive():
            self.dl_handler.join()
            
        if self.up_handler.isAlive():
            self.up_handler.join()

class UpdateHandler(Thread):
    def __init__(self, root, api, db):
        Thread.__init__(self)
        
        self.root = root
        self.api = api
        self.db = db
        self.index = None
    
    def run(self):
        if self.index:
            self.handler()
    
    def handler(self):
        while self.index:
            index = self.index.popleft()
            
            print "<<< Update File: %s" % index
            if not self.api.updateFile(index, self.root + index):
                print '<<< Update File: Fail %s' % self.api.getStatus()
                print self.api.getResult()

class UploadHandler(Thread):
    def __init__(self, root, api, db):
        Thread.__init__(self)
        
        self.root = root
        self.api = api
        self.db = db
        self.index = None
    
    def run(self):
        if self.index:
            self.handler()
    
    def handler(self):
        while self.index:
            index = self.index.popleft()
            
            if self.lm.file_list[index]['type'] == 'dir':
                print "<<< Create Dir: %s" % index
                self.api.uploadFile(index)
                self.db.add({
                    'path': index,
                    'type': 'dir'
                })
            else:
                print "<<< Upload File: %s" % index
                if not self.api.uploadFile(index, self.root + index):
                    print '<<< Upload File: Fail %s' % self.api.getStatus()
                    print self.api.getResult()
                else:
                    self.db.add({
                        'path': index,
                        'type': 'file'
                    })

class DownloadHandler(Thread):
    def __init__(self, root, api, db):
        Thread.__init__(self)
        
        self.root = root
        self.api = api
        self.db = db
        self.index = None
        
    def run(self):
        if self.index:
            self.handler()
    
    def handler(self):
        while self.index:
            index = self.index.popleft()
            
            if self.lm.file_list[index]['type'] == 'dir':
                print ">>> Create Dir: %s" % index
                os.mkdir(self.root + index)
                self.db.add({
                    'path': index,
                    'type': 'dir'
                })
            else:
                print ">>> Download File: %s" % index
                if not self.api.downloadFile(index, self.root + index):
                    print '>>> Download File: Fail %s' % self.api.getStatus()
                    print self.api.getResult()
                else:
                    self.db.add({
                        'path': index,
                        'type': 'file'
                    })
