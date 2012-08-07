# -*- coding: utf-8 -*-

import os
import pyinotify

class Handler(pyinotify.ProcessEvent):
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