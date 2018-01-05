'''
Created on Dec 30, 2017
'''

import socket
import string
from threading import Thread
import threading
from TermImage import TermImage


class RelayChat(threading.Thread):
    ''' source: http://archive.oreilly.com/pub/h/1968 '''
    def __init__(self, host, port, nick, oauth, channel, subtitle, dlog):
        self.host = host
        self.port = port
        self.nick = nick
        self.oauth = oauth
        self.channel = channel
        self.subtitle = subtitle
        self.dlog = dlog
        
        self.server = None
        self.connected = False
        
        Thread.__init__(self)
        self._stop = threading.Event()
        
             
    def stop(self):
        self.s.send("QUIT" + "\r\n")
        self._stop.set()
        
    def connect(self):
        try:
            self.s=socket.socket()
            self.s.connect((self.host, self.port))
            self.s.send("PASS " + self.oauth + "\r\n")
            self.s.send("NICK " + self.nick + "\r\n")
            self.s.send("JOIN " + self.channel + "\r\n")
            self.dlog.msg(self.s.recv(1024))
            self.server = str(self.s.getpeername())
            self.dlog.msg("Connected to " + self.server)
            self.connected = True
            readbuffer = ""
    
            while True:
                    if self._stop.is_set():
                        self.dlog.msg("Disconnecting from " + str(self.server))
                        self.connected = False
                        break
                    readbuffer=readbuffer+self.s.recv(1024)
    #               print(readbuffer)
                    temp=string.split(readbuffer, "\n")
                    readbuffer=temp.pop( )
    
                    for line in temp:
                            line=string.rstrip(line)
                            line=string.split(line)
    
                            try:
                                if (line[2] == self.channel):
                                    comment = ' '.join(line[3:])[1:]
                            except Exception as err:
                                self.dlog.excpt(err, msg=">>>in RelayChat.connect() -> Parse", cn=self.__class__.__name__)
                            
                            self.dlog.msg(str(comment))
                            self.subtitle.subfile_append(comment)
    
                            if(line[0]=="PING"):
                                    self.s.send("PONG %self.s\r\n" % line[1])
                                    
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in RelayChat.connect()", cn=self.__class__.__name__)