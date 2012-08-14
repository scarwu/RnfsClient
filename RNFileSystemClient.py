#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
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
        
        # Create index Part Cache-Local
        upload_index_cl = local_index.difference(cache_index)
        delete_index_cl = cache_index.difference(local_index)
        
        # Create index Part Cache-Server
        delete_index_cs = cache_index.difference(server_index)
        download_index_cs = server_index.difference(cache_index)
        
        # Create index Part Local-Server
        identical_index_ls = server_index.intersection(local_index)
        upload_index_ls = local_index.difference(server_index)
        download_index_ls = server_index.difference(local_index)

        # Union all index
        total_delete_index = delete_index_cl.union(delete_index_cs)
        total_update_index = upload_index_cl.union(upload_index_ls)
        total_download_index = download_index_ls.union(download_index_cs)
        
        # Final index
        local_delete_index = list(total_update_index.intersection(total_delete_index))
        server_delete_index = list(total_download_index.intersection(total_delete_index))
        
        total_update_index = list(total_update_index.difference(total_delete_index))
        total_download_index = list(total_download_index.difference(total_delete_index))
        
        local_delete_index.sort()
        server_delete_index.sort()
        total_download_index.sort()
        total_update_index.sort()
        
        for index in local_delete_index:
            print 'Delete Local File: %s' % index
            local_list.pop(index)
            if local_list[index]['type'] == 'dir':
                os.rmdir(self.dm.config['root'] + '/' + index)
            else:
                os.remove(self.dm.config['root'] + '/' + index)
        
        for index in server_delete_index:
            print 'Delete Server File: %s' % index
            server_list.pop(index)
            self.ra.deleteFile(index)
        
        self.lm.server_list = server_list
        self.lm.local_list = local_list

        self.lm.download_index += deque(total_download_index)
        self.lm.upload_index += deque(total_update_index)
        
        self.lm.saveListCache()

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
    
    # Init LP, EL
    lp = ServerEvent.LongPolling(lm, ra, dh)
    el = FileEvent.EventListener(lm, ra, uh)
    
    # Start Thread
    cs.start()
    lp.start()
    el.start()
