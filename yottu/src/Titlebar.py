# -*- coding: utf-8 -*-
from Bar import Bar
import curses


class Titlebar(Bar):
	def __init__(self, stdscr):
		super(Titlebar, self).__init__(stdscr)
		self.screensize_y, self.screensize_x = stdscr.getmaxyx()
		self.sb_blank = 1
		self.set_title(u"yottu v0.2 - https://github.com/yottu/yottu".encode('utf-8')
		)
		
	def draw(self):
		self.calc_blank()
#		titlebar_text = u' '.join((self.title.encode('utf-8'), u" ".encode('utf-8')*self.sb_blank))
		
		titlebar_text = self.get_title()
		titlebar_text += u" ".encode('utf-8')*self.sb_blank
		try:
			curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # @UndefinedVariable
			self.stdscr.addstr(0, 0, titlebar_text, curses.color_pair(1))  # @UndefinedVariable
			self.stdscr.refresh()
		except:
			quit(self.stdscr)		
		

	def get_title(self):
		return self.__title

	def set_title(self, value):
		self.__title = value[:self.screensize_x]
		self.draw()
	
	
	title = property(None, set_title, None, None)
	title = property(get_title, None, None, None)