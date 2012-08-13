#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
from threading import Thread
from collections import deque

sys.path.append('./Library')

import RNFileSystemSDK
import CustomTools
import ServerEvent
import FileEvent
import UDModel

class ComleteSync(Thread):
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
    
    def handler(self):
        if not self.dh.isAlive():
            self.dh = UDModel.DownloadHandler(self.lm, self.ra)
            self.dh.start()
        if not self.uh.isAlive():
            self.uh = UDModel.UploadHandler(self.lm, self.ra)
            self.uh.start()
    
    def differ(self):
        if(self.ra.getUser()):
            self.lm.user_info = self.ra.getResult()
            print "CS ... %s - %.2f / %.2f / %.2f" % (
                self.lm.user_info['username'],
                self.lm.user_info['used']/1024/1024,
                self.lm.user_info['capacity']/1024/1024,
                self.lm.user_info['upload_limit']/1024/1024
            )
            print "CS ... %s" % self.ra.token
            
        # Get server list
        if(self.ra.getList()):
            server_temp_list = self.ra.getResult()
            server_temp_list.pop('/')
            
            server_list = {}
            for index in self.ra.getResult():
                server_list[index.encode('utf-8')] = server_temp_list[index]
            
            server_index = []
            for index in server_list.keys():
                server_index.append(index)

        # Get local list
        local_list = self.lm.getLocalList()
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
        
        self.lm.server_list = server_list
        self.lm.local_list = local_list

        self.lm.download_index += deque(download_index)
        self.lm.upload_index += deque(upload_index)

if __name__ == '__main__':
    # Init Data Manage
    lm = CustomTools.LocalManage()
    
    # Init RNFileSystem API
    ra = RNFileSystemSDK.API(lm.config)
    
    # Try Login
    if not ra.login():
        print ra.getStatus()
        print ra.getResult()
        print 'RC .. Exit'
        sys.exit()
    
    # Init Download Handler & Upload Handler
    dh = UDModel.DownloadHandler(lm, ra)
    uh = UDModel.UploadHandler(lm, ra)
    
    # Init CS
    cs = ComleteSync(lm, ra, dh, uh)
    
    # Start Complete Sync
    cs.differ()
    
    dh.start()
    uh.start()
    
    dh.join()
    uh.join()
    
    time.sleep(1)
    
    # Init LP, EL
    lp = ServerEvent.LongPolling(lm, ra, dh)
    el = FileEvent.EventListener(lm, ra, uh)
    
    # Start Thread
#    cs.start()
#    lp.start()
#    el.start()
