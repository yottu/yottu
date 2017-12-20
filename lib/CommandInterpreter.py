# -*- coding: utf-8 -*-

'''
Created on Oct 5, 2015

'''
from threading import Thread
import curses
import threading
from DebugLog import DebugLog
from BoardPad import BoardPad
import re
import json
from urllib2 import HTTPError
from PostReply import PostReply
from ConfigParser import NoOptionError
from itertools import izip
import sys
import unicodedata
import subprocess
from __builtin__ import isinstance
from CatalogPad import CatalogPad
import time
import thread

class CommandInterpreter(threading.Thread):
	def __init__(self, stdscr, wl):
		
		self.stdscr = stdscr
		self.wl = wl
		self.wl.ci = self
		self.cfg = self.wl.cfg
		
		self.screensize_y = 0
		self.screensize_x = 0
		
		self.cmd_prefix = "[^] " # TODO use this + its len() instead of all the hardcoded stuff
		self.screensize_y, self.screensize_x = self.stdscr.getmaxyx()
		self.stdscr.addstr(self.screensize_y-1, 0, self.cmd_prefix)
		
		
		Thread.__init__(self)
		
		
		# For Saving/Restoring window state #FIXME
		#self.state_file = "state.pickle"
		#self.state_file = self.cfg.get_config_dir_full_path() + self.state_file
		
		self.cmode = False # command mode
		self.tmode = False # talking mode (no need to prefix /say)
		self.captcha_mask = False # Query captcha input
		
		self.clinepos = 4      # Visual position of the cursor in the command line
		self.cline_buffer = 4  # end of line buffer to wrap the text at when command line is filled
		self.command = u""      # user input
		self.command_pos = 0   # position of cursor in command
		
		self.input_page_size = self.screensize_x-self.cline_buffer-len(self.cmd_prefix)

		self.command_cached = None
		self.command_history = []
		self.command_history_pos = -1
		
		self.context = "int" # context in which command is executed # Overwritten by readconfig()
		self.postno_marked = None # Currently marked postno
		self.filename = (None, None) # Tuple holding path and ranger mode bool
		self.time_last_posted = 0
		
		curses.curs_set(False)  # @UndefinedVariable
		self.terminate = 0
		self.dlog = None
		
		self.nickname = ""
		
		self.socks_proxy_enabled =  False
		self.socks_proxy_port = None
		self.socks_proxy_addr = None
		
		self.readconfig()
		
		self.autojoin()
		

		
		#self.restore_state()
	
	# TODO implement correctly, test, use requests[socks] rather than monkeypatching	
	def use_socks_proxy(self):
		ESOCKS = False
		try:
			import socks
			import socket
		except:
			ESOCKS = True
			
		# If true this will route all connections through a socks5 proxy
		if self.socks_proxy_enabled:
			if ESOCKS:
				raise ImportError("Socks proxy is configured, but module socks is not installed. \
				Try running `pip install PySocks`")
			else:
				socks.set_default_proxy(socks.SOCKS5, self.socks_proxy_addr, int(self.socks_proxy_port))
				socket.socket = socks.socksocket
				self.dlog.msg("SOCKS5 proxy active: " + str(self.socks_proxy_addr) + ":" + str(self.socks_proxy_port))

		elif not ESOCKS:
			socks.set_default_proxy()
			socket.socket = socks.socksocket
			self.dlog.msg("SOCKS5 proxy inactive.")
		
	def readconfig(self):
		try:
			self.cfg.readConfig()
			
			self.dlog = DebugLog(self.wl, debugLevel=int(self.cfg.get("log.level")))
			
			self.context = self.cfg.get("board.default")
			
			self.nickname = self.cfg.get("user.name") or ""
			self.wl.set_nickname(self.nickname)
			
			self.socks_proxy_enabled = self.cfg.get("proxy.socks.enable")
			self.socks_proxy_port = self.cfg.get("proxy.socks.port")
			self.socks_proxy_addr = self.cfg.get("proxy.socks.address")
			
		except (KeyError, NoOptionError, ValueError) as err:
			self.dlog.warn(err, 3)
			
		except Exception as err:
			self.dlog.excpt(err, 3, "in " + str(type(self)) + " function: " + str(sys._getframe().f_code.co_name))
			raise
		
		finally:
			# Set defaults
			if not self.context: self.context = "g"
			if not self.nickname: self.wl.set_nickname(None)
			self.use_socks_proxy()
		
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
					self.dlog.msg("Rejoining thread: >>>/" + board + "/" + thread)
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
				self.stdscr.addstr(self.screensize_y-1, 0, self.cmd_prefix)
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
		cmd_text = "[" + status_char + "] "
		self.stdscr.move(self.screensize_y-1, 0)
		self.stdscr.clrtoeol()
		self.stdscr.addstr(cmd_text)
		self.clinepos = len(cmd_text)


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
		
		
	def cout(self, c, command_add=True, curses_attr=None): # TODO: -- mark --
		''' 
		Decodes byte sequence to UTF-8, outputs it on the command line and in self.command
		Also adjusts clinepos and command_pos
		Calls refresh_cmd_page() to redraw the output
		'''
		try:
			
			try:
				c = c.decode('utf-8') # e.g. 'R' == '\122'  -> u'R' == '\
			except Exception as err:
				self.excpt.warn(err, msg=">>>in cout()")
					
			# normally self.command should be updated with input
			if command_add:
				
				# rebuild command with inserted c if command_pos is not at the end 
				if self.command_pos != len(self.command):
					self.command = self.command[0:self.command_pos] + c + self.command[self.command_pos:]
				
				# else append it	
				else:
					self.command += c
			
			# Return if function was used to redraw command line
			if not c:
				return
			
			# need to reformat the command line if the text doesn't fit
			if self.clinepos-4 >= self.input_page_size:
				self.clear_cmdinput("+")
				self.clinepos = 4
				
				
			self.command_pos += len(c)
			
			# For character mapping see http://unicode.org/reports/tr11/#Recommendations
			# TODO think about handling 'A' since 4chan auto-converts it to Na
			if unicodedata.east_asian_width(c) == 'W' or unicodedata.east_asian_width(c) == 'F':
				self.clinepos += 2
				self.stdscr.addstr(self.screensize_y-1, 0, "[ｱ]", curses.A_BOLD) # @UndefinedVariable
			
			else:
				self.clinepos += 1
				if self.tmode:
					self.stdscr.addstr(self.screensize_y-1, 0, "[>]", curses.A_BOLD)  # @UndefinedVariable
				elif self.cmode and self.command_history_pos == len(self.command_history):
					self.stdscr.addstr(self.screensize_y-1, 0, "[/]", curses.A_BOLD)  # @UndefinedVariable


			#self.stdscr.move(self.screensize_y-1, self.clinepos)
			
			
			self.refresh_cmd_page()

