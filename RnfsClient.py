#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


from collections import deque
import ConfigParser

sys.path.append('./Library')

import ServiceCaller
#import ServerEvent
#import FileEvent
import Database
import Complete
import TransferModel

if __name__ == '__main__':
    is_loop = False
    
    config_path = 'RnfsClient.ini'
    
    if not os.path.exists(config_path):
        file(config_path, 'wb').write(file('RnfsClient.default.ini', 'rb').read())
    
    config_parser = ConfigParser.RawConfigParser()
    config_parser.read(config_path)
    config = {
        'root': config_parser.get('local', 'root'),
        'target': config_parser.get('local', 'target'),
        'host': config_parser.get('server', 'host'),
        'port': config_parser.getint('server', 'port'),
        'ssl': config_parser.getboolean('server', 'ssl'),
        'sync_time': config_parser.getint('time', 'sync'),
        'username': config_parser.get('info', 'username'),
        'password': config_parser.get('info', 'password')
    }
    
    if not os.path.exists(config['root']):
        os.mkdir(config['root'])
        
    if not os.path.exists(config['target']):
        os.mkdir(config['target'])
    
    # Initialize RNFileSystem API
    api = ServiceCaller.API({
        'root': config['root'],
        'username': config['username'],
        'password': config['password'],
        'host': config['host'],
        'port': config['port'],
        'ssl': config['ssl']
    })
    
    # Try Login
    if not api.login():
        print api.getStatus()
        print api.getResult()
        print 'Exit'
        sys.exit()
        
    # Initialize DataBase
    db = Database.Index(config['root'])
    
    # Initialize Transfer Manager
    transfer = TransferModel.Manager(config['root'], api, db)
    
    # Initialize CS
    complete_sync = Complete.Sync({
        'root': config['root'],
        'sync_time': config['sync_time'],
        'target': config['target']
    }, api, transfer, db)
    
    # Start Complete Sync
    complete_sync.differ(wait=True)

    # Initialize LP, EL
#    long_polling = ServerEvent.LongPolling({}, api, transfer, db)
#    file_event = FileEvent.EventListener({}, api, transfer, db)
    
    # Start Thread
#    if is_loop:
#        complete_sync.start()
#        long_polling.start()
#        file_event.start()
