'''
Created on Sep 28, 2015

'''
from Pad import Pad
from ThreadFetcher import ThreadFetcher
from PostReply import PostReply
from DebugLog import DebugLog
from TermImage import TermImage
import urllib

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr):
		super(BoardPad, self).__init__(stdscr)
		self.board = ""
		self.threadno = ""
		self.nickname = ""
		self.threadFetcher = None
		self.postReply = None
		self.comment = ""
		self.tdict = {}
		self.dlog = DebugLog(self)

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

		
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
		
	def display_captcha(self):
		try:
			self.postReply.display_captcha()
		except:
			# FIXME: Better error handling
			self.dlog.msg("Could not display captcha, check if /usr/lib/w3m/w3mimgdisplay is installed")
		
	def join(self, board, threadno, nickname="asdfasd"):
		self.board = board
		self.threadno = threadno
		self.nickname = nickname
		self.threadFetcher = ThreadFetcher(self.threadno, self.stdscr, self.board, self, self.nickname)
		self.threadFetcher.setDaemon(True)
		self.threadFetcher.start()
		self.postReply = PostReply(self.board, self.threadno)
		
	def post(self, comment):
		self.comment = comment
		self.postReply.get_captcha_challenge()
		self.display_captcha()
			
		
	def set_captcha(self, captcha):
		self.postReply.set_captcha_solution(captcha)
		self.postReply.post(self.comment)
		self.threadFetcher.update()
		
		
		# FIXME needs cleaning up and putting things in the right classes etc
	def show_image(self, postno):
		try:
			postno = int(postno)
			img_ext =  str(self.get_tdict()[postno]['ext'])
			img_filename = str(self.get_tdict()[postno]['tim']) + img_ext
			img_filename_thumb = str(self.get_tdict()[postno]['tim']) + "s.jpg"
			self.dlog.msg("Namely: " + str(img_filename) )
		except Exception as err: 
			self.dlog.msg("Exception in assembling file name: " + str(err))

			
		try:
			urllib.urlretrieve("https://i.4cdn.org/"+self.board+ "/"+img_filename, "yottu-image" + img_ext)
		except Exception as err:
			self.dlog.msg("E: " + str(err))
		try:
			TermImage.display("yottu-image" + img_ext)
		except Exception as err:
			self.dlog.msg("Exception in TermImage call: " + str(err))
			
			
	
	tdict = property(get_tdict, set_tdict, None, None)
		
	