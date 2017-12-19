'''
Created on May 29, 2017

'''
import unicodedata

class Bar(object):
    '''
    classdocs
    '''
    
    def __init__(self, stdscr, wl):
        self.stdscr = stdscr
        self.wl = wl
        
        self.dlog = wl.dlog
        
        self.screensize_y, self.screensize_x = stdscr.getmaxyx()
        
    def on_resize(self):
        self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
        self.draw()
        
    def calc_blank(self):
        lineLength = 0
        for letter in self.title.decode('utf-8'):
            lineLength += 1
            
            # Wide unicode takes two spaces
            if unicodedata.east_asian_width(letter) is 'W':
                lineLength +=1
            
#        self.dlog.msg("Added " + str(curnewlines) + " 
        self.sb_blank = self.screensize_x - lineLength