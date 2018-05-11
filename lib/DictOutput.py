# -*- coding: utf-8 -*-
'''
Created on Oct 4, 2015

'''
from __future__ import division

from Notifier import Notifier

from random import randint
import curses
import re
import datetime
import time
import json

from bs4 import BeautifulSoup

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

class DictOutput(object):
	def __init__(self, bp):
		self.bp = bp
		self.tdict = {} # contains all posts (including OP)
		self.originalpost = {} # contains the OP post
		
		self.no_abs_to_rel_dict = {} # dict that associates absolute with relative post numbers 
		self.no_rel = 0 # counter for relative post numbers
		
		self.thread = "" # json
		self.pages = "" # json (/board/threads.json)
		self.nickname = self.bp.get_nickname()
		self.comment_tbm = None
		self.comment_tbm_timeout = 0
		
		self.dlog = self.bp.wl.dlog
		
		self.title = u""
		self.cfg = self.bp.wl.cfg
		
		self.db = self.bp.wl.db
		#self.db = Database()

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value
		
	def mark(self, comment):
		''' look for comment to be marked as user post in the next n refreshes '''
		
		if comment == "":
			comment = "[File only]"
		
		self.comment_tbm_timeout = 3 # is decreased every refresh
		self.comment_tbm = comment # FIXME does not work with utf-8
		self.comment_tbm = re.sub('>>(\d+)', '\g<1>', self.comment_tbm)
		self.comment_tbm = re.sub('\n', ' ', self.comment_tbm)
		
	
	def refresh_pages(self, jsonpages):
		try:
			for page in json.loads(jsonpages):
				for thread in page['threads']:
					
					if str(self.originalpost['no']) == str(thread['no']):
						self.bp.tb.page = int(page['page'])
					
		except Exception as e:
			self.bp.tb.page = 0
			self.dlog.warn(e, logLevel=3, msg=">>>in DictOutput.refresh_pages()")

	def refresh(self, jsonobj, jsonpages=None):
		self.thread = jsonobj
		self.pages = jsonpages
		
		#self.tdict['OP'] = {'no': 213, 'com': 'unset', 'sub': 'unset'.encode('utf-8'), 'semantic-url': 'unset'.encode('utf-8')}
		
		# Get some information about the thread (post count, reply count, etc) from the first post
		self.bp.stdscr.noutrefresh() 
		try:
			self.originalpost.update({'no': self.thread['posts'][0]['no']})
			
			try: 
				self.originalpost.update({'replies': self.thread['posts'][0]['replies']})
				self.originalpost.update({'images': self.thread['posts'][0]['images']})
				self.originalpost.update({'bumplimit': self.thread['posts'][0]['bumplimit']})
				self.originalpost.update({'imagelimit': self.thread['posts'][0]['imagelimit']})
				
				try:
					self.originalpost.update({'archived': self.thread['posts'][0]['archived']})
				except KeyError:
					self.originalpost['archived'] = 0


					
				self.bp.tb.bumplimit = self.originalpost['bumplimit']
				self.bp.tb.imagelmit = self.originalpost['imagelimit']
				self.bp.tb.images = self.originalpost['images']
				self.bp.tb.replies = self.originalpost['replies']
				
				try:
					self.originalpost.update({'unique_ips': self.thread['posts'][0]['unique_ips']})
					if int(self.originalpost['unique_ips']) > int(self.bp.tb.unique_ips) and self.bp.tb.unique_ips != 0:
						self.bp.tb.unique_ips_changed = True
					else:
						self.bp.tb.unique_ips_changed = False
					
					
					self.bp.tb.unique_ips = self.originalpost['unique_ips']

				# Archived threads do not set unique_ips
				except:
					self.bp.tb.unique_ips = "?"
				
				# Look up catalog page the thread is currently in
				self.refresh_pages(jsonpages)

			except Exception as e: 
				self.dlog.warn(e, logLevel=3, msg=">>>in DictOutput.refresh() -> OP")
			
			try:
				self.originalpost.update({'semantic_url': self.thread['posts'][0]['semantic_url'].encode('utf-8')})
			except:
				pass 
			
			try:
				com = self.clean_html(self.thread['posts'][0]['com']) 
				self.originalpost.update({'com': com.encode('utf-8')})
				self.title = self.originalpost['com']
			except: pass
			
			try:
				sub = self.clean_html(self.thread['posts'][0]['sub'])
				self.originalpost.update({'sub': sub.encode('utf-8')})
				self.title = self.originalpost['sub']
			except:
				pass
			
		except Exception as e:
			self.dlog.warn(e, msg=">>>in DictOutput.refresh()", cn=self.__class__.__name__)
			raise
		
		db_posts = []
		try:
			# Array containing posts from previous sessions
			db_posts = self.db.get_postno_from_threadno(self.originalpost['no'])
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in refresh() -> db_posts", cn=self.__class__.__name__)
		
		for posts in self.thread['posts']:
			
			# skip post if base data can't be processed
			try:
				
				no = posts['no']
				
				# skip post if it was already processed
				if no in self.tdict:
					continue
				
				self.no_abs_to_rel_dict[no] = self.no_rel
				
				name = posts['name'][:16]
				time = datetime.datetime.fromtimestamp(posts['time']).strftime('%H:%M')
			except:
				continue
				
			#color = randint(11, 240)
			color = self.no_rel%244+11
			
			# re-assign black color # TODO is this term/color-independent?
			if color%244 == 26:
				color = 11
	
			refposts = "" # posts referenced in a reply
			try: country = posts['country']
			except: country = ""
			try:
				com = posts['com']
				com = re.sub('<br>', ' ', com)
				# save all post quotes in a list (without >>)
				refposts = re.findall('&gt;&gt;(\d+)', com)
				# remove >> from quotes for now
				com = re.sub('&gt;&gt;(\d+)', '\g<1>', com)
				#com = re.sub('&#039;', '\'', com)
				#com = re.sub('&gt;', '>', com)
				#com = re.sub('&lt;', '<', com)
				#com = re.sub('&quot;', '"', com)
				#com = re.sub('<[^<]+?>', '', com)
				com = self.clean_html(com)
			except: com = "[File only]"  # @UndefinedVariable
			try:
				trip = posts['trip']
			except:
				trip = ""
			try:
				filename = self.clean_html(posts['filename'])
			except:
				filename = ""
			
			try:
				fsize = posts['fsize']
			except:
				fsize = 0
				
			try:
				tim = posts['tim']
			except:
				tim = ""
			try:
				ext = self.clean_html(posts['ext'])
				file_ext_short = ext[1:2].upper()
			except:
				ext = ""
				file_ext_short = " "
				
			# Compare comment content to recently posted comment
			try:
				marked = False
				if self.comment_tbm_timeout > 0:
					
					self.dlog.msg("comment wrote: " + str(com) + " comment to be matched: " + str(self.comment_tbm), 4)
					# TODO regex match with n percentage accuracy should work better
					if com == self.comment_tbm:
						marked = True
						self.comment_tbm = None
						self.comment_tbm_timeout = 0
						self.bp.update_db(no)
						
					self.bp.threadFetcher.update_n = 3
					self.comment_tbm_timeout -= 1
				if no in db_posts:
					marked = True
			except:
				pass
			
	
			try:
				
				# TODO maybe just use the structure from 4chan's json. Maybe.
				self.tdict[no] = {'country':country, 'name':name, 'time':time,
						'com':com, 'trip':trip, 'color':color, 'filename':filename,
						'tim':tim, 'ext':ext, 'marked':marked, 'refposts':refposts,
						'fsize':fsize }
				
				def filter_scan(filterdict):
					filter_matched = False
					for rule in json.loads(filterdict):

						for section in json.loads(rule['filter']):
							
							
							try: test = json.loads(rule['filter'])
							except: pass
							
							if self.tdict[no][section] in test[section] and self.tdict[no][section]:
								self.dlog.msg("--Matched: " + str(self.tdict[no][section]) + " in " + str(test[section]), 4)
								filter_matched = True
							elif self.tdict[no][section] not in test[section]:
								self.dlog.msg("--Not matched: " + str(self.tdict[no][section]) + " in " + str(test[section]), 4)
								filter_matched = False
								break
							else:
								self.dlog.msg("--Not matched (section does not exist): " + str(section), 4)
								filter_matched = False
								break
							
					self.dlog.msg("--Matched (" + str(rule) + "): " + str(filter_matched), 4)
					return filter_matched
				
				# Scan for matched filters 
				filter_matched = False
				if self.cfg.get('filter.ignore.list') and filter_scan(self.cfg.get('filter.ignore.list')):
					filter_matched = True
				if self.cfg.get('filter.except.list') and filter_scan(self.cfg.get('filter.except.list')):
					filter_matched = False
				
						
				# ####### FIXME: Remove. This is to test filtering
