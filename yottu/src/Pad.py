'''
Created on Oct 9, 2015

Basic class for ncurses pads such as CommandPad and BoardPad

'''
from __future__ import division
import curses
import unicodedata
from DebugLog import DebugLog
import re
from Titlebar import Titlebar
from Statusbar import Statusbar

class Pad(object):
	reservedscreen = 3
	padbuffersize = 4096

	def __init__(self, stdscr, wl):
		self.stdscr = stdscr
		self.wl = wl # WindowLogic
		
		self.screensize_y, self.screensize_x = self.stdscr.getmaxyx();
		height = self.screensize_y-Pad.reservedscreen; width = self.screensize_x
		
		self.pheight = height;
		self.pwidth = width
		self.mypad = curses.newpad(height+Pad.padbuffersize, width)  # @UndefinedVariable
		curses.curs_set(False)  # @UndefinedVariable
		
		self.padr = 0; self.padu = 0; self.padd = 0
		self.mypad.refresh(0, self.padr, self.padu, self.padd, self.pheight, self.pwidth)
		
		# count new lines added by this function for autoscrolling
		(self.pposy, self.pposx) = self.mypad.getyx()
		(self.pmaxy, self.pmaxx) = self.mypad.getmaxyx()
		self.actualpmaxy = self.pmaxy-Pad.padbuffersize
		
		self.tb = Titlebar(self.stdscr)
		self.sb = Statusbar(self.stdscr, "(<Pad>)")
		
		self.dlog = DebugLog("debug.log")
		
		self.dlog.msg("pmaxy: " + str(self.pmaxy), 5)
		self.dlog.msg("actualpmaxy: " + str(self.actualpmaxy), 5)
		
		self._active = False # Pad is actively viewed by user
		
		self.autoScroll = True
		self.size = 0 # Number of lines in pad
		self.position = 0
		self.line = ''.encode('utf-8')
		self.marked_line = None


	# Updater polls this method every n seconds
	def on_update(self):
		pass
		
	def stop(self):
		self._stop.set()
		
	def active(self):
		self._active = True
		
		# Reset window's unread properties and remove unread status from status bar
		self.wl.set_property(self, 'sb_unread', False)
		self.wl.windowListProperties[self]['sb_lines'] = 0
		self.wl.windowListProperties[self]['sb_mentioned'] = False
		self.generate_unread_window_element()
		
		self.sb.draw()
		self.tb.draw()
		self.draw()
		
	def inactive(self):
		self._active = False
		
	def on_resize(self):
		screensize_y, screensize_x = self.stdscr.getmaxyx()
		curses.resize_term(screensize_y, screensize_x)  # @UndefinedVariable
		
		height = screensize_y-self.reservedscreen; width = screensize_x
		self.pheight = height
		self.pwidth = width
		
		self.mypad.resize(self.pheight+Pad.padbuffersize, self.pwidth)
		
		(self.pposy, self.pposx) = self.mypad.getyx()
		(self.pmaxy, self.pmaxx) = self.mypad.getmaxyx()
		self.actualpmaxy = self.pmaxy-Pad.padbuffersize
		self.draw()
		
	
	def addstr(self, string, options=curses.A_NORMAL, indent=0, mentioned=False):  # @UndefinedVariable
		try:
			
			# check if comment needs to be line wrapped, indent it if so
			if indent:
				stringpos = 0
				
				# iterate over every character, note that BoardPad sends a string
				# for every word delimited by a space
				for character in string:
					(self.pposy, self.pposx) = self.mypad.getyx()
					
					# wrap oversized word at the end of the line if it fits in one line
					if stringpos == 0:
						space_needed = self.pposx + len(string)
						indented_space = self.pmaxx - indent

						if space_needed > self.pwidth and len(string) < indented_space:
							self.mypad.addstr("\n")
							
							#self.line += u"\n".decode('utf-8')
							(self.pposy, self.pposx) = self.mypad.getyx()
							self.size = self.pposy
					
					# indent after line wrap		
					if self.pposx == 0:
						self.mypad.addstr(" "*indent)
						
					# output the character and adjust the pad size
					self.mypad.addstr(character, options)
					(self.pposy, self.pposx) = self.mypad.getyx()
					self.size = self.pposy
					
					stringpos += 1
			
			# add string to current position		
			else:
				self.mypad.addstr(string, options)
				(self.pposy, self.pposx) = self.mypad.getyx()
				self.size = self.pposy
		
			if mentioned:
				self.wl.windowListProperties[self]['sb_mentioned'] = True
		except Exception as err:
			self.dlog.msg("Pad.addstr() - indent != 0: " + str(err))
			
		
		if re.search(r'\n', string):
			if not self._active:
				try:
					#self.dlog.msg("Not Active: " + str(self))
					self.wl.set_property(self, 'sb_unread', True)
					self.wl.windowListProperties[self]['sb_lines'] += 1
						
					self.generate_unread_window_element()
					
				except Exception as err:
					self.dlog.msg("Pad.addstr() -> not self._active: " + str(err))
			self.auto_scroll()
		
	def calcline(self, line):
		''' returns the width of an unicode string '''
		lineLength = 0
		
		try:
			for letter in line.decode('utf-8'):
				lineLength += 1
				
				# Wide unicode takes two spaces
				if unicodedata.east_asian_width(letter) is 'W':
					lineLength +=1
					
		except Exception as err:
			self.dlog.msg("Pad.calcline(): " + str(err))	
			
		finally:	
			return lineLength
		
	def generate_unread_window_element(self):
		''' 
		generate list of tuples with (str, curses attribute) for unread windows
		this is passed to Statusbar which has no direct access to WindowLogic
		'''
		
		unread_windows = []
		# iterate over all window objects
		for window in self.wl.windowListProperties:
			
			# if the current window has unread messages
			if self.wl.get_property(window, 'sb_unread'):
				
				# get its index number
				windowNumber = self.wl.get_window_list().index(window)
				unread_lines = self.wl.get_property(window, 'sb_lines')
				
				# and append the index as a tuple with curses attribute to a list
				if self.wl.get_property(window, 'sb_mentioned'):
					unread_windows.append((windowNumber, curses.A_BOLD | curses.color_pair(2), # @UndefinedVariable
										unread_lines)) 
					
				else:		
					unread_windows.append((windowNumber, curses.A_BOLD | curses.color_pair(1),  # @UndefinedVariable
										unread_lines))
		
		# update the attribute of the current window's status bar
		active_win = self.wl.get_active_window_ref()
		active_win.sb.set_unread_windows(unread_windows)
	
	def set_auto_scroll(self, value):
		self.__autoScroll = value
		


	def get_position(self):
		return self.__position


	def set_position(self, value):
		self.dlog.msg("set_position: value/actualpmaxy: " + str(value) + "/" + str(self.actualpmaxy) + "\n", 5)
		self.__position = value
		if self._active:
			self.dlog.msg("set_position: moving to " + str(value), 5)
			self.move(value)
		
	def auto_scroll(self):
		if self.autoScroll is True:
			self.set_position(self.size)
			
	# FIXME merge moveup and down into one def
	def moveup(self, lines=1):
		newPos = self.get_position()-lines
		if newPos >= self.actualpmaxy:
			self.set_position(newPos)
		else:
			self.home()
		
	def movedown(self, lines=1):
		newPos = self.get_position()+lines
		self.dlog.msg("self.size: " + str(self.size), 5)
		if newPos <= self.size:
			self.set_position(newPos)
		else:
			self.set_position(self.size)
	
	def home(self):
		self.set_position(self.actualpmaxy)

	def end(self):
		self.set_position(self.size)
		
	# 
	def move(self, pos):
		try:
			self.dlog.msg("Pad: in move", 5)
			self.dlog.msg("pmaxy: " + str(self.pmaxy), 5)
			self.dlog.msg("pmaxx: " + str(self.pmaxy), 5)
			self.dlog.msg("actualpmaxy: " + str(self.actualpmaxy), 5)

			newPos = pos-(self.pmaxy-(Pad.padbuffersize))
			
			self.dlog.msg("newPos: " + str(newPos), 5)

			self.mypad.refresh(newPos, 0, 1, 0, self.actualpmaxy, self.pmaxx)
		except Exception as e:
			self.dlog.excpt(e)
			raise
		
			
	
	def get_post_no_of_marked_line(self):
		y,x = self.save_position()
		try:
			if self.marked_line is not None:
				
				postno = ""
				for pos in range(6, 20):
					char = chr(self.mypad.inch(self.marked_line, pos) & curses.A_CHARTEXT)  # @UndefinedVariable
					
					if pos == 6 or pos == 7:
						if char != ">":
							return None
					else:
						try:
							if int(char):
								pass
							
							postno += char
						except Exception as err:
							if len(postno) > 0:
								return postno
							return None 
						
				
		except Exception as err:
			self.dlog.msg("Pad.get_postno_of_marked_line: " + str(err))
			return None
		finally:
			self.restore_postion(y, x)
		
	
	def reverseline(self, pos_y, mode=curses.A_STANDOUT):  # @UndefinedVariable
		'''Changes background to font and font to background in a pos_y (y-pos)'''
		try:
			for x in range (0, self.pwidth):
				
				charattr = self.mypad.inch(pos_y, x)
				
				# Filter some attributes for preservation
				attrs = charattr & curses.A_ATTRIBUTES ^ curses.A_STANDOUT ^ curses.A_COLOR # @UndefinedVariable
			#	color = charattr & curses.A_COLOR  # @UndefinedVariable
			#	char = chr(charattr & curses.A_CHARTEXT)  # @UndefinedVariable
				
			#	color_pair_number = curses.pair_number(color)  # @UndefinedVariable
				
				self.mypad.chgat(pos_y, x, 1,  attrs | mode)  # @UndefinedVariable
			#	self.dlog.msg("Size of char: " + char +" | " + str(len(char)) + " | inch(): " + str(charattr) + " | cpn: " + str(color_pair_number))

		except Exception as err:
			self.dlog.msg("Pad.reverseline(): " + str(err))
			raise
	
	# FIXME: resizing messes up the position
	def markline(self, pos_y):
		try:
			self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()

			y, x = self.save_position()
			
			self.unmarkline()
			previous_marked_line = self.marked_line
			
			# pos_y: absolute y-postion on screen, value from curses.get_mouse()
			# get_position(): position in virtual pad
			# screensize_y: number of lines on screen
			# unused_lines: lines the pad does not cover + 1 for command input
			
			unused_lines = 2
			
			# Marked line relative to screen not counting pad size
			marked_line_rel = pos_y - unused_lines
			self.marked_line = marked_line_rel
			
			if self.size > self.screensize_y:
				self.marked_line += (self.get_position() - self.screensize_y + 3)
				
			#self.dlog.msg("ml: " + str(self.marked_line) + " = pos_y: " + str(pos_y) + " + pos(): " + str(self.get_position()) + " - ss_y: " + str(self.screensize_y) + " + 1")
			
			# Just unmark the pos_y if clicked twice
			if previous_marked_line == self.marked_line:
				self.marked_line = None
				return
			
			self.reverseline(self.marked_line)
			
		except Exception as err:
			self.dlog.msg("Pad.markline(): " + str(err))
			
		finally:
			self.restore_postion(y, x)
			self.draw()
			
	def unmarkline(self):
		try:
			if self.marked_line is not None:
				self.reverseline(self.marked_line, curses.A_NORMAL)  # @UndefinedVariable
		except Exception as err:
			self.dlog.msg("Pad.unmarkline(): " + str(err))
			pass
		
		
	def save_position(self):
		y, x = self.mypad.getyx()
		return y, x
	
	def restore_postion(self, y, x):
		self.mypad.move(y, x)

	def show_image(self):
		pass
			
	def draw(self):
		self.set_position(self.get_position())
		self.stdscr.refresh()
		
	position = property(get_position, set_position, None, None)
