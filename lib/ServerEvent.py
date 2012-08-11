#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

class LongPolling(Thread):
    def __init__(self, ra, dm):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
    
    def handler(self, data):
        if data['action'] == 'create':
            if data['type'] == 'dir':
                os.mkdir(self.dm.config['root'] + data['path'])
            elif data['type'] == 'file':
                self.ra.downloadFile(data['path'], self.dm.config['root'] + data['path'])
                
        elif data['action'] == 'update':
            pass
        
        elif data['action'] == 'rename':
            os.rename(data['path'], data['newpath'])
            
        elif data['action'] == 'delete':
            if data['type'] == 'dir':
                os.rmdir(self.dm.config['root'] + data['path'])
            elif data['type'] == 'file':
                os.remove(self.dm.config['root'] + data['path'])
    
    def run(self):
        while(1):
            self.ra.sendPolling(self.config['polling_time'])
            
            print "LP %s %s" % (self.ra.getStatus(), self.ra.getResult())
            
            if self.ra.getStatus() == 200:
                self.handler(self.ra.getResult())
                
            elif self.ra.getStatus() == 401:
                print 'LP ... Login'
                if self.ra.login():
                    self.dm.saveToken(self.ra.config['token'])
                else:
                    print self.ra.getStatus()
                    print self.ra.getResult()
                    print 'RC ... Exit'
                    sys.exit()
                    
            elif self.ra.getStatus() == 408:
                print 'LP ... Reconnect'
            else:
                print self.ra.getStatus()
                print self.ra.getResult()
                print 'RC ... Exit'
                sys.exit()