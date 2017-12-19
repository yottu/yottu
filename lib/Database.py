'''
Created on Dec 10, 2017


'''

import sqlite3

# Table: posts
# +--------------------+-------+----------+--------+
# | KEY_P = ID(Serial) | board | threadno | postno |
# +--------------------+-------+----------+--------+
# |       2349823      |   g   | 12345678 | 123456 |
# +--------------------+-------+----------+--------+

class Database(object):
    def __init__(self, wl):
        self.wl = wl
        
        self.dlog = wl.dlog
        self.cfg = wl.cfg
        
        self.dbfile = None
        self.enabled = False
        
        self.on_config_change()
        
    
    def on_config_change(self, *args, **kwargs):
        try:
            
            self.dbfile = self.cfg.get('database.sqlite.path')
            self.enabled = self.cfg.get('database.sqlite.enable')
            
            if self.enabled:
                self.create_tables()
                
        except Exception as e:
            self.dlog.excpt(e, msg=">>>in Database.on_config_change()", cn=self.__class__.__name__)
        
    def create_tables(self):
        ''' Create tables if they don't exist '''
        
        try:
            if not self.enabled:
                return
            
            conn = sqlite3.connect(self.dbfile)  # @UndefinedVariable
            c = conn.cursor()
            
            # Try creating tables, do nothing if they already exist
            try:
                c.execute('''CREATE TABLE yottu_posts (id INTEGER PRIMARY KEY, board TEXT, threadno MEDIUMINT, postno MEDIUMINT, active BOOLEAN)''')
            except: pass
            
            conn.commit()
            c.close()
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Database.create_tables()", cn=self.__class__.__name__)
            raise

        
    def insert_post(self, board, threadno, postno, active=1):
        
        try:
            # INSERT (board, threadno, postno) INTO yottu_posts
            if not self.enabled:
                self.dlog.msg("Database disabled: Not inserting values.", 4)
                return
                    
            values = [board, threadno, postno, active,]
            conn = sqlite3.connect(self.dbfile) # @UndefinedVariable
            c = conn.cursor()
            
            # TODO check if postno already exists 
                            
            c.execute('INSERT INTO yottu_posts VALUES (NULL, ?, ?, ?, ?)', values)
            conn.commit()
            
            if c.rowcount:
                self.dlog.msg("Database: Inserted " + str(values))
            else:
                self.dlog.msg("Failure inserting values into DB: " + str(values))
                
            c.close()
        
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Database.insert_post()", cn=self.__class__.__name__)
                
    def delete_post(self, board, postno):
        try:
            
            if not self.enabled:
                self.dlog.msg("Database disabled: Not deleting values.", 4)
                return
            
            values = [board, postno,]
            conn = sqlite3.connect(self.dbfile) # @UndefinedVariable
            c = conn.cursor()
            
            # TODO check if postno already exists 
                            
            c.execute('DELETE FROM yottu_posts WHERE board = ? AND postno = ?', values)
            conn.commit()
            
            if c.rowcount:
                self.dlog.msg("Database: Inserted " + str(values))
            else:
                self.dlog.msg("Failure inserting values into DB: " + str(values))
            
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Database.delete_post()", cn=self.__class__.__name__)
        
    def get_postno_from_threadno(self, threadno):
        # FIXME this also needs to check the board
        if not self.enabled:
            return []
    
        param = [threadno,]
        conn = sqlite3.connect(self.dbfile)  # @UndefinedVariable
        c = conn.cursor()
        c.execute('SELECT postno FROM yottu_posts WHERE threadno = ?', param)
        
        # Fetch post numbers and store into res array
        res = []
        for row in c:
            res.append(row[0])
            
        return res


    
    def get_active(self):
        ''' Return array containing tuples of all active user posts '''
        try:
            if not self.enabled:
                return
            
            conn = sqlite3.connect(self.dbfile) # @UndefinedVariable
            c = conn.cursor()
            c.execute('''SELECT board, postno, threadno FROM yottu_posts WHERE active = 1''')
            
            # Structure:  
            #  {board: {'404': False, 'threadop': {'userposts': {userpost}, 'active': True}}})
            
            rows = c.fetchall()
            return rows
                
                
                
            
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Database.get_active()", cn=self.__class__.__name__)
        
    
    
                
