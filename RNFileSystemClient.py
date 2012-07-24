#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import httplib
import pyinotify
import json
import ConfigParser

class RNFileSystemSDK():
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('RNFileSystemClient.cfg')
        
        self.username = self.config.get('local', 'username')
        self.password = self.config.get('local', 'password')
        self.token = self.config.get('local', 'token')
        self.server = self.config.get('server', 'host')
        self.port = self.config.getint('server', 'port')
        self.ssl = self.config.getboolean('server', 'ssl')
    
    def __send(self, config):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
        
        # URL
        url = "/" + config['api']
        
        if config['path'] != None:
            url += "/" + config['path']
        
        # Parameter
        if str.lower(config['method']) == 'get':
            params = None
            if config['params'] != None:
                url += "?" + config['params']
        else:
            params = config['params']
        
        # Send Request
        conn.request(str.upper(config['method']), url, params, config['headers'])
        response = conn.getresponse()
        result = {
            "status": response.status,
            "reason": response.reason,
            "data": response.read()
        }
        conn.close()
        return result
    
    '''
    JSON Encoder
    '''
    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    def __decode(self, data):
        if data == '':
            return None
        else:
            return json.loads(data)

    def getResult(self):
        return self.result
    
    '''
    Authentication API
    '''
    def __updateToken(self):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('PUT', '/auth', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()

        if response.status == 200:
            return True
        else:
            return False
    
    def login(self):
        if self.__updateToken():
            return True
            
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('POST', '/auth', self.__encode({
            'username': self.username,
            'password': self.password
        }))
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        if response.status == 200:
            self.token = self.result['token']
            
            # Write-back
            self.config.set('local', 'token', self.token)
            self.config.write(open('RNFileSystemClient.cfg', 'wb'))
            return True
        else:
            return False
    
    def logout(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('DELETE', '/auth', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        if response.status == 200:
            # Write-back
            self.config.set('local', 'token', '')
            self.config.write(open('RNFileSystemClient.cfg', 'wb'))
            return True
        else:
            return False
    
    '''
    User API
    '''
    def getUser(self):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('GET', '/user/'+self.username, None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        return response.status == 200
    
    '''
    File API
    '''
    def getList(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)

        conn.request('GET', '/file', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        return response.status == 200

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
class RNFileSystemClient():
    def __init__(self):
        self.RNFS = RNFileSystemSDK()
        
#        # Inotify event mask
#        self.event_mask = 0
#        self.event_mask |= pyinotify.IN_DELETE
#        self.event_mask |= pyinotify.IN_CREATE
#        self.event_mask |= pyinotify.IN_MODIFY
#        self.event_mask |= pyinotify.IN_MOVED_TO
#        self.event_mask |= pyinotify.IN_MOVED_FROM
#        
#        # Check root directory
#        if os.path.exists(config.get('local', 'dir')) == False:
#            os.mkdir(config.get('local', 'dir'))
#        
#        # Event Listener
#        wm = pyinotify.WatchManager()
#        wm.add_watch(config.get('local', 'dir'), self.event_mask, rec=True, auto_add=True)
#        self.notifier = pyinotify.Notifier(wm, EventHandler())
    
    '''
    Run Client
    '''
    def run(self):
        if self.RNFS.login():
            print self.RNFS.token;
            if(self.RNFS.getList()):
                print json.dumps(self.RNFS.getResult())
            if(self.RNFS.getUser()):
                print json.dumps(self.RNFS.getResult())
        else:
            print 'Login Failed'
            sys.exit()
        
#        self.notifier.loop()

if __name__ == '__main__':
    R = RNFileSystemClient()
    R.run()
    