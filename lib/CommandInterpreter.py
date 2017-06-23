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
from ConfigParser import NoOptionError
import sys
import unicodedata
import subprocess
from __builtin__ import isinstance
from CatalogPad import CatalogPad
import time

class CommandInterpreter(threading.Thread):
	def __init__(self, stdscr, wl):
		
		self.stdscr = stdscr
		self.wl = wl
		self.wl.ci = self
		self.screensize_y = 0
		self.screensize_x = 0
		
		self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
		self.stdscr.addstr(self.screensize_y-1, 0, "[^] ")
		
		
		Thread.__init__(self)
		
		self.cfg = Config.Config(".config/yottu/", "config")
		
		# For Saving/Restoring window state #FIXME
		#self.state_file = "state.pickle"
		#self.state_file = self.cfg.get_config_dir_full_path() + self.state_file
		
		self.cmode = False # command mode
		self.tmode = False # talking mode (no need to prefix /say)
		self.captcha_mask = False # Query captcha input
		
		self.clinepos = 4
		self.command = ""
		self.command_pos = 0 # position of cursor in command
		self.command_cached = None
		self.context = "int" # context in which command is executed # Overwritten by readconfig()
		self.postno_marked = None # Currently marked postno
		self.filename = (None, None) # Tuple holding path and ranger mode bool
		self.time_last_posted = 0
		
		curses.curs_set(False)  # @UndefinedVariable
		self.terminate = 0
		self.dlog = DebugLog(self.wl, debugLevel=3)
		
		self.command_history = []
		self.command_history_pos = -1
		
		self.nickname = ""
		self.readconfig()
		
		self.autojoin()
		
		#self.restore_state()
		
	def readconfig(self):
		try:
			self.cfg.readConfig()
			
			self.context = self.cfg.get("default_context")
			self.nickname = self.cfg.get("nickname")
			self.wl.set_nickname(self.nickname)

		
		except KeyError or NoOptionError or ValueError as err:
			self.dlog.warn(err, 3)
			pass
			
		except Exception as err:
			self.dlog.excpt(err, 3, "in " + str(type(self)) + " function: " + str(sys._getframe().f_code.co_name))
			raise
		
		finally:
			# Set defaults
			if not self.context: self.context = "g"
			if not self.nickname: self.wl.set_nickname(None)
		
	# FIXME: context not saved, ConfigParser limited to one string (one thread)
	# FIXME: key value should actually assign values to keys {'threadno': 12345, 'board': 'int'} 
	# TODO threadno should be a string to search the catalog for
	# on multiple results make a selectable catalog list 
	def autojoin(self):
		try:
			threads = self.cfg.get("autojoin_threads")
			if (threads):
				for kv in json.loads(threads):
					#self.dlog.msg(str(kv.items()[0][0]))
					board = kv.items()[0][0]
					thread = kv.values()[0]
					self.dlog.msg("Joining thread: >>>/" + board + "/" + thread)
					self.wl.join_thread(board, thread)
		except Exception:
			pass
		
		
	def setting_list(self, key):
		try:
			listing = self.cfg.get(key)
			self.wl.compadout("Values for " + key + ": " + str(listing))
		except:
			raise
		
		
	def on_resize(self):
		try:
			self.stdscr.clear()
			self.stdscr.refresh()
			self.screensize_y, self.screensize_x = self.stdscr.getmaxyx();
			
			self.wl.on_resize()
	
			self.stdscr.move(self.screensize_y-1, 0)
			self.stdscr.clrtoeol()
			if self.command != "":
				if self.tmode:
					self.stdscr.addstr(self.screensize_y-1, 0, "[>] " + self.command[4:])
				elif self.cmode:
					self.stdscr.addstr(self.screensize_y-1, 0, "[/] " + self.command)
			else:
				self.stdscr.addstr(self.screensize_y-1, 0, "[^] ")
			self.stdscr.move(self.screensize_y-1, self.clinepos)
		except Exception as err:
			self.dlog.msg("CommandInterpreter.on_resize(): " + str(err))

		

		

		
	def parse_param(self, string):
		''' return list from whitespace separated string '''
		''' TODO: Implement validity matching logic '''
		return string.split()
	
	def show_image_marked(self, **kwargs):
		try:
			if self.postno_marked:
					self.wl.get_active_window_ref().show_image(self.postno_marked, **kwargs)
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
		self.command_pos = 0
		self.clear_cmdinput("c")
		self.cmode = True
		self.cstrout("captcha ")

	def clear_cmdinput(self, status_char="^"):
		# save current position 
		#(y, x) = self.stdscr.getyx()
			
		# clear line
		cmd_text = "[" + status_char + "] "
		self.stdscr.move(self.screensize_y-1, 0)
		self.stdscr.clrtoeol()
		self.stdscr.addstr(cmd_text)
		self.clinepos = len(cmd_text)
		
		
		# redraw active window
		#active_window = self.wl.get_active_window_ref()
		# ...
		
		# restore position
		#self.stdscr.move(y, x)

	def attach_file(self):
		''' start ranger to select filename '''
		#import ranger
		#curses.endwin()
		#foo = ranger.main()
		
		filename = "/tmp/file"
		
		# Just toggle the file for now
		if self.tmode:
			if self.filename[0]:
				self.filename = (None, None)
				
				(y, x) = self.stdscr.getyx()
				self.stdscr.move(self.screensize_y-1, 0)
				self.stdscr.addstr("[>] ")
				#self.wl.get_active_window_ref().sb.setStatus("File: None")
				self.stdscr.move(y, x)
			else:
				self.filename = (filename, True)
				(y, x) = self.stdscr.getyx()
				self.stdscr.move(self.screensize_y-1, 0)
				self.stdscr.addstr("[F] ")
				self.stdscr.move(y, x)
				#self.wl.get_active_window_ref().sb.setStatus("File: " + str(filename)) 
			pass
		
	def cstrout_right(self):
		# split right part of command by newlines into cmd array
		cmd_right = self.command[self.command_pos-1:].split("\n")
		
		# output command and substitute \n for ¬ character
		cmd_right_pos = self.clinepos
		for i, line in enumerate(cmd_right):
			self.stdscr.addstr(self.screensize_y-1, cmd_right_pos, line)
			cmd_right_pos += len(line)
			try:
				if cmd_right[i+1]:
					self.stdscr.addstr(self.screensize_y-1, cmd_right_pos, "¬")
					cmd_right_pos+=1
			except IndexError:
				pass
		
	def cout(self, c, command_add=True):
		try:
			
			if command_add:
				
				# FIXME if command_pos is not at the end
				if self.command_pos != len(self.command):
					self.command = self.command[0:self.command_pos] + c + self.command[self.command_pos:]

					# split right part of command by newlines into cmd array
					cmd_right = self.command[self.command_pos:].split("\n")
					
					# output command and substitute \n for ¬ character
					cmd_right_pos = self.clinepos
					for i, line in enumerate(cmd_right):
						self.stdscr.addstr(self.screensize_y-1, cmd_right_pos, line)
						cmd_right_pos += len(line)
						try:
							cmd_right[i+1] # throws IndexError
							self.stdscr.addstr(self.screensize_y-1, cmd_right_pos, "¬")
							cmd_right_pos+=1
						except IndexError:
							pass
						#self.stdscr.addstr(self.screensize_x-1, self.clinepos, self.command[self.command_pos-1:])
				else:
					self.command += c
					
			self.stdscr.addstr(self.screensize_y-1, self.clinepos, c)
			self.command_pos += 1
							
			if unicodedata.east_asian_width(c.decode('utf-8')) is 'W':
				self.clinepos += 2
