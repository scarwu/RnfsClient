#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append('../Library')

import RNFileSystemSDK
import CustomTools

if __name__ == "__main__":
    lm = CustomTools.LocalManage()
    
    # Initialize RNFileSystem API
    ra = RNFileSystemSDK.API(lm.config)
    
    if not ra.login():
        print ra.getStatus()
        print ra.getResult()
        print 'RC .. Exit'
        sys.exit()
    
    print ra.token
    
    ra.sendPolling(lm.config['polling_time'])
    
    print ra.getStatus()
    print ra.getResult()
