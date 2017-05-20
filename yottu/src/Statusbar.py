
import time
import curses


class Statusbar(object):

	def __init__(self, stdscr, nickname, board, threadno):
		self.stdscr = stdscr
		self.set_nickname(nickname)
		self.board = board
		self.threadno = threadno
		self.screensize_x, self.screensize_y = stdscr.getmaxyx();
		self.sb_clock = "[" + time.strftime('%H:%M') + "]"
		self.sb_name = "[" + self.nickname + "]" #TODO /set name
		self.sb_win = "[W#:4chan/"+ self.board + "/" + self.threadno + "]" #TODO
		self.sb_status = ""
		self.sb_blank = 0
		
	def on_resize(self):
		self.screensize_x, self.screensize_y = self.stdscr.getmaxyx()
		self.draw()

	def get_nickname(self):
		return self.__nickname


	def set_nickname(self, value):
		self.__nickname = value
	
	def calc_blank(self, len_counter):
		# FIXME dont use hardcoded ints
		self.sb_blank = self.screensize_y - 5 - (len(self.sb_status) + len(self.sb_clock) + len(self.sb_name) + len(self.sb_win) + len_counter)
			
	def draw(self, update_n=0):
		self.sb_clock = "[" + time.strftime('%H:%M') + "]"
		
		# calculate digits of the countdwon timer
		len_counter = len(str(update_n))
		self.calc_blank(len_counter)
		
		statusbar_text = u' '.join((self.sb_clock, self.sb_name, self.sb_win, " "*self.sb_blank, self.sb_status, str(update_n))).encode('UTF-8')
		try:
			curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
			self.stdscr.addstr(self.screensize_x-2, 0, statusbar_text, curses.color_pair(1))
			
			# TODO cursor needs to be moved to the string (clinepos) of ci
			self.stdscr.move(self.screensize_x-1, 1)
			self.stdscr.refresh()
			
		except:
			quit(self.stdscr)
		
		return statusbar_text

	
	def setStatus(self, status):
		self.sb_status = status
		
		
	nickname = property(None, set_nickname, None, None)
	nickname = property(get_nickname, None, None, None)
	
	
			
		