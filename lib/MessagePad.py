# -*- coding: utf-8 -*-
'''
Created on Dec 15, 2017

'''

from Pad import Pad
import curses

class MessagePad(Pad):
    def __init__(self, stdscr, wl):
        super(MessagePad, self).__init__(stdscr, wl)

        self.sb.set_nickname("(msg)")
        self.sb.set_sb_windowno(2)
        self.tb.set_title("-- Messages --")
        
    def on_resize(self):
        self.dlog.msg("MessagePad: on_resize", 5)
        super(MessagePad, self).on_resize()
        self.tb.on_resize()
        self.sb.on_resize()
        
    def on_update(self):
        self.sb.draw()
    
    def active(self):
        super(MessagePad, self).active()

        
    def inactive(self):
        super(MessagePad, self).inactive()
        

    
