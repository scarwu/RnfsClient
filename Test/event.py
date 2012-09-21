# -*- coding: utf-8 -*-

import os
import pyinotify

class EventListener():
    def __init__(self):

        target = '/tmp/test'
        
        if not os.path.exists(target):
            os.mkdir(target)
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVE_SELF
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(target, self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler(target))
    
        self.notifier.loop()
        
class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, target):
        pyinotify.ProcessEvent.__init__(self)
        self.target = target
            
    def process_IN_MOVED_FROM(self, event):
        path = event.pathname[len(self.target):]
        if os.path.isdir(event.pathname):
            print "EL ... (D) MOVE F %s" % path
        else:
            print "EL ... (F) MOVE F %s" % path
            
    def process_IN_MOVED_TO(self, event):
        path = event.pathname[len(self.target):]
        if os.path.isdir(event.pathname):
            print "EL ... (D) MOVE T %s" % path
        else:
            print "EL ... (F) MOVE T %s" % path
    
    def process_IN_MOVE_SELF(self, event):
        path = event.pathname[len(self.target):]
        print "EL ... (D) MOVE S %s" % path

if __name__ == '__main__':
    e = EventListener()
