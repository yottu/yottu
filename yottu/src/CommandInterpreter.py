# -*- coding: utf-8 -*-

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
from urllib2 import HTTPError
from PostReply import PostReply

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
		self.captcha_mask = False # Query captcha input
		
		self.clinepos = 4
		self.command = ""
		self.command_cached = None
		self.context = "int" # context in which command is executed
		self.postno_marked = None # Currently marked postno
		
		curses.curs_set(False)  # @UndefinedVariable
		self.terminate = 0
		self.dlog = DebugLog(self.wl)
		
		self.command_history = []
		self.command_history_pos = -1
		
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
		try:
			self.stdscr.clear()
			self.stdscr.refresh()
			self.screensize_x, self.screensize_y = self.stdscr.getmaxyx();
			
			self.wl.on_resize()
	
			self.stdscr.move(self.screensize_x-1, 0)
			self.stdscr.clrtoeol()
			if self.command != "":
				if self.tmode:
					self.stdscr.addstr(self.screensize_x-1, 0, "[>] " + self.command[4:])
				elif self.cmode:
					self.stdscr.addstr(self.screensize_x-1, 0, "[/] " + self.command)
			else:
				self.stdscr.addstr(self.screensize_x-1, 0, "[^] ")
			self.stdscr.move(self.screensize_x-1, self.clinepos)
		except Exception as err:
			self.dlog.msg("CommandInterpreter.on_resize(): " + str(err))

		

		

		
	def parse_param(self, string):
		''' return list from whitespace separated string '''
		''' TODO: Implement validity matching logic '''
		return string.split()
	
	def show_image_marked(self, ext=False, options=[]):
		try:
			if self.postno_marked:
				if ext is True:
					self.wl.get_active_window_ref().show_image(self.postno_marked, True, options)
				else:
					self.wl.get_active_window_ref().show_image(self.postno_marked)
		except HTTPError as err:
				self.wl.get_active_window_ref().sb.setStatus("Image: " + str(err.code))
		except Exception as err:
			self.dlog.msg("CommandInterpreter.show_image_marked(): " + str(err))

	
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

	def query_captcha(self):
		self.command = ""
		self.clear_cmdinput("c")
		self.cmode = True
		self.cstrout("captcha ")

	def clear_cmdinput(self, status_char):
		# save current position 
		#(y, x) = self.stdscr.getyx()
		
		# clear line
		cmd_text = "[" + status_char + "] "
		self.stdscr.move(self.screensize_x-1, 0)
		self.stdscr.clrtoeol()
		self.stdscr.addstr(cmd_text)
		self.clinepos = len(cmd_text)
		
		
		# redraw active window
		#active_window = self.wl.get_active_window_ref()
		# ...
		
		# restore position
		#self.stdscr.move(y, x)
		
	def cout(self, c):
		self.stdscr.addstr(self.screensize_x-1, self.clinepos, c)
		self.command += c
		self.clinepos += 1
		
	def cstrout(self, text):
		self.stdscr.addstr(self.screensize_x-1, self.clinepos, text)
		self.command += text
		self.clinepos += len(text)


	def cmd_history(self, count):
		''' output cmd from history and save position+count '''
		
		#self.dlog.msg(str(self.command_history))
		
		# cache unfinished command in buffer if history is searched while writing
		if len(self.command) and (self.command_history_pos == len(self.command_history)):
			#self.dlog.msg("Caching at pos " + str(self.command_history_pos) + " Command: " + self.command)
			#self.dlog.msg("len of history: " + str(len(self.command_history)))
			if self.command != "say ":
				self.command_cached = self.command
		
		
		
		try:
			newPos = self.command_history_pos + count
			if newPos >= 0 and newPos <= len(self.command_history):
				self.command = ""
				
				self.command_history_pos += count

				# on end reached output cached command if it exists				
				if newPos == len(self.command_history):
					if self.command_cached is not None:
						cmd = self.command_cached
						self.command_cached = None
					else:
						cmd = ""
						
				else:
					cmd = self.command_history[self.command_history_pos]
				
				self.clear_cmdinput(str(self.command_history_pos))
				self.clinepos = 4

				#cmd = self.command
				#self.command = ""
				self.cstrout(cmd)
				

				
		except:
			pass
	
	def cmd_history_add(self):
		
		# remove first element if history contains more than 50 elements
		if len(self.command_history) > 50:
			self.command_history.pop(0)
		self.command_history_pos += 1
		self.command_history.append(self.command)
		self.command_history_pos = len(self.command_history)
				

	def exec_com(self):
		
		# add to command history 
		self.cmd_history_add()
		
		cmd_args = self.command.split()
		
		if len(cmd_args) == 0:
			return

		
		self.dlog.msg("Trying to execute command: " + self.command, 5)
		
		# Text input
		if re.match("say", self.command):
			self.clear_cmdinput("x")
			cmd_args.pop(0)
			comment = " ".join(cmd_args)
			# Check if executed on a BoardPad
			active_window = self.wl.get_active_window_ref()
			if not isinstance(active_window, BoardPad):
				self.dlog.msg("/say must be used in a thread.")
				return
			
			active_thread_OP = active_window.threadno
			self.dlog.msg("Creating post on " + str(active_window.board) + "/"
						+ str(active_thread_OP) + " | Comment: " + str(comment))
			try:
				active_window.post_prepare(str(comment))
				self.captcha_mask = True
			except Exception as err:
				self.dlog.msg("CommandInterpreter: BoardPad.set_captcha(): " + str(err))

			

		# /captcha: show (0 args) and solve captcha (>0 args)
		elif re.match(r"^captcha", self.command):
			
			active_window = self.wl.get_active_window_ref()
			
			try:
				if len(cmd_args) == 1:
					active_window.display_captcha()
					return

			except Exception as err:
				self.dlog.msg("Can't display captcha: " + str(err))
				return
				
			self.clear_cmdinput("c")
				
			try:
				cmd_args.pop(0)
				captcha = " ".join(cmd_args)
				active_window.set_captcha(str(captcha))
				active_window.post_submit()
				active_window.update_thread()
			except PostReply.PostError as err:
				active_window.sb.setStatus(str(err))
			except Exception as err:
				self.dlog.msg("Can't submit captcha: " + str(err))
				
				curses.ungetch('/')  # @UndefinedVariable
				#self.cmode
				#self.cmd_history(-1)
				return
			
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
					self.dlog.msg("Listing autojoins - valid parameters: add <board> <thread>, remove <board> <thread>, list, save")
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
				
		elif re.match("clear", self.command):
			# FIXME this might be both, too much and not enough clearing/redrawing
			self.stdscr.clear()
			self.clear_cmdinput("^")
			self.wl.get_active_window_ref().draw()
			self.on_resize()
					
		elif re.match("quit", self.command):
			self.terminate = 1
			
		else:
			self.dlog.msg("Invalid command: " + self.command)
		


	def line_marked(self):
		try:
			postno = self.wl.get_active_window_ref().get_post_no_of_marked_line()
			
			# FIXME postno_marked should be an attribute of bp
			self.postno_marked = postno
			if postno:
				self.wl.get_active_window_ref().show_image_thumb(self.postno_marked)
			

		except Exception as err:
			self.dlog.msg("CommandInterpreter.line_marked(): " + str(err))
	
	
	def run(self):
		'''Loop that refreshes on input'''
		# Enable mouse events
		# TODO returns a 2-tuple with mouse capabilities that should be processed
		curses.mousemask(-1)  # @UndefinedVariable
	
