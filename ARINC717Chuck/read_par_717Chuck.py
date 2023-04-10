#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 Read the decoding library, the parameter configuration file VEC xx.par file.Such as 010xxx.par
    Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
"""
import os
# import zipfile
import gzip
import csv
from io import StringIO
#import config_vec as conf

#PAR=None  #Save the read -in configuration. When used as a module, use it when being called.
#DataVer=None

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    par_conf=read_parameter_file(FNAME)

    if PARAMLIST:
        #----------Show all parameter names-------------
        ii=0
        for vv in par_conf:
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()

        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            ii=0
            for row in par_conf:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
        return

    if PARAM is not None and len(PARAM)>0:
        #----------Display configuration content of a single parameter-------------
        param=PARAM.upper()
        idx=[]
        ii=0
        for row in par_conf: #Find out all the records
            if row[0] == param: idx.append(ii)
            ii +=1
        if len(idx)>0:
            for ii in range(len(par_conf[0])):
                print(ii,end=',\t')
                for jj in idx:
                    print(par_conf[jj][ii], end=',\t')
                print(par_conf[0][ii])
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        '''
        #Only find the first record, usually the PAR parameter will only have one record
        idx=0
        for row in par_conf:
            if row[0] == param: break
            idx +=1
        if idx < len(par_conf):
            for ii  in range(len(par_conf[0])):
                print(ii, par_conf[idx][ii], par_conf[0][ii], sep=',\t')
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        '''
        print()
        return

    #loc=(0,2,3,4,5,6,7,8,9,17,20)
    #tmp.iat[0,2]='1-Equip/Label/SDI'  # Source1 (Equip/Label/SDI)
    #tmp.iat[0,3]='2-Equip/Label/SDI'  # Source2 (Equip/Label/SDI)
    #tmp.iat[0,5]='S_Bit' # Sign Bit
    #tmp.iat[0,7]='D_Bits'  # Data Bits
    #tmp.iat[0,9]='FormatMode'   # Display Format Mode
    #tmp.iat[0,10]='字段长.分数部分'   # Field Length.Fractional Part
    #loc=(0,24,25,36,37,38,39,40)

    loc=(0,2,3,4,5,6,7,8,9,17,20,24,25,36,37,38,39,40)
    #tmp.iat[0,2]='InternalFormat' # Internal Format (Float ,Unsigned or Signed)
    par_len=len(par_conf)-1
    print('---------- recorder num:',par_len,'------------')
    for ii in range(len(par_conf[0])):
        print(ii,end=',')
        for jj in range(1,6):
            print('\t',par_conf[jj][ii], end=',')
        print('\t',par_conf[0][ii])


    #----Write CSV file--------
    if len(TOCSV)>4:
        print('Write to CSV file:',TOCSV)
        if TOCSV.endswith('.gz'):
            fp=gzip.open(TOCSV,'wt',encoding='utf8')
        else:
            fp=open(TOCSV,'w',encoding='utf8')
        buf=csv.writer(fp,delimiter='\t')
        buf.writerows(par_conf)
        fp.close()
    return

def read_parameter_file(dataver):
    #global PAR
    #global DataVer

    # dataver='%06d' % int(dataver)  #6 -bit string
    #if PAR is not None and DataVer==dataver:
    #    return PAR
    #else:
    #    DataVer=dataver
    #    PAR=None

    # filename_zip=dataver+'.par'     #.The file name in VEC compressed package
    # zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.VEC file name

    # if os.path.isfile(zip_fname)==False:
    #     print('ERR,ZipFileNotFound',zip_fname,flush=True)
    #     raise(Exception('ERR,ZipFileNotFound'))

    # try:
    #     fzip=zipfile.ZipFile(zip_fname,'r') #Open the zip file
    # except zipfile.BadZipFile as e:
    #     print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
    #     raise(Exception('ERR,FailOpenZipFile'))
    
    par_conf=[]
    with open(dataver,'rb') as fp:
        ki=-1
        offset=0  #Overturn
        PAR_offset={}  #Records of various rows, offset and length
        one_par={}  #Record summary of a single parameter
        for line in fp.readlines():
            line=line.decode('utf-8').strip('\r\n //') #strips the // marks and newlines at the beginning of the file header
            tmp1=line.split('|',1) #splits the pipe from the values
            tmp2=tmp1[1].split('\t') #Splits the values by tab after the numbered header    
            if tmp1[0] == '1':  #Beginning of the record
                ki +=1
                if ki>0:
                    #print('one_par:',one_par,'\n')
                    par_conf.append( one_PAR(PAR_offset,one_par) )
                    #if ki==1:
                    #    print('par_conf(%d):'%len(par_conf), par_conf,'\n')
                    #    print('PAR_offset:',PAR_offset,'\n')
                    #if ki>2:
                    #    break
                one_par={}

            if ki==0:  #File header, record header
                if tmp1[0] in PAR_offset: #There should be no duplication in the file header
                    raise(Exception('ERROR, "%s" in PAR_offset' % (tmp1[0]) ))
                else:
                    PAR_offset[ tmp1[0] ]=[ offset , len(tmp2) ]  #Record records should be in the location of the entire record
                    offset += len(tmp2)  #Overturn
            #Record a complete parameter record
            if tmp1[0] not in one_par:
                one_par[ tmp1[0] ]=[]
                for jj in tmp2:
                    one_par[ tmp1[0] ].append( [jj,] )
            else:
                for jj in range( len(tmp2) ):
                    one_par[ tmp1[0] ][jj].append( tmp2[jj] )

            if tmp1[0] == '8': #End of the record
                continue
        par_conf.append( one_PAR(PAR_offset,one_par) )

    # fzip.close()

    #PAR=par_conf
    return par_conf       #Return to list

def one_PAR(PAR_offset,one_par):
    '''
    Dotted a line of record. A record of a parameter
       Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
    '''
    ONE=[]
    for kk in PAR_offset:  #Each recorded child line
        for jj in range( PAR_offset[ kk ][1] ):  #According to the length of the child, all are initialized to empty list
            ONE.append([])
        if kk in one_par:
            if PAR_offset[kk][1] != len(one_par[kk]):  #The number of recorded records is incorrect
                raise(Exception('one_par[%s] length require %d not %d' % (kk, PAR_offset[kk][1], len(one_par))))

            offset=PAR_offset[ kk ][0]
            for jj in range( len(one_par[ kk ]) ):  #The corresponding item of One_PAR to the corresponding position of one
                ONE[offset+jj].extend( one_par[kk][jj] )
    for jj in range( len(ONE) ):  #Organize records.Only one record, remove list
        if len(ONE[jj])==0:
            ONE[jj]=None
        elif len(ONE[jj])==1:
            ONE[jj]=ONE[jj][0]

    #print('ONE(%d):'%len(ONE),  ONE, '\n')
    return ONE



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'Command line tool.')
    print(u' Read the decoding library, the parameter configuration file VEC xx.par file.Such as 010xxx.par')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10XXX      The parameter configuration table in dataver')
    print('   --csv xxx.csv        save to "xxx.csv" file.')
    print('   --csv xxx.csv.gz     save to "xxx.csv.gz" file.')
    print('   --paramlist          list all param name.')
    print('   -p,--param alt_std   show "alt_std" param.')
    print(u'\n Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com')
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

    data_path = '/workspaces/FlightDataDecode/ARINC429Chuck/DataFrames/'
    FNAME = data_path + '5461.par'
    DUMPDATA=False
    TOCSV=''
    PARAMLIST=False
    PARAM=None
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
    #     elif op in('-p','--param',):
    #         PARAM=value
    # if len(args)>0:  #Command line remaining parameters
    #     FNAME=args[0]  #Only take the first one
    # if FNAME is None:
    #     usage()
    #     exit()

    main()

