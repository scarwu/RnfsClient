# -*- coding: utf-8 -*-

import os
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

class EventBuffer(Thread):
    def __init__(self, target, api ,transfer, db):
        Thread.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
        
        self.event_buffer = None
    
    def add(self, action, event=None):
        if action == 'moved_from':
            self.event_buffer = event
            
        elif action == 'moved_to':
            self.event_buffer = None
            self.movedTo(event)
        else:
            event = self.event_buffer
            self.event_buffer = None
            self.movedFrom(event)
    
    def movedTo(self, event):
        path = event.pathname[len(self.target):]
        try:
            src_path = event.src_pathname[len(self.target):]
            print "FileEvent (X) Rename %s -> %s" % (src_path, path)
            self.db.update()
            self.api.update()
        except:
            if not self.db.isExists(path):
                if event.dir:
                    print "FileEvent (D) Create (Moved to) %s" % path
                    
                    # Server Create dir
                    self.transfer.upload([{
                        'path': path,
                        'type': 'dir'
                    }])
                else:
                    print "FileEvent (F) Create (Moved to) %s" % path
                    
                    # Upload File
                    self.transfer.upload([{
                        'path': path,
                        'type': 'file',
                        'size': os.path.getsize(event.pathname),
                        'hash': self.md5Checksum(event.pathname),
                        'time': int(os.path.getctime(event.pathname)),
                        'version': 0
                    }])
    
    def movedFrom(self, event):
        path = event.pathname[len(self.target):]
        if self.db.isExists(path):
            print "FileEvent (x) Delete (Moved from) %s" % path
            
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
    
    def run(self):
        time.sleep(1)
        self.add('x')

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, target, api ,transfer, db):
        pyinotify.ProcessEvent.__init__(self)
        
        self.target = target
        self.api = api
        self.transfer = transfer
        self.db = db
        
        self.buffer = EventBuffer(target, api ,transfer, db)
    
    # Delete File
    def process_IN_DELETE(self, event):
        self.buffer('x')
        
        path = event.pathname[len(self.target):]
        
        if self.db.isExists(path):
            print "FileEvent (X) Delete %s" % path
            
            # Server Delete
            self.api.deleteFile(path)
            
            # DB Delete
            self.db.delete(path)
    
    # Create File
    def process_IN_CREATE(self, event):
        self.buffer('x')
        
        path = event.pathname[len(self.target):]
        
        if not self.db.isExists(path):
            if event.dir:
                print "FileEvent (D) Create %s" % path
                
                # Server Create dir
                self.transfer.upload([{
                    'path': path,
                    'type': 'dir'
                }])
            else:
                print "FileEvent (F) Create %s" % path
                
                # Upload File
                self.transfer.upload([{
                    'path': path,
                    'type': 'file',
                    'size': os.path.getsize(event.pathname),
                    'hash': self.md5Checksum(event.pathname),
                    'time': int(os.path.getctime(event.pathname)),
                    'version': 0
                }])
    
    # File Modify
    def process_IN_MODIFY(self, event):
        self.buffer('x')
        
        path = event.pathname[len(self.target):]
        
        if not event.dir:
            print "FileEvent (F) Modify %s" % event.pathname
            self.transfer.update([{
                'path': path,
                'type': 'file',
                'size': os.path.getsize(event.pathname),
                'hash': self.md5Checksum(event.pathname),
                'time': int(os.path.getctime(event.pathname)),
                'version': self.db.get(path)[path]['version']+1,
                'to': 'server'
            }])
    
    # File Moved from
    def process_IN_MOVED_FROM(self, event):
        self.buffer('move_from', event)
    
    # File Moved to
    def process_IN_MOVED_TO(self, event):
        self.buffer('move_to', event)
        
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
