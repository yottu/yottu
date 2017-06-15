import urllib2
import json
import DebugLog
import socket
import curses
import os
from StringIO import StringIO
import gzip

class Autism:
	def __init__(self, board, threadno="catalog", domain="a.4cdn.org"):
		self.domain = domain
		self.board = board
		self.threadno = threadno
		self.jsoncontent = ""
		self.lasttime = ""
		self.dlog = DebugLog.DebugLog()
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
		chunkSize = 4096
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

				
				request = urllib2.Request(uri)
				request.add_header('Accept-encoding', 'gzip')

				socket.setdefaulttimeout(timeout) # TODO user setting
			
				if (source != "image" and self.lasttime != ""):
					request.add_header('If-Modified-Since', self.lasttime)
				
				# Fetch data and store into content
				opener = urllib2.build_opener()
				datastream = opener.open(request)
				content = ""
				while True:

					data = datastream.read(chunkSize)
					if not data:
						if datastream.info().get('Content-Encoding') == 'gzip':
							f = gzip.GzipFile(fileobj=StringIO(content))
							content = f.read()
						break
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
						except:
							continue
						
					#self.dlog.msg("ContentFetcher: Data transmission from >>>/" + self.board + "/" + self.threadno + "/ (" + str((len(content)+len(data))/1024) + "K)", 3)
				
				if source == "board":
					self.lasttime = datastream.headers.get('Last-Modified')
				
				return content
			
			except urllib2.ssl.SSLError as e:
				self.dlog.msg(str(e) + " New timeout: " + str(timeout))
				continue
			except urllib2.HTTPError:
					raise
			except Exception:
				raise
			break
		
	def save_image(self, img_tim, img_ext, orig_filename, thumb=False):
		try:
			target_path = "./cache/" # FIXME should be set through Config.py
			thumb_path = "./cache/thumbs/"
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