# 				pattern = re.compile(ur'Japanese', re.UNICODE)
# 				filter_matched = False
# 				if country in ["DE", "TH"] and self.bp.board == "int" and name == "Anonymous" \
# 					and trip == "" and pattern.search(self.originalpost['com']):
# 					
# 					filter_matched = True
# 					
# 					# Exception for filter
# 					for letter in com:
# 						if unicodedata.east_asian_width(letter) in ['W', 'F']:
# 							filter_matched = False
# 							break
# 				elif country == "US" and name == "Anonymous":
# 					filter_matched = True
							
				if filter_matched:
					self.dlog.msg("--FILTER TEST: Skipping comment: " + str(no))
					continue
			except Exception as err:
				self.dlog.warn(err, msg=">>>in DictOutput.refresh() (-> filter)")
				
			try:			
				#if filter_matched:	
				#		
				#	continue
				####### End of filter test ###########
				

				
				# Write [TIME] <Name>
				self.bp.addstr("", curses.color_pair(color))  # @UndefinedVariable
				self.bp.addstr(time)
				
				if self.cfg.get("board.postno.style") is 'relative':
					self.bp.addstr(" >>" + str(self.no_rel).zfill(3), curses.color_pair(color))  # @UndefinedVariable
				else:
					self.bp.addstr(" >>" + str(no), curses.color_pair(color))  # @UndefinedVariable
				

					
				# Add country code	
				self.bp.addstr(" " + country)
				
				# Count of characters that are in every new BoardPad line (for indentation on nl in bp)
				indent = len(time)+len(str(no))+len(country)+4
	
				# Make own nickname bold
				if re.match(str(self.nickname), name) or marked:
					
