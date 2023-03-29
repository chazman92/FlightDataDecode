#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Read raw.dat in WGL.
Decoding a parameter.
Only support ArinC 573/717 PCM format
------
https://github.com/aeroneous/PyARINC429   #py3.5
https://github.com/KindVador/A429Library  #C++

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
   * Take a single byte, position SYNC1 each time, and the sequence of synchronous words is 1, 2, 3, 4, and the interval is 0x400.
     The file should be processed, supplemented.There is no Frame lack in the middle.

    The program will be read in the aligned bit format format.
"""
#import struct
#from datetime import datetime
import zipfile
import psutil         #非必需库
#from io import BytesIO
#Pandas is not a necessary library.Get the parameter back is the list table of the dist.Pandas is not used.
import pandas as pd   #非必需库
#import config_vec as conf
#import read_air as AIR
import read_fra_chuck as FRA
import read_par_chuck as PAR
#from decimal import Decimal
#import arinc429  #did not use
#https://github.com/aeroneous/PyARINC429   #py3.5

class DATA:
    'Used to save the classes of configuration parameters'
    pass

def main():
    global FNAME,WFNAME,DUMPDATA
    global PARAM,PARAMLIST

    #print('mem:',sysmem())

    # reg=getREG(FNAME)
    air = [4]
    air[0] = FNAME

    if PARAMLIST:
        #-----------List all the parameter names in the record--------------
        fra=getFRA(air[0],'')  #The second parameter will be ignored
        if len(fra)<1:
            print('Empty dataVer.')
            return
        #---regular parameter
        ii=0
        for vv in fra['2'].iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        #---superframe parameter
        ii=0
        for vv in fra['4'].iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        print('mem:',sysmem())
        return

    if PARAM is None:
        #-----------Configuration content of print parameters-----------------
        for vv in ('ALT_STD','AC_TAIL7'): #Print these two sample parameter names
            fra=getFRA(air[0],vv)
            if len(fra)<1:
                print('Empty dataVer.')
                continue
            print('parameter:',vv)
            print('Word/SEC:{0[0]}, synchro len:{0[1]} bit, sync1:{0[2]}, sync2:{0[3]}s, sync3:{0[4]}, sync4:{0[5]}, '.format(fra['1']))
            print('   superframe counter:subframe:{0[6]:<5}, word:{0[7]:<5}, bitOut:{0[8]:<5}, bitLen:{0[9]:<5}, value in 1st frame:{0[10]:<5}, '.format(fra['1']) )
            for vv in fra['2']:
                print('Part:{0[0]:<5}, recordRate:{0[1]:<5}, subframe:{0[2]:<5}, word:{0[3]:<5}, bitOut:{0[4]:<5}, bitLen:{0[5]:<5}, bitIn:{0[6]:<5}, type:{0[7]:<5}, '.format(vv) )
            print()
        print('dataVer:',air[0])
    else:
        #-----------Get a parameter--------------------
        fra =getFRA(air[0],PARAM)
        par =getPAR(air[0],PARAM)
        if len(fra)<1:
            print('Empty dataVer.')
            return
        if len(fra['2'])<1 and len(fra['4'])<1:
            print('Parameter not found.')
            return
        #print(PARAM,'(fra):',fra)
        #print(PARAM,'(par):',par)
        #print()

        print('PARAM:',PARAM)
        if len(fra['2'])>0:
            pm_list=get_param(fra,par) #Get a parameter, regula
        else:
            pm_list=get_super(fra,par) #Get a parameter, superframe
        #print(pm_list)
        print('Result[0]:',pm_list[0]) #Print the first set of values
        print('DataVer:',air[0])

        df_pm=pd.DataFrame(pm_list)

        #-----------Parameter write to CSV file--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            #df_pm.to_csv(WFNAME,index=False)
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return

        #-----------Part of the content of the parameter--------------------
        pd.set_option('display.min_row',200)
        print( df_pm['v'][1000:1200].tolist() )

    print('mem:',sysmem())
    return

def get_super(fra,par):
    '''
 Get the superframe parameter and return to Arinc 429 Format
  -------------------------------------
  bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
      |  | SSM |                            DATA field                  | SDI|     label     | 
     _/  \     | MSB -->                                        <-- LSB |    |               | 
    /     \    
   |parity |   
  -------------------------------------  
    Author: Southern Airlines, llgz@csair.com
    '''
    global FNAME,WFNAME,DUMPDATA

    #初始化变量
    word_sec=int(fra['1'][0])
    sync_word_len=int(fra['1'][1])//12  #整除, 同步字的字数(长度)
    sync1=int(fra['1'][2],16)  #同步字1
    sync2=int(fra['1'][3],16)
    sync3=int(fra['1'][4],16)
    sync4=int(fra['1'][5],16)
    superframe_counter_set=[{
            #counter1
            'part':1,
            'rate':1,
            'sub' :int(fra['1'][6]),
            'word':int(fra['1'][7]),
            'bout':int(fra['1'][8]),
            'blen':int(fra['1'][9]),
            'v_first':int(fra['1'][10]),
            'bin' :12,
            'occur': -1,
            },
            #Counter2 does not read from the configuration file (TODO)
            #{'part':1,}
            ]
    if sync_word_len>1: #If synchronous words> 1 word
        sync1=(sync1 << (12 * (sync_word_len-1))) +1  #Synchronous word for growth
        sync2=(sync2 << (12 * (sync_word_len-1))) +1
        sync3=(sync3 << (12 * (sync_word_len-1))) +1
        sync4=(sync4 << (12 * (sync_word_len-1))) +1

    #----------Parameter configuration sorting-----------
    super_set=[]
    for vv in fra['3']: #All content becomes int
        p_set={  #Temporary variables
            'frameNo':int(vv[0]),
            'sub' :int(vv[1]),
            'word':int(vv[2]),
            'bout':int(vv[3]),
            'blen':int(vv[4]),
            'counterNo' :int(vv[5]),
            }
        super_set.append(p_set)
    super_set=super_set[0] #Only the first item, usually a super parameter only corresponds to one frameno

    #TheCollationOfTheParameterConfiguration,TreatAPeriodAsABigFrameProcessing
    superpm_set=[]
    p_set=[]  #Temporary variables
    last_part=0
    for vv in fra['4']: #All content becomes int
        vv[0]=int(vv[0]) #part
        if vv[0]<=last_part:
            #Part = 1,2,3 according to the part group
            superpm_set.append(p_set)
            p_set=[]
        last_part=vv[0]
        #frameNo=vv[2]   #The corresponding configuration of Frameno should be found in the super_set, which is simplified here.
        p_set.append({
            'part':vv[0],
            'rate': 1,
            'sub' :super_set['sub'],
            'word':super_set['word'] + (int(vv[3])-1) * word_sec * 4, #subframe + (Frame-1) * word_sec *4
            'bout':int(vv[4]),  #The following two bouts, blen should be set in Super_Set. After getting the data, use the configuration here to remove the final bits.
            'blen':int(vv[5]),  #But because the content in Super_Set is 12,12.So the final configuration is used here.
            'bin' :int(vv[6]),
            'occur' : -1,
            'resol': float(vv[7]), #resolution
            'period':int(vv[1]),
            })
    if len(p_set)>0: #Last group
        superpm_set.append(p_set)

    #----------Print parameter-----------
    print('Frame definition: Word/SEC:%d, syncLen(word):%d, sync1234: %X,%X,%X,%X'%(word_sec,sync_word_len,sync1,sync2,sync3,sync4) )
    print('   SuperFrame Counter:',superframe_counter_set)
    print()
    print('super_set: ',super_set )
    print('superpm: len:%d'%( len(superpm_set)) )
    for vv in superpm_set:
        print(vv)
    print('param(par):',par)
    print()

    #----------Data Type Warning-----------
    if par['type'].find('BCD')!=0 and \
            par['type'].find('BNR LINEAR (A*X)')!=0 and \
            par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
            par['type'].find('CHARACTER')!=0 and \
            par['type'].find('DISCRETE')!=0 and \
            par['type'].find('PACKED BITS')!=0 and \
            par['type'].find('UTC')!=0 :
        print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) )

    #----------Open the zip compression file-----------
    try:
        fzip=zipfile.ZipFile(FNAME,'r') #Open the zip file
    except zipfile.BadZipFile as e:
        print('==>ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%FNAME))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    #----------Find the starting position-----------
    ttl_len=len(buf)
    frame_pos=0  #Frame starts position, byte pointer
    frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
    if frame_pos > 0:
        print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
    if frame_pos >= ttl_len - sync_word_len *2:
        #No synchronous word was found throughout the file
        print('==>ERR, SYNC not found at end of DATA.',flush=True)
        raise(Exception('ERR,SYNC not found at end of DATA.'))

    period=superpm_set[0][0]['period']   #Simply obtain Period from the first record of the first group

    #----------Calculate the counter_mask-----------
    #Some libraries are increased by 1, n periods cycle.Some are increasing 256, a period cycle.
    #Determine MASK according to the counter value in the two Frames.
    frame_counter  = get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
    frame_counter -= get_arinc429(buf, frame_pos + word_sec * 4 * 2, superframe_counter_set, word_sec )
    if abs(frame_counter) ==1:
        count_mask = ( 1 << int(pow(period, 0.5)) ) -1  #Square root SQRT: pow(x, 0.5) or (x ** 0.5)
        #count_mask= 0xf
    else:
        count_mask= 0
    print('counter sep:',frame_counter,period,bin(count_mask) )
    
    #----------Looking for the starting position of Superframe-----------
    val_first=super_set['counterNo'] #superframe counter 1/2
    if val_first==2: val_first=1  #Counter2 does not read from the configuration (TODO)
    val_first=superframe_counter_set[val_first-1]['v_first']
    pm_sec=0.0   #The timeline of the parameter, the number of seconds
    frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
    pm_sec += sec_add  #Add time incremental

    #----------Read parameter-----------
    ii=0    #count
    pm_list=[] #parameter list
    while True:
        # There are several DataVER data, not starting from the file header, only sync1 will find it wrong.It is not ruled out that it will be wrong/chaos in the middle.
        #So every time you must confirm the location of First Frame.The actual test was found that there were synchronous words errors, but the Frame interval was correct.
        frame_pos2=frame_pos   #Save the old position
        frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
        pm_sec += sec_add  #Add time incremental
        if frame_pos>=ttl_len -2:
            #----- Beyond the end of the file, exit -----
            break

        for pm_set in superpm_set:
            #Get Anrinc429, the first step should be set with the bout, blen settings in Super_Set, and after getting the data, use the configuration in Superpm_Set to take out the final BITS.
            #But because the content in Super_Set is 12,12.So the final configuration is used here.
            value=get_arinc429(buf, frame_pos, pm_set, word_sec )  #ARINC 429 format
            value =arinc429_decode(value ,par )
            # There is a resolution in superpm_set seems useless.In the AGS configuration, it is said to be automatically calculated and not allowed to change.
            #Try to ride, the data is wrong.
            #if pm_set[0]['resol'] != 0.0 and pm_set[0]['resol'] != 1.0: 
            #    value *= pm_set[0]['resol']

            pm_list.append({'t':round(pm_sec,10),'v':value})
            #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
            #pm_list.append({'t':round(pm_sec,10),'v':value,'c':frame_counter})

        pm_sec += 4.0 * period  #A frame is 4 seconds
        frame_pos += word_sec * 4 * 2 * period   # 4Subframe, 2bytes, skipped a period directly, even if there is a Frame error/lack in the middle, it doesn't matter.
    return pm_list

def find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync, val_first, superframe_counter_set, period, count_mask ):
    '''
    To judge the location of the FIRST FRAME, if not, push 1 frame and look back.
        According to the content of Superframe_Counter, find the Frame position of the value of Conter
        Author: Southern Airlines, llgz@csair.com
    '''
    pm_sec=0.0   #The timeline of the parameter, the number of seconds
    while True:
        frame_pos2=frame_pos   #Save the old position
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync )  #Determine synchronization words, or continue to find new positions
        if frame_pos>=ttl_len -2:
            #----- Beyond the end of the file, exit -----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #If the synchronization is lost, after the synchronization, the time will be 4 seconds.(This should be determined according to the jump distance, it is simple and rude here)

        frame_counter=get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
        if count_mask > 0:
            frame_counter &= count_mask
        if frame_counter==val_first:
            #print('Found first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            break
        else:
            print('NotFound first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            pm_sec += 4.0   #A frame is 4 seconds
            frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes

    return frame_pos, pm_sec  #Return position, time increment

def get_param(fra,par):
    '''
   Get the regular parameter and return to ArinC 429 Format
  -------------------------------------
  bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
      |  | SSM |                            DATA field                  | SDI|     label     | 
     _/  \     | MSB -->                                        <-- LSB |    |               | 
    /     \    
   |parity |   
  -------------------------------------  
    Author: Southern Airlines, llgz@csair.com
    '''
    global FNAME,WFNAME,DUMPDATA

    #Initialize variables
    word_sec=int(fra['1'][0])
    sync_word_len=int(fra['1'][1])//12  #Extract, the number (length) of the synchronous word (length)
    sync1=int(fra['1'][2],16)  #Synchronous word 1
    sync2=int(fra['1'][3],16)
    sync3=int(fra['1'][4],16)
    sync4=int(fra['1'][5],16)
    superframe_counter_set=[{
            'part':1,
            'rate':1,
            'sub' :int(fra['1'][6]),
            'word':int(fra['1'][7]),
            'bout':int(fra['1'][8]),
            'blen':int(fra['1'][9]),
            'v_first':int(fra['1'][10]),
            'bin' :12,
            'occur': -1,
            }]
    if sync_word_len>1: #If synchronous words> 1 word
        sync1=(sync1 << (12 * (sync_word_len-1))) +1  #Synchronous word for growth
        sync2=(sync2 << (12 * (sync_word_len-1))) +1
        sync3=(sync3 << (12 * (sync_word_len-1))) +1
        sync4=(sync4 << (12 * (sync_word_len-1))) +1

    param_set=getDataFrameSet(fra['2'],word_sec)  #Configuration of sorting parameter location records

    #----------Print parameter-----------
    print('Frame definition: Word/SEC:%d, syncLen(word):%d, sync1234: %X,%X,%X,%X'%(word_sec,sync_word_len,sync1,sync2,sync3,sync4) )
    print('   SuperFrame Counter:',superframe_counter_set)
    print()
    print('param(fra): len:%d'%( len(param_set)) )
    for vv in param_set:
        print(vv)
    print('param(par):',par)
    print()

    #----------Data Type Warning-----------
    if par['type'].find('BCD')!=0 and \
            par['type'].find('BNR LINEAR (A*X)')!=0 and \
            par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
            par['type'].find('CHARACTER')!=0 and \
            par['type'].find('DISCRETE')!=0 and \
            par['type'].find('PACKED BITS')!=0 and \
            par['type'].find('UTC')!=0 :
        print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) )

    #----------Open the zip compression file-----------
    # try:
    #     fzip=zipfile.ZipFile(FNAME,'r') #Open the zip file
    # except zipfile.BadZipFile as e:
    #     print('==>ERR,FailOpenZipFile',e,FNAME,flush=True)
    #     raise(Exception('ERR,FailOpenZipFile,%s'%FNAME))
    # filename_zip='raw.dat'
    # buf=fzip.read(filename_zip)
    # fzip.close()


    #read into buffer
    dar_file='ARINC429Chuck/DataFrames/N2002J-REC25038.DAT'
    fp=open(dar_file,'rb')
    buf=fp.read()
    fp.close()

    #----------Find the starting position-----------
    ttl_len=len(buf)
    frame_pos=0  #Frame starts position, byte pointer
    frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
    if frame_pos > 0:
        print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
    if frame_pos >= ttl_len - sync_word_len *2:
        #No synchronous word was found throughout the file
        print('==>ERR, SYNC not found at end of DATA.',flush=True)
        raise(Exception('ERR,SYNC not found at end of DATA.'))
    
    #----------Read parameter-----------
    ii=0    #count
    pm_list=[] #parameter list
    pm_sec=0.0   #The timeline of the parameter,秒数
    while True:
        #There are several DataVER data, not starting from the file header, only sync1 will find it wrong.It is not ruled out that it will be wrong/chaos in the middle.
        #So use Find_Sync1 () to judge each time.The actual test was found that there were synchronous words errors, but the Frame interval was correct.
        frame_pos2=frame_pos   #Save the old position
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )  #Determine synchronization words, or continue to find new positions
        if frame_pos>=ttl_len -2:
            #----- Beyond the end of the file, exit -----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #If the synchronization is lost, after the synchronization, the time will be 4 seconds.(This should be determined according to the jump distance, it is simple and rude here)


        sec_add = 4.0 / len(param_set)  #A frame is 4 seconds
        for pm_set in param_set:
            value=get_arinc429(buf, frame_pos, pm_set, word_sec )  #ARINC 429 format
            value =arinc429_decode(value ,par )

            pm_list.append({'t':round(pm_sec,10),'v':value})
            #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
            pm_sec += sec_add   #Time axis accumulation

        frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes
    return pm_list

def find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync):
    '''
    Determine whether the Frame_POS position meets the characteristics of synchronization.If not satisfied, continue to find the next starting location
    '''
    #ttl_len=len(buf)
    while frame_pos<ttl_len - sync_word_len *2:  #Find the starting position of Frame
        #----It seems that it is enough to judge that the two consecutive synchronous words are correct.-----
        if getWord(buf,frame_pos, sync_word_len) == sync[0] and \
                getWord(buf,frame_pos+word_sec*2,sync_word_len) == sync[1] :
        #if getWord(buf,frame_pos, sync_word_len) == sync[0] and \
        #        getWord(buf,frame_pos+word_sec*2,sync_word_len) == sync[1] and \
        #        getWord(buf,frame_pos+word_sec*4,sync_word_len) == sync[2] and \
        #        getWord(buf,frame_pos+word_sec*6,sync_word_len) == sync[3] :
            #print('==>Mark,x%X'%(frame_pos,))
            break
        frame_pos +=1
    return frame_pos

def getDataFrameSet(fra2,word_sec):
    '''
    The configuration of the compilation parameters in the ArIinc717 position (position in 12 bit word)
        If it is not Self-Distant, there will be configuration of each position.Record all positions.
            You need to make up for other subframes according to the Rate value.
            For example: Rate = 4, that is, 1-4Subframe.Rate = 2 is in 1,3 or 2,4Subframe.
        If it is Self-Distant, there is only the configuration of the first position.Based on Rate, make up for all location records and group.
            You need to make up for other Subframe and Word position according to the Rate value.
            Subframe's complement is the same as above. The interval between Word is to use Word/SEC to remove the record number.Uniformly divided into each subframe.
            Author: Southern Airlines, llgz@csair.com
    '''
    # ---Group---
    group_set=[]
    p_set=[]  #Temporary variables
    last_part=0
    for vv in fra2:
        vv[0]=int(vv[0]) #part
        if vv[0]<=last_part:
            #Part = 1,2,3 according to the part group
            group_set.append(p_set)
            p_set=[]
        last_part=vv[0]
        #Rate: 1 = 1/4Hz (a record of a Frame), 2 = 1/2Hz, 4 = 1Hz (a record of each subframe), 8 = 2Hz, 16 = 4Hz, 32 = 8Hz (each subframe has 8 records in 8 recordsCure
        p_set.append({
            'part':vv[0],
            'rate':int(vv[1]),
            'sub' :int(vv[2]),
            'word':int(vv[3]),
            'bout':int(vv[4]),
            'blen':int(vv[5]),
            'bin' :int(vv[6]),
            #'occur' :int(vv[7]) if len(vv[7])>0 else -1,
            })
    if len(p_set)>0: #Last group
        group_set.append(p_set)

    # -------------------------------
    #Print ('group configuration: len:%d'%(len (group_set)))
    #for vv in group_set:
    #    print(vv)

    # --------Based on the Rate replacement record-------
    param_set=[]
    frame_rate=group_set[0][0]['rate']
    if frame_rate>4:
        frame_rate=4           #A few filga in a Frame
    subf_sep=4//frame_rate  #Divide
    for subf in range(0,4,subf_sep):  #Subframe, only the Rate supplement based on the first record
        for group in group_set:
            frame_rate=group[0]['rate']
            if frame_rate>4:
                sub_rate=frame_rate//4  #There are several records in a subframe, which is divided
            else:
                sub_rate=1
            word_sep=word_sec//sub_rate  #Divide
            for word_rate in range(sub_rate):  #Make up Word, according to the first Rate recorded by the group record
                p_set=[]  #Temporary variables
                for vv in group:
                    p_set.append({
                        'part':vv['part'],
                        'rate':vv['rate'],
                        'sub' :vv['sub']+subf,
                        'word':vv['word']+word_rate*word_sep,
                        'bout':vv['bout'],
                        'blen':vv['blen'],
                        'bin' :vv['bin'],
                       # 'occur':vv['occur'],
                        })
                param_set.append(p_set)
    return param_set

def arinc429_decode(word,conf):
    '''
    PAR may have the Type: 'Constant' 'Discrete' 'Packed Bits' 'BNR Linear (A*X)' 'Compute on Group' 'Character' 'BCD' BNR Segments (A*X+B) 'UTC'
        Par's actual Type: 'BNR LINEAR (A*X)' 'BNR Segments (A*X+B)' Character '' BCD '' '' UTC 'Packed Bits'
            Author: Southern Airlines, llgz@csair.com
    '''
    if conf['type'].find('BNR')==0 or \
            conf['type'].find('PACKED BITS')==0:
        return arinc429_BNR_decode(word ,conf)
    elif conf['type'].find('BCD')==0 or \
            conf['type'].find('CHARACTER')==0:
        return arinc429_BCD_decode(word ,conf)
    elif conf['type'].find('UTC')==0:
        val=arinc429_BNR_decode(word ,conf)
        ss= val & 0x3f         #6bits
        mm= (val >>6) & 0x3f   #6bits
        hh= (val >>12) & 0x1f  #5bits
        return '%02d:%02d:%02d' % (hh,mm,ss)
    else:
        return arinc429_BNR_decode(word ,conf)

def arinc429_BCD_decode(word,conf):
    '''
    Take the value from the ArIinc429 format
        conf=[{ 'ssm'    :tmp2.iat[0,5],   #SSM Rule (0-15)0,4 
                'signBit':tmp2.iat[0,6],   #bitLen,SignBit
                'pos'   :tmp2.iat[0,7],   #MSB
                'blen'  :tmp2.iat[0,8],   #bitLen,DataBits
                'part': [{
                    'id'     :tmp2.iat[0,36],  #Digit
                    'pos'    :tmp2.iat[0,37],  #MSB
                    'blen'   :tmp2.iat[0,38],  #bitLen,DataBits
                'type'    :tmp2.iat[0,2],     #Type(BCD,CHARACTER)
                'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                    }]
    Author: Southern Airlines, llgz@csair.com
    '''
    if conf['type']=='CHARACTER':
        if len(conf['part'])>0:
            #有分步配置
            value = ''
            for vv in conf['part']:
                #According to Blen, obtain the mask value
                bits= (1 << vv['blen']) -1
                #Move the value to the right (move to BIT0) and get the value
                tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                value +=  chr(tmp)
        else:
           #According to Blen, get mask value
            bits= (1 << conf['blen']) -1
            #Move the value to the right (move to BIT0) and get the value
            value = ( word >> (conf['pos'] - conf['blen']) ) & bits
            value =  chr(value)
            characters = arinc429_to_characters(value)
        return value
    else:  #BCD
        #Symbol
        sign=1
        if conf['signBit']>0:
            bits=1
            bits <<= conf['signBit']-1  #Bit bit number starts from 1, so -1
            if word & bits:
                sign=-1

        if len(conf['part'])>0:
            #Stepped configuration
            value = 0
            for vv in conf['part']:
                #According to Blen, obtain the mask value
                bits= (1 << vv['blen']) -1
                #Move the value to the right (move to BIT0) and get the value
                tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                value = value * 10 + tmp
        else:
            #According to Blen, get mask value
            bits= (1 << conf['blen']) -1
            #Move the value to the right (move to BIT0) and get the value
            value = ( word >> (conf['pos'] - conf['blen']) ) & bits
        return value * sign

def arinc429_BNR_decode(word,conf):
    '''
    Take the value from the ArIinc429 format
        conf=[{ 'ssm'    :tmp2.iat[0,5],   #SSM Rule (0-15)0,4 
                'signBit':tmp2.iat[0,6],   #bitLen,SignBit
                'pos'   :tmp2.iat[0,7],   #MSB
                'blen'  :tmp2.iat[0,8],   #bitLen,DataBits
                'part': [{
                    'id'     :tmp2.iat[0,36],  #Digit
                    'pos'    :tmp2.iat[0,37],  #MSB
                    'blen'   :tmp2.iat[0,38],  #bitLen,DataBits
                'type'    :tmp2.iat[0,2],     #Type(BCD,CHARACTER)
                'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                    }]
    Author: Southern Airlines, llgz@csair.com
    '''
    #According to Blen, obtain the mask value
    bits= (1 << conf['blen']) -1
    #Move the value to the right (move to BIT0) and get the value
    value = ( word >> (conf['pos'] - conf['blen']) ) & bits

    #Symbol
    if conf['signBit']>0:
        bits = 1 << (conf['signBit']-1)  #Bit bit number starts from 1, so -1
        if word & bits:
            value -= 1 << conf['blen']
    #Resolution
    if conf['type'].find('BNR LINEAR (A*X)')==0:
        if conf['Resol'].find('Resol=')==0:
            value *= float(conf['Resol'][6:])
    elif conf['type'].find('BNR SEGMENTS (A*X+B)')==0:
        if len(conf['A'])>0:
            value *= float(conf['A'])
        if len(conf['B'])>0:
            value += float(conf['B'])
    else:
    #---- known Packed Bits, UTC, Discrete, you should process it according to BNR ---
            #Other types that cannot be recognized, press BNR by default
            #Here, no need to give an error prompt
        pass
    return value 

def get_arinc429(buf, frame_pos, param_set, word_sec ):
    '''
    According to FRA configuration, obtain 32bit word in the Arinc429 format
        Another: There are multiple different records in the FRA configuration, corresponding to multiple 32bit word (completed)
        BIT position is numbered from 1.Word position is also numbered from 1.The position of the synchronous word is 1, and the data word starts from 2 (assuming that synchronous words only occupy 1Word).
        Author: Southern Airlines, llgz@csair.com
    '''
    value=0
    pre_id=0
    for pm_set in param_set:
        #if pm_set ['part']> Pre_id: #There are multiple sets of configuration, only the first group is executed.// The configuration has been sorted, and there is only one group.
        #    pre_id=pm_set['part']
        #else:
        #    break
        word=getWord(buf,
                frame_pos + word_sec *2 *(pm_set['sub']-1) +(pm_set['word']-1)*2  #The position occupied by the synchronous word, number is 1, so -1
                )
        #According to Blen, obtain the mask value
        bits= (1 << pm_set['blen']) -1
        #According to BOUT, move the mask to the corresponding location
        bits <<= pm_set['bout'] - pm_set['blen']
        word &= bits  #Gain
        #Move the value to the target location
        move=pm_set['bin'] - pm_set['bout']
        if move>0:
            word <<= move
        elif move<0:
            word >>= -1 * move
        value |= word
    return value

def getWord(buf,pos, word_len=1):
    '''
    Read two bytes and take 12bit as a word.The low position is in front.LittleEndian, Low-Byte First.
        Support 12bits, 24bits, 36bits, 48bits, 60bits
        Author: Southern Airlines, llgz@csair.com
    '''
    #print(type(buf), type(buf[pos]), type(buf[pos+1])) #bytes, int, int

    ttl=len(buf)  #When reading the data, the starting position and the offset of Subframe and Word may exceed the limit
    if word_len==1:
        if pos+1 >= ttl:
            return 0  #Excellence returns 0
        else:
            return ((buf[pos +1] << 8 ) | buf[pos] ) & 0xFFF

    #Word_len> 1 // Only by getting a synchronous word greater than 1 word can it useful
    word=0
    for ii in range(0,word_len):
        if pos+ii*2+1 >= ttl:
            high = 0
        else:
            high = ((buf[pos+ii*2+1] << 8 ) | buf[pos +ii*2] ) & 0xFFF
        word |= high << (12 * ii)
    return word

def getPAR(dataver,param):
    '''
    Obtain the position configuration of the 32bit word of the parameter in Arinc429
    Pick out useful, sort it out, return to
       Author: Southern Airlines, llgz@csair.com
    '''
    global DATA
    if not hasattr(DATA,'par'):
        DATA.par=PAR.read_parameter_file(dataver)
    if DATA.par is None or len(DATA.par.index)<1:
        return {}
    param=param.upper()  #改大写
    tmp=DATA.par
    tmp2=tmp[ tmp.iloc[:,0]==param ].copy(deep=True) #dataframe ,Find the record line of the corresponding parameter
    #pd.set_option('display.max_columns',78)
    #pd.set_option('display.width',156)
    #print('=>',type(tmp2))
    #print(tmp2)
    if len(tmp2.index)<1:
        return {}
    else:
        tmp_part=[]
        if isinstance(tmp2.iat[0,36], list):
            #If there are multiple parts of the configuration of bits, combine it
            for ii in range(len(tmp2.iat[0,36])):
                tmp_part.append({
                        'id'  :int(tmp2.iat[0,36][ii]),  #Digit ,Sequential labeling
                        'pos' :int(tmp2.iat[0,37][ii]),  #MSB   ,Start position
                        'blen':int(tmp2.iat[0,38][ii]),  #bitLen,DataBits,Data length
                        })
        return {
                'ssm'    :int(tmp2.iat[0,5]) if len(tmp2.iat[0,5])>0 else -1,   #SSM Rule , (0-15)0,4 
                'signBit':int(tmp2.iat[0,6]) if len(tmp2.iat[0,6])>0 else -1,   #bitLen,SignBit  ,Symbol position
                'pos'   :int(tmp2.iat[0,7]) if len(tmp2.iat[0,7])>0 else -1,   #MSB  ,Start position
                'blen'  :int(tmp2.iat[0,8]) if len(tmp2.iat[0,8])>0 else -1,   #bitLen,DataBits ,The total length of the data part
                'part'    :tmp_part,
                'type'    :tmp2.iat[0,2],    #Type(BCD,CHARACTER)
                'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                'A'       :tmp2.iat[0,29] if tmp2.iat[0,29] is not None else '',    #Coef A(Res)
                'B'       :tmp2.iat[0,30] if tmp2.iat[0,30] is not None else '',    #Coef b
                'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                }

def getFRA(dataver,param):
    '''
    Get the position configuration of the 12bit word in Arinc717
    Pick out useful, sort it out, return to
       Author: Southern Airlines, llgz@csair.com
    '''
    global PARAMLIST
    global DATA

    if not hasattr(DATA,'fra'):
        DATA.fra=FRA.read_parameter_file(dataver)
    if DATA.fra is None:
        return {}

    if PARAMLIST:
        return DATA.fra

    ret2=[]  #for regular
    ret3=[]  #for superframe
    ret4=[]  #for superframe pm
    if len(param)>0:
        param=param.upper() #Rectify
        #---find regular parameter----
        tmp=DATA.fra['2']
        tmp=tmp[ tmp.iloc[:,0]==param].copy()  #dataframe
        #print(tmp)
        if len(tmp.index)>0:  #Find a record
            for ii in range( len(tmp.index)):
                tmp2=[  #regular Parameter configuration
                    tmp.iat[ii,1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit word. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                    tmp.iat[ii,2],   #Recording Rate(1 for 1/4Hz,2 for 1/2Hz, 4 for 1 Hz,8 for 2Hz ...)
                    tmp.iat[ii,3],   #Output Word (Subframe)
                    tmp.iat[ii,4],   #Output Word (Word), Several Word (SYNC WORD number as 1) in Subframe
                    tmp.iat[ii,5],   #bitOut, In 12bit, several bits start
                    tmp.iat[ii,6],   #bitLen, A few bits in total
                    tmp.iat[ii,7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits, write writing
                    #tmp.iat[ii,12],  #Occurence No
                    tmp.iat[ii,8],   #Imposed,Computed
                    ]
                ret2.append(tmp2)
        #---find superframe parameter----
        tmp=DATA.fra['4']
        tmp=tmp[ tmp.iloc[:,0]==param].copy()  #dataframe
        #print(tmp)
        if len(tmp.index)>0:  #Find a record
            superframeNo=tmp.iat[0,3]
            for ii in range( len(tmp.index)):
                tmp2=[ #superframe Single parameter record
                    tmp.iat[ii,1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit word. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                    tmp.iat[ii,2],   #period, In the cycle, every few frames appear once
                    tmp.iat[ii,3],   #superframe no, Corresponding to the Superframe No
                    tmp.iat[ii,4],   #Frame,  Located in several Frames (by superframe counter, find Frame with number 1)
                    tmp.iat[ii,5],   #bitOut, In 12bit, several bits start
                    tmp.iat[ii,6],   #bitLen, A few bits in total
                    tmp.iat[ii,7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits, write writing
                    tmp.iat[ii,10],  #resolution, Unused
                    ]
                ret4.append(tmp2)
            tmp=DATA.fra['3']
            tmp=tmp[ tmp.iloc[:,0]==superframeNo].copy()  #dataframe
            for ii in range( len(tmp.index)):
                tmp2=[ #superframe Global configuration
                    tmp.iat[ii,0],   #superframe no
                    tmp.iat[ii,1],   #subframe,Which subframe is located (1-4)
                    tmp.iat[ii,2],   #word, Several Word (SYNC WORD number as 1) in Subframe
                    tmp.iat[ii,3],   #bitOut, In 12bit, several bits start (usually = 12)
                    tmp.iat[ii,4],   #bitLen, A total of several bits (usually = 12)
                    tmp.iat[ii,5],   #superframe counter 1/2, Corresponding to the number of counters in the total configuration
                    ]
                ret3.append(tmp2)
                    

    return { '1':
            [  #Frame total configuration, up to two records (indicating two counters)
                DATA.fra['1'].iat[1,1],  #WORD/SEC, the number of Word per second, that is, word/subframe
                DATA.fra['1'].iat[1,2],  #sync length, Synchronous word length (bits = 12,24,36)
                DATA.fra['1'].iat[1,3],  #sync1, Synchronous word, first 12bits
                DATA.fra['1'].iat[1,4],  #sync2
                DATA.fra['1'].iat[1,5],  #sync3
                DATA.fra['1'].iat[1,6],  #sync4
                DATA.fra['1'].iat[1,7],  #subframe,[superframe counter],There are from each frame, these 4 items are the position of the counter
                DATA.fra['1'].iat[1,8],  #word,    [superframe counter]
                DATA.fra['1'].iat[1,9],  #bitOut,  [superframe counter]
                DATA.fra['1'].iat[1,10], #bitLen,  [superframe counter]
                DATA.fra['1'].iat[1,11], #Value in 1st frame (0/1), The value of the number of numbers 1, the value of the counter (the minimum value of the counter)
                ],
             '2':ret2,
             '3':ret3,
             '4':ret4,
            }

def arinc429_to_characters(arinc_word):
    # Extract the 18-bit data segment from the ARINC 429 word (bits 11-28)
   
    encoding_table = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
    10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T',
    20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: ' ', 27: '0', 28: '1', 29: '2',
    30: '3', 31: '4', 32: '5', 33: '6', 34: '7', 35: '8', 36: '9', 37: '.', 38: ',', 39: '-'
    }

    data_segment = (arinc_word >> 3) & 0x3FFFF

    # Split the data segment into three 6-bit segments
    char_segments = [0, 0, 0]
    char_segments[0] = (data_segment >> 12) & 0x3F
    char_segments[1] = (data_segment >> 6) & 0x3F
    char_segments[2] = data_segment & 0x3F

    # Convert the 6-bit segments into characters using the provided encoding table
    characters = [encoding_table[seg] for seg in char_segments]

    return ''.join(characters)


# def getAIR(reg):
#     '''
#     Get the configuration of the decoding library corresponding to the tail number.
#     Pick out useful, sort it out, return to
#        Author: Southern Airlines, llgz@csair.com
#     '''
#     reg=reg.upper()
#     df_flt=AIR.csv(conf.aircraft)
#     tmp=df_flt[ df_flt.iloc[:,0]==reg].copy()  #dataframe
#     if len(tmp.index)>0:  #Find a record
#         return [tmp.iat[0,12],   #dataver
#                 tmp.iat[0,13],   #dataver
#                 tmp.iat[0,16],   #recorderType
#                 tmp.iat[0,16]]   #recorderType
#     else:
#         return [0,0,0]

# def getREG(fname):
    # '''
    # From the name of the ZIP file, find out the tail number of the machine
    #    Author: Southern Airlines, llgz@csair.com
    # '''
    # basename=os.path.basename(fname)
    # tmp=basename.strip().split('_',1)
    # if len(tmp[0])>6: #787's file name is useless
    #     return tmp[0][:6]
    # elif len(tmp[0])>0:
    #     return tmp[0]
    # else:
    #     return ''

def showsize(size):
    '''
    Show, for Human Readable
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

def sysmem():
    '''
    Get the memory occupied by the Python program
    '''
    size=psutil.Process(os.getpid()).memory_info().rss #The actual physical memory, including shared memory
    #size=psutil.Process(os.getpid()).memory_full_info().uss #The actual physical memory used does not include shared memory
    return showsize(size)

import os
import sys
import getopt
def usage():
    print(u'Usage:')
    print(u'   Command line tool.')
    print(u' Read in WGL raw.dat,Decoder a parameter according to the parameter coding rules.')

    print(sys.argv[0]+' [-h|--help]')
    print('   * (Necessary parameters)')
    print('   -h, --help                 print usage.')
    print(' * -f, --file xxx.wgl.zip     "....wgl.zip" filename')
    print(' * -p, --param alt_std        show "ALT_STD" param. Automatically all uppercase.')
    print('   --paramlist                list all param name.')
    print('   -w xxx.csv            Parameter writing file"xxx.csv"')
    print('   -w xxx.csv.gz         Parameter writing file"xxx.csv.gz"')
    print(u'\n               author:Southern Airlines, llgz@csair.com')
    print(u'I think this project is helpful to you. Please send me an email and make me happy.')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
    print()
    return

if __name__=='__main__':
    # if(len(sys.argv)<2):
    #     usage()
    #     sys.exit()
    # try:
    #     opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:p:',['help','file=','paramlist','param=',])
    # except getopt.GetoptError as e:
    #     print(e)
    #     usage()
    #     sys.exit(2)
    # FNAME=None
    # WFNAME=None
    # DUMPDATA=False
    # PARAMLIST=False
    # PARAM=None
    # for op,value in opts:
    #     if op in ('-h','--help'):
    #         usage()
    #         exit()
    #     elif op in('-f','--file'):
    #         FNAME=value
    #     elif op in('-w',):
    #         WFNAME=value
    #     elif op in('-d',):
    #         DUMPDATA=True
    #     elif op in('--paramlist',):
    #         PARAMLIST=True
    #     elif op in('-p','--param',):
    #         PARAM=value
    # if len(args)>0:  #Command line remaining parameters
    #     FNAME=args[0]  #Only take the first one

    FNAME='5471'
    WFNAME=None
    DUMPDATA=True
    PARAMLIST=False
    PARAM='ACID1'
    # if FNAME is None:
    #     usage()
    #     exit()
    # if os.path.isfile(FNAME)==False:
    #     print(FNAME,'Not a file')
    #     sys.exit()

    main()

