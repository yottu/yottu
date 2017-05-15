'''
Created on Oct 5, 2015

'''
from threading import Thread
import curses
import threading
from DebugLog import DebugLog
from BoardPad import BoardPad
import Config
import re

class CommandInterpreter(threading.Thread):
	def __init__(self, stdscr, wl):
		self.stdscr = stdscr
		self.wl = wl
		self.screensize_x = 0
		self.screensize_y = 0
		
		self.screensize_x, self.screensize_y = self.stdscr.getmaxyx();
		self.stdscr.addstr(self.screensize_x-1, 0, "[^] ")
		
		Thread.__init__(self)
		
		self.cfg = Config.Config(".config/yottu/", "config")
		self.cmode = False # command mode
		self.tmode = False # talking mode (no need to prefix /say)
		self.clinepos = 4
		self.command = ""
		self.context = "int" # context in which command is executed
		
		
		curses.curs_set(False)
		
		self.terminate = 0
		
		self.dlog = DebugLog(self.wl)
		
	def on_resize(self):
		self.stdscr.clear()
		self.stdscr.refresh()
		self.screensize_x, self.screensize_y = self.stdscr.getmaxyx();
		self.wl.on_resize()
		self.stdscr.addstr(self.screensize_x-1, 0, "[^] ")
		
	def cout(self, c):
		self.stdscr.addstr(self.screensize_x-1, self.clinepos, c)
		self.command += c
		self.clinepos += 1
		
	def clean(self):
		self.stdscr.addstr(self.screensize_x-1, 0, str(" "*(self.screensize_y-1)))
		self.command = ""
		self.clinepos = 4
		
	def parse_param(self, string):
		''' return list from whitespace separated string '''
		''' TODO: Implement validity matching logic '''
		return string.split()
		
	def exec_com(self):
		
		cmd_args = self.command.split()
		
		
		
		if len(cmd_args) == 0:
			return

		
		self.dlog.msg("Trying to execute command: " + self.command, 5)
		
		# Text input
		if re.match("say", self.command):
			cmd_args.pop(0)
			comment = " ".join(cmd_args)
			# Check if executed on a BoardPad
			active_window = self.wl.get_active_window_ref()
			if not isinstance(active_window, BoardPad):
				self.dlog.msg("/say must be used on a BoardPad, not " + str(active_window))
				return
			
			active_thread_OP = active_window.threadno
			self.dlog.msg("Creating post on " + str(self.context) + "/"
						+ str(active_thread_OP) + " | Comment: " + str(comment))
			active_window.post(str(comment))

		elif re.match("captcha", self.command):
			cmd_args.pop(0)
			captcha = " ".join(cmd_args)
			active_window = self.wl.get_active_window_ref()
			active_window.set_captcha(str(captcha))

		
		# "Joining" a new thread
		elif re.match("join", self.command):
			
			try:
				joinThread = re.sub('>', '', cmd_args[1])
				self.wl.join_thread(self.context, joinThread)
				self.wl.compadout("Joining /" + self.context + "/" + cmd_args[1])
			except IndexError:
				self.wl.compadout("Usage: /join <thread number>")
			except:
				raise
			
		elif re.match("catalog", self.command):
			
			try:
				self.wl.compadout("Creating catalog for " + self.context)
				search = cmd_args[1]
				self.wl.catalog(self.context, search)
			except IndexError:
				self.wl.catalog(self.context)
			except:
				raise
			
		elif re.match("board", self.command):
			
			try:
				self.context = cmd_args[1]
				self.context = re.sub('\/', '', self.context)
			except IndexError:
				self.wl.compadout("Current board context: /" + self.context + "/")
			except:
				raise
			
		elif re.match("part", self.command):
			self.wl.destroy_active_window()
			
		elif re.match("load", self.command):
			self.cfg.readConfig()
			
		elif re.match("save", self.command):
			self.cfg.writeConfig()
			
			
		elif re.match("set", self.command):
			
			# Show settings if no args are given
			if len(cmd_args) is 1: 
				configItems = self.cfg.getSettings()
				self.wl.compadout("[Main]")
				for pair in configItems:
					self.wl.compadout(pair[0] + ": " + pair[1])
					
			# Else assign new value to setting
			else:
				key = cmd_args[1]
				val = ' '.join(cmd_args[2:])
				try:
					self.cfg.set(key, val)
				except Exception as e:
					self.dlog.excpt(e)
					
					
		elif re.match("window", self.command):
			
			if len(cmd_args) is 1:
				self.wl.compadout("Active window: " + str(self.wl.get_active_window()))
				
					
		elif re.match("quit", self.command):
			self.terminate = 1
			
		else:
			self.dlog.msg("Invalid command: " + self.command)
		
	# Loop that refreshes on input
	def run(self):
		curses.mousemask(-1)
		while True:
						
			if self.terminate is 1:
				self.dlog.msg("CommandInterpreter: self.terminate is 1")
				break
			
			
			# moves cursor to current position 
			#self.stdscr.move(self.screensize_x-1, self.clinepos)
			if self.cmode:
				curses.curs_set(True)
				
			c = self.stdscr.getkey()
			
			if c == "KEY_RESIZE":
				self.dlog.msg("CommandInterpreter: KEY_RESIZE")
				self.on_resize()
				continue
			
			if self.cmode:
				curses.curs_set(True)
	
			self.dlog.msg("getkey(): "+ c, 5)
			#c = self.stdscr.getch()
			
			if self.cmode or self.tmode:
				
				if c == "KEY_BACKSPACE":
					
					# Delete last character after, len("[/] ") == 4 
					if self.clinepos > 4:
						self.command = self.command[:-1]
						self.clinepos = self.clinepos - 1
						self.stdscr.addstr(self.screensize_x-1, self.clinepos, " ")
						self.stdscr.move(self.screensize_x-1, self.clinepos)
						
					continue
				
				try:
					if c == u'\n' or ord(c) == 27:
						if c == u'\n':
							self.exec_com()
						self.cmode = False
						self.tmode = False
						self.clean()
						self.stdscr.addstr(self.screensize_x-1, 0, "[^] ")
						curses.curs_set(False)
						continue
				except Exception as e:
					self.dlog.excpt(e)
					pass
					
				try:
					self.cout(c)
					continue
				except:
					pass
						
			# Quit application
			if c == u'q':
				self.terminate = 1
			
			# Command input mode
			elif c == u'/' or c == u'i':
				self.stdscr.addstr(self.screensize_x-1, 0, "[/] ")
				self.cmode = True
				
			# Text input mode
			elif c == u't':
				self.stdscr.addstr(self.screensize_x-1, 0, "[>] ")
				self.command = "say "
				self.tmode = True
				
			# Scroll
			elif c == 'KEY_HOME':
				self.wl.home()
			elif c == 'KEY_END':
				self.wl.end()
			elif c == 'KEY_PPAGE':
				self.wl.moveup(5)
			elif c == 'KEY_NPAGE':
				self.wl.movedown(5)
			elif c == 'KEY_UP' or c == u'w':
				self.wl.moveup()
			elif c == 'KEY_DOWN' or c == u's':
				self.wl.movedown()
				
				
			# change pad	
			elif c == u'1':
				try:
					self.wl.raise_window(0)
				except:
					raise
			elif c == u'2':
				try:
					self.wl.raise_window(1)
				except:
					raise
			elif c == u'3':
				try:
					self.wl.raise_window(2)
				except:
					raise
			elif c == u'4':
				try:
					self.wl.raise_window(3)
				except:
					raise
			elif c == u'5':
				try:
					self.wl.raise_window(4)
				except:
					raise
			elif c == u'6':
				try:
					self.wl.raise_window(5)
				except:
					raise
			elif c == u'7':
				try:
					self.wl.raise_window(6)
				except:
					raise
			elif c == u'8':
				try:
					self.wl.raise_window(7)
				except:
					raise
			elif c == u'9':
				try:
					self.wl.raise_window(8)
				except:
					raise
			elif c == u'0':
				try:
					self.wl.raise_window(9)
				except:
					raise
			elif c == u'3':
				try:
					self.wl.raise_window(2)
				except:
					raise
			elif c == u'n':
				try:
					self.wl.next() #TODO: implement in wl
				except:
					raise
			elif c == u'p':
				try:
					self.wl.prev() #TODO: implement in wl
				except:
					raise
			elif c == "KEY_MOUSE":
				mouse_state = curses.getmouse()[4]
				self.dlog.msg("getmouse(): "+ str(mouse_state), 5)
				#self.stdscr.addstr(str(mouse_state))
				if int(mouse_state) == 134217728:
					self.wl.movedown(5)
				elif int(mouse_state) == 524288:
					self.wl.moveup(5)
			else:
				self.dlog.msg("Unbound key: " + str(c))
	#				mypad.refresh(padl, padr, padu, padd, pheight, pwidth)
			#elif c == curses.BUTTON5_PRESSED:
			#	padl += 15
