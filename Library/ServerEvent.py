# -*- coding: utf-8 -*-

import os
import sys
from threading import Thread

class LongPolling(Thread):
    def __init__(self, target, api ,transfer, db):
        Thread.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
    
    def handler(self, callback):
        if callback['action'] == 'create':
            callback['path'] = callback['path'].encode('utf-8')
            
            if callback['type'] == 'dir':
                print "LP (D) CREATE %s" % callback['path']
                if not os.path.exists(self.target + callback['path']):
                    os.mkdir(self.target + callback['path'])
                
                self.db.add({
                    'path': callback['path'],
                    'type': 'dir'
                })
                    
            elif callback['type'] == 'file':
                print "LP (F) CREATE %s" % callback['path']
                self.transfer.download([callback])

#        elif callback['action'] == 'update':
#            callback['path'] = callback['path'].encode('utf-8')
#            self.transfer.update([callback])
        
#        elif callback['action'] == 'rename':
#            callback['path'] = callback['path'].encode('utf-8')
#            callback['newpath'] = callback['newpath'].encode('utf-8')
#            
#            print "LP (X) RENAME %s -> %s" % (callback['path'], callback['newpath'])
#            os.rename(self.target + callback['path'], self.target + callback['newpath'])
            
        elif callback['action'] == 'delete':
            callback['path'] = callback['path'].encode('utf-8')
            
            if callback['type'] == 'dir':
                print "LP (D) DELETE %s" % callback['path']
                os.rmdir(self.target + callback['path'])
            elif callback['type'] == 'file':
                print "LP (F) DELETE %s" % callback['path']
                os.remove(self.target + callback['path'])

            self.db.delete(callback['path'])

    def run(self):
        print "LP ... Start"
        while(1):
            self.api.sendPolling()

            if self.api.getStatus() == 200:
                for callback in self.api.getResult():
                    self.handler(callback)
                    
            elif self.api.getStatus() == 408:
                print 'LP ... Reconnect'
            else:
                print self.api.getStatus()
                print self.api.getResult()
                print 'LP ... Exit'
                sys.exit()
