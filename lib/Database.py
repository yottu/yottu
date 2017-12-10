'''
Created on Dec 10, 2017


'''

import sqlite3
from DebugLog import DebugLog
from Config import Config

# Table: posts
# +--------------------+-------+----------+--------+
# | KEY_P = ID(Serial) | board | threadno | postno |
# +--------------------+-------+----------+--------+
# |       2349823      |   g   | 12345678 | 123456 |
# +--------------------+-------+----------+--------+

class Database(object):
    def __init__(self):
        self.dlog = DebugLog()
        self.dbfile = "./yottu.db"
        self.enabled = False
        self.on_config_change()
        if self.enabled:
            self.create_tables()
        
    
    def on_config_change(self):
        try:
            cfg = Config(debug=False)
            self.dbfile = cfg.get('database.sqlite.path')
            self.enabled = cfg.get('database.sqlite.enable')
        except Exception as e:
            self.dlog.excpt(e, msg=">>>in Database.on_config_change()", cn=self.__class__.__name__)
        
    def create_tables(self):
        ''' Create tables if they don't exist '''
        conn = sqlite3.connect(self.dbfile)  # @UndefinedVariable
        c = conn.cursor()
        try:
            c.execute('''CREATE TABLE yottu_posts (id INTEGER PRIMARY KEY, board TEXT, threadno MEDIUMINT, postno MEDIUMINT)''')
        
        # Tables already exist
        except: 
            pass
        conn.commit()
        c.close()
    
    def connect(self):
        conn = sqlite3.connect(self.dbfile)  # @UndefinedVariable
        return conn.cursor() 
        
    def insert_post(self, board, threadno, postno):
        
        # INSERT (board, threadno, postno) INTO yottu_posts
        if self.enabled:
                
                values = [board, threadno, postno,]
                conn = sqlite3.connect(self.dbfile) # @UndefinedVariable
                c = self.connect()
                c.execute('INSERT INTO yottu_posts VALUES (NULL, ?, ?, ?)', values)
                conn.commit()
                c.close()
                
                self.dlog.msg("Database: Inserted " + str(values))
        
    def get_postno_from_threadno(self, threadno):
        if self.enabled:
            param = [threadno,]
            c = self.connect() 
            c.execute('SELECT postno FROM yottu_posts WHERE threadno = ?', param)
            
            # Fetch post numbers and store into res array
            res = []
            for row in c:
                res.append(row[0])
                
            return res
                
