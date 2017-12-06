'''
Created on Oct 5, 2015

'''
from threading import Thread
from DictOutput import DictOutput
from Autism import Autism
from DebugLog import DebugLog

import curses
import time
import threading
from requests.exceptions import HTTPError

class ThreadFetcher(threading.Thread):
	def __init__(self, threadno, stdscr, board, bp, nickname):
		self.threadno = str(threadno)
		self.stdscr = stdscr
		self.board = board
		self.bp = bp
		self.nickname = nickname
		self.contentFetcher = Autism(self.board, self.threadno)

		
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
		try:
			self.tb.set_title(self.dictOutput.getTitle())
		except:
			pass
		self.tb.draw()
		
	def inactive(self):
		self._active = False
		
	def on_resize(self):
		self.sb.on_resize()
		self.tb.on_resize()
		
	def save_image(self, *args, **kwargs):
		try:
			return self.contentFetcher.save_image(*args, **kwargs)
		except:
			raise
			

	def run(self):
		dlog = DebugLog()
		dlog.msg("ThreadFetcher: Running on /" + self.board + "/" + self.threadno, 4)
		
		try:
			self.dictOutput = DictOutput(self.bp)
			self.bp.postReply.dictOutput = self.dictOutput # Needed for marking own comments
		except Exception as e:
			dlog.excpt(e, msg=">>>in ThreadFetcher.run()", cn=self.__class__.__name__)
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
				self.contentFetcher.setstdscr(self.stdscr)
				thread_state = self.contentFetcher.get()
				thread = getattr(self.contentFetcher, "jsoncontent")
				
					
				self.dictOutput.refresh(thread)
				self.bp.set_tdict(self.dictOutput.get_tdict())
				
				self.bp.autofocus()
				
				# Set title if window is active
				if self._active:
					self.tb.set_title(self.dictOutput.getTitle())
					
				# Immediately refresh cached threads
				if thread_state is "cached":
					self.sb.draw("CACHED")
					self.update()	
					
				# reset interval on thread refresh
				if self.update_n > 9:
					self.update_n = 9
					
				# decrease interval on highly active threads
				elif self.update_n > 1:
					self.update_n -= 1
					

				
			except HTTPError as e:
				error_code = e.response.status_code
				
				# stop updating if thread 404'd
				if error_code == 404:
					self.sb.setStatus(str(e.response.reason) + ": " + str(e.response.url))
					dlog.excpt(e)
					break
				
				# assume temporary error for e.g. 403	
				elif  400 <= error_code < 500:
					self.sb.setStatus(str(e.response.reason) + ": " + str(e.response.url))
					dlog.warn(e)
				
				# increase update interval on stale thread 
				elif error_code == 304:
					if self.update_n < 20:
						self.update_n += 1

					self.sb.setStatus(str(error_code))
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
						wait_n = self.bp.calc_post_wait_time()
						if wait_n > 0:
							self.sb.draw(update_n=update_n, wait_n=wait_n)
						else:
							self.sb.draw(update_n)
				except Exception as e:
					dlog.excpt(e, cn=self.__class__.__name__)
					pass
				

				time.sleep(1)
				
		# End of thread loop
				
		dlog.msg("ThreadFetcher: Leaving /" + self.board + "/" + self.threadno, 3)
				
	tdict = property(get_tdict, set_tdict, None, None)
