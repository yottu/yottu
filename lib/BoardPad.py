'''
Created on Sep 28, 2015

'''
from Pad import Pad
from ThreadFetcher import ThreadFetcher
import curses
from PostReply import PostReply
from DebugLog import DebugLog
from TermImage import TermImage
from Autism import Autism
from Config import Config
import thread
import time

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr, wl):
		super(BoardPad, self).__init__(stdscr, wl)
		
		self.board = ""
		self.threadno = ""
		self.comment = ""
		self.subject = "" # TODO not implemented
		
		
		
		self.filename = None
		self.ranger = False # If true filename contains path to actual filename
		
		self.tdict = {}
		self.threadFetcher = None
		self.postReply = None
		self.contentFetcher = None
		
		self.time_last_posted = 0 # Time last posted
		self.time_last_posted_board = 0 # Time last posted on board
		self.time_last_posted_thread = 0 # Time last post was made in this thread
		self.thread_wait = 60   # static time to wait after posting in the same thread
		self.board_wait =  60   # static time to wait after posting on the same board
		self.global_wait = 0    # static time to wait after posting
		self.create_wait = 600  # static time to wait before making a new thread
		
		self.dlog = DebugLog(self)

		
	class NoDictError(Exception):
		def __init__(self,*args,**kwargs):
			Exception.__init__(self,*args,**kwargs)

	def get_comment(self):
		return self.__comment


	def set_comment(self, value):
		self.__comment = value
		
	def init_cooldowns(self):
		# get board specifc cooldowns from hardcoded list
		boards_longdelay = ['vg'] # TODO complete list
		
		if self.board in boards_longdelay:
			self.thread_wait = 90
			self.board_wait = 60
			self.global_wait = 0
			self.create_wait = 600
		

	def calc_post_wait_time(self):
		''' returns the time that has to be waited to make a new post on this board '''
	
		cur_time = int(time.time())
		
		# wait time or 0 if it is negative
		cur_thread_wait = max(0, self.time_last_posted_thread + self.thread_wait - cur_time)
		cur_board_wait =  max(0, self.time_last_posted_board + self.board_wait - cur_time)
		cur_global_wait = max(0, self.time_last_posted + self.global_wait - cur_time)
		
		return max(cur_thread_wait, cur_board_wait, cur_global_wait)


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
		self.init_cooldowns()
		
		self.sb.set_board(self.board)
		self.sb.set_threadno(self.threadno)
		
		# FIXME ContentFetcher should probably only be called through ThreadFetcher since it is blocking 
		self.contentFetcher = Autism(self.board, self.threadno)
		self.contentFetcher.setstdscr(self.stdscr)
		
		self.threadFetcher = ThreadFetcher(self.threadno, self.stdscr, self.board, self, self.nickname)
		self.threadFetcher.setDaemon(True)
		self.threadFetcher.start()
		
		self.postReply = PostReply(self.board, self.threadno)
		self.postReply.bp = self
		
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
		
		if not self.filename and not self.comment:
			raise ValueError("Either filename or comment must be set.")
		
		# TODO this timer is intra/interthread/board specific # FIXME timer values are not correct
		wait = self.calc_post_wait_time()
		
		if wait > 0:
			thread.start_new_thread(self.postReply.defer, (wait,), dict(nickname=self.nickname, 
									comment=self.comment, subject=self.subject,
									file_attach=self.filename, ranger=self.ranger))
			response = ("deferred", wait)
			
		else:
			response = self.postReply.post(nickname=self.nickname, comment=self.comment,
										subject=self.subject, file_attach=self.filename,
										ranger=self.ranger)
			

		
		self.filename = None
		self.ranger = None
		
			
		return response
			
	def post_success(self, time):
		''' called after a post was made successfully on this BoardPad '''
		
		self.time_last_posted_thread = time
		# iterate over BoardPads and update last posted time
		for window in self.wl.get_window_list():
			if isinstance(window, BoardPad):
				window.time_last_posted = time
				if window.board == self.board:
					window.time_last_posted_board = time
			
			
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
			orig_filename = u''.join(self.get_tdict()[postno]['filename']) # Uploaders filename
			
			# Return if post has no image attached
			if not img_ext or not img_tim:
				return None
			
		except Exception as err: 
			self.dlog.msg("BoardPad: Exception in assembling filename name: " + str(err))
			raise

		target_filename = self.threadFetcher.save_image(img_tim, img_ext, orig_filename, thumb=thumb)
		
		try:
			
			cfg = Config(debug=False)
			if img_ext.lower() in [ ".jpg", ".png", ".gif" ]:
				file_path = cfg.get('file.image.directory')
			else:
				file_path = cfg.get('file.video.directory')
				
			# use external viewer (e.g. feh)
			
			if ext is True and img_ext == ".webm":
				self.dlog.msg("--Testing")
				subfile = file_path + cfg.get('file.video.subfile')
				if self.threadFetcher.dictOutput.create_sub(postno=postno, subfile=subfile):
					TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg, subfile=subfile)
				else:
					TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg)
				
			elif ext is True:
				TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg)
				
				
			else:
				if thumb:
					file_path = cfg.get('file.thumb.directory')
					
				TermImage.display(target_filename, file_path)
					

					
		except Exception as err:
			self.dlog.msg("Exception in TermImage call: " + str(err))
			
	def play_all_videos(self):
		try:
			# Create list with post numbers containing videos
			postno_vlist = []
			for postno, values in self.tdict.items():
				if values['ext'].lower() == ".webm":
					postno_vlist.append(postno)
			
			
			for i, postno in enumerate(postno_vlist, 1):
					
					# Download next video in a thread
					if i < len(postno_vlist):
						thread.start_new_thread(self.download_image, (postno_vlist[i],))
					
					# Play current video	
					self.show_image(postno, ext=True, fullscreen=True)
					
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in play_all_videos()", cn=self.__class__.__name__)
			
	def video_stream(self, source):
		try:
			# Testing TODO clean up
			
			cfg = Config(debug=False)
			file_path = cfg.get('file.video.directory')
			subfile = file_path + cfg.get('file.video.subfile')
			if self.threadFetcher.dictOutput.create_sub(postno=self.threadFetcher.dictOutput.originalpost['no'], subfile=subfile):
				self.dlog.msg("Streaming from source " + source)
				self.threadFetcher.dictOutput.append_to_subfile = True
				TermImage.display_webm(source, stream=True, wait=False, fullscreen=True, path=file_path, subfile=subfile)
				
				
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in video_stream()", cn=self.__class__.__name__)
	
	def download_image(self, postno):
		try:
			postno = int(postno)
			if not self.tdict:
				raise self.NoDictError("BoardPad has no thread dictionary.")
			img_ext =  str(self.get_tdict()[postno]['ext']) # image extension, eg ".jpg"
			img_tim = str(self.get_tdict()[postno]['tim'])  # Actual filename as saved on server
			orig_filename = u''.join(self.get_tdict()[postno]['filename']) # Uploaders filename
			
			# Return if post has no image attached
			if not img_ext or not img_tim:
				return None
			
		except Exception as err: 
			self.dlog.msg("BoardPad: Exception in assembling filename name: " + str(err))
			raise

		target_filename = self.threadFetcher.save_image(img_tim, img_ext, orig_filename)
		
			
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
		
	