'''
Created on May 9, 2017

'''
from threading import Thread
from CatalogOutput import CatalogOutput
from Autism import Autism
import curses
import time
import threading
from DebugLog import DebugLog

class CatalogFetcher(threading.Thread):
	def __init__(self, stdscr, board, cp, search=""):
		self.stdscr = stdscr
		self.board = board
		self.cp = cp # CatalogPad
		self.search = search
		self.sb = self.cp.sb
		self.tb = self.cp.tb
		Thread.__init__(self)
		self._stop = threading.Event()
		self._active = False # CatalogPad the CatalogFetcher runs in is active
		
	def stop(self):
		self._stop.set()
		
	def active(self):
		self._active = True
		self.tb.set_title("/" + self.board + "/ -- catalog")
		self.tb.draw()
		
	def inactive(self):
		self._active = False
		
	def on_resize(self):
		self.sb.on_resize()
		self.tb.on_resize()
	

	def run(self):
		dlog = DebugLog()
		dlog.msg("CatalogFetcher: Running on /" + self.board + "/", 4)
		
		try:
			catOutput = CatalogOutput(self.cp, self.search)
			getCatalog = Autism(self.board)
		except Exception as e:
			dlog.excpt(e)
			self.stdscr.addstr(0, 0, str(e), curses.A_REVERSE)  # @UndefinedVariable
			self.stdscr.refresh()
		

		
		while True:
			
			dlog.msg("CatalogFetcher: Fetching for /" + self.board + "/", 3)
			if self._stop.is_set():
				dlog.msg("CatalogFetcher: Stop signal for /" + self.board + "/", 3)
				break
	
			try:
				getCatalog.setstdscr(self.stdscr)
				catalog_state = getCatalog.get("catalog")
				catalog = getattr(getCatalog, "jsoncontent")
				result_postno = catOutput.refresh(catalog)
				
				if self._active:
					self.tb.set_title("/" + self.board + "/ -- catalog")
				
				if catalog_state is "cached":
					getCatalog.get("catalog")
					catalog = getattr(getCatalog, "jsoncontent")
					result_postno = catOutput.refresh(catalog)
					
					
				if len(result_postno) == 1:
					self.cp.wl.destroy_active_window()
					self.cp.wl.join_thread(self.board, str(result_postno.pop()))
					break
				
			except Exception as e:
				self.sb.setStatus(str(e))
				dlog.excpt(e)
				pass
				
			if self._active:		
				self.tb.draw()
				
			for update_n in range (90, -1, -1):
				if self._stop.is_set():
					break
				
				try:
					if self._active:
						self.sb.draw(update_n)
				except Exception as e:
					dlog.excpt(e)
					pass
				

				time.sleep(1)