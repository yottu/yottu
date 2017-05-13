'''
Created on Sep 28, 2015

'''
from Pad import Pad
from ThreadFetcher import ThreadFetcher

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr):
		super(BoardPad, self).__init__(stdscr)
		self.threadFetcher = None
		
	def on_resize(self):
		self.dlog.msg("BoardPad: on_resize")
		super(BoardPad, self).on_resize()
		self.threadFetcher.on_resize()
		
	def stop(self):
		self.threadFetcher.stop()
	
	def active(self):
		super(BoardPad, self).active()
		try:
			self.threadFetcher.active()
		except:
			raise
		
	def inactive(self):
		super(BoardPad, self).inactive()
		try:
			self.threadFetcher.inactive()
		except:
			raise
		
		
	def join(self, board, threadno, nickname="asdfasd"):
		self.threadFetcher = ThreadFetcher(threadno, self.stdscr, board, self, nickname)
		self.threadFetcher.setDaemon(True)
		self.threadFetcher.start()
		