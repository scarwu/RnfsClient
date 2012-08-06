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
        
        # RNFS SDK
        self.RNFS = RNFileSystemSDK.API(self.config_path)
        
        # Local Disk
        self.local = CustomTools.FileHandler(self.config_path)
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Check root directory
        if os.path.exists(self.config.get('local', 'target')) == False:
            os.mkdir(self.config.get('local', 'target'))
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(self.config.get('local', 'target'), self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventListener.Handler())
    
    '''
    Run Client
    '''
    def run(self):
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
                server_list = []
                list = self.RNFS.getResult()
                list.pop('/')
                for path in list:
                    server_list.append(path)
                server_list = set(server_list)
                print server_list
            
            print "\nLocal List -"
            local_list = []
            for path in self.local.getLocalList():
                for key in path:
                    local_list.append(key)
            local_list = set(local_list)
            print local_list
            
            print "\nUL List"
            print local_list.difference(server_list)
            
            print "\nDL List"
            print server_list.difference(local_list)
            
            print "\nFixed List"
            print server_list.intersection(local_list)
                        
        else:
            print 'Login Failed'
            sys.exit()
        
#        self.notifier.loop()

if __name__ == '__main__':
    R = RNFileSystemClient()
    R.run()
    