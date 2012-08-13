# -*- coding: utf-8 -*-

import os
import hashlib
import pyinotify
from threading import Thread

import UDModel

class EventListener(Thread):
    def __init__(self, lm ,ra, uh):
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
        wm.add_watch(lm.config['root'], self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler(lm ,ra, uh))
    
    def run(self):
        print "EL ... Start"
        # Start Loop
        self.notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, lm ,ra, uh):
        pyinotify.ProcessEvent.__init__(self)
        
        self.lm = lm
        self.ra = ra
        self.uh = uh
    
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    def process_IN_DELETE(self, event):
        path = event.pathname[len(self.lm.config['root']):]
        print "EL (X) DELETE %s" % path
        self.ra.deleteFile(path);
        
    def process_IN_CREATE(self, event):
        path = event.pathname[len(self.lm.config['root']):]
        if os.path.isdir(event.pathname):
            print "EL (D) CREATE %s" % path
            self.lm.local_list[path] = {
                'type': 'dir'
            }
            self.lm.upload_index.append(path)
            if not self.uh.isAlive():
                self.uh = UDModel.UploadHandler(self.lm, self.ra)
                self.uh.start()
        else:
            print "EL (F) CREATE %s" % path
            self.lm.local_list[path] = {
                'type': 'file',
                'hash': self.md5Checksum(event.pathname),
                'size': os.path.getsize(event.pathname)
            }
            self.lm.upload_index.append(path)
            if not self.uh.isAlive():
                self.uh = UDModel.UploadHandler(self.lm, self.ra)
                self.uh.start()
            
#    def process_IN_MODIFY(self, event):
#        path = event.pathname[len(self.lm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MODIFY %s" % event.pathname
#        else:
#            print "EL ... (F) MODIFY %s" % event.pathname
#            
#    def process_IN_MOVED_FROM(self, event):
#        path = event.pathname[len(self.lm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE F %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE F %s" % event.pathname
#            
#    def process_IN_MOVED_TO(self, event):
#        path = event.pathname[len(self.lm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE T %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE T %s" % event.pathname