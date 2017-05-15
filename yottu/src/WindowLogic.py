'''
Created on Oct 9, 2015

This class is for creating a CommandPad and managing BoardPads

'''
from CommandPad import CommandPad
from BoardPad import BoardPad
import threading
from threading import Thread
from DebugLog import DebugLog
from CatalogPad import CatalogPad
from sqlalchemy.orm.session import ACTIVE


class WindowLogic(threading.Thread):
	'''
	classdocs
	'''

	def __init__(self, stdscr):
		
		self.stdscr = stdscr
		self.dlog = DebugLog(self)
		try:
			self.windowList = []
			
			self.compad = CommandPad(stdscr)
			
			self.windowList.append(self.compad)
			self.set_active_window(0)
			self.compad.draw()
			
#			board = "int"
#			threadno = "50294416"
			self.nickname = "asdfasd"
			
			
#			self.bp = BoardPad(stdscr)
#			self.bp.join(board, threadno, self.nickname)
#			self.windowList.append(self.bp)
#			self.set_active_window(1)
			
			Thread.__init__(self)
			self._stop = threading.Event()
		except:
			raise
		
	def join_thread(self, board, thread):
		try:
			self.dlog.msg("Creating new boardpad for " + thread + " on /" + board + "/")
			boardpad = BoardPad(self.stdscr)
			boardpad.join(board, thread, self.nickname)
			self.windowList.append(boardpad)
			self.raise_window(len(self.windowList)-1)
		except Exception, err:
			self.dlog.excpt(err)
			
	def on_resize(self):
		activeWindow = self.get_active_window()
		for window in self.windowList:
			window.on_resize()
		self.set_active_window(activeWindow)
			
	def catalog(self, board, search=""):
		try:
			catalogpad = CatalogPad(self.stdscr)
			catalogpad.join(board, search)
			self.windowList.append(catalogpad)
			self.raise_window(len(self.windowList)-1)
		except Exception, err:
			self.dlog.excpt(err)
			
	def destroy_active_window(self):
		activeWindow = self.get_active_window()
		self.dlog.msg("Parting window " + str(activeWindow))
		if activeWindow > 0:
			self.raise_window(0)
			
			try:
				self.windowList[activeWindow].stop()
				self.windowList.remove(self.windowList[activeWindow])
			except Exception, err:
				self.dlog.excpt(err)++-2
			
	def get_active_window(self):
		"""Returns the index number of the active window"""
		return self.__activeWindow
	
	def get_active_window_ref(self):
		"""Returns the active window"""
		return self.windowList[self.__activeWindow]


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
		if len(self.windowList) > num >= 0:
			self.set_active_window(num)
			self.windowList[self.get_active_window()].draw()
	
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
		
	activeWindow = property(get_active_window, set_active_window, None, None)
