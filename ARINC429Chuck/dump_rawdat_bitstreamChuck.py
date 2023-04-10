#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Read raw.dat in WGL.The 12bit Frame is expanded to 16bit and 0 4Bit is 0.Convenient for the next process.

'''
    1 Frame has 4 subframe
    1 subframe duration 1 sec
    1 sec has 64,128,256,512 or 1024 words (words/sec)
    1 word has 12 bit
    Synchronization word location: 1st word of each subframe
    Synchronization word length:   12,24 or 36 bits
      For standard synchro word:
                           sync1      sync2      sync3      sync4 
      12bits sync word -> 247        5B8        A47        DB8 
      24bits sync word -> 247001     5B8001     A47001     DB8001 
      36bits sync word -> 247000001  5B8000001  A47000001  DB8000001 

   |<------------------------     Frame     -------------------------->| 
   |   subframe 1   |   subframe 2   |   subframe 3   |   subframe 4   | 
   |                |                |                | Duration=1sec  | 
   |* # #  ... # # #|* # #  ... # # #|* # #  ... # # #|* # #  ... # # #| 
    |          |     |                |                |          | 
   synchro     |    synchro          synchro          synchro     | 
    247        |     5B8              A47              DB8        | 
      ________/^\_____________               ____________________/^\_  
     /  Regular Parameter     \      Frame  /     Superframe word    \  
    |12|11|10|9|8|7|6|5|4|3|2|1|        1  |12|11|10|9|8|7|6|5|4|3|2|1| 
        (12 bits)                      ...         .........        
                                       32  |12|11|10|9|8|7|6|5|4|3|2|1| 

  ---------BITSTREAM FILE FORMAT---------- 
      bit:  F E D C B A 9 8 7 6 5 4 3 2 1 0  
    byte1  :x:x:x:x:x:x:x:x:x:x:x|S:Y:N:C:H: 
    byte2  :R:O: :1:-:-:>|W:O:R:D: :1:-:-:-: 
    byte3  :-:-:>|W:O:R:D: :2:-:-:-:-:-:>|W: 
    byte4  :O:R:D: :3:-:-:-:-:-:>|W:O:R:D: : 
    byte5  :4:-:-:-:-:-:>|W:O:R:D: :5:-:-:-: 
    byte6  :-:-:>| : : : : : : : : : : : : : 
     ...              ... ...  
  ----------------------------------------  

  ----------ALIGNED BIT FILE FORMAT-----------  
  bit: F E D C|B A 9 8 7 6 5 4 3 2 1 0 
    
      |X X X X|      ... ...          |low address
      |X X X X|      ... ...          | 
      |-------|-----------------------| -- 
      |X X X X|SYNCHRONIZATION WORD 1 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe1 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 2 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe2 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 3 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe3 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 4 | 
      |X X X X|      ... ...          | 
      |X X X X|      ... ...          |high address

  bit F: CUT,     Location: First word of the frame.
       set 1 if the frame is not continuous with the previous frame;
       set 0 if the frame is continuous;
       set 0 for the other words of the frame;

  bit E: UNKNOWN, Location: First word of each subframe.
       set 1 if the subframe begins with its synchro word, but is not followed with the next synchro word;
       set 0 otherwise;
       set 0 for the other words of the subframe;

  bit D: BAD,     Location: First word of each subframe.
       set 1 if the subfrae does not begin with its synchro words;
       set 0 otherwise;
       set 0 for the other words of the subframe;

  bit C: PAD,     Location: All words.
       set 1 in the first word of the subframe if the subframe contains at least one extra word;
       set 0 otherwise;
       set 1 for each extra word
  --------------------------------------------  

Based on the description of the above documents.Theoretically, the order of synchronous synchronous words should be: Sync1, Sync2, Sync3, Sync4, the number of Words/SEC.
   Author: Southern Airlines, llgz@csair.com
  --------------------------
'''
Real read files, (BitStream Format, Words/SEC = 1024, Synchro Word Length = 12bits)
  * Take a single byte every time, move the BIT from the high position of the byte, and then move into the Bit from the low level of the 12bit's word, and assemble it into a word every 12bits.
    Looking for synchronization words, there is no regular order.

  * Read a single byte, try, move the BIT from the low level of the byte, and then move into the Bit from the high position of the 12bits Word, and assemble it into a word every 12bits.
    Then the order of Synchro seems to be counterproductive, Sync4, Sync3, Sync2, Sync1, the interval between them is 0x1000, which is 4 times that of 1024.do not know why.
