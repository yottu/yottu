import urllib2
import json
import DebugLog
import socket
import curses

class Autism:
	def __init__(self, board, threadno="catalog", domain="a.4cdn.org"):
		self.domain = domain
		self.board = board
		self.threadno = threadno
		self.jsoncontent = ""
		self.lasttime = ""
		self.content = ""
		self.dlog = DebugLog.DebugLog()

	@property
	def jsoncontent(self):
		return self.jsoncontent

	@jsoncontent.setter
	def jsoncontent(self, value):
		self.jsoncontent = value

	@jsoncontent.deleter
	def jsoncontent(self):
		del self.jsoncontent
	
	# source = ["board", "catalog"]
	def _query(self, source):
		chunkSize = 4096
		for i in range(1, 10):
			try:
				timeout = 300*i
				
				# Build uri path for thread or catalog
				if source == "board":
					path = "/" + self.board + "/thread/" + self.threadno + ".json"
				elif source == "catalog":
					path = "/" + self.board + "/catalog.json"
					
				uri = "http://" + self.domain + path # TODO user setting for http/https
				
				self.dlog.msg("JsonFetcher: In _query for " + uri, 3)

				
				request = urllib2.Request(uri)
				socket.setdefaulttimeout(timeout) # TODO user setting
			
				if (self.lasttime != ""):
					request.add_header('If-Modified-Since', self.lasttime)
				
				# Fetch data and store into self.content
				opener = urllib2.build_opener()
				datastream = opener.open(request)
				self.content = ""
				while True:
					data = datastream.read(chunkSize)
					if not data:
						break
					socket.setdefaulttimeout(timeout)
					self.content += data
					
					# Show thread download progress in statusbar 
					if self.stdscr:
						try: # TODO this should be in another class
							screensize_x, screensize_y = self.stdscr.getmaxyx();
							statusText = str((len(self.content)+len(data))/1024) + "K"
							curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
							self.stdscr.addstr(screensize_x-2, screensize_y-5-len(statusText), "GET: " + statusText, curses.color_pair(1))
							self.stdscr.refresh()
						except:
							continue
						
					self.dlog.msg("JsonFetcher: Retrieving thread " + self.threadno + " (" + str((len(self.content)+len(data))/1024) + "K)", 3)
	
				self.jsoncontent = json.loads(self.content)
				self.lasttime = datastream.headers.get('Last-Modified')
			except urllib2.ssl.SSLError as e:
				self.dlog.msg(str(e) + " New timeout: " + str(timeout))
				continue
			except Exception:
				raise
			break
			
	def get(self, source="board"):
		self._query(source)
		
	def setstdscr(self, stdscr):
		self.stdscr = stdscr