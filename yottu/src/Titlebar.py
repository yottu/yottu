# -*- coding: utf-8 -*-

import time
import curses
import unicodedata


class Titlebar(object):
	def __init__(self, stdscr):
		self.stdscr = stdscr
		self.screensize_x, self.screensize_y = stdscr.getmaxyx()
		self.sb_blank = 1
		self.set_title(u"yottu v0.1 - https://github.com/yottu/yottu".encode('utf-8')
		)
		
	def on_resize(self):
		self.screensize_x, self.screensize_y = self.stdscr.getmaxyx()
		self.draw()

	def get_title(self):
		return self.__title

	def set_title(self, value):
		self.__title = value
		self.draw()

		
	def draw(self):
		self.calc_blank()
#		titlebar_text = u' '.join((self.title.encode('utf-8'), u" ".encode('utf-8')*self.sb_blank))
		
		titlebar_text = self.get_title()
		titlebar_text += u" ".encode('utf-8')*self.sb_blank
		try:
			curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
			self.stdscr.addstr(0, 0, titlebar_text, curses.color_pair(1))
			self.stdscr.refresh()
		except:
			quit(self.stdscr)
	
	
	def calc_blank(self):
		lineLength = 0
		for letter in self.title.decode('utf-8'):
			lineLength += 1
			
			# Wide unicode takes two spaces
			if unicodedata.east_asian_width(letter) is 'W':
				lineLength +=1
			
#		self.dlog.msg("Added " + str(curnewlines) + " 
		self.sb_blank = self.screensize_y - lineLength
	
	
	title = property(None, set_title, None, None)
	title = property(get_title, None, None, None)