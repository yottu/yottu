'''
Created on May 15, 2017

@author: yottudev@gmail.com
'''
from subprocess import call
import subprocess



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
    def display_feh(filename, options=[], path="./"):
        ''' Returns: (stdoutdata, stderrdata)'''
        try:
            cmd = "feh"
            default_options = ['--auto-zoom']
            full_cmd = [cmd] + default_options + options + [path+filename]
            
            if isinstance(full_cmd, list):
                        proc = subprocess.Popen(full_cmd)
            #output = proc.communicate()
            
            return
        except:
            raise
        
    @staticmethod        
    def display_mpv(filename, options=[], path="./"):
        ''' Returns: (stdoutdata, stderrdata)'''
        try:
            cmd = "mpv"
            default_options = ['-fs', '--no-terminal']
            full_cmd = [cmd] + default_options + options + [path+filename]
            
            if isinstance(full_cmd, list):
                        proc = subprocess.Popen(full_cmd)
            #output = proc.communicate()
            
            return
        except:
            raise