# 				(y, x) = self.stdscr.getyx()
# 				self.stdscr.move(self.screensize_y-1, 0)
# 				self.stdscr.addstr("[ｱ]")
# 				self.stdscr.move(y, x)
			else:
				self.clinepos += 1
# 				(y, x) = self.stdscr.getyx()
# 				self.stdscr.move(self.screensize_y-1, 0)
# 				self.stdscr.addstr("[>]")
# 				self.stdscr.move(y, x)

# 			tmp_debug = self.command
# 			self.dlog.msg("--DEBUG:     COMMAND: " + tmp_debug.replace("\n", "|"))
# 			self.dlog.msg("--DEBUG: CMD_POINTER: " + " "*(self.command_pos+1) + "^" + str(self.command_pos) + "/" + str(len(self.command)))
# 			self.dlog.msg("--DEBUG:   CHARACTER: " + self.command.decode('utf-8')[self.command_pos:self.command_pos+1])
									


		except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
			self.dlog.excpt(err, msg=" >>>in cout()")
		except Exception as err:
			self.dlog.excpt(err, msg=" >>>in cout()")
		
		
	def cstrout(self, text, command_add=True):
		try:
			
			for letter in text.decode('utf-8'):
				self.cout(letter.encode('utf-8'), command_add)
				
		except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
			self.dlog.excpt(err, msg=" >>>in cstrout()")
		except Exception as err:
			self.dlog.excpt(err, msg=" >>>in cstrout()")


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
				self.command_pos = 0
				
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
				

		except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
			self.dlog.excpt(err, msg=" >>>in cmd_history()")		
		except:
			pass
	
	def cmd_history_add(self):
		
		# remove first element if history contains more than 50 elements
		if len(self.command_history) > 50:
			self.command_history.pop(0)
		self.command_history_pos += 1
		self.command_history.append(self.command)
		self.command_history_pos = len(self.command_history)


	def line_marked(self):
		try:
			activeWindow = self.wl.get_active_window_ref()
			postno = activeWindow.get_post_no_of_marked_line()
			
			# FIXME postno_marked should be an attribute of bp
			self.postno_marked = postno
			if postno and isinstance(activeWindow, BoardPad):
				# Don't display help when command line is in usage
				if not self.cmode:
					image_filename = activeWindow.tdict[int(self.postno_marked)]['filename']
					post_is_me = activeWindow.tdict[int(self.postno_marked)]['marked']
					if post_is_me:
						mark = "un[m]ark"
					else:
						mark = "[m]ark"
					
					# generate help text
					help_text = "Post: " + mark + " as own"
					if image_filename:
						help_text = "Image: [v]iew, [f]eh/ext ([F]ullscreen), [b]g - " + help_text 

					# align right	
					help_text = (self.screensize_x-5-len(help_text))*" " + help_text
					
					self.stdscr.addstr(self.screensize_y-1, 4, help_text[:self.screensize_x-5] )

				self.wl.get_active_window_ref().show_image_thumb(self.postno_marked)
			elif postno and isinstance(activeWindow, CatalogPad):
				activeWindow.unmarkline()
				self.postno_marked = None
				self.wl.join_thread(activeWindow.board, postno)
				
				
				
			else:
				# Clear help message
				if not self.cmode:
					self.clear_cmdinput()
				
			

		except Exception as err:
			self.dlog.msg("CommandInterpreter.line_marked(): " + str(err))
	
				

	def exec_com(self):
		# add to command history 
		self.cmd_history_add()
		

		cmd_args = self.command.split()
		## FIXME don't re.match the entire command just use this:
		#cmd = cmd_args.pop(0)
		cmd_args_count = len(cmd_args) - 1
		
		if len(cmd_args) == 0:
			return

		
		self.dlog.msg("Trying to execute command: " + self.command, 5)
		
		# Text input
		if re.match("say", self.command):
			self.clear_cmdinput("x")
			cmd_args.pop(0)
			
			# cut off the "say " while keeping newlines
			comment = self.command[4:]
			
			# Check if executed on a BoardPad
			active_window = self.wl.get_active_window_ref()
			if not isinstance(active_window, BoardPad):
				self.dlog.msg("/say must be used in a thread.")
				return
			
			active_thread_OP = active_window.threadno
			self.dlog.msg("Creating post on >>>/" + str(active_window.board) + "/"
						+ str(active_thread_OP) + " | Comment: " + comment, 4)
			try:
				active_window.post_prepare(comment=comment, filename=self.filename[0], ranger=self.filename[1])
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
				response = active_window.post_submit() # throws PostError
				
				# Post succeeded
				if response == 200:
					active_window.update_thread()
					self.time_last_posted = int(time.time())
				elif isinstance(response, tuple):
					self.dlog.msg("Deferred comment: " + str(response), 3)
				else:
					self.dlog.msg("Could not post comment for " + str(response[1]) + " seconds.", 3)

			except PostReply.PostError as err:
				#active_window.update_thread()
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
				
			
				cmd_args.pop(0) # "autojoin"
				key = cmd_args.pop(0) # also for single argument commands 
				
				if cmd_args_count == 1:
						
					if key == "clear" and cmd_args_count == 1:
						self.cfg.clear(setting_key)
						
					elif key == "save" and cmd_args_count == 1:
						# Iterate over window list
						self.cfg.clear(setting_key)
						for window in self.wl.get_window_list():
							
							if isinstance(window, BoardPad):
								# Add board and threadno of every BoardPad to config
								self.cfg.add(setting_key, window.board, window.threadno)
					else:
						raise IndexError
					
					self.cfg.writeConfig()
					self.setting_list(setting_key)
					return
				
				board = cmd_args.pop(0)
				threadno = cmd_args.pop(0)
				
				if key == "add":
					self.cfg.add(setting_key, board, threadno)
				elif key == "remove":
					self.cfg.remove(setting_key, board, threadno)
				else:
					raise IndexError
					
			except IndexError as err:
				self.wl.compadout("Valid parameters: add <board> <thread>, remove <board> <thread>, list")
				self.setting_list(setting_key)
				return
			except:
				self.dlog.msg("Exception in CommandInterpreter.exec_com() -> autojoin")
				raise
		
		# Ignore feature
		elif re.match("ignore", self.command):
			if cmd_args_count == 0:
				self.wl.compadout("no ignore in list")
				return
				
			try:
				pass
			except:
				pass		
		
		# "Joining" a new thread
		elif re.match("join", self.command):
			
			try:
				joinThread = re.sub('>', '', cmd_args[1])
				
				board = False
				
				# Directly join thread if integer was given 
				if isinstance(joinThread, int):
					self.wl.join_thread(self.context, joinThread)
				
				else:
					joinThread = joinThread.split("/")
					search = joinThread.pop()
					
					if joinThread:
						board = joinThread.pop()
					
					self.wl.catalog(board or self.context, search)
				
			except IndexError:
				self.wl.compadout("Usage: /join <thread number>")
				self.wl.compadout("       /join <board/search string>")
				self.wl.compadout("       /join <search string>")
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
			self.readconfig()
			
		elif re.match("save", self.command):
			self.cfg.writeConfig()
			
		elif re.match("nick", self.command):
			cmd_args.pop(0)
			if cmd_args:
				self.wl.set_nickname(u' '.join(cmd_args))
		
		elif re.match("help", self.command):
			self.wl.compad.usage_help()
			
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
		
	
	def launch_file_brower(self, options=[]):
		try:
			cmd = "/usr/bin/xterm"
			# FIXME put hardcoded stuff into config
			default_options = ['-e', '/usr/bin/ranger --choosefile="/tmp/file" ~/img/']
			full_cmd = [cmd] + default_options + options 
			
			if isinstance(full_cmd, list):
				proc = subprocess.Popen(full_cmd)
				#output = proc.communicate()
			return
		except:
			raise
	
	
	# Toggle post as user's for easy (You)s 
	def claim_post_toggle(self):
		activeWindow = self.wl.get_active_window_ref()
		
		if self.postno_marked:
			tdict_marked = activeWindow.tdict[int(self.postno_marked)]['marked']
			
			if tdict_marked == False:
				
				activeWindow.tdict[int(self.postno_marked)]['marked'] = True
				activeWindow.sb.setStatus("Post marked.")
			else:
				activeWindow.tdict[int(self.postno_marked)]['marked'] = False
				activeWindow.sb.setStatus("Post no longer marked.")
	
	
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
				#self.stdscr.move(self.screensize_y-1, self.clinepos)
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
					try:
						
						# function key pressed (such as KEY_LEFT)
						# will be handled by getkey() instead
						if c > 256:
							curses.ungetch(c)  # @UndefinedVariable
							c = self.stdscr.getkey()
							#self.dlog.msg("c (getkey): " + str(c))
							break
						
						
						inputstr += chr(c)
						c = self.stdscr.getch()
