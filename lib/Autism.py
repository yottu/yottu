import requests
import socket
import json
import curses
import DebugLog
from Config import Config
import os
from requests.exceptions import SSLError, HTTPError

class Autism:
	def __init__(self, board, threadno="catalog", domain="a.4cdn.org"):
		self.domain = domain
		self.board = board
		self.threadno = threadno
		self.jsoncontent = ""
		self.lasttime = ""
		self.dlog = DebugLog.DebugLog()
		self.cfg = Config(debug=False)
		self.stdscr = None

	@property
	def jsoncontent(self):
		return self.jsoncontent

	@jsoncontent.setter
	def jsoncontent(self, value):
		self.jsoncontent = value

	@jsoncontent.deleter
	def jsoncontent(self):
		del self.jsoncontent
	
	# source can be "board" or "catalog" or "image"
	def _query(self, source, image_filename=None):
		''' Returns datastream of a url generated from its context '''
					
		chunk_size = 4096
		for i in range(1, 10):
			try:
				timeout = 300*i
				
				domain = self.domain
				
				# Build uri path for thread or catalog
				if source == "board":
					path = "/" + self.board + "/thread/" + self.threadno + ".json"
				elif source == "catalog":
					path = "/" + self.board + "/catalog.json"
				elif source == "image":
					domain = "i.4cdn.org"
					path = "/" + self.board + "/" + image_filename
				else:
					return None
					
				uri = "https://" + domain + path # TODO user setting for http/https
				
				self.dlog.msg("JsonFetcher: In _query for " + uri, 5)

				
				headers = {'Accept-encoding': 'gzip'}

				socket.setdefaulttimeout(timeout) # TODO user setting
			
				if (source != "image" and self.lasttime != ""):
					headers.update({'If-Modified-Since': self.lasttime})
				
				# Fetch data and store into content
				content = ""
				request = requests.get(uri, headers=headers, stream=True)
				request.raise_for_status()
				for data in request.iter_content(chunk_size=chunk_size):

					socket.setdefaulttimeout(timeout)
					content += data
					
					# Show thread download progress in the location of the statusbar 
					if self.stdscr:
						try:
							screensize_y, screensize_x = self.stdscr.getmaxyx();
							statusText = source.upper() + "-GET: " + str((len(content)+len(data))/1024) + "K"
							curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # @UndefinedVariable
							sb_progress = ""
							self.stdscr.addstr(screensize_y-2, screensize_x-3-len(statusText), statusText, curses.color_pair(1))  # @UndefinedVariable
							self.stdscr.refresh()
						except Exception as err:
							self.dlog.warn(err, logLevel=3, msg=">>>in ContentFetcher.query()")
							continue
						
					#self.dlog.msg("ContentFetcher: Data transmission from >>>/" + self.board + "/" + self.threadno + "/ (" + str((len(content)+len(data))/1024) + "K)", 3)
				
				if source == "board":
					#self.lasttime = datastream.headers.get('Last-Modified')
					self.lasttime = request.headers.get('Last-Modified')

#				# TODO: remove, requests seems to automatically deflate				
# 				try:
# 					if request.headers.get('Content-Encoding') == 'gzip':
# 						content = gzip.GzipFile(fileobj=StringIO(content)).read()
# 				except:
# 					pass
				
				# Raise redirection status codes mainly to catch 304 Not Modified
				if 300 <= request.status_code < 400:
					http_error_msg = u'%s' % (request.status_code)
					http_error = HTTPError(http_error_msg, response=request)
					raise(http_error)
				
				request.raise_for_status()
				
				return content
			
			except SSLError as e:
				self.dlog.msg(str(e) + " New timeout: " + str(timeout))
				continue
			except HTTPError:
				raise
			except Exception:
				raise
			break
		
	def save_image(self, img_tim, img_ext, orig_filename, thumb=False):
		try:

			if img_ext.lower() == ".webm":
				target_path = self.cfg.get('file.video.directory')
			else:
				target_path = self.cfg.get('file.image.directory')
				
			thumb_path = self.cfg.get('file.thumb.directory')
			target_ext = img_ext.lower()
		
		
			try:
				
				# Thumbnails always have a .jpg extension
				if thumb:
					target_filename = self.board + "-" + img_tim[:64] + "s.jpg"
					filename = str(img_tim)+"s.jpg"
					target_path = thumb_path
					
				else:
					target_filename = self.board + "-" + img_tim[:64] + "-" + orig_filename + target_ext
					filename = str(img_tim+img_ext)
					
			except:
				raise
				
			# Create path if it doesn't exist
			if not os.path.isdir(target_path):
				os.makedirs(target_path)
				
			# Fetch and write image if it doesn't already exist	
			if not os.path.exists(target_path + target_filename):
				imagedata = self._query("image", filename)
				with open(target_path + target_filename, "wb") as f:
					f.write(imagedata)
					
			return target_filename
	
		except:
			raise

	# FIXME just return the content
	def get(self, source="board"):
		content = self._query(source)
		self.jsoncontent = json.loads(content)
		
	def setstdscr(self, stdscr):
		self.stdscr = stdscr