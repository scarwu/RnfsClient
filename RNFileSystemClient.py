#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import httplib
import urllib
import pyinotify
import json
import ConfigParser

'''
File system event handler
'''
class EventHandler(pyinotify.ProcessEvent):
    # Delete
    def process_IN_DELETE(self, event):
        print "(X) DELETE %s" % event.pathname
    # Create
    def process_IN_CREATE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CREATE %s" % event.pathname
        else:
            print "(F) CREATE %s" % event.pathname
    # Modify
    def process_IN_MODIFY(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MODIFY %s" % event.pathname
        else:
            print "(F) MODIFY %s" % event.pathname
    # Colse Write
    def process_IN_CLOSE_WRITE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CWRITE %s" % event.pathname
        else:
            print "(F) CWRITE %s" % event.pathname
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
Reborn Server Client
'''
class RebornClient():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read('reborn.cfg')
        
        self.username = config.get('local', 'user')
        self.password = config.get('local', 'pass')
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Check root directory
        if os.path.exists(config.get('local', 'dir')) == False:
            os.mkdir(config.get('local', 'dir'))
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(config.get('local', 'dir'), self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler())
        
        # Service Caller
        self.sc = ServiceCaller(config.get('server', 'host'), config.getint('server', 'port'), config.getboolean('server', 'ssl'))
    
    '''
    Json Encoder
    '''
    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    '''
    Login Reborn
    '''
    def __login(self):
        result = self.sc.send({
            'method': 'post',
            'api': 'auth',
            'path': None,
            'params': self.__encode({
                "username": self.username,
                "password": self.password
            }),
            'headers': {}
        })
        
        if result['status'] != 200:
            return False
        else:
            data = json.loads(result['data'])
            self.token = data['token']
            return True
    
    '''
    Compare files
    '''
    def __compare(self):
        result = self.sc.send({
            'method': 'put',
            'api': 'auth',
            'path': None,
            'params': None,
            'headers': {'Reborn-Token': self.token}
        })
        if result['status'] == 200:
            print 'OK'
        else:
            print result['data']
            
        result = self.sc.send({
            'method': 'get',
            'api': 'user',
            'path': 'cixty',
            'params': None,
            'headers': {'Reborn-Token': self.token}
        })
        print result['data']
    
    '''
    Sync files
    '''
    def __sync(self):
        pass
    
    '''
    Run Client
    '''
    def run(self):
        if self.__login() == False:
            print 'Login Failed'
            sys.exit()
        else:
            print 'Login Success'
        
        self.__compare()
        self.__sync()
        
        # self.notifier.loop()

if __name__ == '__main__':
    R = RebornClient()
    R.run()
    