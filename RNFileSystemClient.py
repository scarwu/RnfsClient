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
            print "\n%s\n" % self.RNFS.token
            
            if(self.RNFS.getUser()):
                info = self.RNFS.getResult()
                for key in info:
                    print "%12s: %s" % (key, info[key])
            
            print "\nGet File List ..."
            # Get server list
            if(self.RNFS.getList()):
                server_full_list = self.RNFS.getResult()
                server_full_list.pop('/')
                
                server_list = []
                for index in server_full_list.keys():
                    server_list.append(index.encode('utf-8'))
                server_list.sort()
                
            # Get local list
            local_full_list = self.FH.getLocalList()

            local_list = local_full_list.keys()
            local_list.sort()
            
            print "Calculate Differ List ..."
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
                print "\nStart Download -"
                count = 0
                for index in download_list:
                    count += 1
                    if server_full_list[index.decode('utf-8')]['type'] == 'dir':
                        os.mkdir(self.local_path + index)
                    else:
                        sys.stdout.write("\r%6d / %6d" % (count, download_file_count))
                        sys.stdout.flush()
                        if not self.RNFS.downloadFile(index, self.local_path + index):
                            print '\n%s ... Fail' % index
                print ''
            
            if upload_file_count > 0:
                print "\nStart Upload -"
                count = 0
                for index in upload_list:
                    count += 1
                    if local_full_list[index]['type'] == 'dir':
                        self.RNFS.uploadFile(index)
                    else:
                        out = "%6d / %6d - %d bytes" % (count, upload_file_count, local_full_list[index]['size'])
                        line = "\r%-" + columns + "s"
                        sys.stdout.write(line % out)
                        sys.stdout.flush()
                        if not self.RNFS.uploadFile(index, self.local_path + index):
                            print '\n%s ... Fail' % index
                print ''
            
            print '\nInitialize Finish'
                        
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
    