#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pyinotify

class EventHandler(pyinotify.ProcessEvent):
    # Delete
    def process_IN_DELETE(self, event):
        print "(X) DELETE %s" % event.pathname
    # Create
    def process_IN_CREATE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CREATE %s" % event.pathname
        else:
            print "(F) CREATE %s" % event.pathname
    # Modify
    def process_IN_MODIFY(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MODIFY %s" % event.pathname
        else:
            print "(F) MODIFY %s" % event.pathname
    # Colse Write
    def process_IN_CLOSE_WRITE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CWRITE %s" % event.pathname
        else:
            print "(F) CWRITE %s" % event.pathname
    def process_IN_MOVED_FROM(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MOVE F %s" % event.pathname
        else:
            print "(F) MOVE F %s" % event.pathname
    def process_IN_MOVED_TO(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MOVE T %s" % event.pathname
        else:
            print "(F) MOVE T %s" % event.pathname
         
if __name__ == '__main__':
    local = "/tmp/event_test"
    
    event_mask = 0
    event_mask |= pyinotify.IN_DELETE
    event_mask |= pyinotify.IN_CREATE
    event_mask |= pyinotify.IN_MODIFY
    event_mask |= pyinotify.IN_MOVED_TO
    event_mask |= pyinotify.IN_MOVED_FROM
        
    if os.path.exists(local) == False:
        os.mkdir(local)
        
    # Event Listener
    wm = pyinotify.WatchManager()
    wm.add_watch(local, event_mask, rec=True, auto_add=True)
    
    notifier = pyinotify.Notifier(wm, EventHandler())
    notifier.loop()
    