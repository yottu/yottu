'''
Created on May 9, 2017

'''
from threading import Thread
from CatalogOutput import CatalogOutput
from Autism import Autism
import curses
import time
import threading
import Config
from DebugLog import DebugLog

class CatalogFetcher(threading.Thread):
	def __init__(self, stdscr, board, cp, search="", cache_only=False):
		self.stdscr = stdscr
		self.board = board
		self.cp = cp # CatalogPad
		self.search = search
		self.cache_only = cache_only # True: Do not re-fetch immediately if cached catalog is available
		self.sb = self.cp.sb
		self.tb = self.cp.tb
		
		cfg = Config.Config(debug=False)
		try:
			self.catalog_update_time = int(cfg.get('catalog.update.time'))
		except:
			self.catalog_update_time = 180
		
		Thread.__init__(self)
		self._stop = threading.Event()
		self._update = threading.Event()
		self._active = False # CatalogPad the CatalogFetcher runs in is active
		
	def stop(self):
		self._stop.set()
		
	def update(self, notail=False):
		''' Update catalog immediately '''
		self._update.set()
		
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
					self.sb.setStatus("CACHED")
					
					# Don't refresh catalog if cache only is requested 
					if self.cache_only is False:
						getCatalog.get("catalog")
						catalog = getattr(getCatalog, "jsoncontent")
						result_postno = catOutput.refresh(catalog)
				
				else:
					self.sb.setStatus("")
					
					
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
				
			for update_n in range (self.catalog_update_time, -1, -1):
				if self._stop.is_set():
					break
				
				if self._update.is_set():
					self._update.clear()
					break
				
				try:
					if self._active:
						self.sb.draw(update_n)
				except Exception as e:
					dlog.excpt(e)
					pass
				

				time.sleep(1)