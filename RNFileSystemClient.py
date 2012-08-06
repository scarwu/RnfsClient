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
            
            print "\n------------------------------"
            
            print "\nServer List -"
            if(self.RNFS.getList()):
                server_full_list = self.RNFS.getResult()
                server_full_list.pop('/')
                
                server_list = server_full_list.keys()
                server_list.sort()
                print server_list
            
            print "\nLocal List -"
            local_full_list = self.FH.getLocalList()

            local_list = local_full_list.keys()
            local_list.sort()
            print local_list
            
            print "\n------------------------------"
            
            print "\nDL List -"
            download_list = list(set(server_list).difference(set(local_list)))
            download_list.sort()
            print download_list
            
            print "\nUL List -"
            upload_list = list(set(local_list).difference(set(server_list)))
            upload_list.sort()
            print upload_list

            print "\nIdentical List -"
            identical_list = list(set(server_list).intersection(set(local_list)))
            identical_list.sort()
            print identical_list
            
            print "\n------------------------------"
            
            print "\nStart Download -"
            for index in download_list:
                if server_full_list[index]['type'] == 'dir':
                    os.mkdir(self.local_path + index)
                else:
                    print "Download file: " + index
                    if self.RNFS.downloadFile(index, self.local_path + index):
                        print '...Success'
                    else:
                        print '...Fail'
            
            print "\nStart Upload -"
            for index in upload_list:
                if local_full_list[index]['type'] == 'dir':
                    self.RNFS.uploadFile(index)
                else:
                    print "Upload file: " + index
                    if self.RNFS.uploadFile(index, self.local_path + index):
                        print '...Success'
                    else:
                        print '...Fail'
                        
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
    