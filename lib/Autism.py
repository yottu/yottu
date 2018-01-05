import requests
import socket
import json
import curses
import DebugLog
from Config import Config
import os
from requests.exceptions import SSLError, HTTPError
import datetime

class Autism:
	def __init__(self, board, threadno="catalog", domain="a.4cdn.org"):
		self.domain = domain
		self.board = board
		self.threadno = str(threadno)
		self.jsoncontent = ""
		self.lasttime = ""
		self.tail_size = 0
		self.is_tail = False
		self.notail = False # True: Force downloading the complete json file
		self.cached_file_exists = False
		self.dlog = DebugLog.DebugLog()
		self.stdscr = None
		self.sb = None
		


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
		

					
		chunk_size = 1024
		for i in range(1, 10):
			try:
				timeout = 300*i
				
				domain = self.domain
				
				# Build uri path for thread or catalog
				if source == "board":
					path = "/" + self.board + "/thread/" + self.threadno
					
					# only fetch last 50 replies on update and if jsondata contains field tail_size
					if self.lasttime and self.tail_size and not self.notail:
						self.is_tail = True
						path += "-tail"
						
					path += ".json"
					
				elif source == "catalog":
					path = "/" + self.board + "/catalog.json"
				elif source == "image":
					domain = "i.4cdn.org"
					path = "/" + self.board + "/" + image_filename
				else:
					return None
					
				uri = "https://" + domain + path # TODO user setting for http/https
				
				self.dlog.msg("ContentFetcher: In _query for " + uri, 4)

				
				headers = {'Accept-encoding': 'gzip'}

				socket.setdefaulttimeout(timeout) # TODO user setting
			
				if (source != "image" and self.lasttime != ""):
					headers.update({'If-Modified-Since': self.lasttime})
				
				# Fetch data and store into content
				content = ""
				request = requests.get(uri, headers=headers, stream=True)
				
				# Get content length for percentage progress
				try:
					content_length = int(request.headers['Content-length'])
					self.dlog.msg("ContentFetcher: Headers: " + str(request.headers), 5)
				except KeyError or ValueError:
					content_length = False
					
				request.raise_for_status()
				for data in request.iter_content(chunk_size=chunk_size):

					socket.setdefaulttimeout(timeout)
					content += data
					
					# Show thread download progress in the location of the statusbar 
					if self.stdscr and self.sb:
						try:
							# Save position
							#saved_y, saved_x = self.stdscr.getyx()

							#screensize_y, screensize_x = self.stdscr.getmaxyx();
							statusText = " " + source.upper() + "-GET: " + str(len(content)/1024) + "K"
							
							# show the progress bar/total size for uncompressed images,
							# TODO need to work with request.raw to get the correct size for gzip'd content 
							if content_length and source == 'image':
								statusText += "/" + str(content_length/1024) + "K" + "(" + str(len(content)*100/(content_length)) + "%)"
							
							self.sb.setStatus(statusText)	
							#self.stdscr.addstr(screensize_y-2, screensize_x-3-len(statusText), statusText, curses.color_pair(1))  # @UndefinedVariable
							# Restore prior position
							#self.stdscr.move(saved_y, saved_x)
							#self.stdscr.refresh()
						except Exception as err:
							self.dlog.warn(err, logLevel=3, msg=">>>in ContentFetcher.query()")
							continue
						
					#self.dlog.msg("ContentFetcher: Data transmission from >>>/" + self.board + "/" + self.threadno + "/ (" + str((len(content)+len(data))/1024) + "K)", 3)
				
				# Raise redirection status codes mainly to catch 304 Not Modified
				if 300 <= request.status_code < 400:
					http_error_msg = u'%s' % (request.status_code)
					http_error = HTTPError(http_error_msg, response=request)
					raise(http_error)
				
				request.raise_for_status()
			
				if source is not "image":
					#self.lasttime = datastream.headers.get('Last-Modified')
					self.lasttime = request.headers.get('Last-Modified')

