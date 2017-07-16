'''
Created on May 15, 2017

@author: yottudev@gmail.com
'''
from subprocess import call
import subprocess
import os


class TermImage(object):
    '''
    classdocs
    '''
    
    @staticmethod
    def run_w3mimgdisplay(w3m_args):
        try:
            # Binary (Part of Package w3m-img (Debian)) 
            w3m_bin="/usr/lib/w3m/w3mimgdisplay"
            
            # Source: Taymon https://stackoverflow.com/questions/13332268/python-subprocess-command-with-pipe
            ps = subprocess.Popen(('echo', w3m_args), stdout=subprocess.PIPE)
            output = subprocess.check_output((w3m_bin), stdin=ps.stdout)
            ps.wait()
            return output
        except:
            raise
    
    @staticmethod
    def exec_cmd(full_cmd):
        if isinstance(full_cmd, list):
            with open(os.devnull, 'w') as f:
                return subprocess.Popen(full_cmd, stdout=f, stderr=subprocess.STDOUT)
        
    @staticmethod
    def display(filename, path="./"):
        ''' Display image in terminal using w3mimgdisplay'''
        try:
            # Source for figuring out w3m_args: z3bra http://blog.z3bra.org/2014/01/images-in-terminal.html
            # args for getting the image dimensions
            w3m_args="5;" + path+filename
            xy = TermImage.run_w3mimgdisplay(w3m_args)
            x, y = xy.split()
            
            w3m_args="0;1;0;0;" + str(x) + ";" + str(y) + ";;;;;" + path+filename + "\n4;\n3;"
            TermImage.run_w3mimgdisplay(w3m_args)
        except:
            raise
        
    @staticmethod
    def display_ext(filename, **kwargs):
        ''' Automatically chooses best external viewer (hopefully) '''
        
        # get file extension from filename
        file_ext = filename.split(".").pop().lower()
        
        if file_ext == "jpg" or file_ext == "png":
            TermImage.display_img(filename, **kwargs)
            
        elif file_ext == "gif":
            TermImage.display_gif(filename, **kwargs)
            
        elif file_ext == "webm":
            TermImage.display_webm(filename, **kwargs)
            
        else:
            raise LookupError("No viewer for file extension configured: " + file_ext)
    
    @staticmethod        
    def display_img(filename, fullscreen=False, path="./", setbg=False):
        
        try:
            cmd = "feh"
            default_options = ['-q'] # quiet
            
            options = ['--auto-zoom']
            if fullscreen:
                options += ['-D-5', '-F'] # -D-5=Slideshow delay, -F=fullscreen
            
            options.append('--start-at') # 
            options_post = [path] # needed to browse other images in path
            
            if setbg:
                options = ['--bg-max']
                options_post = []
            
            full_cmd = [cmd] + default_options + options + [path+filename] + options_post
            
            TermImage.exec_cmd(full_cmd)
            return
            
            
        except:
            raise
        
    @staticmethod        
    def display_webm(filename, fullscreen=False, path="./", subfile=False, wait=True, **unused):
        ''' Returns: (stdoutdata, stderrdata)'''
        try:
            cmd = "mpv"
            default_options = ['--no-terminal']
            
            options = []
            if fullscreen:
                options.append('-fs')
            
            if subfile:
                options.append('--sub-file=' + str(subfile))
            
            full_cmd = [cmd] + default_options + options + [path+filename]
            
            proc = TermImage.exec_cmd(full_cmd)
            if wait:
                proc.wait()
            return
        
        except:
            raise
            
    @staticmethod        
    def display_gif(filename, fullscreen=False, path="./", **unused):
        ''' Returns: (stdoutdata, stderrdata)'''
        try:
            cmd = "sxiv"
            default_options = ['-q', '-a'] # quiet, play animations
            
            
            options = []
            if fullscreen:
                options = ['-f', '-sf', '-S1'] # fullscreen, scale to fit screen, loop
            
            full_cmd = [cmd] + default_options + options + [path+filename]
            
            TermImage.exec_cmd(full_cmd)
            return
            
        except:
            raise
            
