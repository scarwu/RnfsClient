# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

import UDModel

class LongPolling(Thread):
    def __init__(self, lm ,ra, dh):
        Thread.__init__(self)
        
        self.lm = lm
        self.ra = ra
        self.dh = dh
    
    def handler(self, callback):
        if callback['action'] == 'create':
            callback['path'] = callback['path'].encode('utf-8')
            
            if callback['type'] == 'dir':
                self.lm.server_list[callback['path']] = {'type': 'dir'}
                self.lm.local_list[callback['path']] = {'type': 'dir'}
                
                print "LP (D) CREATE %s" % callback['path']
                if os.path.exists(self.lm.config['root'] + callback['path']):
                    os.mkdir(self.lm.config['root'] + callback['path'])
                    
            elif callback['type'] == 'file':
                self.lm.server_list[callback['path']] = {
                    'type': 'file',
                    'size': callback['size'],
                    'hash': callback['hash'],
                }
                self.lm.local_list[callback['path']] = {
                    'type': 'file',
                    'size': callback['size'],
                    'hash': callback['hash'],
                }
                
                print "LP (F) CREATE %s" % callback['path']
                self.lm.download_index.append(callback['path'])
                if not self.dh.isAlive():
                    self.dh = UDModel.DownloadHandler(self.lm, self.ra)
                    self.dh.start()

        elif callback['action'] == 'update':
            callback['path'] = callback['path'].encode('utf-8')
            pass
        
        elif callback['action'] == 'rename':
            callback['path'] = callback['path'].encode('utf-8')
            callback['newpath'] = callback['newpath'].encode('utf-8')
            
            self.lm.server_list[callback['newpath']] = self.lm.server_list[callback['path']]
            self.lm.server_list.pop(callback['path'])
             
            self.lm.local_list[callback['newpath']] = self.lm.local_list[callback['path']]
            self.lm.local_list.pop(callback['path'])
            
            print "LP (X) RENAME %s -> %s" % (callback['path'], callback['newpath'])
            os.rename(self.lm.config['root'] + callback['path'], self.lm.config['root'] + callback['newpath'])
            
        elif callback['action'] == 'delete':
            callback['path'] = callback['path'].encode('utf-8')
            
            self.lm.server_list.pop(callback['path'])
            self.lm.local_list.pop(callback['path'])
            
            if callback['type'] == 'dir':
                print "LP (D) DELETE %s" % callback['path']
                os.rmdir(self.lm.config['root'] + callback['path'])
            elif callback['type'] == 'file':
                print "LP (F) DELETE %s" % callback['path']
                os.remove(self.lm.config['root'] + callback['path'])
    
    def run(self):
        print "LP ... Start"
        while(1):
            self.ra.sendPolling(self.lm.config['polling_time'])

            if self.ra.getStatus() == 200:
                self.handler(self.ra.getResult())
                self.lm.saveListCache()
                    
            elif self.ra.getStatus() == 408:
                print 'LP ... Reconnect'
            else:
                print self.ra.getStatus()
                print self.ra.getResult()
                print 'LP ... Exit'
                sys.exit()
