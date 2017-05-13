'''
Created on Oct 9, 2015

Basic class for ncurses pads such as CommandPad and BoardPad

'''
from __future__ import division
import curses
import unicodedata
from DebugLog import DebugLog
import math
import re

class Pad(object):
	reservedscreen = 3
	padbuffersize = 4096

	def __init__(self, stdscr):
		self.stdscr = stdscr
		
		
		screensize_y, screensize_x = self.stdscr.getmaxyx();
		height = screensize_y-Pad.reservedscreen; width = screensize_x
		
		self.pheight = height;
		self.pwidth = width
		self.mypad = curses.newpad(height+Pad.padbuffersize, width)
		curses.curs_set(False)
		
		self.padr = 0; self.padu = 0; self.padd = 0
		self.mypad.refresh(0, self.padr, self.padu, self.padd, self.pheight, self.pwidth)
		
		
		# count new lines added by this function for autoscrolling
		(self.pposy, self.pposx) = self.mypad.getyx()
		(self.pmaxy, self.pmaxx) = self.mypad.getmaxyx()
		self.actualpmaxy = self.pmaxy-Pad.padbuffersize
		
		self.dlog = DebugLog("debug.log")
		
		self.dlog.msg("pmaxy: " + str(self.pmaxy))
		self.dlog.msg("actualpmaxy: " + str(self.actualpmaxy))

		self._active = False # Pad is actively viewed by user
		
		self.autoScroll = True
		self.size = 0 # Number of lines
		self.position = 0
		self.line = ''.encode('utf-8')



		
	def stop(self):
		self._stop.set()
		
	def active(self):
		self._active = True
		
	def inactive(self):
		self._active = False
		
	def on_resize(self):
		screensize_y, screensize_x = self.stdscr.getmaxyx()
		curses.resize_term(screensize_y, screensize_x)
		
		height = screensize_y-self.reservedscreen; width = screensize_x
		self.pheight = height;
		self.pwidth = width
		
		self.mypad.resize(self.pheight+Pad.padbuffersize, self.pwidth)
		
		(self.pposy, self.pposx) = self.mypad.getyx()
		(self.pmaxy, self.pmaxx) = self.mypad.getmaxyx()
		self.actualpmaxy = self.pmaxy-Pad.padbuffersize
		self.movedown()
		
		

	def set_auto_scroll(self, value):
		self.__autoScroll = value
		
	def get_height(self):
		return self.__height


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
		
	def calcline(self, line):
		lineLength = 0
		for letter in line.decode('utf-8'):
			lineLength += 1
			
			# Wide unicode takes two spaces
			if unicodedata.east_asian_width(letter) is 'W':
				lineLength +=1
			
		# note that __future__ division is needed for correct ceiling
		curnewlines = math.ceil(lineLength/self.pmaxx)
		self.size += int(curnewlines)
#		self.dlog.msg("Added " + str(curnewlines) + " Total: " + str(self.size) + " new lines for " + str(len(line)) + "c\n" )
	
	def addstr(self, string, options=curses.A_NORMAL):
		
		self.mypad.addstr(string, options)
		self.line += string.decode('utf-8')

		
		if re.search(r'\n', string):
			self.calcline(self.line.encode('utf-8'))
			self.auto_scroll()
			self.line = ''.encode('utf-8')
		
			
	def draw(self):
		self.set_position(self.get_position())
		
		
	position = property(get_position, set_position, None, None)
	height = property(get_height, None, None, None)
