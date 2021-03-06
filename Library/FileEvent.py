# -*- coding: utf-8 -*-
'''
File Event Handler

@package     RESTful Network File System
@author      ScarWu
@copyright   Copyright (c) 2012-2013, ScarWu (http://scar.simcz.tw/)
@license     https://github.com/scarwu/RnfsClient/blob/master/LICENSE
@link        https://github.com/scarwu/RnfsClient
'''

import time
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
        print "FileEvent Start"
        
        # Start Loop
        self.notifier.loop()

class EventCounter(Thread):
    def __init__(self, handler):
        Thread.__init__(self)
        
        self.handler = handler
    
    def run(self):
        time.sleep(1)
        self.handler.addEvent(None)

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, target, api ,transfer, db):
        pyinotify.ProcessEvent.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
        
        self.counter = EventCounter(self)
        
        self.event_buffer = None
    
    # Delete File
    def process_IN_DELETE(self, event):
        self.addEvent(None)
        
        path = event.pathname[len(self.target):]
        
        if self.db.isExists(path):
            print "FileEvent Delete %s" % path
            
            # Server Delete
            self.api.deleteFile(path)
            
            # DB Delete
            self.db.delete(path)
    
    # Create File
    def process_IN_CREATE(self, event):
        self.addEvent(None)
        
        path = event.pathname[len(self.target):]
        
        if not self.db.isExists(path):
            if event.dir:
                print "FileEvent Create Dir %s" % path
                
                # Server Create dir
                self.transfer.upload([{
                    'path': path,
                    'type': 'dir'
                }])
            else:
                print "FileEvent Create File %s" % path
                
                # Upload File
                self.transfer.upload([{
                    'path': path,
                    'type': 'file',
                    'update': False
                }])
    
    # File Modify
    def process_IN_MODIFY(self, event):
        self.addEvent(None)
        
        path = event.pathname[len(self.target):]
        
        if not event.dir:
            print "FileEvent Modify %s" % path
            self.transfer.upload([{
                'path': path,
                'type': 'file',
                'update': True
            }])
    
    # File Moved from
    def process_IN_MOVED_FROM(self, event):
        self.addEvent('moved_from', event)
    
    # File Moved to
    def process_IN_MOVED_TO(self, event):
        self.addEvent('moved_to', event)
    
    # Add Event to Buffer
    def addEvent(self, action=None, event=None):
        if self.counter.isAlive():
            self.counter._Thread__stop()
        
        if action == 'moved_from':
            if self.event_buffer != None:
                self.movedFrom(self.event_buffer) 
                self.event_buffer = None
            
            self.event_buffer = event

        elif action == 'moved_to':
            self.event_buffer = None
            self.movedTo(event)
            
        elif self.event_buffer != None:
            self.movedFrom(self.event_buffer)
            self.event_buffer = None
        
        if self.event_buffer != None:
            self.counter = EventCounter(self)
            self.counter.start()
    
    def movedTo(self, event):
        path = event.pathname[len(self.target):]
        try:
            src_path = event.src_pathname[len(self.target):]
            print "FileEvent (X) Rename %s -> %s" % (src_path, path)
            self.db.move(src_path, path)
            self.api.moveFile(src_path, path)
        except:
            if not self.db.isExists(path):
                if event.dir:
                    print "FileEvent Create Dir (Moved to) %s" % path
                    
                    # Server Create dir
                    self.transfer.upload([{
                        'path': path,
                        'type': 'dir'
                    }])
                else:
                    print "FileEvent Create File (Moved to) %s" % path
                    
                    # Upload File
                    self.transfer.upload([{
                        'path': path,
                        'type': 'file',
                        'update': False
                    }])
    
    def movedFrom(self, event):
        path = event.pathname[len(self.target):]
        if self.db.isExists(path):
            print "FileEvent Delete (Moved from) %s" % path
            
            # Server Delete
            self.api.deleteFile(path)
            
            # DB Delete
            self.db.delete(path)
    
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
