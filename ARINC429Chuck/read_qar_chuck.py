#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import getopt
import struct
#from datetime import datetime
import zipfile

def main():
    global FNAME,DUMPDATA

    #Commented out zip code becasue DAR files are not zipped
    # try:
    #     fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    # except zipfile.BadZipFile as e:
    #     print('ERR,FailOpenZipFile',e,FNAME,flush=True)
    #     raise(Exception('ERR,FailOpenZipFile'))
    # filename_zip='eoflocat.qar'
    # buf=fzip.read(filename_zip)
    # fzip.close()
    buf = FNAME
    
    ss=struct.Struct('8s')
    ttl_size=len(buf)
    #print(buf[12:20])
    #print(buf[32:40])
    #print(ss.unpack_from(buf[12:20]))
    for ii in range(0,ttl_size,32):
        print(buf[ii:ii+28].strip(b'\0').decode(),end=',\t')
        tm2=struct.unpack('<l',buf[ii+28:ii+32])[0]
        print(tm2,end=',\t')
        tm3=struct.unpack('<l',buf[ii+8:ii+12])[0]
        print()


def usage():
    print('Usage:')
    print(' command line tool.')
    print(' read eofloacat.qar in wgl. Not useful.')
    print(sys.argv[0]+' [-h|--help]')
    print('-h, --help print usage.')
    print(' -f, --file= "....wgl.zip" filename')
    print()
    return
if __name__=='__main__':
    # if(len(sys.argv)<2):
    #     usage()
    #     exit()
    # try:
    #     opts, args = getopt.gnu_getopt(sys.argv[1:],'hvdf:',['help','file=','pd'])
    # except getopt.GetoptError as e:
    #     print(e)
    #     usage()
    #     exit(2)
    # FNAME=None
    # DUMPDATA=False
    # for op,value in opts:
    #     if op in ('-h','--help'):
    #         usage()
    #         exit()
    #     elif op in('-f','--file'):
    #         FNAME=value
    #     elif op in('-d',):
    #         DUMPDATA=True
    # if len(args)>0:  #Command line remaining parameters
    #     FNAME=args[0]  #only take the first
    
    #hardcode DAR filename
    FNAME = 'ARINC429Chuck/DataFrames/N2002J-REC25038.DAT'
    print(FNAME)
    if FNAME is None:
        usage()
        sys.exit()
    if os.path.isfile(FNAME) is False:
        print(FNAME,'Not a file')
        sys.exit()

    main()

