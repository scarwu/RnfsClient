# -*- coding: utf-8 -*-

import os
import sqlite3

class Index:
    def __init__(self, path):
        path = path + '/index.sqlite3'
        
        if os.path.exists(path) == False:
            self.conn = sqlite3.connect(path)
            c = self.conn.cursor()
            
            # Files Table
            c.execute(
                "CREATE TABLE files (" +
                    "path TEXT NOT NULL," +
                    "type TEXT NOT NULL," +
                    "size INTEGER," +
                    "hash TEXT," +
                    "version INTEGER" +
                ")"
            )

            self.conn.commit()
            c.close()
        else:
            self.conn = sqlite3.connect(path)
        
    def isExsist(self, path):
        pass
    
    def add(self, data):
        if data['type'] == 'file':
            c = self.conn.cursor()
            c.execute(
                'INSERT INTO files (path, type, size, hash, version) VALUES ("%s", "%s", "%s", "%s", "%s")'
                % (data['path'], data['type'], data['size'], data['hash'], data['version'])
            )
            self.conn.commit()
            c.close()
        else:
            c = self.conn.cursor()
            c.execute('INSERT INTO files (path, type) VALUES ("%s", "dir")' % data['path'])
            self.conn.commit()
            c.close()
    
    def delete(self, path):
        c = self.conn.cursor()
        c.execute('DELETE FROM files WHERE path="%s"' % path)
        self.conn.commit()
        c.close()
    
    def upadte(self, path, data):
        c = self.conn.cursor()
        c.execute('UPDATE files SET size="%s", hash="%s", version="%s" WHERE path="%s"' % (data['size'], data['hash'], data['version'], path))
        self.conn.commit()
        c.close()
    
    def get(self, path=None):
        if path != None:
            c = self.conn.cursor()
            c.execute('SELECT * FROM files WHERE path="%s"' % path)
            self.conn.commit()
            c.close()
        else:
            c = self.conn.cursor()
            c.execute('SELECT * FROM files')
            self.conn.commit()
            c.close()
    
    def clean(self):
        c = self.conn.cursor()
        c.execute('DELETE FROM files')
        self.conn.commit()
        c.close()
        