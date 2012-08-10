#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pyinotify
import ConfigParser

import time
from threading import Thread

sys.path.append('./lib')

import RNFileSystemSDK
#import EventListener
import CustomTools
     
'''
Event Listener
'''
class EventListener(Thread):
    def __init__(self, root, rnfs_api, local_info):
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
        wm.add_watch(root, self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler(rnfs_api, local_info))
    
    def run(self):
        # Start Loop
        self.notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, rnfs_api, local_info):
        pyinotify.ProcessEvent.__init__(self)
        
        self.rnfs_api = rnfs_api
        self.local_info = local_info
    
    def process_IN_DELETE(self, event):
        print "(X) DELETE %s" % event.pathname
    def process_IN_CREATE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CREATE %s" % event.pathname
        else:
            print "(F) CREATE %s" % event.pathname
    def process_IN_MODIFY(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MODIFY %s" % event.pathname
        else:
            print "(F) MODIFY %s" % event.pathname
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

'''
Long Polling
'''
class LongPolling(Thread):
    def __init__(self, time_interval, root, rnfs_api, local_info):
        Thread.__init__(self)
        self.time_interval = time_interval
        self.root = root
        self.rnfs_api = rnfs_api
        self.local_info = local_info
    
    def run(self):
        while(1):
            self.rnfs_api.sendPolling(self.time_interval)
            if self.rnfs_api.getStatus() == 401:
                if self.rnfs_api.login():
                    self.saveToken(self.rnfs_api.token)
                else:
                    sys.exit()
            elif self.rnfs_api.getStatus() == 200:
                print self.rnfs_api.getResult()
            elif self.rnfs_api.getResult() == 408:
                pass
            else:
                sys.exit()

'''
Complete Sync
'''
class ComleteSync(Thread):
    def __init__(self, time_interval, root, rnfs_api, local_info):
        Thread.__init__(self)
        self.time_interval = time_interval
    
    def run(self):
        time.sleep(self.time_interval)

class RNFileSystemClient():
    def __init__(self):
        self.config_path = 'RNFileSystemClient.ini'
        self.config_parser = ConfigParser.RawConfigParser()
        self.config_parser.read(self.config_path)
        self.config = {
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
        
        # RNFileSystem API
        self.rnfs_api = RNFileSystemSDK.API(self.config)
        
        # Local Disk
        self.local_info = CustomTools.FileHandler(self.config['root'])

        # Check root directory
        if os.path.exists(self.config['root']) == False:
            os.mkdir(self.config['root'])
    
    def saveToken(self, token):
        self.config_parser.set('info', 'token', token)
        self.config_parser.write(open(self.config_path, 'wb'))
    
    def completeSync(self):
        if self.rnfs_api.login():
            self.saveToken(self.rnfs_api.token)
            print "%s\n" % self.rnfs_api.token
            
            if(self.rnfs_api.getUser()):
                info = self.rnfs_api.getResult()
                for key in info:
                    print "%12s: %s" % (key, info[key])
            
            # Get server list
            if(self.rnfs_api.getList()):
                server_full_list = self.rnfs_api.getResult()
                server_full_list.pop('/')
                server_list = []
                for index in server_full_list.keys():
                    server_list.append(index.encode('utf-8'))
                server_list.sort()
            
            # Get local list
            local_full_list = self.local_info.getLocalList()
            local_list = local_full_list.keys()
            local_list.sort()
            
            # Create download list
            download_list = list(set(server_list).difference(set(local_list)))
            download_list.sort()

            # Create upload list
            upload_list = list(set(local_list).difference(set(server_list)))
            upload_list.sort()
            
            # Create identical list
            identical_list = list(set(server_list).intersection(set(local_list)))
            identical_list.sort()
            
            download_file_count = len(download_list)
            upload_file_count = len(upload_list)

            rows, columns = os.popen('stty size', 'r').read().split()

            if download_file_count > 0:
                print ''
                count = 0
                for index in download_list:
                    count += 1
                    if server_full_list[index.decode('utf-8')]['type'] == 'dir':
                        os.mkdir(self.config['root'] + index)
                    else:
                        out = "DL: %6d / %6d - %d bytes" % (count, download_file_count, 0)
                        line = "\r%-" + columns + "s"
                        sys.stdout.write(line % out)
                        sys.stdout.flush()
                        if not self.rnfs_api.downloadFile(index, self.config['root'] + index):
                            if self.rnfs_api.getStatus() == 401:
                                print '\nRetry upload %s' % index
                                if self.rnfs_api.login():
                                    self.saveToken(self.rnfs_api.token)
                                    if not self.rnfs_api.downloadFile(index, self.config['root'] + index):
                                        print '\nFail ... %s' % self.rnfs_api.getStatus()
                                        print self.rnfs_api.getResult()
                                else:
                                    sys.exit()
                            else:
                                print '\nFail ... %s' % self.rnfs_api.getStatus()
                                print self.rnfs_api.getResult()
                print ''
            
            if upload_file_count > 0:
                count = 0
                for index in upload_list:
                    count += 1
                    if local_full_list[index]['type'] == 'dir':
                        self.rnfs_api.uploadFile(index)
                    else:
                        out = "UL: %6d / %6d - %d bytes" % (count, upload_file_count, local_full_list[index]['size'])
                        line = "\r%-" + columns + "s"
                        sys.stdout.write(line % out)
                        sys.stdout.flush()
                        if not self.rnfs_api.uploadFile(index, self.config['root'] + index):
                            if self.rnfs_api.getStatus() == 401:
                                print '\nRetry upload %s' % index
                                if self.rnfs_api.login():
                                    self.saveToken(self.rnfs_api.token)
                                    if not self.rnfs_api.uploadFile(index, self.config['root'] + index):
                                        print '\nFail ... %s' % self.rnfs_api.getStatus()
                                        print self.rnfs_api.getResult()
                                else:
                                    sys.exit()
                            else:
                                print '\nFail ... %s' % self.rnfs_api.getStatus()
                                print self.rnfs_api.getResult()
                print ''
                        
        else:
            print 'Login Failed'
            sys.exit()
    
    '''
    Run Client
    '''
    def run(self):
        print 'Initialize'
        self.completeSync()
        
        print '\nStart Threads'
        print '1. EL',
        EventListener(self.config['root'], self.rnfs_api, self.local_info).start()
        print '... OK'
        
        print '2. LP',
        LongPolling(self.config['polling_time'], self.config['root'], self.rnfs_api, self.local_info).start()
        print '... OK'
        
        print '3. CS',
        ComleteSync(self.config['sync_time'], self.config['root'], self.rnfs_api, self.local_info).start()
        print '... OK'
        
        print '\nClient Bootstrap Success'

if __name__ == '__main__':
    R = RNFileSystemClient()
    R.run()
    