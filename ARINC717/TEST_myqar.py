#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pandas as pd
import Get_param_from_arinc717_aligned as A717

def main():
    global FNAME,WFNAME,DUMPDATA
    global PARAM,PARAMLIST

    print('mem:',sysmem())
    #myQAR=A717.ARINC717(FNAME)
    myQAR=A717.ARINC717('')
    print('mem:',sysmem())
    myQAR.qar_file(FNAME)
    print('mem:',sysmem())

    if PARAMLIST:
        #-----------List all parameter names in the record--------------
        regularlist,superlist=myQAR.paramlist()
        #---regular parameter
        ii=0
        for vv in regularlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        print('--------------------------------------------')
        #---superframe parameter
        ii=0
        for vv in superlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        print('mem:',sysmem())

        #-----------Parameter write to CSV file write to CSV file--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            df_pm=pd.concat([pd.DataFrame(regularlist),pd.DataFrame(superlist)])
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return
        return

    if PARAM is None:
        #-----------Configuration content of print parameterstion content of print parameters-----------------
        for vv in ('ALT_STD','AC_TAIL7'):
            fra=myQAR.getFRA(vv)
            if len(fra)<1:
                print('Empty dataVer.')
                continue
            print('parameter:',vv)
            print('Word/SEC:{0[0]}, synchro len:{0[1]} bit, sync1:{0[2]}, sync2:{0[3]}s, sync3:{0[4]}, sync4:{0[5]}, '.format(fra['1']))
            print('   superframe counter:subframe:{0[6]:<5}, word:{0[7]:<5}, bitOut:{0[8]:<5}, bitLen:{0[9]:<5}, value in 1st frame:{0[10]:<5}, '.format(fra['1']) )
            for vv in fra['2']:
                print('Part:{0[0]:<5}, recordRate:{0[1]:<5}, subframe:{0[2]:<5}, word:{0[3]:<5}, bitOut:{0[4]:<5}, bitLen:{0[5]:<5}, bitIn:{0[6]:<5}, type:{0[7]:<5}, '.format(vv) )
            print()
        print('DataVer:',myQAR.dataVer())
    else:
        #-----------Get a parameter--------------------
        pm_list=myQAR.get_param(PARAM)
        #print(pm_list)
        if len(pm_list)<1:
            PARAM=PARAM.upper()
            print('参数 "%s" 没找到, 或者获取失败.'% PARAM)
            print(pm_list)
            print('DataVer:',myQAR.dataVer())
            return
        print('Result[0]:',pm_list[0]) #打印第一组值
        print('DataVer:',myQAR.dataVer())

        df_pm=pd.DataFrame(pm_list)

        #-----------Parameter write to CSV file--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            #df_pm.to_csv(WFNAME,index=False)
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return

        #-----------Part of the content of the parameter--------------------
        pd.set_option('display.min_row',200)
        if len(pm_list)>1200:
            print( df_pm['v'][1000:1200].tolist() )
        else:
            print( df_pm['v'][10:90].tolist() )

    print('mem:',sysmem())
    myQAR.close()
    print('closed.')
    print('mem:',sysmem())
    return

def showsize(size):
    '''
    显示，为了 human readable
    '''
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
import psutil         #Non -essential library
def sysmem():
    '''
    Get the memory occupied by the Python program
    '''
    size=psutil.Process(os.getpid()).memory_info().rss #The actual physical memory, including shared memory
    #size = psutil.process (os.getpid ()). Memory_full_info (). Uss #actual physical memory used
    return showsize(size)

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   Command line tool.')
    print(u' Read the raw.dat in WGL, and decode a parameter according to the parameter coding rules.')

    print(sys.argv[0]+' [-h|--help]')
    print('   * (Necessary parameters)')
    print('   -h, --help                 print usage.')
    print(' * -f, --file xxx.wgl.zip     "....wgl.zip" filename')
    print(' * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。')
    print('   --paramlist                list all param name.')
    print('   -w xxx.csv         Parameter writing file "xxx.csv"')
    print('   -w xxx.csv.gz        Parameter writing file "xxx.csv.gz"')
    print(u'\n               Author: Southern Airlines, llgz@csair.com')
    print(u' I think this project is helpful to you, please seal the email to me, let me be happy. ')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:p:',['help','file=','paramlist','param=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    PARAMLIST=False
    PARAM=None
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
        elif op in('--paramlist',):
            PARAMLIST=True
        elif op in('-p','--param',):
            PARAM=value
    if len(args)>0:  #Command line remaining parameters
        FNAME=args[0]  #Only take the first one
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

