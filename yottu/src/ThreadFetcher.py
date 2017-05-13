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

class ThreadFetcher(threading.Thread):
	def __init__(self, threadno, stdscr, board, bp, nickname):
		self.threadno = threadno
		self.stdscr = stdscr
		self.board = board
		self.bp = bp
		self.nickname = nickname		
		self.sb = Statusbar(self.stdscr, self.nickname, self.board, self.threadno)
		self.tb = Titlebar(self.stdscr)
		Thread.__init__(self)
		self._stop = threading.Event()
		self._active = False # BoardPad the ThreadFetcher runs in is active
		
	def stop(self):
		self._stop.set()
		
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
		dlog.msg("ThreadFetcher: Running on /" + self.board + "/" + self.threadno, 3)
		
		try:
			dictOutput = DictOutput(self.bp)
			getThread = Autism(self.board, self.threadno)
		except Exception as e:
			dlog.excpt(e)
			self.stdscr.addstr(0, 0, str(e), curses.A_REVERSE)
			self.stdscr.refresh()
				
		self.tb.draw()
		
		while True:
			
			dlog.msg("ThreadFetcher: Fetching for /" + self.board + "/" + self.threadno, 3)
			if self._stop.is_set():
				dlog.msg("ThreadFetcher: Stop signal for /" + self.board + "/" + self.threadno, 3)
				break
	
			try:
				getThread.setstdscr(self.stdscr)
				getThread.get()
				thread = getattr(getThread, "jsoncontent")
				dictOutput.refresh(thread)
				self.tb.set_title(dictOutput.getTitle())
			except Exception as e:
				self.sb.setStatus(str(e))
				dlog.excpt(e)
				pass
				
			for update_n in range (9, -1, -1):
				if self._stop.is_set():
					break
				
				try:
					if self._active:
						self.sb.draw(update_n)
				except Exception as e:
					dlog.excpt(e)
					pass
				

				time.sleep(1)