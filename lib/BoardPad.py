'''
Created on Sep 28, 2015

'''
from Pad import Pad
from ThreadFetcher import ThreadFetcher
from PostReply import PostReply
from DebugLog import DebugLog
from TermImage import TermImage
from Autism import Autism
import thread

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr, wl):
		super(BoardPad, self).__init__(stdscr, wl)
		self.board = ""
		self.threadno = ""
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


	#FIXME apparently I don't need these in python, since there are no private attributes
	def get_tdict(self):
		return self.__tdict
	def set_tdict(self, value):
		self.__tdict = value
	def get_tdict_val(self, key1, key2):
		return self.__tdict[key1][key2]
	def set_tdict_val(self, key1, key2, value):
		self.__tdict[key1][key2] = value

		
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
			if not self.postReply.display_captcha():
				self.dlog.msg("w3mimgdisplay: Could not overlay captcha")
		except:
			self.dlog.msg("Could not display captcha. Check if w3mimgdisplay and feh are installed.")
		
	def join(self, board, threadno, nickname):
		self.board = board
		self.threadno = threadno
		self.set_nickname(nickname)
		
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
			response = self.postReply.post(self.nickname, self.comment, self.subject, self.filename, self.ranger)
		elif self.comment:
			response = self.postReply.post(self.nickname, self.comment)
		else:
			raise ValueError("Either filename or comment must be set.")
		
		self.filename = None
		self.ranger = None
		
		if response == 200:
			self.threadFetcher.dictOutput.mark(self.comment)
		
		return response
			
			
	def update_thread(self):
		''' update (fetch) thread immediately '''
		self.threadFetcher.update()
		
	def show_image_thumb(self, postno):
		self.show_image(postno, ext=False, thumb=True)
		
		
	def show_image(self, postno, ext=False, fullscreen=False, thumb=False, setbg=False):
		try:
			postno = int(postno)
			if not self.tdict:
				raise self.NoDictError("BoardPad has no thread dictionary.")
			
			img_ext =  str(self.get_tdict()[postno]['ext']) # image extension, eg ".jpg"
			img_tim = str(self.get_tdict()[postno]['tim'])  # Actual filename as saved on server
			orig_filename = str(self.get_tdict()[postno]['filename']) # Uploaders filename
			
			# Return if post has no image attached
			if not img_ext or not img_tim:
				return None
			
		except Exception as err: 
			self.dlog.msg("BoardPad: Exception in assembling filename name: " + str(err))
			raise

		target_filename = self.threadFetcher.save_image(img_tim, img_ext, orig_filename, thumb=thumb)
		
		try:
			# use external viewer (e.g. feh)
			if ext is True:
				TermImage.display_ext(target_filename, fullscreen=fullscreen, path="./cache/", setbg=setbg)
				
			else:
				if img_ext == ".jpg" or img_ext == ".png" or img_ext == ".gif":
					file_path = "./cache/"
					if thumb:
						file_path += "thumbs/"

					TermImage.display(target_filename, file_path)
					
				else:
					self.dlog.msg(img_ext + " filename not viewable.")
					
		except Exception as err:
			self.dlog.msg("Exception in TermImage call: " + str(err))
			
	def download_images(self):
		Pad.download_images(self)
		try:
			for postno, values in self.tdict.items():
				img_tim = str(values['tim'])
				img_ext = values['ext']
				orig_filename = values['filename'][:64]
				if not img_ext or not img_tim or not orig_filename:
					continue
				
				# FIXME too many parallel downloads
				thread.start_new_thread(self.threadFetcher.save_image, (img_tim, img_ext, orig_filename))
				
		except (KeyError, TypeError) as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.download_images()")
			pass
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.download_images()")
			pass
		
				
	
	tdict = property(get_tdict, set_tdict, None, None)
	comment = property(get_comment, set_comment, None, None)
		
	