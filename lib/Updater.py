'''
Created on May 19, 2017

@author: yottudev@gmail.com
'''
from threading import Thread
import threading
from time import sleep
from DebugLog import DebugLog
import curses

class Updater(threading.Thread):
    ''' Class solely handles detecting resizes # TODO figure out a better way '''
    
    def __init__(self, stdscr, wl):
        self.stdscr = stdscr
        self.wl = wl
        
        
        self.dlog = DebugLog()
        self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
        
        Thread.__init__(self)
        self._stop = threading.Event()
        self.dlog.msg("Updater started.")

    def detect_resize(self):
        resize = curses.is_term_resized(self.screensize_y, self.screensize_x)  # @UndefinedVariable
        if (resize):
            try:
                self.dlog.msg("Resize detected.")
                self.wl.on_resize()
            
            finally:
                self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
            
            
    def run(self):
        while True:
            try:
                if self._stop.is_set():
                    self.dlog.msg("Updater stopped.")
                    break
            
                self.detect_resize()
                self.wl.on_update()
                sleep(1)
            except:
                raise
            
    def stop(self):
        self._stop.set()

