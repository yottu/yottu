'''
Created on Dec 11, 2017

@author: yottudev@gmail.com
'''

from Autism import Autism
from Notifier import Notifier

import re
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')


class ThreadWatcher(object):
    def __init__(self, wl):
        
        self.wl = wl
        self.dlog = self.wl.dlog
        self.db = self.wl.db
        self.cfg = self.wl.cfg
        
        # Dict of containing board, OP of thread and the posts made in that thread to watch for replies
        # Structure: {'board': {threadop: {'userposts': {123, 124}, 'active': True}} } to watch 
        self.threadops = {}
        self.seen = []
        self.load()
        
        self.update_interval_max = 1800
        self.update_interval_min = 30
        
        self.cfg.register(self)
        
    def on_config_change(self, *args, **kwargs):
        self.load()
        
    def insert(self, board, userpost, threadop=None):
        ''' Add new thread to watch '''
        
        if not self.cfg.get('threadwatcher.enable'):
            return False
        
        try:
            # userpost is new thread
            if not threadop:
                threadop = userpost
            #    self.threadops.update({board: {'404': False, 'threadop': {'userposts': {userpost}, 'active': True}}})
                
            try:
                if not self.threadops.has_key(board):
                    self.threadops.update({board: {threadop: {'userposts': {userpost}, 'active': True}}})
                    
                elif not self.threadops[board].has_key(threadop):
                    self.threadops[board].update({threadop: {'userposts': {userpost}, 'active': True}})
                    
                else:
                    self.threadops[board][threadop]['userposts'].add(userpost)
                    
                self.dlog.msg("ThreadWatcher: Added >>>/" + str(board) + "/" + str(userpost), 3)

            except KeyError:
                self.threadops.update({board: {threadop: {'userposts': {userpost}, 'active': True}}})

        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.insert()", cn=self.__class__.__name__)
    
    def remove(self, board, userpost, threadop=None):
        ''' Remove a post from the watch list '''
        
        if not self.cfg.get('threadwatcher.enable'):
            return False
        
        # userpost is op
        if not threadop:
            threadop = userpost
        
        try:
            self.threadops[board][threadop]['userposts'].remove(userpost)
            
            # remove stub
            if len(self.threadops[board][threadop]['userposts']) is 0:
                self.threadops[board].pop(threadop)
                
        except KeyError as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.remove()", cn=self.__class__.__name__)
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.remove()", cn=self.__class__.__name__)
            raise
        
    def remove_inactive_threads(self):
        ''' Remove all marked as inactive threads from the watch list '''
        
        if not self.cfg.get('threadwatcher.enable'):
            return False
        
        try:
            for board, ops in self.threadops.items():
                for thread, values in ops.items():
                
                    if not values['active']:
                        del self.threadops[board][thread]
                    
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.remove_inactive_threads()", cn=self.__class__.__name__)
    
    def load(self):
        ''' Load user made posts from database and inserts it into self.threadops '''
        
        if not self.cfg.get('threadwatcher.enable'):
            return False
        
        try:
            for db_board_userpost_threadop in self.db.get_active():
                self.dlog.msg("Loading tuple " + str(db_board_userpost_threadop) + " into ThreadWatcher")
                self.insert(*db_board_userpost_threadop)
                
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.load()", cn=self.__class__.__name__)
        
        
    def update(self):
        ''' Refresh active threads in dictionary and marks inactive '''
        
        if not self.cfg.get('threadwatcher.enable'):
            return False
        
        try:
            boardpad_list = self.wl.get_boardpad_list()
            
            opcount = 0
            boardcount = 0
            for board in self.threadops:
                
                opcount_changed = False
                
                for op in self.threadops[board]:
                    
                    opcount += 1
                    opcount_changed = True
                    
                    # Only watch threads that are not opened in a BoardPad except if cfg overrides it
                    skip = False
                    for boardpad in boardpad_list:
                        if str(board) == str(boardpad.board) and str(op) == str(boardpad.threadno):
                                self.dlog.msg("ThreadWatcher: Not watching opened thread: " + str(op), 4)
                                if not self.wl.cfg.get('threadwatcher.skip_active_boards'):
                                    skip = True
                    
                    # If OP did not 404 or is active in window
                    if self.threadops[board][op]['active'] and not skip:
                        userposts = self.threadops[board][op]['userposts']
                        self.threadops[board][op]['active'] = self.query(board, op, userposts)
                        
                    # Update DB if thread is not active
                    if not self.threadops[board][op]['active']:
                        self.db.set_inactive(board, op)
                        continue
                else:
                    # Only count boards containing at least one user made post
                    if opcount_changed:
                        boardcount += 1

            if opcount == 1: opcstr = "one thread"
            else: opcstr = str(opcount) + " threads"
            
            if boardcount == 1: bcstr = "one board"
            else: bcstr = str(boardcount) + " boards"
                    
            self.dlog.msg("ThreadWatcher: Watching " + opcstr + " on " + bcstr, 3)
            
            self.remove_inactive_threads()
                        
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.update()", cn=self.__class__.__name__)

                    
    def query(self, board, op, userposts):
        ''' Get thread.json '''
        ''' Return: False if Thread 404'd else True '''
        
        try:
            
            contentFetcher = Autism(board, threadno=op)
            contentFetcher.setstdscr(self.wl.stdscr)
            contentFetcher.sb = self.wl.sb
            if contentFetcher.get() == "cached":
                contentFetcher.get()
                    
        except HTTPError as err:
            self.dlog.excpt(err, logLevel=4, msg=">>>in ThreadWatcher.query()", cn=self.__class__.__name__)
            if err.response.status_code == 404:
                return False
            
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.query()", cn=self.__class__.__name__)
            
        try:
            # Trigger marking archived posts as inactive
            try:
                if contentFetcher.jsoncontent['posts'][0]['archived']:
                    return False
            except KeyError:
                pass
            
            for userpost in userposts:
                self.get_replies(contentFetcher.jsoncontent, board, op, userpost)
            
            return True
        
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.query()", cn=self.__class__.__name__)     
            
        return True   
        
            
            
    def get_replies(self, jsoncontent, board, op, userpost):
        try:
            
            # TODO for loop from DictOutput.create_sub(), might want to put this in an extra class
            for post in jsoncontent['posts']:
                if (board, post['no']) in self.seen:
                    continue
                
                # Extract all references from post 
                try:
                    refposts = re.findall('&gt;&gt;(\d+)', post['com'])
                # Skip file only comments
                except:
                    continue
                
                for refpost in refposts:
                    if str(refpost) == str(userpost):
                        
                        threadlink = ">>>/" + str(board) + "/" + str(op) + " "
                        reply = self.clean_html(post['com'])
                        
                        subject = "[File Only]"
                        if jsoncontent['posts'][0].has_key('sub'):
                            subject = jsoncontent['posts'][0]['sub'][:23]
                        elif jsoncontent['posts'][0].has_key('com'):
                            subject = self.clean_html(jsoncontent['posts'][0]['com'][:23])
                         
                        self.notify(threadlink + str(subject) + " " + reply)
                        self.seen.append((board, post['no']))
                        continue
                    continue
            

        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.query()", cn=self.__class__.__name__)
            raise 
        
        


    # source: https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
    # Copy of function also exists in DictOutput # TODO merge
    def clean_html(self, html):
        
        html = re.sub('<br>', ' ', html)
        soup = BeautifulSoup(html)
        
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # get text
        text = soup.get_text()
        
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return(text)
        
    def notify(self, message):
        ''' Write userpost and response to MessagePad '''
        try:
            #Notifier.send("ThreadWatcher", str(message))
            self.wl.msgpadout(str(message))
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in ThreadWatcher.notify()", cn=self.__class__.__name__)
