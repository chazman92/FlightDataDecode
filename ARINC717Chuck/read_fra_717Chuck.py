#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Read the decoding library, the parameter configuration file VEC xx.fra file.Such as 010xxx.fra
Only support ArinC 573 PCM format
   Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
"""
import os
import zipfile
import gzip
from io import StringIO
# import config_vec as conf

#FRA=None  #Save the read -in configuration. When used as a module, use it when being called.
#DataVer=None

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    fra_conf=read_parameter_file(FNAME)
    if fra_conf is None:
        return

    #print(fra_conf)
    #print(fra_conf.keys())

    if PARAMLIST:
        #----------Show all parameter names-------------
        #print(fra_conf['2'].iloc[:,0].tolist())
        #---regular parameter
        print('------------------------------------------------')
        ii=0
        for vv in fra_conf['2']:
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        #---superframe parameter
        print('------------------------------------------------')
        ii=0
        for vv in fra_conf['4']:
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
            ii=0
            for row in fra_conf['2']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            ii=0
            for row in fra_conf['4']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            fp.close()
        return

    if PARAM is not None and len(PARAM)>0:  #Display a single parameter name
        #----------Display the configuration content of a single parameter-------------
        param=PARAM.upper()
        #---regular parameter
        idx=[]
        ii=0
        for row in fra_conf['2']: #Find out all the records
            if row[0] == param: idx.append(ii)
            ii +=1
        if len(idx)>0:
            for ii in range(fra_conf['2_items']):
                print(ii,end=',\t')
                for jj in idx:
                    print(fra_conf['2'][jj][ii], end=',\t')
                print(fra_conf['2'][0][ii])
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        print()
        #---superframe parameter
        idx=[]
        ii=0
        for row in fra_conf['4']: #Find out all the records
            if row[0] == param: idx.append(ii)
            ii +=1
        if len(idx)>0:
            for ii in range(fra_conf['4_items']):
                print(ii,end=',\t')
                for jj in idx:
                    print(fra_conf['4'][jj][ii], end=',\t')
                print(fra_conf['4'][0][ii])
        else:
            print('Parameter %s not found in Superframe parameter.'%param)
        print()

        return

    print_fra(fra_conf, '1')
    print_fra(fra_conf, '2')
    if len(fra_conf['3'])>1:
        print_fra(fra_conf, '3')
    else:
        print('No Superframe.')

    if len(fra_conf['4'])>1:
        print_fra(fra_conf, '4')
    else:
        print('No Superframe Parameter.')
    print()

    if len(TOCSV)>4:
        print('==>ERR,  There has 4 tables. Can not save to 1 CSV.')

def print_fra(fra_conf, frakey ):
    if frakey not in fra_conf:
        print('ERR, %s not in list' % frakey)
        return
    fra_len=len(fra_conf[frakey])-1
    print('----',frakey,'------------- recorder num:',fra_len,'-----')
    if fra_len>6:
        show_len=6
    else:
        show_len=fra_len
    for ii in range(fra_conf[frakey+'_items']):
        print(ii,end=',')
        for jj in range(1,show_len+1):
            print('\t',fra_conf[frakey][jj][ii], end=',')
        print('\t',fra_conf[frakey][0][ii])

def read_parameter_file(dataver):
    '''
    fra_conf={
         '1': [ 
            [x,x,,....],   <-- items number
            [x,x,,....],
             ...
            ]
         '2': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '3': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '4': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '1_items': xx,
         '2_items': xx,
         '3_items': xx,
         '4_items': xx,

    }
    '''
    #global FRA
    #global DataVer

    # if isinstance(dataver,(str,float)):
    #     dataver=int(dataver)
    # if str(dataver).startswith('787'):
    #     print('ERR,dataver %s not support.' % (dataver,) )
    #     print('Use "read_frd.py instead.')
    #     return None
    
    # dataver='%06d' % dataver  #6 -bit string

    # if FRA is not None and DataVer==dataver:
    #    return FRA
    # else:
    #    DataVer=dataver
    #    FRA=None

    # filename_zip=dataver+'.fra'     #.vec compressed package file name
    # zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.vec file name

    # if os.path.isfile(zip_fname)==False:
    #     print('ERR,ZipFileNotFound',zip_fname,flush=True)
    #     raise(Exception('ERR,ZipFileNotFound,%s'%(zip_fname)))

    # try:
    #     fzip=zipfile.ZipFile(zip_fname,'r') #Open the zip file
    # except zipfile.BadZipFile as e:
    #     print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
    #     raise(Exception('ERR,FailOpenZipFile,%s'%(zip_fname)))
    
    
    fra_conf={}
    with open(dataver,'rb') as fp:
        for line in fp.readlines():
            line_tr=line.decode('utf-8').strip('\r\n //')
            tmp1=line_tr.split('|',1)
            tmp2=tmp1[1].split('\t')
            
            if tmp1[0] in fra_conf:
                if fra_conf[ tmp1[0]+'_items' ] != len(tmp2):
                    print('ERR,data(%s) length require %d, but %d.' % (tmp1[0], fra_conf[ tmp1[0]+'_items' ], len(tmp2)) )
                    #raise(Exception('ERR,DataLengthNotSame,data(%s) require %d but %d.'% (tmp1[0], fra_conf[ tmp1[0]+'_items' ], len(tmp2)) ))
                fra_conf[ tmp1[0] ].append( tmp2 )
            else:
                fra_conf[ tmp1[0] ]=[ tmp2, ]
                fra_conf[ tmp1[0]+'_items' ]=len(tmp2)
    # fzip.close()
    #FRA=fra_conf
    #return FRA
    return fra_conf       #Return to list



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'Command line tool.')
    print(u'Read the decoding library, the parameter configuration file VEC xx.fra file.Such as 010xxx.fra ')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10XXX      dataver The parameter configuration table')
    print('   --csv xxx.csv        save to "xxx.csv" file.')
    print('   --csv xxx.csv.gz     save to "xxx.csv.gz" file.')
    print('   --paramlist          list all param name.')
    print('   -p,--param alt_std   show "alt_std" param.')
    print(u'\n               Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com')
    print()
    return
if __name__=='__main__':
    # if(len(sys.argv)<2):
    #     usage()
    #     exit()
    # try:
    #     opts, args = getopt.gnu_getopt(sys.argv[1:],'hvp:f:',['help','ver=','csv=','paramlist','param='])
    # except getopt.GetoptError as e:
    #     print(e)
    #     usage()
    #     exit(2)
    data_path = '/workspaces/FlightDataDecode/DataFrames/'
    FNAME = data_path + '5461.fra'
    DUMPDATA=False
    TOCSV=''
    PARAMLIST=False
    PARAM='ACID1'
    # for op,value in opts:
    #     if op in ('-h','--help'):
    #         usage()
    #         exit()
    #     elif op in('-v','--ver'):
    #         FNAME=value
    #     elif op in('-d',):
    #         DUMPDATA=True
    #     elif op in('--csv',):
    #         TOCSV=value
    #     elif op in('--paramlist',):
    #         PARAMLIST=True
    #     elif op in('--param','-p',):
    #         PARAM=value
    # if len(args)>0:  #Command line remaining parameters
    #     FNAME=args[0]  #Only take the first one
    # if FNAME is None:
    #     usage()
    #     exit()

    main()

