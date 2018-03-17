'''
Created on Sep 28, 2015

'''
import thread
import time

from Pad import Pad
from ThreadFetcher import ThreadFetcher
from PostReply import PostReply
from TermImage import TermImage
from Autism import Autism
from Subtitle import Subtitle
from RelayChat import RelayChat
import re

class BoardPad(Pad):
	'''
	classdocs
	'''
	def __init__(self, stdscr, wl):
		super(BoardPad, self).__init__(stdscr, wl)
		self.board = ""
		self.threadno = ""
		self.url = "" # URL of thread
		
		self.db = wl.db
		self.cfg = wl.cfg
		
		# Attributes used while creating a new post
		self.post_comment = ""
		self.post_subject = "" # TODO not implemented
		self.post_filename = None
		self.post_ranger = False # If true post_filename contains path to actual filename
		
		self.tdict = {}
		self.threadFetcher = None
		self.postReply = None
		self.contentFetcher = None
		
		self.subtitle = None # Subtitle class, gets initialized when needed
		
		self.catalog_page = None # CatalogFetcher will update this with the current page  # TODO NotImplemented
		
		self.time_last_posted = 0 # Time last posted
		self.time_last_posted_board = 0 # Time last posted on board
		self.time_last_posted_thread = 0 # Time last post was made in this thread
		self.thread_wait = 60   # static time to wait after posting in the same thread
		self.board_wait =  60   # static time to wait after posting on the same board
		self.global_wait = 0    # static time to wait after posting
		self.create_wait = 600  # static time to wait before making a new thread
		
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
		self.dlog.msg("BoardPad: on_resize", 5)
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
				self.wl.compadout("w3mimgdisplay: Could not overlay captcha, try the -X switch if you are using ssh")
				self.dlog.msg("w3mimgdisplay: Could not overlay captcha, try the -X switch if you are using ssh")
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in NoDictError.display_captcha()", cn=self.__class__.__name__)
			self.dlog.msg("Could not display captcha. Check if w3mimgdisplay and feh are installed.")
		
	def join(self, board, threadno, nickname):
		try:
			self.board = board
			self.threadno = threadno
			self.set_nickname(nickname)
			self.init_cooldowns()
			
			self.url = "https://boards.4chan.org/" + str(self.board) + "/thread/" + str(self.threadno)
			
			self.sb.set_board(self.board)
			self.sb.set_threadno(self.threadno)
			
			# FIXME ContentFetcher should probably only be called through ThreadFetcher since it is blocking 
			self.contentFetcher = Autism(self.board, self.threadno)
			self.contentFetcher.setstdscr(self.stdscr)
			self.contentFetcher.sb = self.sb
			
			self.postReply = PostReply(self.board, self.threadno)
			self.postReply.bp = self
			
			self.threadFetcher = ThreadFetcher(self.threadno, self.stdscr, self.board, self, self.nickname)
			self.threadFetcher.setDaemon(True)
			self.threadFetcher.start()
			
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.join()", cn=self.__class__.__name__)

		
	def post_prepare(self, comment="", filename=None, ranger=False, subject=""):
		self.post_comment = comment
		self.post_filename = filename
		self.post_ranger = ranger
		self.post_subject = subject
		self.get_captcha()
		
	def get_captcha(self):
		self.postReply.get_captcha_challenge()
		self.sb.setStatus(self.postReply.captcha2_challenge_text)
		self.display_captcha()
			
		
	def set_captcha(self, captcha):
		self.postReply.set_captcha2_solution(captcha)
		
	def post_submit(self):		
		try:
		
			if not self.post_filename and not self.post_comment:
				raise ValueError("Either filename or comment must be set.")
			
			# TODO this timer is intra/interthread/board specific # FIXME timer values are not correct
			wait = self.calc_post_wait_time()
			
			if wait > 0:
				thread.start_new_thread(self.postReply.defer, (wait,), dict(nickname=self.nickname, 
										comment=self.post_comment, subject=self.post_subject,
										file_attach=self.post_filename, ranger=self.post_ranger))
				response = ("deferred", wait)
				
			else:
				response = self.postReply.post(nickname=self.nickname, comment=self.post_comment,
											subject=self.post_subject, file_attach=self.post_filename,
											ranger=self.post_ranger)
				
	
			
			self.post_filename = None
			self.post_ranger = None
			
				
			return response
	
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.post_submit()", cn=self.__class__.__name__)
			raise

			
	def post_success(self, time):
		''' called after a post was made successfully on this BoardPad '''
		
		self.time_last_posted_thread = time
		# iterate over BoardPads and update last posted time
		for window in self.wl.get_window_list():
			if isinstance(window, BoardPad):
				window.time_last_posted = time
				if window.board == self.board:
					window.time_last_posted_board = time
					
	def update_db(self, postno):
		''' Insert user made posts into database/threadwatcher if enabled in config '''
		
		try:
			if self.cfg.get('database.sqlite.enable'):
				self.db.insert_post(self.board, self.threadno, postno)
			if self.cfg.get('threadwatcher.enable'):
				self.wl.tw.insert(self.board, postno, self.threadno)
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in BoardPad.update_db()", cn=self.__class__.__name__)
							
	def update_thread(self, notail=False):
		''' update (fetch) thread immediately '''
		self.threadFetcher.update(notail)
		
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
			self.dlog.msg("BoardPad: Exception in assembling filename: " + str(err))
			raise

		target_filename = self.threadFetcher.save_image(img_tim, img_ext, orig_filename, thumb=thumb)
		
		try:
			
			if img_ext.lower() in [ ".jpg", ".png", ".gif" ]:
				file_path = self.cfg.get('file.image.directory')
			else:
				file_path = self.cfg.get('file.video.directory')
				
			# use external viewer (e.g. feh)
			
			if ext is True and img_ext == ".webm":
				
				
				subfile = file_path + self.cfg.get('file.video.subfile')
				subtitle = Subtitle(subfile, self.dlog)
				
				if subtitle.create_sub(postno=postno, tdict=self.tdict):
					TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg, subfile=subfile)
				else:
					TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg)
				
			elif ext is True:
				TermImage.display_ext(target_filename, fullscreen=fullscreen, path=file_path, setbg=setbg)
				
				
			else:
				if thumb:
					file_path = self.cfg.get('file.thumb.directory')
					
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
	
	# FIXME this doesn't require a boardpad, so it should be in the Pad class
	def twitch_stream(self, channel):
		try:
			termimg = TermImage()
			
			source = "https://twitch.tv/" + channel
			
			twitch_nick = self.cfg.get('video.twitch.nick')
			twitch_oauth = self.cfg.get('video.twitch.oauth')
			twitch_subfile = None
			twitch_host = self.cfg.get('video.twitch.irc_host')
			twitch_port = self.cfg.get('video.twitch.irc_port')
			
			if not twitch_nick and not twitch_oauth:
				self.wl.compadout("set twitch_nick and oauth to connect to twitch chat")
				
			
			else:
				twitch_subfile = self.cfg.get('file.video.directory') \
							+ self.cfg.get('file.video.twitch.subfile')
				sub = Subtitle(twitch_subfile, self.dlog, stream=True)
				sub.create_sub()
				
				irc = RelayChat(twitch_host, twitch_port, twitch_nick, twitch_oauth, "#" + channel, sub, self.dlog)
				thread.start_new_thread(irc.connect, ())
			
				subfile = self.cfg.get('file.video.directory') + self.cfg.get('file.video.subfile')
				self.subtitle = Subtitle(subfile, self.dlog, stream=True)
				self.subtitle.append_to_subfile = True
				self.subtitle.create_sub(postno=self.threadFetcher.dictOutput.originalpost['no'], tdict=self.tdict)
			
			
			thread.start_new_thread(termimg.stream, (self, irc, source, twitch_subfile, subfile))
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.twitch_stream()", cn=self.__class__.__name__)
		
	
	def video_stream(self, source, site=None, wait=False):
		'''
		Stream video from an URL 
		'''
		
		if site == "twitch":
			
			twitch_channel = source.split("/").pop()
			self.twitch_stream(twitch_channel)
			return
			
		elif site == "youtube":
			source = "https://youtube.com/?v=" + source.split("v=").pop()
		
		try:
			file_path = self.cfg.get('file.video.directory')
			subfile =  file_path + self.cfg.get('file.video.subfile')
			self.subtitle = Subtitle(subfile, self.dlog, stream=True)
				
			
			self.subtitle.append_to_subfile = True
			if self.subtitle.create_sub(postno=self.threadFetcher.dictOutput.originalpost['no'], tdict=self.tdict):
				self.dlog.msg("Streaming from source " + source)
				
				TermImage.display_webm(source, stream=True, wait=wait, fullscreen=True, path=file_path, subfile=subfile)
				
			else:
				raise RuntimeError("Could not create subtitle file: " + str(subfile))
				TermImage.display_webm(source, stream=True, wait=wait, fullscreen=True, path=file_path)

				
				
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
			self.dlog.msg("BoardPad: Exception in assembling filename: " + str(err))
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
		
	def search_string_instances(self, search_string):
		''' return list of tuples (whole comment, [matches]) in a tdict containing search string '''
		
		com_match_list = []
		try:
			for post in self.tdict.values():
				com = post['com'].encode('utf-8')

				try:
					matched = re.findall(search_string, com)
				except:
					pass
				
				
				if matched:
					self.dlog.msg("--DEBUG: " + str(search_string) + " in " + str(com) + ": " + str(matched))
					com_match_list.append((com, matched))
				
			return com_match_list
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.search_string_instances()", cn=self.__class__.__name__)
	
	def search_mp_out(self, search_string):
		
		try:
			search_string = search_string.encode('utf-8')
			
			result = self.search_string_instances(search_string)
			if result:
				for i, match in enumerate(result, 1):
					self.wl.msgpadout(search_string + " (" + str(i) + "): " + str(match[0]))
				
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in BoardPad.search_mp_out()", cn=self.__class__.__name__)
			
	def youtube_play_all(self):
		results = self.search_string_instances("youtube.com/\S+")
		results += self.search_string_instances("youtu.be/\w+")
		
		for sources in results:
			self.dlog.msg("--DEBUG: Trying to stream from list " + str(sources[1]))
			for source in sources[1]:
				self.video_stream(source, site="youtube", wait=True)
		

	tdict = property(get_tdict, set_tdict, None, None)
	post_comment = property(get_comment, set_comment, None, None)