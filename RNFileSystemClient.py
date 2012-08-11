#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pyinotify
import ConfigParser
import time
from threading import Thread
from collections import deque

sys.path.append('./lib')

import RNFileSystemSDK
#import EventListener
import CustomTools
     
'''
Event Listener
'''
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

'''
Long Polling
'''
class LongPolling(Thread):
    def __init__(self, ra, dm):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
    
    def handler(self, data):
        if data['action'] == 'create':
            if data['type'] == 'dir':
                os.mkdir(self.dm.config['root'] + data['path'])
            elif data['type'] == 'file':
                self.ra.downloadFile(data['path'], self.dm.config['root'] + data['path'])
                
        elif data['action'] == 'update':
            pass
        
        elif data['action'] == 'rename':
            os.rename(data['path'], data['newpath'])
            
        elif data['action'] == 'delete':
            if data['type'] == 'dir':
                os.rmdir(self.dm.config['root'] + data['path'])
            elif data['type'] == 'file':
                os.remove(self.dm.config['root'] + data['path'])
    
    def run(self):
        while(1):
            self.ra.sendPolling(self.config['polling_time'])
            
            print "LP %s %s" % (self.ra.getStatus(), self.ra.getResult())
            
            if self.ra.getStatus() == 200:
                self.handler(self.ra.getResult())
                
            elif self.ra.getStatus() == 401:
                print 'LP ... Login'
                if self.ra.login():
                    self.dm.saveToken(self.ra.config['token'])
                else:
                    print self.ra.getStatus()
                    print self.ra.getResult()
                    print 'RC ... Exit'
                    sys.exit()
                    
            elif self.ra.getStatus() == 408:
                print 'LP ... Reconnect'
            else:
                print self.ra.getStatus()
                print self.ra.getResult()
                print 'RC ... Exit'
                sys.exit()

'''
Complete Sync
'''
class ComleteSync(Thread):
    def __init__(self, ra, ld, dm):
        Thread.__init__(self)
        
        self.ra = ra
        self.ld = ld
        self.dm = dm
    
    def run(self):
        while(1):
            time.sleep(self.config['sync_time'])
            print 'CS ...'
            self.handler()
    
    def handler(self):
        if self.ra.login():
            self.dm.saveToken(self.ra.config['token'])
        else:
            print self.ra.getStatus()
            print self.ra.getResult()
            print 'RC .. Exit'
            sys.exit()
        
        if(self.ra.getUser()):
            self.dm.user_info = self.ra.getResult()
            print "%12s: %s" % ('User', self.dm.user_info['username'])
            print "%12s: %.2f / %.2f MB" % ('Capacity', self.dm.user_info['used']/1024/1024, self.dm.user_info['capacity']/1024/1024)
            print "%12s: %.2f MB" % ('Upload Limit', self.dm.user_info['upload_limit']/1024/1024)
            print "%12s: %s" % ('Access Token', self.dm.config['token'])
            
        # Get server list
        if(self.ra.getList()):
            server_list = self.ra.getResult()
            server_list.pop('/')
            server_index = []
            for index in server_list.keys():
                server_index.append(index.encode('utf-8'))

        # Get local list
        local_list = self.ld.getLocalList()
        local_index = local_list.keys()

        # Create list
        identical_index = list(set(server_index).intersection(set(local_index)))
        download_index = list(set(server_index).difference(set(local_index)))
        upload_index = list(set(local_index).difference(set(server_list)))
        
        '''
        Do something
        '''

        download_index.sort()
        upload_index.sort()
        
        self.dm.server_list = server_list
        self.dm.local_list = local_list
        self.dm.download_index = deque(download_index)
        self.dm.upload_index = deque(upload_index)
        
