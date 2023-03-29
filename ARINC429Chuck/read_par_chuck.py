import sys
import os
import psutil   #Non -required library
#from datetime import datetime
#pandas ,You can return to the list without using Read_parameter_file (), without returning DataFrame.
import pandas as pd
import zipfile
from io import StringIO
#import config_vec as conf

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    print('begin mem:',sysmem())
    PAR=read_parameter_file(FNAME)

    if PARAMLIST:
        #----------Show all parameter names-------------
        ii=0
        for vv in PAR.iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            PAR.iloc[:,0].to_csv(TOCSV,sep='\t') #typo said PRA Changed to PARAM
#Not sure about this code
        if 0:
            dict2=PAR.iloc[:,[0,2,7,8,17,36,37,38]].to_dict('split')
            #print(dict2)
            #print(dict2['data'])
            for vv in dict2['data']:
                if not isinstance(vv[7],list) or len(vv[7])<1:
                    continue
                print(vv)
        return

    if PARAM is not None and len(PARAM)>0:
        #----------Display configuration content of a single parameter-------------
        param=PARAM.upper()
        tmp=PAR
        tmp2=tmp[ tmp.iloc[:,0]==param ].copy() #dataframe
        tmp=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )
        pd.set_option('display.max_columns',48)
        pd.set_option('display.width',156)
        print(len(tmp.columns))
        print(tmp)
        return

    pd.set_option('display.max_columns',18)
    pd.set_option('display.width',156)
    pd.set_option('display.min_row',33)
    pd.set_option('display.min_row',330)
    tmp=PAR[[0,2,3,4,5,6,7,8,9,17,20]]
    tmp.iat[0,2]='1-Equip/Label/SDI'  # Source1 (Equip/Label/SDI)
    tmp.iat[0,3]='2-Equip/Label/SDI'  # Source2 (Equip/Label/SDI)
    tmp.iat[0,5]='S_Bit' # Sign Bit
    tmp.iat[0,7]='D_Bits'  # Data Bits
    tmp.iat[0,9]='FormatMode'   # Display Format Mode
    tmp.iat[0,10]='Field length. Score part'   # Field Length.Fractional Part
    print(tmp)
    #print(tmp.iat[0,9])
    #print(tmp.iat[0,10])
    tmp=PAR[[0,24,25,36,37,38,39,40]]
    tmp.iat[0,2]='InternalFormat' # Internal Format (Float ,Unsigned or Signed)
    print(tmp)

    '''
    ii=0
    for vv1 in PAR:
        print(vv1,'\n')
        ii +=1
        if ii>4:
            break
    '''

    print('PAR(%d):'%len(PAR))
    print('PAR:',getsizeof(PAR))
    print('end mem:',sysmem())
    #print(PAR.loc[:,2].unique() ) #List all Type
    #print(PAR.loc[:,6].unique() ) #List all signbit
    #print(PAR.loc[:,7].unique() ) #List all MSB
    #print(PAR.loc[:,8].unique() ) #List all DataBit
    #print(PAR.loc[:,12].unique() ) #List all computation: value = constant value or resol = coef ...
    #print(PAR.loc[:,29].dropna().tolist() ) #List all COEF A (res), there are array
    #print(PAR.loc[:,30].dropna().tolist() ) #List all COEF B, there are several arrays
    #print(PAR.loc[:,31].dropna().tolist() ) #List all dots, none
    #print(PAR.loc[:,32].dropna().tolist() ) #List all X, none
    #print(PAR.loc[:,33].dropna().tolist() ) #List all Y, none
    #print(PAR.loc[:,34].unique() ) #List all COEF A, all NONE
    #print(PAR.loc[:,35].unique() ) #List all POWER, none
    #print(PAR.loc[0] ) #List all column
    if len(TOCSV)>0:
        print('Write to CSV file:',TOCSV)
        PAR.to_csv(TOCSV)