# 			tmp_debug = self.command
# 			self.dlog.msg("--DEBUG:     COMMAND: " + tmp_debug.replace("\n", "|"))
# 			self.dlog.msg("--DEBUG: CMD_POINTER: " + " "*(self.command_pos+1) + "^" + str(self.command_pos) + "/" + str(len(self.command)))
# 			self.dlog.msg("--DEBUG:   CHARACTER: " + self.command.decode('utf-8')[self.command_pos:self.command_pos+1])


		except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
			self.dlog.excpt(err, cn=self.__class__.__name__, msg=" >>>in cout()")
		except Exception as err:
			self.dlog.excpt(err, cn=self.__class__.__name__, msg=" >>>in cout()")
		
		
	def cstrout(self, text, command_add=True):
		''' Expects a non-unicode string which will be looped character-wise into cout '''
		try:
			
			# Without decode/encode unicode charaters will be split up
			for letter in text.decode('utf-8'):
				self.cout(letter.encode('utf-8'), command_add)
				
		except (TypeError, UnicodeDecodeError, UnicodeEncodeError) as err:
			self.dlog.excpt(err, msg=" >>>in cstrout()")
		except Exception as err:
			self.dlog.excpt(err, msg=" >>>in cstrout()")

# 	def replace_command_input(self, new_cmd):
# 		''' Replace and redraw the visual representation of command without manipulating self.command '''
# 		# Save pointers
# 		clinepos_save = self.clinepos
# 		cmd_pos_save = self.command_pos
# 		
# 		# Calculate size/position of input line pages			
# 		self.input_page_size = self.screensize_x-self.cline_buffer-self.cmd_prefix 	# Size of input page
# 		input_page_pos = (self.command_pos)/self.input_page_size # current input page
# 		
# 		
# 		# Clear input line
# 		self.stdscr.move(self.screensize_y-1, 4)
# 		self.stdscr.clrtoeol()
# 		
# 		# Output visual command representation
# 		self.clinepos = 4 
# 		
# 		if self.tmode:	
# 			offset = 4
# 		else:
# 			offset = 0
# 			
# 		self.cstrout(self.command[input_page_pos*self.input_page_size or offset:((input_page_pos+1)*self.input_page_size)], command_add=False)
# 			
# 		
# 		# Restore pointers	
# 		self.clinepos = clinepos_save
# 		self.command_pos = cmd_pos_save
		


	def cmd_history(self, count):
		''' output cmd from history and save position+count '''
		
		#self.dlog.msg(str(self.command_history))
		
		# cache unfinished command in buffer if history is searched while writing
		if len(self.command) and (self.command_history_pos == len(self.command_history)):
			#self.dlog.msg("Caching at pos " + str(self.command_history_pos) + " Command: " + self.command)
			#self.dlog.msg("len of history: " + str(len(self.command_history)))
			if self.command != u"say ":
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
						cmd = u''.join(self.command_cached)
						self.command_cached = None
					else:
						cmd = u''
						
				else:
					cmd = self.command_history[self.command_history_pos]
				
				self.clear_cmdinput(str(self.command_history_pos))
				self.clinepos = 4

				self.cstrout(cmd.encode('utf-8'))
				#self.stdscr.addstr(self.screensize_y-1, 0, "[" + str(self.command_history_pos) + "]", curses.A_BOLD)
				

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
					image_filename = activeWindow.tdict[(int(self.postno_marked))]['filename']
					image_filename += activeWindow.tdict[int(self.postno_marked)]['ext']
					image_filesize = activeWindow.tdict[int(self.postno_marked)]['fsize']
					post_is_me = activeWindow.tdict[int(self.postno_marked)]['marked']
					if post_is_me:
						mark = "un[m]ark"
					else:
						mark = "[m]ark"
					
					# generate help text
					help_text = "Post: " + mark + " as own"
					if image_filename:
						help_text = " (" + str(image_filesize/1024) + "K) [v]iew, [f]eh/ext ([F]ullscreen), [b]g - " + help_text
						max_filename_chars = self.screensize_x-9-len(help_text)
						if max_filename_chars < len(image_filename):
							image_filename = image_filename[:max_filename_chars] + "(..)"
						help_text = image_filename + help_text 

					# align right	
					help_text = (self.screensize_x-5-len(help_text))*" " + help_text
					
					self.stdscr.addstr(self.screensize_y-1, 4, help_text[:self.screensize_x-5].encode('utf-8'), curses.A_DIM )  # @UndefinedVariable

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
		
		if self.command[0] == '/':
			self.command = self.command.lstrip('/')

		cmd_args = self.command.split()
		
		## FIXME don't re.match the entire command just use this:
		#cmd = cmd_args.pop(0)
		cmd_args_count = len(cmd_args) - 1
		
		if len(cmd_args) == 0:
			return

		
		self.dlog.msg("Trying to execute command: " + self.command.encode('utf-8'), 5)
		
		# Text input
		if re.match(u"say", self.command):
			self.clear_cmdinput("x")
			cmd_args.pop(0)
			
			# cut off the "say " while keeping newlines
			comment = self.command[4:]
			
			# Do nothing if comment is empty and no file is attached
			if not comment and not self.filename[1]:
				return
			
			# Check if executed on a BoardPad
			active_window = self.wl.get_active_window_ref()
			if not isinstance(active_window, BoardPad):
				self.dlog.msg("/say must be used in a thread.")
				return
			
			active_thread_OP = active_window.threadno
			self.dlog.msg("Creating post on >>>/" + str(active_window.board) + "/"
						+ str(active_thread_OP) + " | Comment: " + comment.encode('utf-8'), 4)
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
		elif re.match("ignore", self.command) or re.match("except", self.command):
			list_ = cmd_args.pop(0)
			
			if list_ == "ignore":
				filterlist = self.cfg.get('filter.ignore.list')
			elif list_ == "except":
				filterlist = self.cfg.get('filter.except.list')
		
			def list_filter(filterlist):
				self.wl.compadout(u"Filter rules for list " + list + u":")
				for i, rule in enumerate(json.loads(filterlist)):
					output = unicode(i)
					for section in json.loads(rule['filter']):
						output += u" " + section + ": " + unicode(json.loads(rule['filter'])[section])
					#for i, pattern in enumerate(json.loads(rule['pattern'])):
					#	if i%2 == 0:
					#		output += u" - pattern: " + unicode(pattern) + " in " + unicode(json.loads(rule['pattern'])[i+1])
					self.wl.compadout(output)
						
				
				
			if cmd_args_count == 0:
				if filterlist:
					list_filter(filterlist)
				else:	
					self.wl.compadout(u"There are no filter rules in list " + list)
				return
			else:
				# build dict from array
				i = iter(cmd_args)
				filter_dict = dict(izip(i, i))
				
				# add it to the filter list # TODO validation
				self.cfg.add('filter.' + list + ".list", 'filter', json.dumps(filter_dict))
				
			try:
				pass
			except:
				pass		
		
		# "Joining" a new thread
		elif re.match("join", self.command):
			
			try:
				joinThread = re.sub('>', '', cmd_args[1].encode('utf-8'))
				
				board = False
				
				# Directly join thread if integer was given
				
				try:
					self.wl.join_thread(self.context, int(joinThread))
					self.wl.compadout("Joining " + str(int(joinThread)))
				
				# Open catalog and search
				except:
					joinThread = joinThread.split("/")
					search = joinThread.pop()
					
					if joinThread:
						board = joinThread.pop()
						
					try:
						self.wl.join_thread(board, int(search))
					except:
						self.wl.catalog(board or self.context, search)
				
			except IndexError:
				self.wl.compadout("Usage: /join <thread number>")
				self.wl.compadout("       /join <board/search string>")
				self.wl.compadout("       /join <search string>")
			except:
				raise
			
		elif re.match("catalog", self.command) or re.match("search", self.command):
			mode = cmd_args.pop(0).encode('utf-8')
			
			cache_only = False
			if mode == u"search":
				cache_only = True
			
			
			
			self.dlog.msg("--DEBUG: mode is " + mode + " cache_only is " + str(cache_only))
			try:
				self.wl.compadout("Creating catalog for " + self.context)
				search = cmd_args[0].encode('utf-8')
				self.wl.catalog(self.context, search, cache_only=cache_only)
			except IndexError:
				self.wl.catalog(self.context, cache_only=cache_only)
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
			if self.cfg.get('config.autoload'):
				self.dlog.msg("Autoloading..")
				self.readconfig()
				
		elif re.match("mpv", self.command) \
		  or re.match("twitch", self.command) \
		  or re.match("youtube", self.command):
			
			try:
				site = cmd_args.pop(0)
				mpv_source = cmd_args.pop(0)
			except:
				self.wl.compadout("Usage: /mpv <source>")
				return
			
			# Check if executed on a BoardPad # FIXME this code is reused several times, make it a function
			active_window = self.wl.get_active_window_ref()
			if not isinstance(active_window, BoardPad):
				self.dlog.msg("/mpv must be used in a thread.")
				return
			
			active_window.video_stream(mpv_source, site=site)
			
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
					self.wl.compadout(pair[0] + ": " + str(pair[1]))
					
			# Else assign new value to setting, save & load if configured
			else:
				key = cmd_args[1]
				val = ' '.join(cmd_args[2:])
				try:
					self.cfg.set(key, val)
					self.dlog.msg("Set " + key + " = " + str(val))
					
					if self.cfg.get('config.autosave'):
						self.dlog.msg("Autosaving..")
						self.cfg.writeConfig()
					
						if self.cfg.get('config.autoload'):
							self.dlog.msg("Autoloading..")
							self.readconfig()
						
					
				except Exception as e:
					self.dlog.excpt(e)
					
		
		elif re.match("tw", self.command):
			try:
				arg = cmd_args.pop(1)
				
				if arg == "update":
					self.wl.compadout("ThreadWatcher: Updating ..")
					self.wl.tw.update()
				
			except IndexError:
				self.wl.compadout("ThreadWatcher: -Not Implemented- /tw update to force update")
					
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
			self.dlog.msg("Invalid command: " + self.command.encode('utf-8'))
		
	
	def launch_file_brower(self, options=[]):
		try:
			cmd = "/usr/bin/xterm"
			# FIXME put hardcoded stuff into config
			default_options = ['-e', '/usr/bin/ranger --choosefile="/tmp/file" ~/img/']
			full_cmd = [cmd] + default_options + options 
			
			if isinstance(full_cmd, list):
				subprocess.Popen(full_cmd)
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
				self.wl.tw.insert(activeWindow.board, self.postno_marked, activeWindow.threadno)
				self.wl.db.insert_post(activeWindow.board, activeWindow.threadno, self.postno_marked)
				activeWindow.sb.setStatus("Post marked.")
			else:
				activeWindow.tdict[int(self.postno_marked)]['marked'] = False
				self.wl.tw.remove(activeWindow.board, self.postno_marked, activeWindow.threadno)
				self.wl.db.delete_post(activeWindow.board, self.postno_marked)
				activeWindow.sb.setStatus("Post no longer marked.")
	
	

	
	
	def run(self):
		'''Loop that refreshes on input'''
		
		# Enable mouse events
		# TODO returns a 2-tuple with mouse capabilities that should be processed
		curses.mousemask(-1)  # @UndefinedVariable
		
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
					
				# Set keyname to easily parse CTRL characters
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
				
	
################ Keys only valid in cmode ################ TODO: -- mark --
				elif self.cmode or self.tmode:
					curses.curs_set(True)  # @UndefinedVariable
					