# 		while True:
# 					#test
# 			try:
# 				inputstr = ''
# 				self.stdscr.nodelay(0)
# 				c = self.stdscr.getch()
# 				self.dlog.msg("c: " + str(c))
# 				self.stdscr.nodelay(1)
# 				while True:
# 					if c > 256:
# 						curses.ungetch(c)
# 						c = self.stdscr.getkey()
# 						self.dlog.msg("c (getkey): " + str(c))
# 						break
# 					inputstr += chr(c)
# 					c = self.stdscr.getch()
# 					self.dlog.msg("also c: " + str(c))
# 					self.dlog.msg("inputstr:  " + inputstr)
# 					if c == -1:
# 						break
# 				
# 			except Exception as err:
# 				self.dlog.msg("Exception: " + str(err))
# 				pass
			
			#self.dlog.msg("Char: " + str(len(c)))
#			continue
			
#			self.dlog.msg("I should not be here.")
		
		try:
			while True:			
					
				if self.terminate is 1:
					self.dlog.msg("CommandInterpreter: self.terminate is 1")
					#self.save_state()
					break
				
				
				# moves cursor to current position 
				#self.stdscr.move(self.screensize_x-1, self.clinepos)
				if self.cmode:
					curses.curs_set(True)  # @UndefinedVariable
					
				
				if self.captcha_mask:
					self.query_captcha()
					self.captcha_mask = False
					continue	
				
				#c = self.stdscr.getkey()
				
				inputstr = ''
				self.stdscr.nodelay(0)
				c = self.stdscr.getch()
				#self.dlog.msg("c: " + str(c))
				self.stdscr.nodelay(1)
				while True:
					if c > 256:
						curses.ungetch(c)  # @UndefinedVariable
						c = self.stdscr.getkey()
						#self.dlog.msg("c (getkey): " + str(c))
						break
					inputstr += chr(c)
					c = self.stdscr.getch()
					#self.dlog.msg("also c: " + str(c))
					#self.dlog.msg("inputstr:  " + str(inputstr))
					if c == -1:
						break

				if len(inputstr) == 1:
					c = inputstr
				#elif len(inputstr) > 1:
				#	c = -2
				
				# Catch resize
				if c == "KEY_RESIZE":
					self.dlog.msg("CommandInterpreter: KEY_RESIZE")
					self.on_resize()
					continue
				
				# Scroll
				elif c == 'KEY_HOME':
					self.wl.home()
					continue
				elif c == 'KEY_END':
					self.wl.end()
					continue
				elif c == 'KEY_PPAGE':
					self.wl.moveup(5)
					continue
				elif c == 'KEY_NPAGE':
					self.wl.movedown(5)
					continue

					
				### Mouse control ###	
				elif c == "KEY_MOUSE":
					try:
						# pointer id, x, y, unused, action
						(mid, x, y, z, bstate) = curses.getmouse()  # @UndefinedVariable
						#bstate = curses.getmouse()[4]  # @UndefinedVariable
						self.dlog.msg("getmouse(): id: "+ str(mid) +" x: "+str(x)+" y: "+str(y)+" z: "+str(z)+" bstate: "+ str(bstate), 5)
						#self.stdscr.addstr(str(bstate))
						
						# Scroll on mouse wheel down
						if int(bstate) == 134217728:
							if y == 0:
								self.wl.next()
							else:
								self.wl.movedown(5)
							
						# Scroll on mouse wheel up (curses.BUTTON4_PRESSED)
						elif int(bstate) == 524288:
							if y == 0:
								self.wl.prev()
							else:
								self.wl.moveup(5)
						
						# Left mouse button clicked (Mark line)
						elif int(bstate) == curses.BUTTON1_CLICKED:  # @UndefinedVariable
							self.wl.get_active_window_ref().markline(y+1)
							
							# FIXME generalize for all pads
							try: 
								self.line_marked()
							except:
									pass
							
							pass
						
						elif int(bstate) == curses.BUTTON3_CLICKED:  # @UndefinedVariable
							self.show_image_marked()
							
					except Exception as err:
						self.dlog.msg("CommandInterpreter -> c == KEY_MOUSE: ", + str(err))
						pass
					continue			
				### End of mouse control ###
				
		
				### Keys only valid in cmode ###
				elif self.cmode or self.tmode:
					curses.curs_set(True)  # @UndefinedVariable
					
					try:	
						# Handle keycaps, FIXME: suppress output of C-M?
						if re.match("^KEY_\w+$", c):
							if c == "KEY_BACKSPACE":
								
								# Delete last character after, len("[/] ") == 4 
								if self.clinepos > 4:
									self.command = self.command[:-1]
									self.clinepos = self.clinepos - 1
									self.stdscr.addstr(self.screensize_x-1, self.clinepos, " ")
									self.stdscr.move(self.screensize_x-1, self.clinepos)
							
							elif c == "KEY_UP":
								self.cmd_history(-1)
									
							elif c == "KEY_DOWN":
								self.cmd_history(1)
								
							continue
					except:
						pass
					
					# On Enter or ESC (27)
					try:
						# Need to avoid the Exception for long unicode strings
						if len(inputstr) == 1 and c != -1 and (c == u'\n' or ord(c) == 27):
							if c == u'\n':
								# Only execute if command is not empty
								if len(self.command) and self.command is not "say ":
									self.exec_com()

						
							# reset history position counter
							self.command_history_pos = len(self.command_history)
							self.command_cached = None		
							self.cmode = False
							self.tmode = False
							self.command = ""
							self.clear_cmdinput("^")
							#self.stdscr.addstr(self.screensize_x-1, 0, "[T] ")
							curses.curs_set(False)  # @UndefinedVariable

						# If user input is not \n or ESC write it to command bar
						else:
							if c != -1:
								self.cout(c)
								
							else:
								self.cstrout(inputstr)
							
						
					except Exception as e:
						self.dlog.excpt(e)
					
					continue
				### End of cmode input ###
				
				elif c == 'KEY_UP':
					self.wl.moveup()
				
				elif c == 'KEY_DOWN':
					self.wl.movedown()
							
				# Quit application
				elif c == u'q':
					self.terminate = 1
				
				# Command input mode
				elif c == u'/' or c == u'i':
					self.clear_cmdinput("/")
					#self.stdscr.addstr(self.screensize_x-1, 0, "[/] ")
					self.clinepos = 4
					self.cmode = True
					
				# Text input mode
				elif c == u't':
					self.clear_cmdinput(">")
					#self.stdscr.addstr(self.screensize_x-1, 0, "[>] ")
					self.clinepos = 4
					self.command = "say "
					
					try:
						if self.postno_marked is not None:
							quote = ">>" + self.postno_marked + " "
							self.cstrout(quote)
					except:
						pass
					
					self.tmode = True
					
				# View image on selected post using w3mimg
				elif c == u'v':
					self.show_image_marked()
				elif c == u'f':
					# View image in external viewer
					self.show_image_marked(True)
				elif c == u'F':
					self.show_image_marked(True, ['--fullscreen'])
				
				elif c == u'w':
					self.wl.moveup()
				elif c == u's':
					self.wl.movedown()
				
				# Refresh thread	
				elif c == u'r':
					try:
						self.wl.get_active_window_ref().update_thread()
					except:
						continue
					
					
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
				
				else:
					#self.dlog.msg("Unbound key: " + str(c))
					continue
				
		except Exception as err:
			self.dlog.msg("CommandInterpreter.run(): " + str(err))
			pass
	# End of run loop