#				# TODO: remove, requests seems to automatically deflate				
# 				try:
# 					if request.headers.get('Content-Encoding') == 'gzip':
# 						content = gzip.GzipFile(fileobj=StringIO(content)).read()
# 				except:
# 					pass
				
				# blank
				if self.sb:
					self.sb.setStatus(" " + source.upper() + "-GET: " + str(content_length/1024) + "K (100%)")

				return content
			
				
			
			except SSLError as e:
				self.dlog.msg(str(e) + " New timeout: " + str(timeout))
				continue
			except HTTPError:
				raise
			except Exception as e:
				self.dlog.excpt(e, msg=">>>in ContentFetcher.get()", cn=self.__class__.__name__)
				raise
			break
		
	def save_image(self, img_tim, img_ext, orig_filename, thumb=False):
		try:
			
			cfg = Config(debug=False)
			if img_ext.lower() == ".webm":
				target_path = cfg.get('file.video.directory')
			else:
				target_path = cfg.get('file.image.directory')
				
			thumb_path = cfg.get('file.thumb.directory')
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
			self.mkdir(target_path)
				
			# Fetch and write image if it doesn't already exist	
			if not os.path.exists(target_path + target_filename):
				imagedata = self._query("image", filename)
				with open(target_path + target_filename, "wb") as f:
					f.write(imagedata)
					
			return target_filename
	
		except:
			raise

	# FIXME just return the content; i dont think the source thing is really needed as param

	
	def seconds_since_lasttime(self):
		''' Returns the time that has passed since the Last-Modified header stored in self.lasttime '''
		
		try:
			last_modified = datetime.datetime.strptime(self.lasttime, "%a, %d %b %Y %H:%M:%S GMT")
			age_seconds = abs(last_modified-datetime.datetime.utcnow()).seconds
		
			return age_seconds
		
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in ContentFetcher.seconds_since_lasttime()", cn=self.__class__.__name__)
	
	
	def get(self, source="board", nocache=False):
		
		class CatalogAgeExceeded(ValueError):
			pass
		# method is run for the first time
		if not self.jsoncontent:
			try:
				cfg = Config(debug=False)
				
				if source is "board":
					target_path = cfg.get('file.thread.directory')
					target_filename = self.board + "-" + self.threadno + ".json"
				elif source is "catalog":
					target_path = cfg.get('file.catalog.directory')
					target_filename = self.board + "-catalog.json"
				
				self.dlog.msg("Reading " + source + " from: " + target_path + target_filename)	
				with open(target_path + target_filename, "r") as f:
						self.jsoncontent = json.loads(f.read())
				
				if source is "board":		
					self.lasttime = self.jsoncontent['posts'][0]['last-modified']
					
				elif source is "catalog":
					self.lasttime = self.jsoncontent[0]['last-modified']

					catalog_age_seconds = self.seconds_since_lasttime()
					
					if catalog_age_seconds > cfg.get('catalog.cache.maxage'):

						raise CatalogAgeExceeded("Catalog maximum age exceeded.")
				
				self.dlog.msg("Last-Modified (" + target_filename + "): " + self.lasttime, 3)
				
				self.cached_file_exists = True
				return "cached"
			
			except IOError as e:
				self.dlog.msg("ContentFetcher: Board not cached: " + e.filename + " (" + e.strerror + ")", 3)
			except CatalogAgeExceeded as e:
				self.lasttime = ""
				self.dlog.msg("ContentFetcher: Not using cache file: " + str(e), 3)
			except Exception as e:
				self.dlog.excpt(e, msg=">>>in ContentFetcher.get()", cn=self.__class__.__name__)
		
		# update content
		content = self._query(source)

		# Add If-Modified-Since value
		#content['posts'][0].update({u'last-modified':u''.join(self.lasttime)})
		
		try:
			self.jsoncontent = json.loads(content)
		except:
			self.dlog.excpt(e, msg=">>>in ContentFetcher.get()", cn=self.__class__.__name__)
		
		#self.dlog.msg(json.dumps(self.jsoncontent['posts'][0]))
		#content = json.dumps(self.jsoncontent)
		if source is 'board':
			self.jsoncontent['posts'][0].update({u'last-modified':u''.join(self.lasttime)})
			
		elif source is 'catalog':
			self.jsoncontent[0].update({u'last-modified':u''.join(self.lasttime)})

		
		#self.jsoncontent['yottu'] = ['']
		# Set the tail size in ContentFetcher if the thread has one
		try:
			self.tail_size = self.jsoncontent['posts'][0]['tail_size']
		except KeyError: # Thread with less than 100 replies
			self.tail_size = 0
		except TypeError: # Catalog
			self.tail_size = 0
		except Exception as e:
			self.dlog.warn(e, 4, ">>>in ContentFetcher.get()")
			self.tail_size = 0
		finally:
			self.save_jsoncontent(source, content)
			
		return
			
	def save_jsoncontent(self, source, content):
		cfg = Config(debug=False)
		if source is "board":
			target_path = cfg.get('file.thread.directory')
			target_filename = self.board + "-" + self.threadno + ".json"
		elif source is "catalog":
			target_path = cfg.get('file.catalog.directory')
			target_filename = self.board + "-catalog.json"
			
		self.mkdir(target_path)
		
		
		
		# Dump json to file unless it is just the tail
		if not self.is_tail:
			self.dlog.msg("Saving " + source + " to: " + target_path + target_filename)
			with open(target_path + target_filename, "w") as f:
				f.write(json.dumps(self.jsoncontent))
		
			
				
	def mkdir(self, dir):
			''' Create directory plus parents if it doesn't exist '''
			if not os.path.isdir(dir):
				os.makedirs(dir)
		
	def setstdscr(self, stdscr):
		self.stdscr = stdscr