# 						self.dlog.msg("also c: " + str(c))
# 						self.dlog.msg("inputstr:  " + str(inputstr))
						if c == -1:
							break
					except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
						self.dlog.excpt(err, msg=" >>>in CommandInterpreter.run() -> getch loop")
						break

				
				try:
					if len(inputstr) == 1:
						c = inputstr
				except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
					self.dlog.excpt(err, msg=" >>>in CommandInterpreter.run() -> assign c to inputstr")
					
					
				
				# Set keyname to easily parse control characters
				keyname = None	
				try: keyname = curses.keyname(ord(c))  # @UndefinedVariable
				except: pass
					
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
				
	
################ Keys only valid in cmode ################
				elif self.cmode or self.tmode:
					curses.curs_set(True)  # @UndefinedVariable
												
# 					tmp_debug = self.command
# 					self.dlog.msg("--DEBUG:     COMMAND: " + tmp_debug.replace("\n", "|"))
# 					self.dlog.msg("--DEBUG: CMD_POINTER: " + " "*(self.command_pos+1) + "^" + str(self.command_pos) + "/" + str(len(self.command)))
# 					self.dlog.msg("--DEBUG:   CHARACTER: " + self.command.decode('utf-8')[self.command_pos:self.command_pos+1])
# 					self.dlog.msg("--DEBUG: Pos: " + str(self.command_pos))
						
					# Catch Meta-Keys // tmode
					if c == -1 and len(inputstr) == 2 and ord(inputstr[0]) == 27:
						
						alt_key = str(inputstr[1])
						
						# Attach a file to post
						if str(alt_key) == 'f':
							self.attach_file()

						# Launch File Browser
						elif str(alt_key) == 'r':
							self.launch_file_brower()
							
						# Quit yottu
						elif str(alt_key) == 'q':
							self.terminate = 1
							
						# Insert \n into self.command and ¬ into stdscr.addstr 	
						elif str(alt_key) == "\n":
							# Output visible \n feedback without adding it to comment
							if self.command_pos != len(self.command):
								
								# Add newline character to self.command
								self.command = self.command[0:self.command_pos] + "\n" + self.command[self.command_pos:]
								
								tmp_cmd = self.command.replace('\n', '¬')
								self.dlog.msg(tmp_cmd)
								
								# clear command input line
								self.stdscr.addstr(self.screensize_y-1, 4, " "*len(self.command)) 
								
								# Draw newline replacement character on command line
								if self.tmode:
									# FIXME "say " is hardcoded into this range
									self.stdscr.addstr(self.screensize_y-1, 4, tmp_cmd[4:])
								elif self.cmode: 
									self.stdscr.addstr(self.screensize_y-1, 4, tmp_cmd)
								#self.stdscr.addstr(self.screensize_y-1, self.clinepos, cmd_tmp[self.command_pos:])
								self.cstrout("¬", command_add=False)

							else:
								self.command += "\n"
								self.cstrout("¬", command_add=False)
								#self.command = self.command.decode('utf-8')[:self.command_pos] + u"\n" + self.command.decode('utf-8')[self.command_pos:]
								
						# Alt+1-0, Alt+n, Alt+p 		
						elif self.change_window(alt_key):
							continue	
							


							#self.stdscr.move(self.screensize_y-1, self.clinepos)
							
						continue
					
					# Unicode character 'DELETE' 0x7f
					try:
						if ord(c) == 127:
							c = "KEY_BACKSPACE"
					except:
						pass
					
					
					try:	
						
						# Handle keycaps, FIXME: suppress output of C-M?
						#try: self.dlog.msg("--DEBUG: c/keynmae(c)/inputsr/cmd:" + str(c) + " | " + str(curses.keyname(ord(c))) + " | " + str(inputstr) + " | " + str(self.command))  # @UndefinedVariable
						#except: pass
						
						if keyname == '^W' or keyname == '^U':
							c = "KEY_BACKSPACE"
						if re.match("^KEY_\w+$", c):
								
							if c == "KEY_LEFT":
								self.adjust_clinepos(characters=-1)

							elif c == "KEY_BACKSPACE":	
							# FIXME keep self.command utf-8
								if keyname == '^W':
									# get len of word+space from self.command at command_pos
									self.backspace(-len(self.command.split(" ").pop(self.command[:self.command_pos].count(" ")))-1) 
								elif keyname == '^U':
									
									self.command = ""
									self.command_pos = 0
									
									if self.tmode:
										self.command = "say "
										self.command_pos = 4
										
									self.clinepos = 4
									self.clear_cmdinput('>')
								else:
									self.backspace()
								
								self.stdscr.move(self.screensize_y-1, self.clinepos)
								
							elif c == "KEY_RIGHT":
								self.adjust_clinepos(characters=1)
							
							elif c == "KEY_UP":
								self.cmd_history(-1)
									
							elif c == "KEY_DOWN":
								self.cmd_history(1)
														
							continue
																									
					except TypeError as err:
						self.dlog.excpt(err, msg="CommandInterpreter.run() -> cmode")
						#pass
					except Exception as err:
						self.dlog.excpt(err, msg="CommandInterpreter.run() -> cmode")
						

					
					# On Enter or ESC (27)
					# FIXME: 27 is just the control character sequence but it works in combination with c == -1
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
							self.command_pos = 0
							self.clear_cmdinput("^")
							
							# Reset attachment file and status
							self.filename = (None, None)
							#self.wl.get_active_window_ref().sb.setStatus("")
							#self.stdscr.addstr(self.screensize_y-1, 0, "[T] ")
							curses.curs_set(False)  # @UndefinedVariable

						# If user input is not \n or ESC write it to command bar
						else:
							if c != -1:
								self.cout(c)
								
							else:
								self.cstrout(inputstr)
							
						
					except Exception as e:
						self.dlog.excpt(e, msg=" >>>in CommandInterpreter.run() -> cmode")
					
					continue
