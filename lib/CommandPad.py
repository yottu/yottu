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
		
	def usage_help(self):
		self.addstr("See Readme.md for a more complete list\n", curses.color_pair(4))  # @UndefinedVariable
		self.addstr("Set default board: /board <board>\n")
		self.addstr("Open catalog: /catalog [search term] (Hotkey: c)\n")
		self.addstr("Join thread using the default board: /join <thread number>\n")
		self.addstr("Join general: /join <board>/<search term> (e.g. /join g/fglt)\n", curses.color_pair(3))  # @UndefinedVariable
		self.addstr("Part window: /part (Hotkey: x)\n")
		self.addstr("Bookmark currently open threads: /autojoin save [clear, add, remove, help]\n")
		self.addstr("Show settings: /set\n")
		self.addstr("Save settings: /save\n")
		self.addstr("Quit: /quit (Hotkey: Alt+Q)\n")
	
	def usage(self):
		self.dlog.msg(str(self.get_position()))
		self.addstr("__   __   _   _    \n")
		self.addstr("\ \ / /__| |_| |_ _  _\n")
		self.addstr(" \ V / _ \  _|  _| || |\n")
		self.addstr("  |_|\___/\__|\__|\_,_|\n")
		self.addstr("Yottu v0.3 - https://github.com/yottu/yottu\n", curses.A_BOLD)  # @UndefinedVariable
		self.addstr("\n")
		self.addstr("Type /help for usage\n")
