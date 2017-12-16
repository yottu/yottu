'''
Created on Oct 9, 2015

This class is for creating a CommandPad and managing BoardPads

'''
from CommandPad import CommandPad
from BoardPad import BoardPad
from DebugLog import DebugLog
from CatalogPad import CatalogPad
from Config import Config
from ThreadWatcher import ThreadWatcher

import curses
from lib.MessagePad import MessagePad
from Database import Database




class WindowLogic(object):
	'''
	classdocs
	'''

	def __init__(self, stdscr):
		
		self.stdscr = stdscr
		curses.use_default_colors() # @UndefinedVariable
		# assign color to post number, pairs 1-10 are reserved
		for i in range(0, curses.COLORS):  # @UndefinedVariable
			curses.init_pair(i + 10, i, -1) # @UndefinedVariable
		# reserved color pairs
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # @UndefinedVariable
		curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_GREEN)  # @UndefinedVariable
		curses.init_pair(3, curses.COLOR_RED, curses.COLOR_GREEN)  # @UndefinedVariable
		curses.init_pair(4, curses.COLOR_RED, -1)  # @UndefinedVariable
		
		self.dlog = DebugLog(self)
		try:
			self.tw = None
			self.db = Database()
			
			self.cfg = Config()
			self.cfg.register(self)
			if self.cfg.get('threadwatcher.enable'):
				self.dlog.msg("Starting ThreadWatcher")
				self.tw = ThreadWatcher(self)

			self.windowList = [] # Array of all window objects (i.e. Pads)
			self.windowListProperties =  {} # Associating a window object with its properties

			self.ci = None

			self.compad = CommandPad(stdscr, self)
			self.msgpad = MessagePad(stdscr, self)

			self.append_pad(self.compad)
			self.append_pad(self.msgpad)
			self.set_active_window(0)

			
			self.nickname = ""
	#		Thread.__init__(self)
	#		self._stop = threading.Event()
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in WindowLogic.__init__()", cn=self.__class__.__name__)
			raise

	def on_config_change(self):
		self.cfg = Config()
		if self.cfg.get('threadwatcher.enable') and not self.tw:
			self.dlog.msg("Starting ThreadWatcher")
			self.tw = ThreadWatcher(self)

	def set_nickname(self, value):
		self.__nickname = value
		if self.__nickname:
			self.__nickname = value
		for window in self.windowList:
			window.set_nickname(self.get_nickname())

	def get_nickname(self):
		return self.__nickname 

	def get_window_list(self):
		return self.__windowList
	
	def get_property(self, window, prop):
		return self.windowListProperties[window][prop]
	
	
	def set_property(self, window, prop, value):
		self.windowListProperties[window][prop] = value


	def set_window_list(self, value):
		self.__windowList = value


	def append_pad(self, window):
		try:
			self.windowList.append(window)
			# Properties of a window instance, note: use deepcopy from copy if not assigning it directly 
			self.windowListProperties[window] = {'sb_unread': False, 'sb_lines': 0, 'sb_mentioned': False}
			
			# Let statusbar of window know what window number it has
			# TODO: This needs to be reset when a window gets destroyed or moved
			window.sb.set_sb_windowno(len(self.windowList))
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in WindowLogic.append_pad()", cn=self.__class__.__name__)

		
	def join_thread(self, board, thread):
		try:
			boardpad = BoardPad(self.stdscr, self)
			boardpad.join(board, thread, self.nickname)
			self.append_pad(boardpad)
			self.raise_window(len(self.windowList)-1)
		except Exception, err:
			self.dlog.excpt(err, msg=">>>in WindowLogic.join_thread()", cn=self.__class__.__name__)
			
	def on_resize(self):
		activeWindow = self.get_active_window()
		for window in self.windowList:
			window.on_resize()
		self.set_active_window(activeWindow)
		
	def on_update(self):
		self.get_active_window_ref().on_update()
			
	def catalog(self, board, search="", cache_only=False):
		try:
			catalogpad = CatalogPad(self.stdscr, self)
			catalogpad.join(board, search=search, cache_only=cache_only)
			self.append_pad(catalogpad)
			
			self.raise_window(len(self.windowList)-1)
		except Exception, err:
			self.dlog.excpt(err, msg=">>>in WindowLogic.catalog()", cn=self.__class__.__name__)
			
	def destroy_active_window(self):
		activeWindow = self.get_active_window()
		activeWindowRef = self.get_active_window_ref()
		self.dlog.msg("Parting window " + str(activeWindow))
		if activeWindow > 0:
			self.raise_window(activeWindow-1)
			
			try:
				activeWindowRef.stop()
				self.windowList.remove(activeWindowRef)
				self.windowListProperties.pop(activeWindowRef)
			except Exception as err:
				self.dlog.excpt(err, cn=self.__class__.__name__)
				
	def destroy_window_ref(self, windowRef):
		#if self.get_active_window_ref() == windowRef:
		#	self.raise_window(self.get_active_window()-1)
		
		try:
			windowRef.stop()
			self.windowList.remove(windowRef)
			self.windowListProperties.pop(windowRef)
		except Exception as err:
			self.dlog.excpt(err, cn=self.__class__.__name__)
		

			
	def get_window(self, window):
		'''Returns the index number of the arg'''
		return self.windowList.index(window)	
	
	def get_window_ref(self, index):
		'''Returns the object of the index in windowList'''
		return self.windowList[index]
			
	def get_active_window(self):
		"""Returns the index number of the active window"""
		return self.__activeWindow
	
	def get_active_window_ref(self):
		"""Returns the active window object"""
		return self.windowList[self.__activeWindow]
	
	def get_boardpad_list(self):
		boardpad_list = []
		for window in self.windowList:
			if (isinstance(window, BoardPad)):
				boardpad_list.append(window)
		return boardpad_list


	def set_active_window(self, value):
		self.__activeWindow = value
		for pad in self.windowList:
			pad.inactive()
		self.windowList[value].active()
		
	def next(self):
		try:
			activeWindow = self.get_active_window();
			self.raise_window(activeWindow+1)
		except:
			pass
			
	def prev(self):
		try:
			activeWindow = self.get_active_window();
			self.raise_window(activeWindow-1)
		except:
			pass
		
	def stop(self):
		self._stop.set()
		
	def raise_window(self, num):
		try:
			if len(self.windowList) > num >= 0:
				self.set_active_window(num)
				self.windowList[self.get_active_window()].draw()
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in WindowLogic.raise_window()")
	
	# FIXME: these should probably called with wl.active_window.<MOVE>	
	def moveup(self, lines=1):
		self.windowList[self.get_active_window()].moveup(lines)
		
	def movedown(self, lines=1):
		self.windowList[self.get_active_window()].movedown(lines)
		
	def home(self):
		self.windowList[self.get_active_window()].home()
		
	def end(self):
		self.windowList[self.get_active_window()].end()
		
		
	def setTitle(self, title):
		self.title = title
		
	def compadout(self, string):
		self.compad.addstr(str(string) + "\n")
		
	def msgpadout(self, string):
		self.msgpad.addstr(str(string) + "\n")
		
	activeWindow = property(get_active_window, set_active_window, None, None)
	windowList = property(get_window_list, set_window_list, None, None)
	nickname = property(get_nickname, set_nickname, None, None)