def read_parameter_file(dataver):

    #dataver='%06d' % int(dataver)  #6 -bit string
    par_file = dataver + '.par'
    data_path = 'ARINC429Chuck/DataFrames/'
    
    #filename_zip=dataver+'.par'     #.vec The file name in the compressed package

    #zip_fname=os.path.join(data_path ,dataver + '.par.zip')  #.zip file name
    # if os.path.isfile(zip_fname)==False:
    #     print('ERR,ZipFileNotFound',zip_fname,flush=True)
    #     raise(Exception('ERR,ZipFileNotFound'))

    # try:
    #     fzip=zipfile.ZipFile(zip_fname,'r') #Open the zip file
    # except zipfile.BadZipFile as e:
    #     print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
    #     raise(Exception('ERR,FailOpenZipFile'))
    
    
    PAR=[]
    with open(data_path + par_file,'rb') as fp:
    #with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
        ki=-1
        offset=0  #Overturn
        PAR_offset={}  #Records of various rows, offset and length
        one_par={}  #Record summary of a single parameter
        for line in fp.readlines():
            line=line.decode('utf-8').strip('\r\n //')
            tmp1=line.split('|',1)
            tmp2=tmp1[1].split('\t')
            if tmp1[0] == '1':  #Beginning of the record
                ki +=1
                if ki>0:
                    #print('one_par:',one_par,'\n')
                    PAR.append( one_PAR(PAR_offset,one_par) )
                    #if ki==1:
                       #print('PAR(%d):'%len(PAR), PAR,'\n')
                       #print('PAR_offset:',PAR_offset,'\n')
                    # if ki>2:
                    #    break
                one_par={}
            if tmp1[0] == '13': #End of the record
                continue
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
        PAR.append( one_PAR(PAR_offset,one_par) )

    #fzip.close()

    return pd.DataFrame(PAR)  #Return to Dataframe
    #return PAR       #Return to list

def one_PAR(PAR_offset,one_par):
    '''
    Editing a line of record. A record of a parameter
       Author: Southern Airlines, llgz@csair.com
    '''
    ONE=[]
    for kk in PAR_offset:  #Each recorded child line
        for jj in range( PAR_offset[ kk ][1] ):  #According to the length of the child, all are initialized to empty list
            ONE.append([])
        if kk in one_par:
            if PAR_offset[kk][1] != len(one_par[kk]):  #The number of recorded records is incorrect
                raise(Exception('one_par[%s] length require %d not %d' % (kk, PAR_offset[kk][1], len(one_par[kk]))))

            offset=PAR_offset[ kk ][0]
            #print(len(one_par[kk]))
            for jj in range( len(one_par[kk]) ):  #The corresponding item of one_par to the corresponding position of the one
                ONE[offset+jj].extend( one_par[kk][jj] )
    for counter_j in range( len(ONE) ):  #Corresponding records.There is only one record, remove the list
        if len (ONE[counter_j]) == 0:
            ONE[counter_j]=None
        elif len(ONE[counter_j])==1:
            ONE[counter_j]=ONE[counter_j][0]

    #print('ONE(%d):'%len(ONE),  ONE, '\n')
    return ONE


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
def getsizeof(buf):
    size=sys.getsizeof(buf)
    return showsize(size)
def sysmem():
    size=psutil.Process(os.getpid()).memory_info().rss #The actual physical memory, including shared memory
    #size=psutil.Process(os.getpid()).memory_full_info().uss #The actual physical memory used does not include shared memory
    return showsize(size)



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   Command line tool.')
    print(u' Read the decoding library, the parameter configuration file VEC xx.par file.Such as 010xxx.par')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10XXX      dataver The parameter configuration table')
    print('   --csv xxx.csv        save to "xxx.csv" file.')
    print('   --csv xxx.csv.gz     save to "xxx.csv.gz" file.')
    print('   --paramlist          list all param name.')
    print('   -p,--param alt_std   show "alt_std" param.')
    print(u'\n               Author: Southern Airlines, llgz@csair.com')
    print()
    return
if __name__=='__main__':
    #turn off options for now
    # if(len(sys.argv)<2):
    #     usage()
    #     sys.exit()
    # try:
    #     opts, args = getopt.gnu_getopt(sys.argv[1:],'hv:p:f:',['help','ver=','csv=','paramlist','param='])
    # except getopt.GetoptError as e:
    #     print(e)
    #     usage()
    #     sys.exit(2)
    FNAME=None
    DUMPDATA=False
    TOCSV=''
    PARAMLIST=True
    PARAM=None
    #hardcode paths

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

    FNAME='5471'
    #ARINC429Chuck/DataFrames/5471.par.zip
    DUMPDATA=True
    TOCSV=''
    PARAMLIST=True
    PARAM=None

    if FNAME is None:
        usage()
        sys.exit()

    main()
    print('mem:',sysmem())

