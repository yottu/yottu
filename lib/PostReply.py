'''
Created on May 15, 2017

@author: yottudev@gmail.com
'''
        
import re
import urllib
import urllib2
from bs4 import BeautifulSoup
import requests # FIXME use either urllib or requests, what is best for python 2 and 3?
from TermImage import TermImage
import mimetypes

import warnings
import os.path
import time
import thread
from DebugLog import DebugLog
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

class PostReply(object):
    '''
    classdocs
    '''

    def __init__(self, board, threadno):
        self.board = board
        self.threadno = threadno
        
        self.sitekey = "6Ldp2bsSAAAAAAJ5uyx_lx34lJeEpTLVkP5k04qc"
        self.captcha_url = "https://www.google.com/recaptcha/api/noscript"
        self.captcha_image_base_url = "https://www.google.com/recaptcha/api/"
        
        self.captcha_image = ""
        self.captcha_image_filename = "yottu-captcha.jpg"
        
        self.captcha_challenge = ""
        self.captcha_solution = ""
        
        self.lock = thread.allocate_lock()
        self.dictOutput = None
        self.bp = None
        
        self.dlog = DebugLog()
        
    class PostError(Exception):
        def __init__(self,*args,**kwargs):
            Exception.__init__(self,*args,**kwargs)

    def get_captcha_solution(self):
        return self.__captcha_solution


    def set_captcha_solution(self, value):
        self.__captcha_solution = value


    def _query(self):
        pass

    def get_captcha_challenge(self):
        """
            1. Query self.captcha_url
            2. From the result get
                a) the value of recaptcha_challenge_field -> self.challenge_field
                b) the captcha image -> self.captcha_image
        """
        
        values = {'k' : self.sitekey}
        data = urllib.urlencode(values)
        req = urllib2.Request(self.captcha_url, data)
        response = urllib2.urlopen(req)
        html_content = response.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        self.captcha_challenge = soup.find('input', {'id': 'recaptcha_challenge_field'}).get('value')
        
        captcha_image_source = soup.img.get('src')
        captcha_image_url = self.captcha_image_base_url + captcha_image_source

        # Get captcha image
        urllib.urlretrieve(captcha_image_url, self.captcha_image_filename)

        #self.save_image(self.captcha_image)
        #self.display_captcha()
            
        
    def save_image(self, filename):
        """save image to file system"""
        
        with open(filename, "w") as f:
            f.write(self.captcha_image)

    def display_captcha(self):
        # Overlay the captcha in the terminal
        try:
            TermImage.display(self.captcha_image_filename)
            return True
        except:
            pass
        # On failure fall back to using the external image viewer
        try:
            TermImage.display_img(self.captcha_image_filename)
            return False
        except:
            raise
    
    def defer(self, time_wait, **kwargs):
        ''' wait for timer to run out before posting '''
        captcha_challenge = self.captcha_challenge
        captcha_solution = self.captcha_solution
        self.dlog.msg("Waiting C: " + captcha_solution + str(kwargs))
        self.bp.sb.setStatus("Deferring comment: " + str(time_wait) + "s")
        
        
        self.lock.acquire()
        self.dlog.msg("Lock acquired C: " + captcha_solution + str(kwargs))
        
        try:   
            while time_wait > 0:
                time.sleep(time_wait)
                # get new lastpost value and see if post needs to be deferred further
                time_wait = self.bp.time_last_posted_thread + 60 - int(time.time()) 
        
            kwargs.update(dict(captcha_challenge=captcha_challenge, captcha_solution=captcha_solution))
            self.dlog.msg("Now posting: C: " + captcha_solution + str(kwargs))
            rc = self.post(**kwargs)
            if rc != 200:
                self.bp.sb.setStatus("Deferred comment was not posted: " + str(rc))
        except Exception as err:
            self.bp.sb.setStatus("Deferred: " + str(err))
            pass
        finally:
            self.lock.release()
        

    def post(self, nickname="", comment="", subject="", file_attach="", ranger=False, captcha_challenge="", captcha_solution=""):
        '''
        subject: not implemented
        file_attach: (/path/to/file.ext) will be uploaded as "file" + extension
        ranger: extract path from ranger's --choosefile file
        '''
        
        if not captcha_challenge or not captcha_solution:
            captcha_challenge = self.captcha_challenge
            captcha_solution = self.captcha_solution
        
        if nickname == None:
            nickname = ""
        else:
            nickname = u''.join(nickname)
        
        # Read file / get mime type
        try:
            if file_attach:
                
                # extract file path from ranger file and re-assign it
                if ranger:
                    with open(file_attach, "r") as f:
                        file_attach = f.read()
                
                _, file_ext = os.path.splitext(file_attach)
                filename = "file" + file_ext
                content_type, _ = mimetypes.guess_type(filename)
                with open(file_attach, "rb") as f:
                    filedata = f.read()
                    
                if content_type is None:
                    raise TypeError("Could not detect mime type of file " + str(filename))
            else:
                filename = filedata = content_type = ""
        except:
            raise

        
        url = "https://sys.4chan.org/" + self.board + "/post"
        #url = 'http://httpbin.org/status/404'
        #url = "http://localhost/" + self.board + "/post"
        #url = 'http://httpbin.org/post'
        #url = "https://requestb.in/1i5x10t1"


        values = { 'MAX_FILE_SIZE' : (None, '4194304'),
                   'mode' : (None, 'regist'),
                   # 'pwd' : ('', 'tefF92alij2j'),
                   'name' : (None, nickname),
                   # 'sub' : ('', ''),
                   'resto' : (None, str(self.threadno)),
                   # 'email' : ('', ''),
                   'com' : (None, comment),
                   'recaptcha_challenge_field' : (None, self.captcha_challenge),
                   'recaptcha_response_field' : (None, self.captcha_solution),
                   'upfile' : (filename, filedata, content_type)
                 }
        
        headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)' }
        
        session = requests.session()
        response = requests.post(url, headers=headers, files=values) 
        
        # raise exception on error code
        response.raise_for_status()
        if re.search("is_error = \"true\"", response.text):
            perror = re.search(r"Error: ([A-Za-z.,]\w*\s*)+", response.text).group(0)
            raise PostReply.PostError(perror)
        
        if response.status_code == 200 and self.dictOutput:
            self.dictOutput.mark(comment)
            self.bp.post_success(int(time.time()))
        else:
            self.dlog.msg("response.status_code: " + str(response.status_code))
            self.dlog.msg("self.dictOutput: " + str(self.dictOutput))
        
        
        return response.status_code
    
    captcha_solution = property(get_captcha_solution, set_captcha_solution, None, None)


