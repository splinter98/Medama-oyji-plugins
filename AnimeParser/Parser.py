import os

from libpyanidb import anidb
#from libpyanidb.hashes import calc_hashes
import ed2k

from cparser import Parser
from config import Config

class AnimeParser(Parser):

   def setconfig(self, config):
      Parser.setconfig(self, config)
      self.intr = anidb.AniDBInterface(user=self.config['aPuser'],password=config['aPpassword'],
                                        dburl=self.config['aPdburl'],
                                        session=self.config['aPsession'])
      self.amask = config['aPdbamask']
      self.fmask = self.config['aPdbfmask']

      self.folder = self.config['aPfolder']
      self.moves=[]
      self.intr.auth(self.intr.user,self.intr.password)


   def ScanFile(self, File):
      """Called to scan the file and return a dict if it matches (empty if not)"""
      filesize = os.stat(File).st_size
      if(filesize is 0 or os.path.splitext(File)[1] not in [".mkv", ".avi", ".ogm", ".mp4"]):
         return {}
      fileinfo={'fmask':  self.fmask, 'amask': self.amask}
      #fileinfo.update(calc_hashes(['ed2k'], File))
      fileinfo.update(ed2k=ed2k.geted2k(File))
      fileinfo['size']=filesize
      print fileinfo
      #return {}
      info = self.intr.file(**fileinfo)
      if info.rescode != "220":
         print "No Info"
         return {}
      return info.datalines[0]


   def SortFile(self, Info, File):
      """Called to place the file in a sensible place"""
      filename = os.path.basename(File)
      self.moves.append([File, os.path.abspath(os.path.join(self.folder, filename))])

   def Catalogue(self, catalogue):
      """take a dict of File and Infos and place the data in a db"""
      pass

   def commit(self):
      for old,new in self.moves:
         print "Moving %s to %s" % (old, new)
      self.moves = []