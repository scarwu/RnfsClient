# -*- coding: utf-8 -*-

import os
import hashlib
import pyinotify
from threading import Thread

class EventListener(Thread):
    def __init__(self, target, api ,transfer, db):
        Thread.__init__(self)
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(target, self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler(target, api ,transfer, db))
    
    def run(self):
        print "EL ... Start"
        # Start Loop
        self.notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, target, api ,transfer, db):
        pyinotify.ProcessEvent.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
    
    # Delete File
    def process_IN_DELETE(self, event):
        path = event.pathname[len(self.target):]
        
        if self.db.isExists(path):
            print "EL (X) DELETE %s" % path
            
            # Server Delete
            self.api.deleteFile(path)
            
            # DB Delete
            self.db.delete(path)
    
    # Create File
    def process_IN_CREATE(self, event):
        path = event.pathname[len(self.target):]
        
        if not self.db.isExists(path):
            if os.path.isdir(event.pathname):
                print "EL (D) CREATE %s" % path
                
                # Server Create dir
                self.transfer.upload([{
                    'path': path,
                    'type': 'dir'
                }])
            else:
                print "EL (F) CREATE %s" % path
                
                # Upload File
                self.transfer.upload([{
                    'path': path,
                    'type': 'file',
                    'size': os.path.getsize(event.pathname),
                    'hash': self.md5Checksum(event.pathname),
                    'version': 0
                }])
                
    def process_IN_MODIFY(self, event):
        path = event.pathname[len(self.target):]
        
        if not os.path.isdir(event.pathname):
            print "EL ... (F) MODIFY %s" % event.pathname
            self.transfer.update([{
                'path': path,
                'type': 'file',
                'size': os.path.getsize(event.pathname),
                'hash': self.md5Checksum(event.pathname),
                'version': self.db.get(path)['version']+1,
                'to': 'server'
            }])
            
#    def process_IN_MOVED_FROM(self, event):
#        path = event.pathname[len(self.target):]
#
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE F %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE F %s" % event.pathname
            
#    def process_IN_MOVED_TO(self, event):
#        path = event.pathname[len(self.target):]
#
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE T %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE T %s" % event.pathname
        
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()