#!/usr/bin/env python

# author:kernel@verycd.com
# created at 02.01.2007

# this tool depend on PyCrypto
# you can install Python-Crypto using:
# 'apt-get install python-crypto' on debian/ubuntu

import sys
from os.path import *
import struct
import urllib
import base64
import Crypto.Hash.MD4
import Crypto.Hash.SHA

EMPARTSIZE = 9728000
EMBLOCKSIZE = 184320

class AICHTree:
    def __init__(self,owner):
        self.owner = owner

        self.left_tree = None
        self.right_tree = None
        self.data_size = None
        self.base_size = None
        self.is_left_tree = True
        self.aich_hash = None

    def Create(self,startpos,length,level,is_left_tree):
        level += 1
        self.level = level
        self.is_left_tree = is_left_tree
        #print level,startpos,length

        self.startpos = startpos
        self.length = length

        #decide the base_size
        self.data_size = length
        if length > EMPARTSIZE:
            self.base_size = EMPARTSIZE
        elif length <= EMPARTSIZE and length > EMBLOCKSIZE:
            self.base_size = EMBLOCKSIZE
        elif length <= EMBLOCKSIZE and length > 0:
            #print level,startpos,length
            #maybe we could put this kind of object into a global list
            self.base_size = None
            self.owner.aich_list.append(self)
            level -= 1
            return

        #calc the blocksize
        if(self.data_size % self.base_size == 0):
            blocksize = self.data_size / self.base_size
        else:
            blocksize = self.data_size / self.base_size + 1
        #print blocksize

        if(blocksize % 2 == 0):
            leftsize = blocksize/2 * self.base_size
        else:
            if(self.is_left_tree):
                leftsize = (blocksize + 1) / 2 * self.base_size
            else:
                leftsize = blocksize/2 * self.base_size
        rightsize = self.data_size - leftsize
        #print leftsize,rightsize

        self.left_tree = AICHTree(self.owner)
        self.left_tree.Create(startpos,leftsize,level,True)
        self.right_tree = AICHTree(self.owner)
        self.right_tree.Create(startpos + leftsize,rightsize,level,False)

        level -= 1
        return

    def CalcAICH(self):
        if (self.left_tree != None) and (self.right_tree != None):

            if self.left_tree.aich_hash == None:
                self.left_tree.CalcAICH()
                #print self.left_tree.aich_hash.hexdigest()

            if self.right_tree.aich_hash == None:
                self.right_tree.CalcAICH()
                #print self.right_tree.aich_hash.hexdigest()

            self.aich_hash = Crypto.Hash.SHA.new()
            self.aich_hash.update(self.left_tree.aich_hash.digest())
            self.aich_hash.update(self.right_tree.aich_hash.digest())

            #if self.level == 4:print self.encode32()
            #self.encode32(self.aich_hash.digest())
        #else:
            #return self.encode32()

    def encode32(self):
        data = self.aich_hash.digest()
        #return encode32(data)
        return base64.b32encode(data)


class PartFile:
    def __init__(self):
        self.aich_tree = None
        self.aich_list = []
        self.hashset = []
        self.cancel = False

    def Attach(self,path):
        self.file = open(path,'rb')
        self.path = path

        #get file size
        self.file.seek(0,2)
        self.size = self.file.tell()

        #create the tree structure
        self.aich_tree = AICHTree(self)
        self.aich_tree.Create(0,self.size,0,True)

        self.file.seek(0)
        self.partcount = 0
        self.md4 = Crypto.Hash.MD4.new()

        self.n = 0
        self.size_finished = 0

    def Go(self):

        for i in self.aich_list:

            if self.cancel:break

            #print i.length
            self.partcount += i.length
            self.size_finished += i.length

            yield self.size_finished * 1.0 / self.size
            #self.file.seek(i.startpos)
            data = self.file.read(i.length)
            i.aich_hash = Crypto.Hash.SHA.new(data)
            self.md4.update(data)

            if self.partcount >= EMPARTSIZE:
                #print md4.hexdigest()
                self.hashset.append(self.md4)
                self.md4 = Crypto.Hash.MD4.new()
                self.partcount = 0

        if self.partcount != 0:
            self.hashset.append(self.md4)
        else:
            #BT,when the size is n*EMPARTSIZE,
            #we must append a null data's md4 to the hashset
            self.hashset.append(Crypto.Hash.MD4.new())
        #yield self.size_finished * 1.0 / self.size

        yield None

    '''
        c = 0.0
        while(c < 1.0):
            c = f.GoByStep()
            #print c * 100

    def GoByStep(self):

        if self.n < len(self.aich_list):
            #print len(self.aich_list)
            i = self.aich_list[self.n]
            self.n += 1

            #print i.length
            self.partcount += i.length
            self.size_finished += i.length

            #self.file.seek(i.startpos)
            data = self.file.read(i.length)
            i.aich_hash = Crypto.Hash.SHA.new(data)
            self.md4.update(data)

            if self.partcount >= EMPARTSIZE:
                #print md4.hexdigest()
                self.hashset.append(self.md4)
                self.md4 = Crypto.Hash.MD4.new()
                self.partcount = 0

        #print self.n,len(self.aich_list)

        if self.n == len(self.aich_list):
            self.n += 1
            if self.partcount != 0:
                self.hashset.append(self.md4)
            else:
                self.hashset.append(Crypto.Hash.MD4.new())

        #return self.size_finished * 1.0 / self.size
        return self.n * 1.0 / len(self.aich_list)
    '''

    def IsFinished(self):
        return self.size_finished == self.size

    def GetED2K(self):
        data = ''
        if len(self.hashset) == 1:
            return self.hashset[0].hexdigest().upper()
        for i in self.hashset:
            data += i.digest()

        md4 = Crypto.Hash.MD4.new(data)
        return md4.hexdigest().upper()

    def GetAICH(self):
        self.aich_tree.CalcAICH()
        #self.aich_tree.encode32(self.aich_list[52].aich_hash.digest())
        return self.aich_tree.encode32().upper()

    def GetHASHSET(self):
        hashset = []
        for i in self.hashset:
            hashset.append(i.hexdigest())
        return ':'.join(hashset).upper()

    def GetSIZE(self):
        return str(self.size).upper()

    def GetNAME(self):
        #return urllib.quote(basename(self.path))
        return basename(self.path)

def geted2k(file):
   f = PartFile()
   f.Attach(file)
   s = f.Go()

   v = True
   while(v):
       v = s.next()

   return f.GetED2K()