class DataManage():
    def __init__(self):
        self.config_path = 'RNFileSystemClient.ini'
        if not os.path.exists(self.config_path):
            file(self.config_path, 'wb').write(file('RNFileSystemClient.sample.ini', 'rb').read())
        
        self.config_parser = ConfigParser.RawConfigParser()
        self.config_parser.read(self.config_path)
        self.config = {
            'config_path': self.config_path,
            'root': self.config_parser.get('local', 'root'),
            'host': self.config_parser.get('server', 'host'),
            'port': self.config_parser.getint('server', 'port'),
            'ssl': self.config_parser.getboolean('server', 'ssl'),
            'sync_time': self.config_parser.getint('time', 'sync'),
            'polling_time': self.config_parser.getint('time', 'polling'),
            'username': self.config_parser.get('info', 'username'),
            'password': self.config_parser.get('info', 'password'),
            'token': self.config_parser.get('info', 'token')
        }
        
        self.user_info = {}
        self.server_list = {}
        self.local_list = {}
        
        self.upload_index = []
        self.download_index = []
        
    def saveToken(self, token):
        self.config_parser.set('info', 'token', token)
        self.config_parser.write(open(self.config['config_path'], 'wb'))

class UploadHandler(Thread):
    def __init__(self, ra, dm):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
    
    def run(self):
        self.dm.is_upload = True
        if self.dm.upload_index:
            self.handler()
        self.dm.is_upload = False
    
    def handler(self):
        while self.dm.upload_index:
            index = self.dm.upload_index.popleft()
            if self.dm.local_list[index]['type'] == 'dir':
                self.ra.uploadFile(index)
            else:
                print "TX ... %s" % index
                if not self.ra.uploadFile(index, self.dm.config['root'] + index):
                    if self.ra.getStatus() == 401:
                        print 'TX ... Retry %s' % index
                        if self.ra.login():
                            self.saveToken(self.ra.config['token'])
                            if not self.ra.uploadFile(index, self.dm.config['root'] + index):
                                print 'TX ... Fail %s' % self.ra.getStatus()
                                print self.ra.getResult()
                        else:
                            print self.ra.getStatus()
                            print self.ra.getResult()
                            print 'TX ... Exit'
                            sys.exit()
                    else:
                        print '\nFail ... %s' % self.ra.getStatus()
                        print self.ra.getResult()

class DownloadHandler(Thread):
    def __init__(self, ra, dm):
        Thread.__init__(self)
        
        self.ra = ra
        self.dm = dm
        
    def run(self):
        self.dm.is_download = True
        if self.dm.download_index:
            self.handler()
        self.dm.is_download = False
    
    def handler(self):
        while self.dm.download_index:
            index = self.dm.download_index.popleft()
            if self.dm.server_list[index.decode('utf-8')]['type'] == 'dir':
                os.mkdir(self.dm.config['root'] + index)
            else:
                print "RX ... %s" % index
                if not self.ra.downloadFile(index, self.dm.config['root'] + index):
                    if self.ra.getStatus() == 401:
                        print 'RX ... Retry %s' % index
                        if self.ra.login():
                            self.dm.saveToken(self.ra.config['token'])
                            if not self.ra.downloadFile(index, self.dm.config['root'] + index):
                                print 'RX ... Fail %s' % self.ra.getStatus()
                                print self.ra.getResult()
                        else:
                            print self.ra.getStatus()
                            print self.ra.getResult()
                            print 'RX ... Exit'
                            sys.exit()
                    else:
                        print '\nFail ... %s' % self.ra.getStatus()
                        print self.ra.getResult()

if __name__ == '__main__':
    # Init Data Manage
    dm = DataManage()
    
    # Init RNFileSystem API & Local Disk
    ra = RNFileSystemSDK.API(dm.config)
    ld = CustomTools.FileHandler(dm.config['root'])

    # Init Download Handler & Upload Handler
    dh = DownloadHandler(ra, dm)
    uh = UploadHandler(ra, dm)

    # Init CS, LP, EL
    cs = ComleteSync(ra, ld, dm)
    lp = LongPolling(ra, dm)
    el = EventListener(ra, dm)
    
    # Start Complete Sync
    cs.handler()
    dh.start()
    uh.start()
    
    while(dm.is_upload or dm.is_download):
        pass
    
    # Start Thread
#    cs.start()
#    lp.start()
#    el.start()

    print '\nClient Bootstrap Success'