# 					if not self.nickname:
# 						nick = "Anonymous"
# 					else:
# 						nick = self.nickname
					self.bp.addstr(" <" + file_ext_short + name + "> ", curses.A_BOLD)  # @UndefinedVariable
	
				# Make name decoration stand out if file is attached
				else:
					self.bp.addstr(" <", curses.color_pair(250))  # @UndefinedVariable
					self.bp.addstr(file_ext_short, curses.color_pair(250) | curses.A_BOLD)  # @UndefinedVariable
					self.bp.addstr(name.encode('utf8'), curses.A_DIM)  # @UndefinedVariable
					if self.cfg.get("board.postno.style") is 'hybrid':
						self.bp.addstr("-" + str(self.no_rel).zfill(3), curses.color_pair(color))  # @UndefinedVariable
					self.bp.addstr("> ", curses.color_pair(250))  # @UndefinedVariable
				
				# width of name including unicode east asian characters + len("<  > ") == 5	
				indent += self.bp.calcline(name.encode('utf8'))+5
				
				comlist = com.split()
				
				try:
					
# 					# Post filename if exists
# 					try:
# 						if filename:
# 							self.bp.addstr("[", curses.A_BOLD)  # @UndefinedVariable
# 							self.bp.addstr(filename[:12])
# 							self.bp.addstr("] ", curses.A_BOLD)  # @UndefinedVariable
# 					except:
# 						pass
					
					# Iterate over every word in a comment
					for word in comlist:
						
						
						# refposts contains all >>(\d+) in a comment
						if word not in refposts:
							# Output non-reference
							self.bp.addstr(u''.join((word + " ")).encode('utf8'), curses.A_NORMAL, indent)  # @UndefinedVariable
						# Handle references (>>(\d+))	
						else:
							
							# Comment and reference color encoding
							try:
								refcolor = self.tdict[int(word)]['color']
								if self.cfg.get("board.postno.style") is not 'absolute':
									self.bp.addstr(">>" + str(self.no_abs_to_rel_dict[int(word)]) + " ", curses.color_pair(refcolor), indent)  # @UndefinedVariable
								else:
									self.bp.addstr(">>" + word + " ", curses.color_pair(refcolor), indent)  # @UndefinedVariable
								
								# Add (You) to referenced posts written by self.nickname
								if re.match(self.tdict[int(word)]['name'], str(self.nickname)) or self.tdict[int(word)]['marked'] == True:
									self.bp.addstr("(You) ", curses.A_BOLD | curses.color_pair(221), indent, mentioned=True)  # @UndefinedVariable
									try:
										Notifier.send(name, com)
									except Exception as e:
											self.dlog.excpt(e, msg=">>>in DictOutput.refresh()", cn=self.__class__.__name__)
											raise
									
								# highlight OP reference
								if re.match(word, str(self.originalpost['no'])):
									try:
										self.bp.addstr("(OP) ", curses.A_BOLD | curses.color_pair(4), indent)  # @UndefinedVariable
									except:
										raise
									
							except KeyError:
								self.bp.addstr(word + " ", curses.A_DIM, indent)  # @UndefinedVariable
							
							except Exception as err:
								self.dlog.excpt(err, msg=">>>in DictOutput.filter_scan()", cn=self.__class__.__name__)
								
				except:
					self.bp.addstr("[File only]", curses.A_DIM, indent)  # @UndefinedVariable
			except:
				raise
	
			self.bp.addstr("\n", curses.A_NORMAL, indent)  # @UndefinedVariable
			self.no_rel += 1
			
		try:
			if self.bp.subtitle.append_to_subfile:
				self.bp.subtitle.subfile_append(com)
		except AttributeError:
			pass
		
		# refetch entire thread on post count mismatch
		try:
			if len(self.tdict) != int(self.thread['posts'][0]['replies']) + 1:
				self.bp.update_thread(notail=True)
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in DictOutput.refresh() ->refetch", cn=self.__class__.__name__)
	
		if self.originalpost['archived']:
			self.bp.threadFetcher.stop()
			self.bp.sb.setStatus("ARCHIVED")
			
		curses.doupdate()  # @UndefinedVariable

	
	def getTitle(self):
		return self.title
	

	# source: https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
	# Copy of function also exists in ThreadWatcher # TODO merge
	def clean_html(self, html):
		soup = BeautifulSoup(html)
		
		# kill all script and style elements
		for script in soup(["script", "style"]):
			script.extract()
		
		# get text
		text = soup.get_text()
		
		# break into lines and remove leading and trailing space on each
		lines = (line.strip() for line in text.splitlines())
		
		# break multi-headlines into a line each
		chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
		
		# drop blank lines
		text = '\n'.join(chunk for chunk in chunks if chunk)
		
		return(text)
	
	
	tdict = property(get_tdict, set_tdict, None, None)
	
