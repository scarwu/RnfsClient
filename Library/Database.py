# -*- coding: utf-8 -*-
'''
Database

@package     RESTful Network File System
@author      ScarWu
@copyright   Copyright (c) 2012-2013, ScarWu (http://scar.simcz.tw/)
@license     https://github.com/scarwu/RnfsClient/blob/master/LICENSE
@link        https://github.com/scarwu/RnfsClient
'''

import os
import re
import sqlite3

class Index:
    def __init__(self, path):
        if os.path.exists(path) == False:
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.conn.execute(
                "CREATE TABLE files (" +
                "path TEXT NOT NULL," +
                "type TEXT NOT NULL" +
                ")"
            )
            self.conn.commit()
        else:
            self.conn = sqlite3.connect(path, check_same_thread=False)
            
        self.conn.create_function("REGEXP", 2, self.regexp)
     
    def regexp(self, expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None
        
    def isExists(self, path):
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM files WHERE path="%s"' % path)
        try:
            count = c.fetchone()[0]
        except:
            count = 0
        c.close()
        return count > 0
    
    def isDir(self, path):
        if not self.isExists(path):
            return None
        
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM files WHERE path="%s" AND type="dir"' % path)
        count = c.fetchone()[0]
        c.close()
        return count > 0
    
    def isFile(self, path):
        if not self.isExists(path):
            return None
        
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM files WHERE path="%s" AND type="file"' % path)
        count = c.fetchone()[0]
        c.close()
        return count > 0
    
    # Get Path Type
    def type(self, path):
        if not self.isExists(path):
            return None
        
        c = self.conn.cursor()
        c.execute('SELECT type FROM files WHERE path="%s"' % path)
        result = c.fetchone()[0]
        c.close()
        return result
    
    # Create Full Path
    def createFullDirPath(self, path, file_type):
        segments = path.split('/')
        segments.remove('')
        
        if 'file' == file_type:
            segments.pop()

        full_path = ''
        for segment in segments:
            full_path += '/' + segment
            if not self.isExists(full_path) and full_path != '/':
                self.conn.execute('INSERT INTO files (path, type) VALUES ("%s", "%s")' % (full_path, 'dir'));
                self.conn.commit()
            elif 'file' == self.type(full_path):
                return False
        
        return True
    
    # Move Files
    def move(self, path, new_path):
        if not self.isExists(path) or self.isExists(new_path):
            return False
        
        self.conn.execute('UPDATE files SET path="%s" WHERE path="%s"' % (new_path, path))
        self.conn.commit()
        
        self.createFullDirPath(new_path, self.type(path))

        if 'dir' == self.type(new_path):
            c = self.conn.cursor()
            c.execute('SELECT path FROM files WHERE path REGEXP "^\/%s\/"' % path.strip('/').replace('/', '\/'))
            
            regex_path = '^\/%s\/(.*)' % path.strip('/').replace('/', '\/')
            for row in c.fetchall():
                p = re.compile(regex_path)
                m = p.match(row[0])
                if m:
                    self.conn.execute('UPDATE files SET path="%s/%s" WHERE path="%s"' % (new_path, m.group(1), row[0]))
                    self.conn.commit()
            
            c.close()
    
    # Add Index
    def add(self, data):
        if self.isExists(data['path']):
            return False
        
        self.createFullDirPath(data['path'], data['type'])
        
        if data['type'] == 'file':
            self.conn.execute('INSERT INTO files (path, type) VALUES ("%s", "%s")' % (data['path'], data['type']))
            self.conn.commit()
    
    # Delete Index
    def delete(self, path):
        self.conn.execute('DELETE FROM files WHERE path="%s"' % path)
        self.conn.commit()
    
    # Get Index Information
    def get(self, path=None):
        if path != None:
            c = self.conn.cursor()
            c.execute('SELECT * FROM files WHERE path="%s"' % path)
            row = c.fetchone()
            result = {}
            result[row[0]] = {'type': row[1]}
                
            c.close()
            return result
        else:
            c = self.conn.cursor()
            result = {}
            for row in c.execute('SELECT * FROM files'):
                result[row[0]] = {'type': row[1]}
                    
            c.close()
            return result
    
    # Clean Table
    def clean(self):
        self.conn.execute('DELETE FROM files')
        self.conn.commit()
        