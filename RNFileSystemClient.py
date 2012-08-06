#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pyinotify
import ConfigParser

sys.path.append('./lib')

import RNFileSystemSDK
import EventListener
import CustomTools

class RNFileSystemClient():
    def __init__(self):
        self.config_path = 'RNFileSystemClient.ini'
        
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_path)
        
        self.local_path = self.config.get('local', 'target')
        
        # RNFS SDK
        self.RNFS = RNFileSystemSDK.API(self.config_path)
        
        # Local Disk
        self.FH = CustomTools.FileHandler(self.config_path)
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Check root directory
        if os.path.exists(self.local_path) == False:
            os.mkdir(self.local_path)
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(self.local_path, self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventListener.Handler())
    
    def completeSync(self):
        if self.RNFS.login():
            print "Token -"
            print self.RNFS.token;
            
            print "\nUser Information -"
            if(self.RNFS.getUser()):
                info = self.RNFS.getResult()
                for key in info:
                    print "%12s: %s" % (key, info[key])
                    
            print "\nServer List -"
            if(self.RNFS.getList()):
                server_full_list = self.RNFS.getResult()
                server_full_list.pop('/')

                server_list = []
                for path in server_full_list:
                    server_list.append(path)
                server_list = set(server_list)
                print server_list
            
            print "\nLocal List -"
            local_full_list = self.FH.getLocalList()
            
            local_list = []
            for path in local_full_list:
                for key in path:
                    local_list.append(key)
            local_list = set(local_list)
            print local_list
            
            print "\nUL List"
            upload_list = local_list.difference(server_list)
            print upload_list
            
            print "\nDL List"
            download_list = server_list.difference(local_list)
            print download_list
            
            print "\nFixed List"
            print server_list.intersection(local_list)
            
            print "\nStart Download"
            for index in download_list:
                if server_full_list[index]['type'] == 'dir':
                    os.mkdir(self.local_path + index)
                else:
                    print "Download file: " + index
                    self.RNFS.downloadFile(index, self.local_path + index)
            
            print "\nStart Upload"
                        
        else:
            print 'Login Failed'
            sys.exit()
    
    '''
    Run Client
    '''
    def run(self):
        self.completeSync()
#        self.notifier.loop()

if __name__ == '__main__':
    R = RNFileSystemClient()
    R.run()
    