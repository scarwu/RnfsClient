# -*- coding: utf-8 -*-

import os
import sqlite3

class Index:
    def __init__(self, path):
        path = path + '/index.sqlite3'
        
        if os.path.exists(path) == False:
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.conn.execute(
                "CREATE TABLE files (" +
                    "path TEXT NOT NULL," +
                    "type TEXT NOT NULL," +
                    "size INTEGER," +
                    "hash TEXT," +
                    "version INTEGER" +
                ")"
            )

            self.conn.commit()
        else:
            self.conn = sqlite3.connect(path, check_same_thread=False)
        
    def isExsist(self, path):
        pass
    
    # Add Index
    def add(self, data):
        if data['type'] == 'file':
            self.conn.execute(
                'INSERT INTO files (path, type, size, hash, version) VALUES ("%s", "%s", "%s", "%s", "%s")'
                % (data['path'], data['type'], data['size'], data['hash'], data['version'])
            )
            self.conn.commit()
        else:
            self.conn.execute('INSERT INTO files (path, type) VALUES ("%s", "dir")' % data['path'])
            self.conn.commit()
    
    # Delete Index
    def delete(self, path):
        self.conn.execute('DELETE FROM files WHERE path="%s"' % path)
        self.conn.commit()
    
    # Update Index
    def upadte(self, path, data):
        self.conn.execute('UPDATE files SET size="%s", hash="%s", version="%s" WHERE path="%s"' % (data['size'], data['hash'], data['version'], path))
        self.conn.commit()
    
    # Get Index Information
    def get(self, path=None):
        if path != None:
            c = self.conn.cursor()
            c.execute('SELECT * FROM files WHERE path="%s"' % path)
            row = c.fetchone()
            
            result = {}
            if row[1] == 'dir':
                result[row[0]] = {
                    'type': 'dir'
                }
            else:
                result[row[0]] = {
                    'type': 'file',
                    'size': row[2],
                    'hash': row[3],
                    'version': row[4],
                }
                    
            c.close()
            
            return result
        else:
            c = self.conn.cursor()
            
            result = {}
            for row in c.execute('SELECT * FROM files'):
                if row[1] == 'dir':
                    result[row[0]] = {
                        'type': 'dir'
                    }
                else:
                    result[row[0]] = {
                        'type': 'file',
                        'size': row[2],
                        'hash': row[3],
                        'version': row[4],
                    }
            
            c.close()
            
            return result
    
    # Clean Table
    def clean(self):
        self.conn.execute('DELETE FROM files')
        self.conn.commit()
        