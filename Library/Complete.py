# -*- coding: utf-8 -*-
from threading import Thread
import time
import sys
import os

import CustomTools

class Sync(Thread):
    def __init__(self, config, api, transfer, db):
        Thread.__init__(self)
        
        self.sync_time = config['sync_time']
        self.root = config['root']
        self.target = config['target']
        
        self.api = api
        self.transfer = transfer
        self.db = db
        
        self.tools = CustomTools.LocalManage(self.target);
    
    def run(self):
        print "CS ... Start"
        while(1):
            time.sleep(self.sync_time)
            self.differ()
            self.handler()
    
    def differ(self, wait=False):
        if(self.api.getUser()):
            user_info = self.api.getResult()
            print "User  %s - %d byte / %d byte / %d byte" % (
                user_info['username'],
                user_info['used'],
                user_info['capacity'],
                user_info['upload_limit']
            )
            print "Token %s" % self.api.token
        
        # Get cache list
        cache_list = self.db.get()
        cache_index = set(cache_list.keys())

        # Get local list
        local_list = self.tools.getLocalList()
        local_index = set(local_list.keys())
        
        # Get server list
        if(self.api.getList()):
            server_list = {}
            for index in self.api.getResult().keys():
                server_list[index.encode('utf-8')] = self.api.getResult()[index]
            server_list.pop('/')
            server_index = set(server_list.keys())
        else:
            print self.api.getResult()
            print 'CS ... Exit'
            sys.exit()
        
        print cache_list
        print local_list
        print server_list
        
        # Delete Index
        local_delete_index = list(cache_index.intersection(local_index).difference(server_index))
        server_delete_index = list(cache_index.intersection(server_index).difference(local_index))
        
        # Upload / Download Index
        update_index = list(local_index.difference(cache_index.union(server_index)))
        download_index = list(server_index.difference(cache_index.union(local_index)))
        
        # Identical Index
#        identical_index = list(server_index.intersection(local_index))
        
        local_delete_index.sort(reverse=True)
        server_delete_index.sort(reverse=True)
        update_index.sort()
        download_index.sort()
        
#        file_list = {}
#        for index in identical_index:
#            file_list[index] = local_list[index]
#        for index in update_index:
#            file_list[index] = local_list[index]
#        for index in download_index:
#            file_list[index] = server_list[index]
        
        for index in local_delete_index:
            print '--- LD: %s' % index
            if os.path.isdir(self.target + '/' + index):
                os.rmdir(self.target + '/' + index)
            else:
                os.remove(self.target + '/' + index)
        
        for index in server_delete_index:
            print '--- SD: %s' % index
            self.api.deleteFile(index)

#        self.transfer.upload();
#        self.transfer.download();
#        self.transfer.update();

#        if wait:
#            self.transfer.wait()
        