'''
Created on Dec 19, 2017

'''
import time
import re

class Subtitle(object):
    '''
    Create advanced substation alpha (.ass) subtitles from comments for mpv usage
    '''

    def __init__(self, subfile, dlog, stream=False):
        
        self.subfile = subfile
        self.dlog = dlog
        self.append_to_subfile = stream # Write new comment to subfile
        
        self.subfile_start = None
        self.subfile_lasttime = None # Time last sub got displayed
        self.subfile_count = 0 # Number of comments in live subfile
        
    # TODO this might need its own class
    def create_sub(self, postno, tdict):
        '''
            create an .ass subfile for overlaying comments generated 
            from a thread dictionary over a mpv playable source
        '''
        
        try:
            self.subfile_start = time.time()
            
            comments = []
            for post in tdict:
                
                # iterate over all replies
                for refpost in tdict[post]['refposts']:
                    
                    # append only if reply quotes post
                    if str(refpost) == str(postno):
                        
                        # skip empty replies
                        if not tdict[post]['com'] == "[File only]":
                            
                            comments.append(re.sub('(\d+)', '', tdict[post]['com']))
                            
                        continue
                    
                    continue
            
            # Don't create subfile if there are no replies unless it's a stream
            if comments or self.append_to_subfile:
                with open(self.subfile, 'w') as fh:
                    fh.write(u"[Script Info]\n# Thank you Liisachan from forum.doom9.org\n".encode('utf-8'))
                    fh.write("ScriptType: v4.00+\nCollisions: Reverse\nPlayResX: 1280\n")
                    fh.write("PlayResY: 1024\nTimer: 100.0000\n\n")
                    fh.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, ")
                    fh.write("SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, ")
                    fh.write("StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, ")
                    fh.write("Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                    fh.write("Style: testStyle,Verdana,48,&H40ffffff,&H00000000,&Hc0000000")
                    fh.write(",&H00000000,-1,0,0,0,100,100,0,0.00,1,1,0,8,0,0,0,0\n")
                    fh.write("[Events]\nFormat: Layer, Start, End, Style, Actor, MarginL, ")
                    fh.write("MarginR, MarginV, Effect, Text\n")
                    
                    if comments:
                        for i, com in enumerate(comments):
                            xpos = str((i*100+20)%480)
                            time_start = str("%02i" % (i+1)) # FIXME math
                            time_end = str("%02i" % (i+12)) # FIXME math
                            fh.write("Dialogue: 0,0:00:" + time_start +".00,0:00:" + time_end + ".00,testStyle,,")
                            fh.write('0000,0000,0000,,{\\move(1440,'
                                    + xpos + ',-512,' + xpos + ')}{\\fad(1000,1000)}')
                            fh.write(com.encode('utf-8')) # TODO FIXME Security
                            fh.write("\n") 
            else:
                return False
        except Exception as e:
            self.dlog.excpt(e, msg=">>>in DictOutput.create_sub()", cn=self.__class__.__name__)
            raise
        
        return True
                

    def subfile_append(self, com):
        ''' Output comment to subfile when streaming a video '''
        try:
            if self.append_to_subfile:
                
                with open(self.subfile, 'a',) as fh:
                    # FIXME replace hardcoded 5 with subtitle display duration
                    xpos = str((self.subfile_count*100+20)%480)
                    
                    # ceil of comment length divided by 50 # FIXME hard coded 50
                    for i in range(0, -(-len(com))//50+1):
                        fh.write("Dialogue: 0," + self.subfile_time(time.time()+3*i) +".00," + self.subfile_time(int(time.time())+3*(i+1)) + ".00,testStyle,,")
                        fh.write('0000,0000,0000,,{\\move(1440,'
                                + xpos + ',-512,' + xpos + ')}{\\fad(1000,1000)}')
                        fh.write(com.encode('utf-8')[i*50:(i+1)*50]) # TODO FIXME Security
                        fh.write("\n")
                        
                    self.subfile_count += 1 
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Subtitle.subfile_append()", cn=self.__class__.__name__)


        
    def subfile_time(self, thetime):
        ''' return time formatted for subtitle file (HH:MM:SS) '''
        try:
            
            # seconds since last subtitle was displayed
            self.subfile_lasttime = int(thetime) - int(self.subfile_start)
            
            sec_format = str("%02i" % ((self.subfile_lasttime)%60))
            min_format = str("%02i" % ((self.subfile_lasttime/60)%60))
            hour_format = str("%02i" % ((self.subfile_lasttime/60/60)%99))
            time_formatted = hour_format + ":" + min_format + ":" + sec_format
            
            return time_formatted
        
        except Exception as err:
            self.dlog.excpt(err, msg=">>>in Subtitle.subfile_time()", cn=self.__class__.__name__)

        
    