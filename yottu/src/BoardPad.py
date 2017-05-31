'''
Created on Sep 28, 2015

'''
from Pad import Pad
from ThreadFetcher import ThreadFetcher
from PostReply import PostReply
from DebugLog import DebugLog
from TermImage import TermImage
from Autism import Autism

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr, wl):
		super(BoardPad, self).__init__(stdscr, wl)
		self.board = ""
		self.threadno = ""
		self.nickname = ""
		self.threadFetcher = None
		self.postReply = None
		self.comment = ""
		self.subject = "" # TODO not implemented
		self.filename = None
		self.ranger = False # If true filename contains path to actual filename
		self.tdict = {}
		self.contentFetcher = None
		self.dlog = DebugLog(self)
		
	class NoDictError(Exception):
		def __init__(self,*args,**kwargs):
			Exception.__init__(self,*args,**kwargs)

	def get_comment(self):
		return self.__comment


	def set_comment(self, value):
		self.__comment = value


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
		
		self.sb.set_nickname(self.nickname)
		self.sb.set_board(self.board)
		self.sb.set_threadno(self.threadno)
		
		# FIXME ContentFetcher should probably only be called through ThreadFetcher since it is blocking 
		self.contentFetcher = Autism(self.board, self.threadno)
		self.contentFetcher.setstdscr(self.stdscr)
		
		self.threadFetcher = ThreadFetcher(self.threadno, self.stdscr, self.board, self, self.nickname)
		self.threadFetcher.setDaemon(True)
		self.threadFetcher.start()
		
		self.postReply = PostReply(self.board, self.threadno)
		
	def post_prepare(self, comment="", filename=None, ranger=False, subject=""):
		self.comment = comment
		self.filename = filename
		self.ranger = ranger
		self.subject = subject
		self.get_captcha()
		
	def get_captcha(self):
		self.postReply.get_captcha_challenge()
		self.display_captcha()
			
		
	def set_captcha(self, captcha):
		self.postReply.set_captcha_solution(captcha)
		
	def post_submit(self):
		if self.filename:
			response = self.postReply.post(self.comment, self.subject, self.filename, self.ranger)
		elif self.comment:
			response = self.postReply.post(self.comment)
		else:
			raise ValueError("Either filename or comment must be set.")
		
		self.filename = None
		self.ranger = None
		return response
			
			
	def update_thread(self):
		''' update (fetch) thread immediately '''
		self.threadFetcher.update()
		
	def show_image_thumb(self, postno):
		self.show_image(postno, False, [], True)
		
	def show_image(self, postno, use_external_image_viewer=False, options=[], thumb=False):
		try:
			postno = int(postno)
			if not self.tdict:
				raise self.NoDictError("BoardPad has no thread dictionary.")
			
			img_ext =  str(self.get_tdict()[postno]['ext']) # image extension, eg ".jpg"
			img_tim = str(self.get_tdict()[postno]['tim'])  # Actual filename as saved on server
			
			# Return if post has no image attached
			if not img_ext or not img_tim:
				return None
			
		except Exception as err: 
			self.dlog.msg("BoardPad: Exception in assembling filename name: " + str(err))
			raise
		
		# Convert to lower case for later comparison
		img_store_ext = img_ext.lower()
		
		if thumb:
			img_store_filename = self.board + "-" + img_tim[:64] + "s.jpg"
		else:
			img_store_filename = self.board + "-" + img_tim[:64] + img_store_ext
		
		# FIXME ContentFetcher should probably only be called through ThreadFetcher since it is blocking 
		try:
			if thumb:
				self.contentFetcher.save_image(str(img_tim+"s.jpg"), img_store_filename)
			else:
				self.contentFetcher.save_image(str(img_tim+img_ext), img_store_filename)
		except:
			raise
		
		try:
			#yottu_image = "yottu-image" + img_ext
			if use_external_image_viewer is True:
				if img_ext == ".jpg" or img_ext == ".png":
					TermImage.display_feh(img_store_filename, options, "./cache/")
				elif img_ext == ".gif":
					self.dlog.msg("No gif viewer configured.")
				elif img_ext == ".webm":
					# TODO maybe use fbdev and redirect output to /dev/null
					# FIXME this might mess up the term in tiled wm
					TermImage.display_mpv(img_store_filename, [], "./cache/")
					#self.dlog.msg("No webm viewer configured.")
			else:
				if img_ext == ".jpg" or img_ext == ".png" or img_ext == ".gif":
					TermImage.display(img_store_filename, "./cache/")
				else:
#					self.statusbar.msg("File not viewable.")
					self.dlog.msg(img_ext + " filename not viewable.")
		except Exception as err:
			self.dlog.msg("Exception in TermImage call: " + str(err))
			
			
	
	tdict = property(get_tdict, set_tdict, None, None)
	comment = property(get_comment, set_comment, None, None)
		
	