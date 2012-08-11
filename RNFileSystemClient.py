#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import ConfigParser
import time
from threading import Thread
from collections import deque

sys.path.append('./lib')

import RNFileSystemSDK
import CustomTools
import ServerEvent
import FileEvent
import UDModel

'''
Data Manage
'''
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
        
        self.upload_index = deque([])
        self.download_index = deque([])
        
        self.is_download = True
        self.is_upload = True
        
    def saveToken(self, token):
        self.config_parser.set('info', 'token', token)
        self.config_parser.write(open(self.config['config_path'], 'wb'))

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
        upload_index = list(set(local_index).difference(set(server_index)))
        
        '''
        Do something
        '''

        download_index.sort()
        upload_index.sort()
        
        self.dm.server_list = server_list
        self.dm.local_list = local_list
        
        if self.dm.download_index:
            self.dm.download_index.append(deque(download_index))
        else:
            self.dm.download_index = deque(download_index)
            
        if self.dm.upload_index:
            self.dm.upload_index.append(deque(upload_index))
        else:
            self.dm.upload_index = deque(upload_index)

if __name__ == '__main__':
    # Init Data Manage
    dm = DataManage()
    
    # Init RNFileSystem API & Local Disk
    ra = RNFileSystemSDK.API(dm.config)
    ld = CustomTools.FileHandler(dm.config['root'])

    # Init Download Handler & Upload Handler
    dh = UDModel.DownloadHandler(ra, dm)
    uh = UDModel.UploadHandler(ra, dm)

    # Init CS, LP, EL
    cs = ComleteSync(ra, ld, dm)
    lp = ServerEvent.LongPolling(ra, dm)
    el = FileEvent.EventListener(ra, dm)
    
    # Start Complete Sync
    cs.handler()
    dh.start()
    uh.start()
    
    while(dm.is_upload or dm.is_download):
        time.sleep(1)
    
    # Start Thread
#    cs.start()
#    lp.start()
#    el.start()

    print '\nClient Bootstrap Success'
