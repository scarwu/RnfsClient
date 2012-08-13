# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

class UploadHandler(Thread):
    def __init__(self, dm, ra):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
    
    def run(self):
        self.dm.is_upload = True
        if self.dm.upload_index:
            self.handler()
        self.dm.is_upload = False
    
    def handler(self):
        while self.dm.upload_index:
            index = self.dm.upload_index.popleft()
            
            if self.dm.local_list[index]['type'] == 'dir':
                self.ra.uploadFile(index)
            else:
                print "<<< TX: %s" % index
                if not self.ra.uploadFile(index, self.dm.config['root'] + index):
                    if self.ra.getStatus() == 401:
                        print '<<< TX: Retry %s' % index
                        if self.ra.login():
                            self.dm.saveToken(self.ra.config['token'])
                            if not self.ra.uploadFile(index, self.dm.config['root'] + index):
                                print '<<< TX: Fail %s' % self.ra.getStatus()
                                print self.ra.getResult()
                        else:
                            print self.ra.getStatus()
                            print self.ra.getResult()
                            print '<<< TX: Exit'
                            sys.exit()
                    else:
                        print '<<< TX: Fail %s' % self.ra.getStatus()
                        print self.ra.getResult()

class DownloadHandler(Thread):
    def __init__(self, dm, ra):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
        
    def run(self):
        if self.dm.download_index:
            self.handler()
    
    def handler(self):
        while self.dm.download_index:
            index = self.dm.download_index.popleft()
            
            if self.dm.server_list[index]['type'] == 'dir':
                os.mkdir(self.dm.config['root'] + index)
            else:
                print ">>> RX: %s" % index
                if not self.ra.downloadFile(index, self.dm.config['root'] + index):
                    if self.ra.getStatus() == 401:
                        print '>>> RX: Retry %s' % index
                        if self.ra.login():
                            self.dm.saveToken(self.ra.config['token'])
                            if not self.ra.downloadFile(index, self.dm.config['root'] + index):
                                print '>>> RX ... Fail %s' % self.ra.getStatus()
                                print self.ra.getResult()
                        else:
                            print self.ra.getStatus()
                            print self.ra.getResult()
                            print '>>> RX: Exit'
                            sys.exit()
                    else:
                        print '>>> RX: Fail %s' % self.ra.getStatus()
                        print self.ra.getResult()
