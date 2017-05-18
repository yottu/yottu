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
import json

class CommandInterpreter(threading.Thread):
	def __init__(self, stdscr, wl):
		self.stdscr = stdscr
		self.wl = wl
		self.screensize_x = 0
		self.screensize_y = 0
		
		self.screensize_x, self.screensize_y = self.stdscr.getmaxyx()
		self.stdscr.addstr(self.screensize_x-1, 0, "[^] ")
		
		
		Thread.__init__(self)
		
		self.cfg = Config.Config(".config/yottu/", "config")
		self.settings = None
		self.readconfig()
		# For Saving/Restoring window state #FIXME
		#self.state_file = "state.pickle"
		#self.state_file = self.cfg.get_config_dir_full_path() + self.state_file
		
		self.cmode = False # command mode
		self.tmode = False # talking mode (no need to prefix /say)
		self.clinepos = 4
		self.command = ""
		self.context = "int" # context in which command is executed
		curses.curs_set(False)  # @UndefinedVariable
		self.terminate = 0
		self.dlog = DebugLog(self.wl)
		
		self.autojoin()

		#self.restore_state()
		
	def readconfig(self):
		self.settings = self.cfg.getSettings()

	# FIXME: context not saved, ConfigParser limited to one string (one thread)
	# FIXME: key value should actually assign values to keys {'threadno': 12345, 'board': 'int'} 
	# TODO threadno should be a string to search the catalog for
	# on multiple results make a selectable catalog list 
	def autojoin(self):
		try:
			threads = self.cfg.list("autojoin_threads")
			if (threads):
				for kv in json.loads(threads):
					self.dlog.msg(str(kv.items()[0][0]))
					board = kv.items()[0][0]
					thread = kv.values()[0]
					self.dlog.msg("Joining thread: >>>" + board + "/" + thread)
					self.wl.join_thread(board, thread)
		except Exception:
			pass
		
		
	def setting_list(self, key):
		try:
			listing = self.cfg.list(key)
			self.dlog.msg("Values for " + key + ": " + str(listing))
		except:
			raise
		
		
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
	
	def clear_cmdinput(self):
		# save current position 
		(y, x) = self.stdscr.getyx()
		
		# clear line
		self.stdscr.move(self.screensize_x-1, 0)
		self.stdscr.clrtoeol()
		self.stdscr.addstr("[x] ")
		
		# redraw active window
		#active_window = self.wl.get_active_window_ref()
		# ...
		
		# restore position
		self.stdscr.move(y, x)
	
	# Save joined threads to file in order to restore on next start	
	# TODO Just restoring the BoardPads doesn't currently restore the Bars 
	# FIXME: this is a mess, either delete or come up with a better concept
# 	def save_state(self):
# 		self.dlog.msg("Saving window state.")
# 		try:
# 			with open(self.state_file, "wb") as fh:
# 				for window in self.wl.windowList:
# 					self.dlog.msg("Iterating " + str(window))
# 					if isinstance(window, BoardPad):
# 				#	self.dlog.msg("Saving BoardPad")
# 						pickle.dump(window.threadno, fh)
# 						self.dlog.msg("Window state saved.")
# 		except Exception as err:
# 			self.dlog.msg("Could not save window state: " + str(err))
# 			raise
		
					
# 	def restore_state(self):
# 		try:
# 			with open(self.state_file, "rb") as fh:
# 				for threadno in pickle.load(fh):
# 					self.dlog.msg("Restored thread: " + str(threadno))
# 					self.command = "join " + str(threadno)
# 					self.exec_com()
# 		except Exception as err:
# 			self.dlog.msg("Could not restore window state: " + str(err))
# 			pass
				

	def exec_com(self):
		
		cmd_args = self.command.split()
		
		if len(cmd_args) == 0:
			return

		
		self.dlog.msg("Trying to execute command: " + self.command, 5)
		
		# Text input
		if re.match("say", self.command):
			self.clear_cmdinput()
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
			

		# /captcha: show (0 args) and solve captcha (>0 args)
		elif re.match(r"^captcha", self.command):
			
			active_window = self.wl.get_active_window_ref()
			
			try:
				if len(cmd_args) == 1:
					try:
						active_window.display_captcha()
						return
					except Exception as err:
						self.dlog.msg("Can't display captcha: " + str(err))
						return
			except Exception as err:
				self.dlog.msg("Can't display captcha: " + str(err))
				return
				
			self.clear_cmdinput()
				
			try:
				cmd_args.pop(0)
				captcha = " ".join(cmd_args)
				active_window.set_captcha(str(captcha))
			except Exception as err:
				self.dlog.msg("Can't submit captcha: " + str(err))
				pass
			
		elif re.match("autojoin", self.command):
			try:
				setting_key = "autojoin_threads"
				
				cmd_args.pop(0)
				key = cmd_args.pop(0) # also for single argument commands 
				
				if key == "clear":
					self.cfg.clear(setting_key)
					self.cfg.writeConfig()
					
				if key == "save":
					# Iterate over window list
					self.cfg.clear(setting_key)
					for window in self.wl.get_window_list():
						
						if isinstance(window, BoardPad):
							# Add board and threadno of every BoardPad to config
							self.cfg.add(setting_key, window.board, window.threadno)
					self.cfg.writeConfig()
				
				if len(cmd_args) != 2:
					self.dlog.msg("Listing autojoins - valid parameters: add <board> <thread>, remove <board> <thread>, list")
					self.setting_list(setting_key)
					return
				
				board = cmd_args.pop(0)
				threadno = cmd_args.pop(0)
				
				if key == "add":
					self.cfg.add(setting_key, board, threadno)
				elif key == "remove":
					self.cfg.remove(setting_key, board, threadno)
				else:
					self.dlog.msg("Valid parameters: add <board> <thread>, remove <board> <thread>, list")
					
			except:
				self.dlog.msg("Exception in CommandInterpreter.exec_com() -> autojoin")
				raise
				
		
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
					self.dlog.msg("Set " + key + " = " + val)
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
		curses.mousemask(-1)  # @UndefinedVariable
		while True:
						
			if self.terminate is 1:
				self.dlog.msg("CommandInterpreter: self.terminate is 1")
				#self.save_state()
				break
			
			
			# moves cursor to current position 
			#self.stdscr.move(self.screensize_x-1, self.clinepos)
			if self.cmode:
				curses.curs_set(True)  # @UndefinedVariable
				
			c = self.stdscr.getkey()
			
			if c == "KEY_RESIZE":
				self.dlog.msg("CommandInterpreter: KEY_RESIZE")
				self.on_resize()
				continue
			
			if self.cmode:
				curses.curs_set(True)  # @UndefinedVariable
	
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
						curses.curs_set(False)  # @UndefinedVariable
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
				self.clear_cmdinput()
				self.stdscr.addstr(self.screensize_x-1, 0, "[/] ")
				self.cmode = True
				
			# Text input mode
			elif c == u't':
				self.clear_cmdinput()
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
				mouse_state = curses.getmouse()[4]  # @UndefinedVariable
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
