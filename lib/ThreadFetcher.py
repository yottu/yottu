'''
Created on Oct 5, 2015

'''
from threading import Thread
from DictOutput import DictOutput
from Autism import Autism

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
		self.dlog = self.bp.wl.dlog
		self.nickname = nickname
		self.contentFetcher = Autism(self.board, self.threadno)
		
		self.sb = self.bp.sb
		self.tb = self.bp.tb
				
		self.tdict = {}
		self.dictOutput = ""
		self.update_n = 9
		self.runtime = 0 # iteration of while loop
		self.refresh_pages = 60 # interval to refresh page thread is on
		
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
		
	def update(self, notail=False):
		''' Update thread immediately '''
		
		# Prevent update loop if post count keeps mismatching
		if self.contentFetcher.notail is False:
			self.contentFetcher.notail = notail
			self._update.set()
		else:
			self.contentFetcher.notail = False
		
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
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in ThreadFetcher.save_image()", cn=self.__class__.__name__)
			raise
			

	def run(self):
		self.dlog.msg("ThreadFetcher: Running on /" + self.board + "/" + self.threadno, 4)
		
		try:
			self.dictOutput = DictOutput(self.bp)
			self.bp.postReply.dictOutput = self.dictOutput # Needed for marking own comments
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in ThreadFetcher.run() ->dictOutput", cn=self.__class__.__name__)
			self.stdscr.addstr(0, 0, str(e), curses.A_REVERSE)  # @UndefinedVariable
			self.stdscr.refresh()
				
		
		while True:
			self.dlog.msg("ThreadFetcher: Fetching for /" + self.board + "/" + self.threadno, 5)
			
			# leave update loop if stop is set
			if self._stop.is_set():
				self.dlog.msg("ThreadFetcher: Stop signal for /" + self.board + "/" + self.threadno, 3)
				break
			
			# Do additional things when update bit is set
			if self._update.is_set():
				pass
	
			try:
				self.sb.setStatus('')
				self.contentFetcher.sb = self.sb
				self.contentFetcher.setstdscr(self.stdscr)
				
				pages = self.contentFetcher.fetch("threads")				
				thread_state = self.contentFetcher.get()
				thread = self.contentFetcher.jsoncontent
					
				self.dictOutput.refresh(thread, jsonpages=pages)
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
					self.dlog.excpt(e)
					break
				
				# assume temporary error for e.g. 403	
				elif  400 <= error_code < 500:
					self.sb.setStatus(str(e.response.reason) + ": " + str(e.response.url))
					self.dlog.warn(e)
				
				# increase update interval on stale thread 
				elif error_code == 304:
					if self.update_n < 20:
						self.update_n += 1

					self.sb.setStatus(str(error_code))
			except Exception as e:
				self.dlog.excpt(e, msg=">>>in ThreadFetcher.run()", cn=self.__class__.__name__)

							
			for update_n in range (self.update_n, -1, -1):
				
				# Leave countdown loop if stop is set
				if self._stop.is_set():
					break
				
				# Update thread immediately
				if self._update.is_set():
					self._update.clear()
					break
				elif self.runtime%self.refresh_pages == 0:
					
				# Update page number thread is on
					try:
						jsonpages = self.contentFetcher.fetch("threads")
						self.dictOutput.refresh_pages(jsonpages)
						# Set title if window is active
						if self._active:
							self.tb.set_title(self.dictOutput.getTitle())
					except Exception as e:
						self.dlog.excpt(e, msg=">>>in ThreadFetcher.run() ->refresh.pages", cn=self.__class__.__name__)
				
				try:
					if self._active:
						wait_n = self.bp.calc_post_wait_time()
						if wait_n > 0:
							self.sb.draw(update_n=update_n, wait_n=wait_n)
						else:
							self.sb.draw(update_n)
				except Exception as err:
					self.dlog.excpt(err, msg=">>>in ThreadFetcher.run() ->sb.draw()", cn=self.__class__.__name__)
				

				time.sleep(1)
				self.runtime +=1
				
		# End of thread loop
				
		self.dlog.msg("ThreadFetcher: Leaving /" + self.board + "/" + self.threadno, 3)
				
	tdict = property(get_tdict, set_tdict, None, None)
