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
        
    def run(self):
        print "LongPolling Start"
        while(1):
            self.api.sendPolling()

            if self.api.getStatus() == 200:
                for callback in self.api.getResult():
                    self.handler(callback)
            elif self.api.getStatus() == 408:
                print 'LongPolling Reconnect'
            else:
                print self.api.getStatus()
                print self.api.getResult()
                print 'LongPolling Exit'
                os.sys.exit()
    
    # Recursive Remove Directory
    def rmRmdir(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    
    def handler(self, callback):
        # Create File
        if callback['action'] == 'create':
            callback['path'] = callback['path'].encode('utf-8')

            if callback['type'] == 'dir':
                print "LongPolling Create Dir %s" % callback['path']
                if not os.path.exists(self.target + callback['path']):
                    # DB add
                    self.db.add({
                        'path': callback['path'],
                        'type': 'dir'
                    })
                    
                    # Client add
                    os.mkdir(self.target + callback['path'])
                
            elif callback['type'] == 'file':
                callback['update'] = False
                print "LongPolling Create File %s" % callback['path']
                
                # Download
                self.transfer.download([callback])
        
        # Update File
        elif callback['action'] == 'update':
            callback['path'] = callback['path'].encode('utf-8')
            callback['update'] = True
            print "LongPolling Update File %s" % callback['path']
            
            # Client Update
            self.transfer.download([callback])
        
        # Rename File
        elif callback['action'] == 'rename':
            callback['path'] = callback['path'].encode('utf-8')
            callback['newpath'] = callback['newpath'].encode('utf-8')
            print "LongPolling Rename %s -> %s" % (callback['path'], callback['newpath'])
            
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
                print "LongPolling Delete Dir %s" % callback['path']
                self.reRmdir(self.target + callback['path'])
            elif callback['type'] == 'file':
                print "LongPolling Delete File %s" % callback['path']
                os.remove(self.target + callback['path'])