################ End of keys only valid in cmode ################
				
				elif c == 'KEY_UP':
					self.wl.moveup()
				
				elif c == 'KEY_DOWN':
					self.wl.movedown()
											
				# Command input mode
				elif c == u'/' or c == u'i':
					self.clear_cmdinput("/")
					#self.stdscr.addstr(self.screensize_y-1, 0, "[/] ")
					self.clinepos = 4
					self.cmode = True
					
				# Text input mode
				elif c == u't':
					if not isinstance(self.wl.get_active_window_ref(), BoardPad):
						self.wl.compadout("/say must be used on a BoardPad")
						continue
					self.clear_cmdinput(">")
					#self.stdscr.addstr(self.screensize_y-1, 0, "[>] ")
					self.clinepos = 4
					self.command = "say "
					self.command_pos = len(self.command)
					
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
					self.show_image_marked(ext=True)
				elif c == u'F':
					self.show_image_marked(ext=True, fullscreen=True)
					
				# Set image as wallpaper	
				elif c == u'b':
					self.show_image_marked(ext=True, setbg=True)
				
				elif c == u'm':
					''' sets the (You) flag to replies of marked post '''
					self.claim_post_toggle()
				
				elif c == u'w':
					self.wl.moveup()
				elif c == u's':
					self.wl.movedown()
					
				elif c == u'D':
					self.wl.get_active_window_ref().download_images()
				# Refresh thread	
				elif c == u'r':
					try:
						self.wl.get_active_window_ref().update_thread()
					except:
						continue
				# Part
				elif c == u'x':
					if self.wl.get_active_window() != 0:
						self.wl.destroy_active_window()
						
				# Catalog
				elif c == u'c':
					self.wl.catalog(self.context)
					
					
				elif self.change_window(c):
					continue

				
				# Catch Meta-Keys // Global
				elif c == -1 and len(inputstr) == 2 and ord(inputstr[0]) == 27:
					
					alt_key = str(inputstr[1])
					
					# Quit yottu
					if alt_key == 'q':
						self.terminate = 1
						
					elif self.change_window(alt_key):
						continue
				
				else:
					self.dlog.msg("Unbound key: " + str(c))
					continue
				
		except (TypeError, UnicodeDecodeError) as err:
			self.dlog.excpt(err, msg=">>>in CommandInterpreter.run()")		
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in CommandInterpreter.run()")
			pass
	# End of run loop
	
	def backspace(self, characters=-1):
		''' deletes last character from self.command, clinepos--, redraws command line '''
				# offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
			
		if characters < 0:
			sign = -1
		else:
			sign = 1
		
		if abs(characters) >= len(self.command[offset:self.command_pos]):
			characters = len(self.command[offset:self.command_pos]) * sign
		
		try:
			# build new string with characters=n characters cut out
			
			cmd = self.command.decode('utf-8')[:self.command_pos+characters] + self.command.decode('utf-8')[self.command_pos:]
			self.command = cmd.encode('utf-8')
			
			# TODO this is probably not wide character safe, need to implement adjust_clinepos()
			self.clinepos += characters
			self.command_pos += characters
			

		except Exception as err:
			self.dlog.excpt(err, cn=self.__class__.__name__)
			return
		
		# clear command input line
		self.stdscr.addstr(self.screensize_y-1, 4, " "*(self.screensize_x-5)) 
		
		tmp_cmd = self.command.replace('\n', '¬')
		if self.tmode:
			# FIXME "say " is hardcoded into this range
			self.stdscr.addstr(self.screensize_y-1, 4, tmp_cmd[4:])
		elif self.cmode:
			self.stdscr.addstr(self.screensize_y-1, 4, tmp_cmd)
		
		
		
			
	def adjust_clinepos(self, characters=1):
		# Delete last character after, len("[/] ") == 4 
		if characters == 0:
			raise IndexError("Argument can not be zero.")
		
		
		# offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
			
		try:
			if characters < 0:
				shift = -1
			else:
				shift = 1
			
			for i in range(abs(characters)):
				if self.command_pos+shift < 0+offset or self.command_pos+shift > len(self.command):
					#self.dlog.msg("cmdlen: " + str(len(self.command)) + "Command Position: " + str(self.command_pos) + " clinepos: " + str(self.clinepos) + " shift: " + str(shift))
					break
				
				try:
					# Need to erase two single width characters for wide unicode characters
					if unicodedata.east_asian_width(self.command.decode('utf-8')[self.command_pos:self.command_pos+1]) is 'W':
						self.clinepos = self.clinepos + shift*2
						
					else:
						self.clinepos = self.clinepos + shift*1
				
				except TypeError:
					#self.dlog.msg("adjust_clinepos(): TypeError")
					self.clinepos = self.clinepos + shift*1
					
				self.command_pos += shift
					
			
		except Exception as err:
			self.dlog.excpt(err, msg=">>adjust_clinepos()", cn=self.__class__.__name__)
				
		self.stdscr.move(self.screensize_y-1, self.clinepos)
				
	
	def change_window(self, c):
		''' Defines keys to change the window with '''
		try:
			
			if c == u'n':
				self.wl.next()
				return True
				
			elif c == u'p':
				self.wl.prev()
				return True
			
			else: 
				for i in range(0, 9):
					if c == u''.join(str(i)):
						if i == 0:
							self.wl.raise_window(9)
							return True
						else:
							self.wl.raise_window(i-1)
							return True
						
			
		except Exception as err:
			self.dlog.excpt(err)
			raise
