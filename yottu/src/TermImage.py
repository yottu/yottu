'''
Created on May 15, 2017

@author: yottu-dev@gmail.com
'''
from subprocess import call

class TermImage(object):
    '''
    classdocs
    '''
        
    @staticmethod
    def display(filename):
        try:
            call(["./imgt", filename])
        except:
            raise