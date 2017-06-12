'''
Created on Oct 5, 2015

'''
from threading import Thread
from DictOutput import DictOutput
from Autism import Autism
import curses
from Statusbar import Statusbar
import time
import threading
from Titlebar import Titlebar
from DebugLog import DebugLog
import urllib2

class ThreadFetcher(threading.Thread):
	def __init__(self, threadno, stdscr, board, bp, nickname):
		self.threadno = threadno
		self.stdscr = stdscr
		self.board = board
		self.bp = bp
		self.nickname = nickname
		
		self.sb = self.bp.sb
		self.tb = self.bp.tb
				
		#self.sb = Statusbar(self.stdscr, self.nickname, self.board, self.threadno)
		#self.tb = Titlebar(self.stdscr)
		self.tdict = {}
		self.dictOutput = ""
		self.update_n = 9
		Thread.__init__(self)
		self._stop = threading.Event()
		self._update = threading.Event()
		self._active = False # BoardPad the ThreadFetcher runs in is active

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

		
	def stop(self):
		self._stop.set()
		
	def update(self):
		self._update.set()
		
	def active(self):
		self._active = True
		self.tb.draw()
		
	def inactive(self):
		self._active = False
		
	def on_resize(self):
		self.sb.on_resize()
		self.tb.on_resize()
		

	def run(self):
		dlog = DebugLog()
		dlog.msg("ThreadFetcher: Running on /" + self.board + "/" + self.threadno, 4)
		
		try:
			self.dictOutput = DictOutput(self.bp)
			getThread = Autism(self.board, self.threadno)
		except Exception as e:
			dlog.excpt(e)
			self.stdscr.addstr(0, 0, str(e), curses.A_REVERSE)  # @UndefinedVariable
			self.stdscr.refresh()
				
		
		while True:
			
			dlog.msg("ThreadFetcher: Fetching for /" + self.board + "/" + self.threadno, 5)
			
			# leave update loop if stop is set
			if self._stop.is_set():
				dlog.msg("ThreadFetcher: Stop signal for /" + self.board + "/" + self.threadno, 3)
				break
			
			# Do additional things when update bit is set
			if self._update.is_set():
				pass
	
			try:
				self.sb.setStatus('')
				getThread.setstdscr(self.stdscr)
				getThread.get()
				thread = getattr(getThread, "jsoncontent")
				self.dictOutput.refresh(thread)
				self.bp.set_tdict(self.dictOutput.get_tdict())
				
				if self._active:
					self.tb.set_title(self.dictOutput.getTitle())
				if self.update > 9:
					self.update_n = 9
				elif self.update > 3:
					self.update -= 1
				
			except urllib2.HTTPError as e:
				if e.code == 404:
					self.sb.setStatus(str(e))
					dlog.excpt(e)
					break
				elif e.code == 304:
					if self.update_n < 20:
						self.update_n += 1

					self.sb.setStatus(str(e.code))
			except Exception as e:
				self.sb.setStatus(str(e))
				dlog.excpt(e)
				pass

							
			for update_n in range (self.update_n, -1, -1):
				
				# Leave countdown loop if stop is set
				if self._stop.is_set():
					break
				
				# Update thread immediately
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
				
		# End of thread loop
				
		dlog.msg("ThreadFetcher: Leaving /" + self.board + "/" + self.threadno, 3)
				
	tdict = property(get_tdict, set_tdict, None, None)
