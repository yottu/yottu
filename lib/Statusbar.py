
import time
import curses
from Bar import Bar


class Statusbar(Bar):

	def __init__(self, stdscr, wl, nickname="", board="", threadno=""):
		super(Statusbar, self).__init__(stdscr, wl)
		
		self.stdscr = stdscr
		self.sb_status = ""
		self.sb_blank = 0
		self.sb_windowno = "X"
		self.unread_windows = [] # List of string and curses attribute tuples
		
		self.board = board
		self.threadno = str(threadno)
		
		self.nickname = nickname
		
		self.screensize_y, self.screensize_x = stdscr.getmaxyx();

	def get_unread_windows(self):
		return self.__unread_windows


	def set_unread_windows(self, value):
		self.__unread_windows = value

	def get_sb_windowno(self):
		return self.__sb_windowno


	def get_board(self):
		return self.__board


	def get_threadno(self):
		return self.__threadno


	def set_sb_windowno(self, value):
		self.__sb_windowno = value
		

	def set_board(self, value):
		self.__board = value
		

	def set_threadno(self, value):
		self.__threadno = str(value)


	def on_resize(self):
		self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
		self.draw()

	def get_nickname(self):
		return self.__nickname


	def set_nickname(self, value):
		self.__nickname = value
		try:
			self.sb_name = u''.join("[" + self.nickname + "]")
		except:
			self.sb_name = u''.join("[Anon]")
	
	def calc_blank(self, len_counter):
		# FIXME dont use hardcoded ints
		try:
			self.sb_blank = self.screensize_x - 4 - (len(self.sb_status) + len(self.sb_clock) + len(self.sb_name) + len(self.sb_win) + len_counter)
		except:
			self.sb_blank = 0
			
	def draw(self, update_n="", wait_n=""):
				
		try:
			self.stdscr.noutrefresh()
			self.sb_clock = "[" + time.strftime('%H:%M') + "]"
			if self.board:
				self.sb_win = "[" + str(self.sb_windowno) + ":4chan/"+ self.board + "/" + str(self.threadno) + "]"
			else:
				self.sb_win = "[" + str(self.sb_windowno) + ":4chan]"
				
			self.sb_clock = "[" + time.strftime('%H:%M') + "]"
# 			if self.nickname:
# 				self.sb_name = "[" + str(self.nickname) + "]"
# 			else:
# 				self.sb_name = "[Anon]"
			
			# calculate digits of the countdown timers
			counter = str(update_n)
			if wait_n:
				counter = str(wait_n) + "|" + counter
			self.calc_blank(len(counter))
		

			# Add Clock, name and Window/Board/Thread
			statusbar_text_head = u' '.join((self.sb_clock, self.sb_name, self.sb_win)).encode('UTF-8')

			# Save position
			saved_y, saved_x = self.stdscr.getyx()


			self.stdscr.addstr(self.screensize_y-2, 0, statusbar_text_head, curses.color_pair(1))  # @UndefinedVariable
			self.stdscr.refresh()
			if self.unread_windows:
				for unread_win, cattrib, unread_lines in self.unread_windows:
					unread_win = str(unread_win+1)
					unread_lines = "(" + str(unread_lines) + ")"
					self.sb_blank -= len(unread_win)+len(unread_lines)+1
					
					# Only draw if enough space is left on the Bar
					if self.sb_blank > 0:
						
						# Add unread window and unread lines
						self.stdscr.addstr(" ", curses.color_pair(1))  # @UndefinedVariable
						self.stdscr.addstr(unread_win, cattrib)  # @UndefinedVariable
						self.stdscr.addstr(unread_lines, curses.color_pair(1))  # @UndefinedVariable
					
			
			# Add fill blanks, status code area and refresh count down		
			statusbar_text_tail = u' '.join((" "*self.sb_blank, self.sb_status, counter))
			self.stdscr.addstr(statusbar_text_tail, curses.color_pair(1))  # @UndefinedVariable
			
			# Restore prior position
			self.stdscr.move(saved_y, saved_x)
			self.stdscr.refresh()
			
			# TODO Find out why Cross-Page-^W messes up clinepos
			if self.wl.ci:
				self.wl.ci.clinepos = saved_x
			
			curses.doupdate()  # @UndefinedVariable
			
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in Statusbar.draw()", cn=self.__class__.__name__)
			#self.wl.ci.clinepos = 4
			raise
		

		return
	
	def setStatus(self, status):
		''' sets Status text located right most before n_update '''
		self.sb_status = status[:self.sb_blank-1]
		self.draw()
		
		
	nickname = property(get_nickname, set_nickname, None, None)
	sb_windowno = property(get_sb_windowno, set_sb_windowno, None, None)
	board = property(get_board, set_board, None, None)
	threadno = property(get_threadno, set_threadno, None, None)
	unread_windows = property(get_unread_windows, set_unread_windows, None, None)
