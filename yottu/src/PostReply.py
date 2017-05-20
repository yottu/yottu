'''
Created on May 15, 2017

@author: yottu-dev@gmail.com
'''
        
import urllib
import urllib2
from bs4 import BeautifulSoup
import requests
from TermImage import TermImage

import warnings
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
        
        f = open(filename, "w")
        f.write(self.captcha_image)
        f.close()

    def display_captcha(self):
        try:
            pass
            TermImage.display(self.captcha_image_filename)
        except:
            raise

    def post(self, comment="", subject="", file=""):

        url = "https://sys.4chan.org/" + self.board + "/post"
        #url = "http://localhost/" + self.board + "/post"
        #url = 'http://httpbin.org/post'
        #url = "https://requestb.in/zzuhovzz"


        values = { 'MAX_FILE_SIZE' : ('', '4194304'),
                   'mode' : ('', 'regist'),
                   # 'pwd' : ('', 'tefF92alij2j'),
                   'name' : ('', 'asdfasd'),
                   # 'sub' : ('', ''),
                   'resto' : ('', str(self.threadno)),
                   # 'email' : ('', ''),
                   'com' : ('', comment),
                   'recaptcha_challenge_field' : ('', self.captcha_challenge),
                   'recaptcha_response_field' : ('', self.captcha_solution),
                   #  'upfile' : ('', '')
                 }
        
        headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)' }
        
        session = requests.session()
        response = requests.post(url, headers=headers, files=values) 
        return response
    
    captcha_solution = property(get_captcha_solution, set_captcha_solution, None, None)


