# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

class LongPolling(Thread):
    def __init__(self, dm ,ra, dh):
        Thread.__init__(self)
        
        self.dm = dm
        self.ra = ra
        self.dh = dh
    
    def handler(self, callback):
        if callback['action'] == 'create':
            if callback['type'] == 'dir':
                print "LP (D) CREATE %s" % callback['path']
                if os.path.exists(self.dm.config['root'] + callback['path']):
                    os.mkdir(self.dm.config['root'] + callback['path'])
            elif callback['type'] == 'file':
                print "LP (F) CREATE %s" % callback['path']
                self.dm.download_list[callback['path']] = {
                    'type': 'file',
#                    'size': callback['size'],
                    'hash': callback['hash'],
                }
                self.dm.download_index.append(callback['path'])
                if not self.dh.isAlive():
                    self.dh.start()
                
        elif callback['action'] == 'update':
            pass
        
        elif callback['action'] == 'rename':
            print "LP (X) RENAME %s -> %s" % (callback['path'], callback['newpath'])
            os.rename(self.dm.config['root'] + callback['path'], self.dm.config['root'] + callback['newpath'])
            
        elif callback['action'] == 'delete':
            if callback['type'] == 'dir':
                print "LP (D) DELETE %s" % callback['path']
                os.rmdir(self.dm.config['root'] + callback['path'])
            elif callback['type'] == 'file':
                print "LP (F) DELETE %s" % callback['path']
                os.remove(self.dm.config['root'] + callback['path'])
    
    def run(self):
        print "LP ... Start"
        while(1):
            self.ra.sendPolling(self.dm.config['polling_time'])

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
                print 'LP ... Exit'
                sys.exit()
