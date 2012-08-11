# -*- coding: utf-8 -*-

import os
import sys
import pyinotify
from threading import Thread

class EventListener(Thread):
    def __init__(self, ra, dm):
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
        wm.add_watch(dm.config['root'], self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler(ra, dm))
    
    def run(self):
        # Start Loop
        self.notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, ra, dm):
        pyinotify.ProcessEvent.__init__(self)
        
        self.ra = ra
        self.dm = dm
    
    def errorHandler(self, status):
        if status == 401:
            print 'EL ... Login'
            if self.ra.login():
                self.dm.saveToken(self.ra.config['token'])
            else:
                print self.ra.getStatus()
                print self.ra.getResult()
                print 'RC ... Exit'
                sys.exit()
                
        elif status == 404:
            print "EL %d %s" % (self.ra.getStatus(), self.ra.getResult())
            
        else:
            print "EL %d %s" % (self.ra.getStatus(), self.ra.getResult())
            print 'RC ... Exit'
            sys.exit()
    
    def process_IN_DELETE(self, event):
        path = event.pathname[len(self.dm.config['root']):]
        print "EL (X) DELETE %s" % path
        # FIXME
        while not self.ra.deleteFile(path):
            self.errorHandler(self.ra.getStatus())
        
    def process_IN_CREATE(self, event):
        path = event.pathname[len(self.dm.config['root']):]
        if os.path.isdir(event.pathname):
            print "EL (D) CREATE %s" % path
            while not self.ra.uploadFile(path):
                self.errorHandler(self.ra.getStatus())
        else:
            print "EL (F) CREATE %s" % path
            while not self.ra.uploadFile(path, event.pathname):
                self.errorHandler(self.ra.getStatus())
            
#    def process_IN_MODIFY(self, event):
#        path = event.pathname[len(self.dm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MODIFY %s" % event.pathname
#        else:
#            print "EL ... (F) MODIFY %s" % event.pathname
#            
#    def process_IN_MOVED_FROM(self, event):
#        path = event.pathname[len(self.dm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE F %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE F %s" % event.pathname
#            
#    def process_IN_MOVED_TO(self, event):
#        path = event.pathname[len(self.dm.config['root']):]
#        if os.path.isdir(event.pathname):
#            print "EL ... (D) MOVE T %s" % event.pathname
#        else:
#            print "EL ... (F) MOVE T %s" % event.pathname