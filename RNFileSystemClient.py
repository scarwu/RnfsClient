#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from threading import Thread
from collections import deque
import ConfigParser

sys.path.append('./Library')

import ServiceCaller
import CustomTools
import ServerEvent
import FileEvent
import Database
import UDModel

class CompleteSync(Thread):
    def __init__(self, lm, ra, dh, uh):
        Thread.__init__(self)
        
        self.lm = lm
        self.ra = ra
        self.dh = dh
        self.uh = uh
    
    def run(self):
        print "CS ... Start"
        while(1):
            time.sleep(self.lm.config['sync_time'])
            self.differ()
            self.handler()
    
    def handler(self, wait=False):
        if not self.dh.isAlive():
            self.dh = UDModel.DownloadHandler(self.lm, self.ra)
            self.dh.start()
        
        if not self.uh.isAlive():
            self.uh = UDModel.UploadHandler(self.lm, self.ra)
            self.uh.start()
            
        if wait:
            self.dh.join()
            self.uh.join()
    
    def differ(self):
        if(self.ra.getUser()):
            self.lm.user_info = self.ra.getResult()
            print "CS ... %s - %d byte / %d byte / %d byte" % (
                self.lm.user_info['username'],
                self.lm.user_info['used'],
                self.lm.user_info['capacity'],
                self.lm.user_info['upload_limit']
            )
            print "CS ... %s" % self.ra.token
        
        # Get cache list
        cache_list = {}
        for index in self.lm.cache_list:
            cache_list[index.encode('utf-8')] = self.lm.cache_list[index]
        cache_index = set(cache_list.keys())

        # Get local list
        local_list = self.lm.getLocalList()
        local_index = set(local_list.keys())
        
        # Get server list
        if(self.ra.getList()):
            server_list = {}
            for index in self.ra.getResult().keys():
                server_list[index.encode('utf-8')] = self.ra.getResult()[index]
            server_list.pop('/')
            server_index = set(server_list.keys())
        else:
            print self.ra.getResult()
            print 'CS ... Exit'
            sys.exit()
            
        # Delete Index
        local_delete_index = list(cache_index.intersection(local_index).difference(server_index))
        server_delete_index = list(cache_index.intersection(server_index).difference(local_index))
        
        # Upload / Download Index
        update_index = list(local_index.difference(cache_index.union(server_index)))
        download_index = list(server_index.difference(cache_index.union(local_index)))
        
        # Identical Index
        identical_index = list(server_index.intersection(local_index))
        
        local_delete_index.sort(reverse=True)
        server_delete_index.sort(reverse=True)
        update_index.sort()
        download_index.sort()
        
        file_list = {}
        for index in identical_index:
            file_list[index] = local_list[index]
        for index in update_index:
            file_list[index] = local_list[index]
        for index in download_index:
            file_list[index] = server_list[index]
        
        for index in local_delete_index:
            print '--- LD: %s' % index
            if os.path.isdir(self.lm.config['root'] + '/' + index):
                os.rmdir(self.lm.config['root'] + '/' + index)
            else:
                os.remove(self.lm.config['root'] + '/' + index)
        
        for index in server_delete_index:
            print '--- SD: %s' % index
            self.ra.deleteFile(index)

        self.lm.file_list = file_list
        self.lm.upload_index += deque(update_index)
        self.lm.download_index += deque(download_index)
        
if __name__ == '__main__':
    is_loop = False
    
    config_path = 'RNFileSystemClient.ini'
    
    if not os.path.exists(config_path):
        file(config_path, 'wb').write(file('RNFileSystemClient.sample.ini', 'rb').read())
    
    config_parser = ConfigParser.RawConfigParser()
    config_parser.read(config_path)
    config = {
        'root': config_parser.get('local', 'root'),
        'target': config_parser.get('local', 'target'),
        
        'host': config_parser.get('server', 'host'),
        'port': config_parser.getint('server', 'port'),
        'ssl': config_parser.getboolean('server', 'ssl'),
        
        'sync_time': config_parser.getint('time', 'sync'),
        
        'username': config_parser.get('info', 'username'),
        'password': config_parser.get('info', 'password')
    }
    
    if not os.path.exists(config['root']):
        os.mkdir(config['root'])
    
    # Initialize DataBase
    db = Database.Index(config['root'])
    
    # Initialize RNFileSystem API
    api = ServiceCaller.API({
        'root': config['root'],
        'username': config['username'],
        'password': config['password'],
        'host': config['host'],
        'port': config['port'],
        'ssl': config['ssl']
    })
    
    # Try Login
    if not api.login():
        print api.getStatus()
        print api.getResult()
        print 'Exit'
        sys.exit()
    
#    # Initialize Download Handler & Upload Handler
#    dh = UDModel.DownloadHandler({}, api)
#    uh = UDModel.UploadHandler({}, api)
#    
#    # Initialize CS
#    complete_sync = CompleteSync({}, api, dh, uh)
#    
#    # Start Complete Sync
#    complete_sync.differ()
#    complete_sync.handler(wait=True)
#    
#    lm.file_list = lm.getLocalList()
#    lm.saveListCache()
#    
#    # Initialize LP, EL
#    long_polling = ServerEvent.LongPolling({}, api, dh)
#    file_event = FileEvent.EventListener({}, api, uh)
#    
#    # Start Thread
#    if is_loop:
#        complete_sync.start()
#        long_polling.start()
#        file_event.start()
