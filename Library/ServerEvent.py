# -*- coding: utf-8 -*-

import os
from threading import Thread

class LongPolling(Thread):
    def __init__(self, target, api ,transfer, db):
        Thread.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
    
    def handler(self, callback):
        # Create File
        if callback['action'] == 'create':
            callback['path'] = callback['path'].encode('utf-8')

            if callback['type'] == 'dir':
                print "LongPolling (D) CREATE %s" % callback['path']
                if not os.path.exists(self.target + callback['path']):
                    # DB add
                    self.db.add({
                        'path': callback['path'],
                        'type': 'dir'
                    })
                    
                    # Client add
                    os.mkdir(self.target + callback['path'])
                
            elif callback['type'] == 'file':
                print "LongPolling (F) CREATE %s" % callback['path']
                
                # Download
                self.transfer.download([callback])
        
        # Update File
        elif callback['action'] == 'update':
            callback['path'] = callback['path'].encode('utf-8')
            callback['to'] = 'client'
            
            # Client Update
            self.transfer.update([callback])
        
        # Rename File
        elif callback['action'] == 'rename':
            callback['path'] = callback['path'].encode('utf-8')
            callback['newpath'] = callback['newpath'].encode('utf-8')
            print "LongPolling (X) RENAME %s -> %s" % (callback['path'], callback['newpath'])
            
            # DB Rename
            self.db.move(callback['path'], callback['newpath'])
            
            # Client Rename
            os.rename(self.target + callback['path'], self.target + callback['newpath'])
            
        
        # Delete
        elif callback['action'] == 'delete':
            callback['path'] = callback['path'].encode('utf-8')
            
            # DB delete
            self.db.delete(callback['path'])
            
            # Local Delete
            if callback['type'] == 'dir':
                print "LongPolling (D) DELETE %s" % callback['path']
                os.rmdir(self.target + callback['path'])
            elif callback['type'] == 'file':
                print "LongPolling (F) DELETE %s" % callback['path']
                os.remove(self.target + callback['path'])
    
    def run(self):
        print "LP ... Start"
        while(1):
            self.api.sendPolling()

            if self.api.getStatus() == 200:
                for callback in self.api.getResult():
                    self.handler(callback)
            elif self.api.getStatus() == 408:
                print 'LongPolling ... Reconnect'
            else:
                print self.api.getStatus()
                print self.api.getResult()
                print 'LongPolling ... Exit'
                os.sys.exit()
