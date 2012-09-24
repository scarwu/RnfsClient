#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pyinotify

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, target):
        pyinotify.ProcessEvent.__init__(self)
        self.target = target
    
    def process_IN_DELETE(self, event):
        path = event.pathname[len(self.target):]
        print "Delete %s" % path
    
    def process_IN_CREATE(self, event):
        path = event.pathname[len(self.target):]
        if os.path.isdir(event.pathname):
            print "(D) Create %s" % path
        else:
            print "(F) Create %s" % path
    
    def process_IN_MODIFY(self, event):
        path = event.pathname[len(self.target):]
        if os.path.isdir(event.pathname):
            print "(D) Modify %s" % path
        else:
            print "(F) Modify %s" % path
            
    def process_IN_MOVED_FROM(self, event):
        path = event.pathname[len(self.target):]
        print event
        print "(F) (Delete) Moved from %s" % path
            
    def process_IN_MOVED_TO(self, event):
        path = event.pathname[len(self.target):]
        try:
            src_path = event.src_pathname[len(self.target):]
            print "(X) Rename %s -> %s" % (src_path, path)
        except:
            if event.dir:
                print "(D) (Create) Moved to %s" % path
            else:
                print "(F) (Create) Moved to %s" % path
            
if __name__ == '__main__':
    target = '/tmp/test'
        
    if not os.path.exists(target):
        os.mkdir(target)
    
    # Inotify event mask
    event_mask = 0
    event_mask |= pyinotify.IN_DELETE
    event_mask |= pyinotify.IN_CREATE
    event_mask |= pyinotify.IN_MODIFY
    event_mask |= pyinotify.IN_MOVED_TO
    event_mask |= pyinotify.IN_MOVED_FROM
    
    # Event Listener
    wm = pyinotify.WatchManager()
    wm.add_watch(target, event_mask, rec=True, auto_add=True)
    notifier = pyinotify.Notifier(wm, EventHandler(target))

    notifier.loop()