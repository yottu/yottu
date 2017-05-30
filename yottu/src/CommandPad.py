'''
Created on Oct 9, 2015

'''

from Pad import Pad
import curses

class CommandPad(Pad):
	def __init__(self, stdscr, wl):
		super(CommandPad, self).__init__(stdscr, wl)

		self.sb.set_nickname("(status)")
		self.sb.set_sb_windowno(1)
		
		self.usage()
		
	def on_resize(self):
		self.dlog.msg("CommandPad: on_resize")
		super(CommandPad, self).on_resize()
		self.tb.on_resize()
		self.sb.on_resize()
		
	def on_update(self):
		self.sb.draw()
	
	def active(self):
		super(CommandPad, self).active()

		
	def inactive(self):
		super(CommandPad, self).inactive()
	
	def usage(self):
		self.dlog.msg(str(self.get_position()))
		self.addstr("__   __   _   _    \n")
		self.addstr("\ \ / /__| |_| |_ _  _\n")
		self.addstr(" \ V / _ \  _|  _| || |\n")
		self.addstr("  |_|\___/\__|\__|\_,_|\n")
		self.addstr("Yottu v0.2 - https://github.com/yottu/yottu\n", curses.A_BOLD)
		self.addstr("\n")
		self.addstr("Set board context: /board <board>\n")
		self.addstr("Display Threads in current board context: /list <board> [not implemented]\n")
		self.addstr("Open a thread in current board context: /join <thread number>\n")
		self.addstr("Show settings: /set\n")
		self.addstr("Save settings: /save\n")
		