"""
#import struct
#from datetime import datetime
import zipfile
import psutil   #Non -required library
from io import BytesIO

def main():
    global FNAME,WFNAME,DUMPDATA

    print('mem:',sysmem())

    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile'))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    word_cnt=0   #12bit countless
    word_cnt2=0  #The location of the previous synchronization word
    ii=0      #BIT position mark
    word=0    #12bit target cache
    mark=-1   #BIT starting position mark
    for bit in getbit(buf):
        ii +=1
        if ii>=12:
            ii=0
            word_cnt +=1
            if word_cnt > 500000:  #The test, temporarily read 500K and end
                break
        #Word >> = 1 #Moved into high bit-> low: >>
        word <<=1  #Move from low bit-> high: <<
        if bit:
            #Word | = 0x800 #From high bit-> low: 0x800
            word |= 0x001  #Move from low bit-> high: 0x1
        word &= 0xfff
        #if (ii==0 or ii==8) and mark<0 and word == 0x247:
        #if mark<0 and word in (0x247,0x5B8,0xA47,0xDB8):
        if mark<0 and word == 0x247:
            mark=ii
            print('==>Mark,%d,x%X'%(ii,word_cnt))
        if ii==mark:
            if word == 0x247:
                print('==>Found sync1.247,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0x5B8:
                print('==>Found sync2.5B8,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0xA47:
                print('==>Found sync3.A47,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0xDB8:
                print('==>Found sync4.DB8,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
        if word_cnt-word_cnt2 >0x1000:  #512=0x200,512*4=0x800, 1024=0x400, 1024*4=0x1000
            mark=-1  #Reset, look for Sync1 again
            pass


    print('mem:',sysmem())


def getbit(buf):
    dat=BytesIO(buf)
    dat.read(3*1024*1024) #3M content, test for test
    while True:
        bb=dat.read(1)
        if not bb:  # when EOF, return b'', len(bb)==0
            break
        word=ord(bb)
        #chK = 0x01 #first low bit-> high: 0x1
        chk=0x80  #First high Bit-> Low: 0x80
        for ii in range(8):
            if chk & word:
                yield True
            else:
                yield False
            #chK << = 1 #first low bit-> high: <<
            chk >>= 1  #Bit-> low: >> >>
    dat.close()
    return 'done'

def showsize(size):
    if size<1024.0*2:
        return '%.0f B'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f K'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f M'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f G'%(size)
def sysmem():
    size=psutil.Process(os.getpid()).memory_info().rss #The actual physical memory, including shared memory
    #sze = psutil.process (os.getpid ()). Memory_full_info (). Uss #actual physical memory, does not include shared memory, does not include shared memory
    return showsize(size)

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   Command line tool.')
    print(u' Read raw.dat in WGL to verify the file structure, and whether the position of each synchronization word exists.')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help     print usage.')
    print('   -f, --file=    "....wgl.zip" filename')
    #print('-W xxx.dat Write the file "xxx.dat"')
    print(u'\n               Author: Southern Airlines, llgz@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:',['help','file=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-w',):
            WFNAME=value
        elif op in('-d',):
            DUMPDATA=True
    if len(args)>0:  #Command line remaining parameters
        FNAME=args[0]  #Only take the first one
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

