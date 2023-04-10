#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Read the Aircraft.air file.The corresponding table of the tail number and the decoding library.
    Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
"""
import csv
import config_vec as conf
import gzip

#AIR = None #Save the configuration of the read in. When used as a module, use it when being called.

def main(reg):
    global FNAME,DUMPDATA
    global ALLREG,ALLVER,ALLTYPE
    global TOCSV

    FNAME=conf.aircraft

    air_csv=air(FNAME)
    #The first line is the title.The second line is the continuation of the first line
    #From the third line, it is the data table
    #The last line is a comment
    columns=air_csv[0]

    if ALLREG:
        #----------Display all machine tail numbers-------------
        #Column 0 is the tail number
        ii=1
        for vv in air_csv:
            if vv[0].startswith('//'):
                continue
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        #----Write CSV file--------
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            loc=(0,2,3,6,12,13)
            loc=(0,12)
            ii=-1
            for row in air_csv:
                ii+=1
                if len(row)<2:
                    continue
                fp.write(str(ii))
                for cc in loc:
                    fp.write('\t'+row[cc])
                fp.write('\n')
            fp.close()
        return

    if ALLVER:
        #----------Display all decoding library numbers-------------
        dataVer=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[12] not in dataVer:
                dataVer.append(row[12])
        dataVer.sort()
        ii=1
        for vv in dataVer:
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        return

    if ALLTYPE:
        #----------Display all model models-------------
        print('All aircraft Type:')
        acType=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[3] not in acType:
                acType.append(row[3])
        acType.sort()
        ii=1
        for vv in acType:
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()

        print('All aircraft BASE:')
        acBase=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[2] not in acBase:
                acBase.append(row[2])
        acBase.sort()
        ii=1
        for vv in acBase:
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        return

    if reg is not None and len(reg)>0: #Records of a specific machine tail number
        reg=reg.upper()
        if not reg.startswith('B-'):
            reg = 'B-'+reg
        print(reg)
        idx=[]
        ii=0
        for row in air_csv: #,, All
            if row[0]==reg: idx.append(ii)
            ii +=1
        if len(idx)>0:
            for ii in range(len(air_csv[idx[0]])):
                print(ii,end=',\t')
                for jj in idx:
                    print(air_csv[jj][ii],end=',\t')
                print(air_csv[0][ii])
        else:
            print('Aircraft registration %s not found.' % reg)
            print()
            return
        print()
        return

    #--------------DUMP------------
    #---Show columns---
    #print(len(columns))
    print('Columns:')
    ii=0
    for row in columns:
        print('   ',ii,'\t',row)
        ii +=1
    col=['// A/C tail', 'Reception date', 'Airline', 'A/C type',
            'A/C type wired no', 'A/C ident', #'A/C serial number',
    #        'A/C in operation (1=YES/0=NO)', 'QAR/DAR recorder model',
    #        'QAR/DAR recorder 2 model', 'FDR recorder model',
    #        'FDR recorder 2 model',
            'Version for analysis/QAR/DAR',
            'Version for analysis/QAR/DAR 2',
    #        'Version for analysis/FDR',
    #        'Version for analysis/FDR2', '//AGS'
            ]
    #---Display the front and back 5 lines of the specified column---
    print('Dump head row:')
    show_col=(0,1,2,3,4,5,12,13,14,15)
    ttl_rows=len(air_csv)
    ii=-1
    for row in air_csv:
        ii +=1
        if len(row)<2:
            continue
        if ii==30:
            print('   ... ...')
        if ii>10 and ii< ttl_rows-10:
            continue
        print(len(row),ii,end='\t')
        for cc in show_col:
            print(row[cc]+',',end='\t')
        print()

    #----Write CSV file--------
    if len(TOCSV)>4:
        print('Write to CSV file:',TOCSV)
        if TOCSV.endswith('.gz'):
            fp=gzip.open(TOCSV,'wt',encoding='utf8')
        else:
            fp=open(TOCSV,'w',encoding='utf8')
        buf=csv.writer(fp,delimiter='\t')
        buf.writerows(air_csv)
        fp.close()
    return


def air(csv_filename):
    #global AIR
    #if AIR is not None:
    #    return AIR
    if not os.path.exists(csv_filename):
        print('   "%s" Not Found.'%csv_filename)
        return
    air_csv=[]
    with open(csv_filename,'r',encoding='utf16') as fp:
        buf=csv.reader(fp,delimiter='\t')
        for row in buf:
            air_csv.append(row)
    #The first line and the second line merge, delete the second line
    air_csv[0].append(','.join(air_csv[1]))
    del air_csv[1]
    #AIR=air_csv
    #return AIR
    return air_csv   #返回list



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'Command line tool.')
    print(u'Read the Aircraft.air file.The corresponding table of the tail number and the decoding library.')
    print(sys.argv[0]+' [-h|--help] ')
    print('   -h, --help      print usage.')
    print('   -d                 dump "aircraft.air" file.')
    print('   --csv xx.csv       save to "xx.csv" file.')
    print('   --csv xx.csv.gz    save to "xx.csv.gz" file.')
    print('   -r,--reg b-1843    show recorder of aircraft,"B-1843" ')
    print('   --allreg           list all REGistration number from "aircraft.air" file.')
    print('   --allver           list all DataVer number from "aircraft.air" file.')
    print('   --alltype          list all aircraft Type from "aircraft.air" file.')
    print(u'\n               Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hdr:',['help','allreg','allver','alltype','reg=','csv=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    REG=None
    ALLREG=False
    ALLVER=False
    ALLTYPE=False
    DUMPDATA=False
    TOCSV=''
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-r','--reg'):
            REG=value
        elif op in('--allver',):
            ALLVER=True
        elif op in('--alltype',):
            ALLTYPE=True
        elif op in('--allreg',):
            ALLREG=True
        elif op in('-d',):
            DUMPDATA=True
        elif op in('--csv',):
            TOCSV=value
    if len(args)>0:  #Command line remaining parameters
        REG=args[0]  #Only take the first one

    if ALLTYPE or ALLREG or ALLVER or DUMPDATA or REG or len(TOCSV)>0:
        main(REG)
    else:
        print('Do nothing.')

