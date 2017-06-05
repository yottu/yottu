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
        self.captcha_challenge = ""
        self.captcha_image = ""
        self.captcha_image_filename = "yottu-captcha.jpg"

        self.captcha_solution = ""
        
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
        try:
            pass
            TermImage.display(self.captcha_image_filename)
        except:
            raise
    

    def post(self, nickname="", comment="", subject="", file_attach="", ranger=False):
        '''
        Note: set_captcha_solution() must be called before this method
        subject: not implemented
        file_attach: (/path/to/file.ext) will be uploaded as "file" + extension
        ranger: extract path from ranger's --choosefile file
        '''
        
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
        #Hurl = "https://requestb.in/18qz8kd1"


        values = { 'MAX_FILE_SIZE' : ('', '4194304'),
                   'mode' : ('', 'regist'),
                   # 'pwd' : ('', 'tefF92alij2j'),
                   'name' : ('', nickname),
                   # 'sub' : ('', ''),
                   'resto' : ('', str(self.threadno)),
                   # 'email' : ('', ''),
                   'com' : ('', comment),
                   'recaptcha_challenge_field' : ('', self.captcha_challenge),
                   'recaptcha_response_field' : ('', self.captcha_solution),
                   'upfile' : (filename, filedata, content_type)
                 }
        
        headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)' }
        
#        session = requests.session()
        response = requests.post(url, headers=headers, files=values) 
        
        # raise exception on error code
        response.raise_for_status()
        if re.search("is_error = \"true\"", response.text):
            perror = re.search(r"Error: ([A-Za-z.,]\w*\s*)+", response.text).group(0)
            raise PostReply.PostError(perror)
        
        return response.status_code
    
    captcha_solution = property(get_captcha_solution, set_captcha_solution, None, None)


