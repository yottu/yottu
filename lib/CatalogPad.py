'''
Created on May 09, 2017

'''
from Pad import Pad
from CatalogFetcher import CatalogFetcher

class CatalogPad(Pad):
    '''
    classdocs
    '''
    def __init__(self, stdscr, wl):
        super(CatalogPad, self).__init__(stdscr, wl)
        self.catalogFetcher = None
        self.board = None
        
    def stop(self):
        self.catalogFetcher.stop()
        
    def on_resize(self):
        super(CatalogPad, self).on_resize()
        self.catalogFetcher.on_resize()
    
    def active(self):
        super(CatalogPad, self).active()
        try:
            self.catalogFetcher.active()
        except:
            raise
        
    def inactive(self):
        super(CatalogPad, self).inactive()
        try:
            self.catalogFetcher.inactive()
        except:
            raise
        
    def join(self, board, search="", cache_only=False):
        self.board = board
        self.catalogFetcher = CatalogFetcher(self.stdscr, board, self, search, cache_only=cache_only)
        self.catalogFetcher.setDaemon(True)
        self.catalogFetcher.start()

    def update_thread(self, notail=False):
        ''' update (fetch) catalog immediately '''
        self.catalogFetcher.update()
