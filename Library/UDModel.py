# -*- coding: utf-8 -*-

import os
from threading import Thread

class UploadHandler(Thread):
    def __init__(self, lm, ra):
        Thread.__init__(self)
        
        self.ra = ra
        self.lm = lm
    
    def run(self):
        if self.lm.upload_index:
            self.handler()
    
    def handler(self):
        while self.lm.upload_index:
            index = self.lm.upload_index.popleft()
            
            if self.lm.file_list[index]['type'] == 'dir':
                self.ra.uploadFile(index)
            else:
                print "<<< TX: %s" % index
                if not self.ra.uploadFile(index, self.lm.config['root'] + index):
                    print '<<< TX: Fail %s' % self.ra.getStatus()
                    print self.ra.getResult()

class DownloadHandler(Thread):
    def __init__(self, lm, ra):
        Thread.__init__(self)
        
        self.ra = ra
        self.lm = lm
        
    def run(self):
        if self.lm.download_index:
            self.handler()
    
    def handler(self):
        while self.lm.download_index:
            index = self.lm.download_index.popleft()
            
            if self.lm.file_list[index]['type'] == 'dir':
                os.mkdir(self.lm.config['root'] + index)
            else:
                print ">>> RX: %s" % index
                if not self.ra.downloadFile(index, self.lm.config['root'] + index):
                    print '>>> RX: Fail %s' % self.ra.getStatus()
                    print self.ra.getResult()
