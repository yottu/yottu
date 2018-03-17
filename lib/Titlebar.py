# -*- coding: utf-8 -*-
from Bar import Bar
import curses


class Titlebar(Bar):
	def __init__(self, stdscr, wl, pad):
		super(Titlebar, self).__init__(stdscr, wl, pad)
		self.screensize_y, self.screensize_x = stdscr.getmaxyx()
		self.sb_blank = 1
		
		self.stats = u" " # space for e.g stats displayed with right alignment 
				
		self.replies = 0
		self.images = 0
		self.unique_ips = 0
		self.bumplimit = 0 # 1 if True
		self.imagelimit = 0 # 1 if True
		self.page = 0
		self.unique_ips_changed = False
		
		self.set_title(u"yottu v0.4 - https://github.com/yottu/yottu".encode('utf-8'))
		
	def draw(self):
		super(Titlebar, self).draw()
		
		try:
			self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
			self.calc_blank()
	#		titlebar_text = u' '.join((self.title.encode('utf-8'), u" ".encode('utf-8')*self.sb_blank))
			
			titlebar_text = self.get_title()
			titlebar_text += u" ".encode('utf-8')*self.sb_blank
			
			# Draw title bar text
			self.stdscr.addstr(0, 0, titlebar_text, curses.color_pair(1))  # @UndefinedVariable
			
			if self.replies:
				self.draw_stats()
				
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in Titlebar.draw()", cn=self.__class__.__name__)
				
	def draw_stats(self):
		''' Draw additional stats to the title bar (Count of replies, images and unique posters) '''
		
		try:	
			
			replies = str(self.replies) + "R "
			images = str(self.images) + "I "
			unique_ips = str(self.unique_ips) + "P "
			page = "[" + str(self.page) + "]"
			self.stats = replies + images + unique_ips + page
			
			try:
				ccolors = curses.color_pair(1) # @UndefinedVariable
				if self.bumplimit:
					ccolors = curses.color_pair(3) # @UndefinedVariable
				self.stdscr.addstr(0, self.screensize_x-len(replies+images+unique_ips+page), \
								u"".join(replies).encode('utf-8'), ccolors)
				
				if self.imagelimit:
					ccolors = curses.color_pair(3) # @UndefinedVariable
				else:
					ccolors = curses.color_pair(1) # @UndefinedVariable
				
				self.stdscr.addstr(0, self.screensize_x-len(unique_ips+images+page), \
								u"".join(images).encode('utf-8'), ccolors)
				
				if self.unique_ips_changed:
					ccolors = curses.color_pair(2) # @UndefinedVariable
				else:
					ccolors = curses.color_pair(1) # @UndefinedVariable
				
				self.stdscr.addstr(0, self.screensize_x-len(unique_ips+page), \
								u"".join(unique_ips).encode('utf-8'), ccolors)
				
				if int(self.page) > 8:
					ccolors = curses.color_pair(3) # @UndefinedVariable
				else:
					ccolors = curses.color_pair(1) # @UndefinedVariable
					
				self.stdscr.addstr(0, self.screensize_x-len(page), \
								u"".join(page).encode('utf-8'), ccolors)
				
			except Exception as err:
				self.dlog.excpt(err, msg=">>>in Titlebar.draw() -> thread stats", cn=self.__class__.__name__)

#			self.stdscr.addstr(0, self.screensize_x-len(self.stats), u"".join(self.stats).encode('utf-8'), curses.color_pair(1))  # @UndefinedVariable
			
			
			
			self.stdscr.refresh()
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in Titlebar.draw()", cn=self.__class__.__name__)
		

	def get_title(self):
		return self.__title

	def set_title(self, value):
		self.__title = value[:self.screensize_x-len(self.stats)]
		self.draw()
	
	
	title = property(None, set_title, None, None)
	title = property(get_title, None, None, None)