# 					try: 
# 						self.dlog.msg("--DEBUG: keyname(c): " + str(curses.keyname(ord(c))))  # @UndefinedVariable
# 						self.dlog.msg("--DEBUG: c/keynmae(c)/inputsr/cmd:" + str(c) + " | " + str(curses.keyname(ord(c))) + " | " + str(inputstr) + " | " + str(self.command))  # @UndefinedVariable
# 					except: pass
												
#					tmp_debug = self.command
#					self.dlog.msg("--DEBUG:     COMMAND: " + tmp_debug.replace("\n", "|"))
# 					self.dlog.msg("--DEBUG: CMD_POINTER: " + " "*(self.command_pos+1) + "^" + str(self.command_pos) + "/" + str(len(self.command)))
# 					self.dlog.msg("--DEBUG:   CHARACTER: " + self.command.decode('utf-8')[self.command_pos:self.command_pos+1])
# 					self.dlog.msg("--DEBUG: Pos: " + str(self.command_pos))
						
					# Catch Meta-Keys // tmode
					alt_key = None
					if c == -1 and len(inputstr) == 2 and ord(inputstr[0]) == 27:
						alt_key = str(inputstr[1])
						
						# Attach a file to post
						if str(alt_key) == 'F':
							self.attach_file()
							continue

						# Launch File Browser
						elif str(alt_key) == 'r':
							self.launch_file_brower()
							continue
							
						# Quit yottu
						elif str(alt_key) == 'q':
							self.terminate = 1
							continue
							
						# move cursor one word forward
						elif str(alt_key) == 'f':
							c = "KEY_RIGHT"
						
						# move cursor one word backward
						elif str(alt_key) == 'b':
							c = "KEY_LEFT"
							
						# Insert \n into self.command and \\ into stdscr.addstr 	
						elif str(alt_key) == "\n":
							# Output visible \n feedback without adding it to comment
							if self.command_pos != len(self.command):
								
								# Add newline character to self.command
								self.command = self.command[0:self.command_pos] + "\n" + self.command[self.command_pos:]
								self.adjust_clinepos(1)
								#self.command_pos += 1
								#self.clinepos += 1
								#self.refresh_cmd_page()
								
								#tmp_cmd = self.command.replace('\n', '\\')
								#self.replace_command_input(tmp_cmd)

							else:
								self.command += "\n"
								self.cstrout("\\", command_add=False)
							
							continue
								
						# Alt+1-0, Alt+n, Alt+p 		
						elif self.change_window(alt_key):
							continue	
							
							#self.stdscr.move(self.screensize_y-1, self.clinepos)
							
					
					# Unicode character 'DELETE' 0x7f
					try:
						if ord(c) == 127:
							c = "KEY_BACKSPACE"
					except:
						pass
					
					try:	
						
						if keyname == '^W' or keyname == '^U' or keyname == '^A' or keyname == '^E' or keyname == '^D':
							c = "KEY_BACKSPACE"
						if keyname == '^B':
							c = "KEY_LEFT"
						if keyname == '^F':
							c = "KEY_RIGHT"
							
						if c != -1 and re.match("^KEY_\w+$", c):
							
							# FIXME math
							# self.command word length before command_pos
							current_word_len_pre = len(self.command[:self.command_pos].split(" ").pop())
							if current_word_len_pre == 0:
								current_word_len_pre = len(self.command[:self.command_pos-1].split(" ").pop()) +1
							# word length at command_pos
							current_word_len = len(self.command.split(" ").pop(self.command[:self.command_pos].count(" ")))
							# word length after command_pos
							current_word_len_post = current_word_len - current_word_len_pre
							if current_word_len_post == 0:
								current_word_len_post = len(self.command.split(" ").pop(self.command[:self.command_pos+1].count(" "))) + 1
							

								
							if c == "KEY_LEFT":
								if alt_key:
									self.adjust_clinepos(-current_word_len_pre)
								else:
									self.adjust_clinepos(characters=-1)

							elif c == "KEY_BACKSPACE":	
							# FIXME keep self.command utf-8
								if keyname == '^W':
									self.backspace(-current_word_len_pre-1)
									
								elif keyname == '^D':
									self.backspace(1)
								
								# FIXME delete left part of cursor
								elif keyname == '^U':
									
									self.command = u""
									self.command_pos = 0
									
									if self.tmode:
										self.command = u"say "
										self.command_pos = 4
										
									self.clinepos = 4
									self.clear_cmdinput('>')
									
								# Move to left or right end of command input line	
								elif keyname == '^A' or keyname == '^E':
									self.command_pos = self.clinepos = 4

									if self.cmode:
										self.command_pos = 0 
										
									self.refresh_cmd_page()
									
									if keyname == '^E':
										
										self.adjust_clinepos(len(self.command)-self.command_pos)
										self.command_pos = len(self.command)
										self.refresh_cmd_page()
										
									self.stdscr.move(self.screensize_y-1, self.clinepos)
									
								else:
									self.backspace()
								
								
								
							elif c == "KEY_RIGHT":
								if alt_key:
									
									self.adjust_clinepos(current_word_len_post)
								else:
									self.adjust_clinepos(characters=1)
							
							elif c == "KEY_UP":
								self.cmd_history(-1)
									
							elif c == "KEY_DOWN":
								self.cmd_history(1)
														
							continue
																									
					except TypeError as err:
						self.dlog.excpt(err, msg="CommandInterpreter.run() -> cmode (KEY_*")
						try: 
							self.dlog.msg("--DEBUG: c/inputsr/cmd:" + str(c) + " | " + str(inputstr) + " | " + str(self.command))  # @UndefinedVariable
						except: pass
						
					except Exception as err:
						self.dlog.excpt(err, msg="CommandInterpreter.run() -> cmode (KEY_*)")
						
					# On Enter or ESC (27)
					# NOTE: 27 is just the control character sequence but it should work in combination with c == -1
					try:
						# Need to avoid the Exception for long unicode strings
						if len(inputstr) == 1 and c != -1 and (c == u'\n' or ord(c) == 27):
							if c == u'\n':
								
								# Only execute if command is not empty
								if len(self.command) and self.command is not u"say ":
									try:
										self.exec_com()
									except Exception as err:
										self.dlog.excpt(err, msg=">>>in exec_com()", cn=self.__class__.__name__)
										raise
									
							# reset history position counter
							self.command_history_pos = len(self.command_history)
							self.command_cached = None		
							self.cmode = False
							self.tmode = False
							self.command = u""
							self.command_pos = 0
							self.clear_cmdinput("^")
							
							# Reset attachment file and status
							self.filename = (None, None)
							#self.wl.get_active_window_ref().sb.setStatus("")
							#self.stdscr.addstr(self.screensize_y-1, 0, "[T] ")
							curses.curs_set(False)  # @UndefinedVariable

						# If user input is not \n or ESC write it to command bar
						
						else:
							if alt_key or (c != -1 and re.match("^KEY_\w+(\(\d\))?", c)) \
							           or (keyname and re.match("^\^\S$", keyname)) \
							           or re.match("^\^\S", inputstr):
								if alt_key:
									self.dlog.msg("Unbound key (Alt): ^[" + str(alt_key) )
								elif keyname:
									self.dlog.msg("Unbound key (Ctrl): " + keyname)
								else:
									self.dlog.msg("Unbound key (ncurses): " + c)
								continue
							

							
							if c != -1:
								self.cout(c)
								
							elif ord(inputstr[0]) == 27:
								raise ValueError("Unknown Escape sequence: " + str(inputstr))
								
							else:
								self.cstrout(inputstr)
							
						
					except Exception as e:
						self.dlog.excpt(e, msg=" >>>in CommandInterpreter.run() -> cmode (input)")
					
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
							quote = ">>" + self.postno_marked + "\n"
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
						
					elif alt_key == 'F':
						thread.start_new_thread(self.wl.get_active_window_ref().play_all_videos, ())
						
					elif self.change_window(alt_key):
						continue
				
				else:
					self.dlog.msg("Unbound key: " + str(c))
					continue
				
		except (TypeError, UnicodeDecodeError) as err:
			self.dlog.excpt(err, msg=">>>in CommandInterpreter.run() (outer)")		
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in CommandInterpreter.run() (outer)")
			pass
	# End of run loop
	
	def backspace(self, characters=-1):
		''' deletes last character from self.command, clinepos--, redraws command line '''
		
		if characters == 0:
			raise IndexError("Argument can not be zero.")
		
		# offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
			
		if characters < 0:
			shift = -1
		else:
			shift = 1

		try:
			

			
			# add double width characters in string to be cut out
			if shift > 0:
				cmd_dispose = u''.join(self.command[self.command_pos:self.command_pos+characters])
				
			else:
				# Prevent erasing more characters than the command length
				if len(self.command[offset:self.command_pos])+characters < 0:
					self.dlog.msg("More characters to delete than command length: " + str(characters), 5)
					characters = len(self.command[offset:self.command_pos]) * shift
					self.dlog.msg("Adjusting characters to be erased to: " + str(characters), 5)
				
				# The substring of self.command to delete
				cmd_dispose = u''.join(self.command[self.command_pos+characters:self.command_pos])
				self.dlog.msg("Deleting substring: " + cmd_dispose.encode('utf-8'), 5)
				
				if not cmd_dispose:
					return
				
			try:
				for char in cmd_dispose:
					# Cross-Page Deletion
					if (self.clinepos == 4 and self.command_pos-offset > 0):
						# Reset to IPS
						self.clinepos = self.input_page_size
						self.refresh_cmd_page()
					
					
					# Save position
					y, x = self.stdscr.getyx()
					
					# For character mapping see http://unicode.org/reports/tr11/#Recommendations
					if unicodedata.east_asian_width(char) == 'W' or unicodedata.east_asian_width(char) == 'F':
	
						self.stdscr.addstr(self.screensize_y-1, 0, "[ｱ]", curses.A_BOLD)  # @UndefinedVariable
						if shift < 0:
							self.clinepos += shift
					
					else:
						if self.tmode:
							self.stdscr.addstr(self.screensize_y-1, 0, "[<]", curses.A_BOLD)  # @UndefinedVariable
						else:
							self.stdscr.addstr(self.screensize_y-1, 0, "[%]", curses.A_BOLD)  # @UndefinedVariable
					
					# Restore position
					self.stdscr.move(y, x)
						
					if shift < 0:
						self.command = u''.join(self.command[:self.command_pos+shift] + self.command[self.command_pos:])
						self.command_pos += shift
						self.clinepos += shift

					else:
						self.command = u''.join(self.command[:self.command_pos] + self.command[self.command_pos+shift:])
						
			except (UnicodeError, IndexError) as err:
				self.dlog.warn(err, msg=">>>in backspace()")
				pass		
			
			self.refresh_cmd_page()
			
		except Exception as err:
			self.dlog.excpt(err, cn=self.__class__.__name__, msg=">>>in backspace()")
			return
		
	def refresh_cmd_page(self):
		''' Redraws the command line page according to command_pos '''
		# Offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
		
		
		# Current input page number starting at 0
		input_page_pos = 0
		
		try:
		# Adjust IPP in case double wide unicode characters are used
			cmd_pages = [ offset ]
			cwidth = 0
			command_pos_cwidth = 0 # for calculating self.clinepos
			for charcount, char in enumerate(self.command[offset:], 1):
				# Single width Page size, needs to consider double width characters:
				self.input_page_size = self.screensize_x-self.cline_buffer-len(self.cmd_prefix)
				# For character mapping see http://unicode.org/reports/tr11/#Recommendations
				if unicodedata.east_asian_width(char) == 'W' or unicodedata.east_asian_width(char) == 'F':
					cwidth += 2
					# 
					if (cwidth)%self.input_page_size == 1:
						self.dlog.msg("x_______________________________x", 4)
						cwidth -= 1
				else:
					cwidth += 1
				
				if (cwidth)%self.input_page_size == 0:
					cmd_pages.append(charcount+offset)
					
				# [0+offset, (1+offset), 2+offset] -> [1-1+offset, 2-1+offset, 3-1+offset]
				if self.command_pos == charcount-1+offset:
					input_page_pos = (cwidth-1)/self.input_page_size
					command_pos_cwidth = cwidth%self.input_page_size
					self.clinepos = command_pos_cwidth-1+len(self.cmd_prefix)
					if (self.clinepos < len(self.cmd_prefix)):
						self.clinepos = self.input_page_size+self.cline_buffer-1
					self.dlog.msg("--Changing IPP: " + str(cwidth-1) + "/" + str(self.input_page_size) + " = " + str(input_page_pos), 5)
					self.dlog.msg("--Set self.clinepos to: " + str(self.clinepos), 5)
			

			if self.command_pos == len(self.command):		
				input_page_pos = (cwidth)/self.input_page_size
				command_pos_cwidth = cwidth%self.input_page_size
				#if (cwidth)%self.input_page_size == 1:
				#	self.clinepos = command_pos_cwidth-1+len(self.cmd_prefix)
				#else:
				self.clinepos = command_pos_cwidth+len(self.cmd_prefix)
				self.dlog.msg("Changing IPP (Max): " + str(input_page_pos), 5)
				
			self.dlog.msg("--Page: " + str(input_page_pos) + " cwidth: " + str(cwidth), 5)
				
				
			try:
				cmd_end_pos = cmd_pages[input_page_pos+1] #+offset
				if cmd_end_pos == cmd_pages[input_page_pos]:
					cmd_end_pos = None
				
			except (IndexError, TypeError):
				cmd_end_pos = None
			

			self.dlog.msg("--Input Page size: " + str(self.input_page_size) + " cwidth: " + str(cwidth), 5)	
			self.dlog.msg("--Start Position: " + str(cmd_pages) + " End Position: " + str(cmd_end_pos), 5)	
				
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in refresh_cmd_page()", cn=self.__class__.__name__)
		
		
		try:
			# Substitute \n for \\
			tmp_cmd = self.command.replace('\n', u'¬')
			
			# Command line page to display
			if input_page_pos == None:
				cmd_display_part = tmp_cmd
			elif cmd_end_pos:
				self.dlog.msg("--Segment      : [" + str(cmd_pages[input_page_pos]) + ":" + str(cmd_end_pos) + "]", 5)  
				cmd_display_part = tmp_cmd[cmd_pages[input_page_pos]:cmd_end_pos]
			else:
				self.dlog.msg("--Segment      : [" + str(cmd_pages[input_page_pos])  + ":]", 5 )
				cmd_display_part = tmp_cmd[cmd_pages[input_page_pos]:]
			
			# Clear command input line
			self.stdscr.move(self.screensize_y-1, len(self.cmd_prefix))
			self.stdscr.clrtoeol()
			
			# Check if page fits page size
			if len(cmd_display_part) > self.input_page_size:
				raise OverflowError("String to display exceeds input page size xowox")
			
			# Output command input page
			#self.dlog.msg("Drawing: " + cmd_display_part.encode('utf-8'))
			#self.stdscr.addstr(self.screensize_y-1, len(self.cmd_prefix), cmd_display_part.encode('utf-8'))
			
		except IndexError as err:
			self.dlog.warn(err, msg=">>> in refresh_cmd_page()")	
			
		except OverflowError as err:
			self.dlog.warn(err, msg=">>> in refresh_cmd_page()")
			self.stdscr.addstr(self.screensize_y-1, len(self.cmd_prefix), cmd_display_part[:self.input_page_size].encode('utf-8'))	
		
		except Exception as err:
			self.dlog.excpt(err, msg=">>> in refresh_cmd_page()", cn=self.__class__.__name__)
			raise
		
		finally:
			self.stdscr.addstr(self.screensize_y-1, len(self.cmd_prefix), cmd_display_part.encode('utf-8'))
			self.stdscr.move(self.screensize_y-1, self.clinepos)
			
		
		self.dlog.msg("--Page Size    : " + str(self.input_page_size) +  " | Page: " + str(input_page_pos), 5)
		self.dlog.msg("--CMD Length   : " + str(len(self.command)) + " Position: " + str(self.command_pos) + " clinepos: " + str(self.clinepos), 5)
		self.dlog.msg("--+cmd_pos     : " + str(self.command_pos) + "-" + str(offset) + "/" + str(self.input_page_size) + " = " + str(input_page_pos), 5)

	

	def adjust_clinepos(self, characters=1):
		# offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
		
		try: 
			if characters == 0:
				raise IndexError("Argument can not be zero.")
				
			if len(self.command[offset:self.command_pos]) + characters < 0:
				raise IndexError("Can't move cursor " + str(characters) + " characters to the left.")
			
			if self.command_pos + characters > len(self.command):
				raise IndexError("Can't move cursor " + str(characters) + " characters to the right.")
			
			
			self.command_pos += characters
			self.refresh_cmd_page()
		
		except IndexError as err:
			self.dlog.warn(err, logLevel=4, msg=">>>in adjust_clinepos()")
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in adjust_clinepos()", cn=self.__class__.__name__)
			
	# TODO remove
	def adjust_clinepos_old(self, characters=1):
		''' move clinepos and command_pos by (-)n characters'''
		
		if characters == 0:
			raise IndexError("Argument can not be zero.")
		#self.dlog.msg("--cmdlen: " + str(len(self.command)) + "Command Position: " + str(self.command_pos) + " clinepos: " + str(self.clinepos) )

		#self.refresh_cmd_page()
		# offset for "say "
		offset = 0
		if self.tmode:
			offset = 4
			
		try:
			if characters < 0:
				shift = -1
			else:
				shift = 1
				
				
			for _ in range(abs(characters)):

				# Prevent cursor from leaving command scope
				if self.command_pos+shift < 0+offset or self.command_pos+shift > len(self.command):
					# Don't break if command position is already out of position
					# (backspace() is called prior to this function and sets command_pos) 
					if self.command_pos <= len(self.command):
						break
				
				# Cursor moving out of screen (left side)
				if self.clinepos+shift < len(self.cmd_prefix) and self.command_pos > offset:
					
					self.clinepos = self.input_page_size+len(self.cmd_prefix) + shift
					self.command_pos += shift
					
					self.refresh_cmd_page()
					
					continue
					
				# Cursor moving out of screen (right side)
				elif self.clinepos+shift >= self.input_page_size+len(self.cmd_prefix):
					self.dlog.msg("--Reset to 4: " + str(self.clinepos) + " | " + str(self.command_pos))
					
					self.clinepos = 4
					self.command_pos += 1
					self.refresh_cmd_page()
					
					continue
					

				
				try:
					y, x = self.stdscr.getyx()

					# Need to move over two single width characters for wide unicode characters
					if shift > 0:
						char = u''.join(self.command[self.command_pos:self.command_pos+shift])
					else:
						char = u''.join(self.command[self.command_pos+shift:self.command_pos])
						
					if not char:
						self.stdscr.addstr(self.screensize_y-1, 0, "[?]")
						
					# For character mapping see http://unicode.org/reports/tr11/#Recommendations
					elif unicodedata.east_asian_width(char) == 'W' or unicodedata.east_asian_width(char) == 'F':
						self.stdscr.addstr(self.screensize_y-1, 0, "[ｱ]")
						self.clinepos += shift
						
					else:
						self.stdscr.addstr(self.screensize_y-1, 0, "[<]")
						
					self.stdscr.move(y, x)
						
						
						
				except UnicodeError as err:
					self.dlog.warn(err, msg=">>adjust_clinepos()")		
				except TypeError as err:
					self.dlog.warn(err, msg=">>>in adjust_clinepos(): TypeError")
				finally:
					self.clinepos += shift
					self.command_pos += shift
		
	
		except Exception as err:
			self.dlog.excpt(err, msg=">>adjust_clinepos()", cn=self.__class__.__name__)
			
		
		#self.stdscr.move(self.screensize_y-1, self.clinepos)
		self.refresh_cmd_page()	

				
	
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
