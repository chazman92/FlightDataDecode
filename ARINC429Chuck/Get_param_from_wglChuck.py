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
import psutil         #Non -essential library
#from io import BytesIO
#pAndas is not a necessary library.Get the parameter back is the list table of the dist.Pandas is not used.
import pandas as pd   #Non -essential library
import config_vec as conf
import read_air as AIR
import read_fra as FRA
import read_par as PAR
#from decimal import Decimal
#import arinc429  #did not use# https://github.com/aeroneous/PyARINC429   #py3.5

class DATA:
    'Used to save the classes of configuration parameters'
    pass

def main():
    global FNAME,WFNAME,DUMPDATA
    global PARAM,PARAMLIST

    #print('mem:',sysmem())

    reg=getREG(FNAME)
    air=getAIR(reg)

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
        print('dataVer:',air[0],air[1])
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
    获取 superframe 参数，返回 ARINC 429 format
  -------------------------------------
  bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
      |  | SSM |                            DATA field                  | SDI|     label     | 
     _/  \     | MSB -->                                        <-- LSB |    |               | 
    /     \    
   |parity |   
  -------------------------------------  
    author:南方航空,LLGZ@csair.com  
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
            #counter2  没有从配置文件读入(todo)
            #{'part':1,}
            ]
    if sync_word_len>1: #如果同步字 > 1 word
        sync1=(sync1 << (12 * (sync_word_len-1))) +1  #生成长的同步字
        sync2=(sync2 << (12 * (sync_word_len-1))) +1
        sync3=(sync3 << (12 * (sync_word_len-1))) +1
        sync4=(sync4 << (12 * (sync_word_len-1))) +1

    #----------参数配置的整理-----------
    super_set=[]
    for vv in fra['3']: #全部内容变为 int
        p_set={  #临时变量
            'frameNo':int(vv[0]),
            'sub' :int(vv[1]),
            'word':int(vv[2]),
            'bout':int(vv[3]),
            'blen':int(vv[4]),
            'counterNo' :int(vv[5]),
            }
        super_set.append(p_set)
    super_set=super_set[0] #只取了第一项,通常一个super参数只会对应一个frameNo

    #----------参数配置的整理,把一个period作为一个大frame处理-----------
    superpm_set=[]
    p_set=[]  #临时变量
    last_part=0
    for vv in fra['4']: #全部内容变为 int
        vv[0]=int(vv[0]) #part
        if vv[0]<=last_part:
            #part=1,2,3 根据part分组
            superpm_set.append(p_set)
            p_set=[]
        last_part=vv[0]
        #frameNo=vv[2]   #应该由frameNo取找super_set中对应的配置,这里简单化了。
        p_set.append({
            'part':vv[0],
            'rate': 1,
            'sub' :super_set['sub'],
            'word':super_set['word'] + (int(vv[3])-1) * word_sec * 4, #subframe + (Frame-1) * word_sec *4
            'bout':int(vv[4]),  #以下两项bout,blen,应该用super_set中的设置,获取数据后,再用这里的配置取出最终bits。
            'blen':int(vv[5]),  #但是因为super_set中的内容都是12,12。所以这里就直接用了最终配置。
            'bin' :int(vv[6]),
            'occur' : -1,
            'resol': float(vv[7]), #resolution
            'period':int(vv[1]),
            })
    if len(p_set)>0: #最后一组
        superpm_set.append(p_set)

    #----------打印参数-----------
    print('Frame定义: Word/SEC:%d, syncLen(word):%d, sync1234: %X,%X,%X,%X'%(word_sec,sync_word_len,sync1,sync2,sync3,sync4) )
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

    #----------打开zip压缩文件-----------
    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('==>ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%FNAME))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    #----------寻找起始位置-----------
    ttl_len=len(buf)
    frame_pos=0  #frame开始位置,字节指针
    frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
    if frame_pos > 0:
        print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
    if frame_pos >= ttl_len - sync_word_len *2:
        #整个文件都没找到同步字
        print('==>ERR, SYNC not found at end of DATA.',flush=True)
        raise(Exception('ERR,SYNC not found at end of DATA.'))

    period=superpm_set[0][0]['period']   #简单的从第一组的第一条记录中获取period

    #----------计算counter_mask-----------
    #有的库 counter 是递增 1, N个period一循环。 有的是递增 256,一个period一循环。
    #根据前后两个Frame中的counter值，确定mask。
    frame_counter  = get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
    frame_counter -= get_arinc429(buf, frame_pos + word_sec * 4 * 2, superframe_counter_set, word_sec )
    if abs(frame_counter) ==1:
        count_mask = ( 1 << int(pow(period, 0.5)) ) -1  #平方根sqrt: pow(x, 0.5) or (x ** 0.5)
        #count_mask= 0xf
    else:
        count_mask= 0
    print('counter sep:',frame_counter,period,bin(count_mask) )
    
    #----------寻找SuperFrame起始位置-----------
    val_first=super_set['counterNo'] #superframe counter 1/2
    if val_first==2: val_first=1  #counter2 没从配置中读入(todo)
    val_first=superframe_counter_set[val_first-1]['v_first']
    pm_sec=0.0   #参数的时间轴,秒数
    frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
    pm_sec += sec_add  #加上时间增量

    #----------读参数-----------
    ii=0    #计数
    pm_list=[] #参数列表
    while True:
        # 有几个dataVer的数据,不是从文件头开始,只匹配sync1会找错。且不排除中间会错/乱。
        #所以每次都要确认first frame的位置。 实际测试,发现有同步字错误,但frame间隔正确。
        frame_pos2=frame_pos   #保存旧位置
        frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
        pm_sec += sec_add  #加上时间增量
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break

        for pm_set in superpm_set:
            #获取anrinc429,第一步应该用super_set中的bout,blen设置,获取数据后,再用superpm_set中的配置取出最终bits。
            #但是因为super_set中的内容都是12,12。所以这里就直接用了最终配置。
            value=get_arinc429(buf, frame_pos, pm_set, word_sec )  #ARINC 429 format
            value =arinc429_decode(value ,par )
            # superpm_set 中有个 resolution 似乎是无用的。AGS配置中,说是自动计算的,不让改。
            # 试着乘上去，数据就不对了。
            #if pm_set[0]['resol'] != 0.0 and pm_set[0]['resol'] != 1.0: 
            #    value *= pm_set[0]['resol']

            pm_list.append({'t':round(pm_sec,10),'v':value})
            #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
            #pm_list.append({'t':round(pm_sec,10),'v':value,'c':frame_counter})

        pm_sec += 4.0 * period  #一个frame是4秒
        frame_pos += word_sec * 4 * 2 * period   # 4subframe, 2bytes,直接跳过一个period,哪怕中间有frame错误/缺失，都不管了。
    return pm_list

def find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync, val_first, superframe_counter_set, period, count_mask ):
    '''
    判断 first frame 的位置，如果不是，则向后推 1 frame再找。
    根据 superframe_counter 的内容，找到conter的值为 first value 的frame位置
       author:南方航空,LLGZ@csair.com  
    '''
    pm_sec=0.0   #参数的时间轴,秒数
    while True:
        frame_pos2=frame_pos   #保存旧位置
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync )  #判断同步字，或继续寻找新位置
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #如果失去同步,重新同步后,时间加4秒。(这里应该根据跳过的距离确定时间增量,这里就简单粗暴了)

        frame_counter=get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
        if count_mask > 0:
            frame_counter &= count_mask
        if frame_counter==val_first:
            #print('Found first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            break
        else:
            print('NotFound first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            pm_sec += 4.0   #一个frame是4秒
            frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes

    return frame_pos, pm_sec  #返回位置, 时间增量

def get_param(fra,par):
    '''
    Get the regula parameter and return to ArinC 429 Format
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
    
    #----------Read parameter-----------
    ii=0    #count
    pm_list=[] #parameter list
    pm_sec=0.0   #The timeline of the parameter, the number of seconds
    while True:
        # There are several data -data data, not starting from the file header, only sync1 will find it wrong.It is not ruled out that it will be wrong/chaos in the middle.
        #So use Find_Sync1 () to judge each time.The actual test was found that there were synchronous words errors, but the Frame interval was correct.
        frame_pos2=frame_pos   #Save the old position
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )  #Determine synchronization words, or continue to find new positions
        if frame_pos>=ttl_len -2:
            #-----Beyond the end of the file, exit-----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #If the synchronization is lost, after the synchronization, the time will be 4 seconds.(This should be determined according to the jump distance, it is simple and rude here)


        sec_add = 4.0 / len(param_set)  #一个frame是4秒
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
    判断 frame_pos 位置，是否满足同步字特征。如果不满足, 继续寻找下一个起始位置
    '''
    #ttl_len=len(buf)
    while frame_pos<ttl_len - sync_word_len *2:  #寻找frame开始位置
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
            #part=1,2,3 According to part groups
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
            'occur' :int(vv[7]) if len(vv[7])>0 else -1,
            })
    if len(p_set)>0: #Last group
        group_set.append(p_set)

    # --------打印 分组配置----------
    #print('分组配置: len:%d'%(len(group_set) ) )
    #for vv in group_set:
    #    print(vv)

    # --------根据rate补齐记录-------
    param_set=[]
    frame_rate=group_set[0][0]['rate']
    if frame_rate>4:
        frame_rate=4           #一个frame中占几个subframe
    subf_sep=4//frame_rate  #整除
    for subf in range(0,4,subf_sep):  #补subframe, 仅根据第一条记录的rate补
        for group in group_set:
            frame_rate=group[0]['rate']
            if frame_rate>4:
                sub_rate=frame_rate//4  #一个subframe中有几个记录 ,整除
            else:
                sub_rate=1
            word_sep=word_sec//sub_rate  #整除
            for word_rate in range(sub_rate):  #补word, 根据分组记录的第一条rate补
                p_set=[]  #临时变量
                for vv in group:
                    p_set.append({
                        'part':vv['part'],
                        'rate':vv['rate'],
                        'sub' :vv['sub']+subf,
                        'word':vv['word']+word_rate*word_sep,
                        'bout':vv['bout'],
                        'blen':vv['blen'],
                        'bin' :vv['bin'],
                        'occur':vv['occur'],
                        })
                param_set.append(p_set)
    return param_set

def arinc429_decode(word,conf):
    '''
    par可能有的 Type: 'CONSTANT' 'DISCRETE' 'PACKED BITS' 'BNR LINEAR (A*X)' 'COMPUTED ON GROUND' 'CHARACTER' 'BCD' 'BNR SEGMENTS (A*X+B)' 'UTC'
    par实际有的 Type: 'BNR LINEAR (A*X)' 'BNR SEGMENTS (A*X+B)' 'CHARACTER' 'BCD' 'UTC' 'PACKED BITS'
        author:南方航空,LLGZ@csair.com  
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
从 Take the value in the arinc429 format
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
            #Stepped configuration
            value = ''
            for vv in conf['part']:
                #According to Blen, obtain the mask value
                bits= (1 << vv['blen']) -1
                #Move the value to the right (move to BIT0) and get the value
                tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                value +=  chr(tmp)
        else:
            #According to Blen, obtain the mask value
            bits= (1 << conf['blen']) -1
            #Move the value to the right (move to BIT0) and get the value
            value = ( word >> (conf['pos'] - conf['blen']) ) & bits
            value =  chr(value)
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
            #According to Blen, obtain the mask value
            bits= (1 << conf['blen']) -1
            #Move the value to the right (move to BIT0) and get the value
            value = ( word >> (conf['pos'] - conf['blen']) ) & bits
        return value * sign

def arinc429_BNR_decode(word,conf):
    '''
从 Take the value in the arinc429 format
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
        #---- Know the Packed Bits, UTC, Discrete, and you should process it according to BNR ---
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
        #if pm_set['part']>pre_id:  #有多组配置，只执行第一组。//配置经过整理，只剩一组了。
        #    pre_id=pm_set['part']
        #else:
        #    break
        word=getWord(buf,
                frame_pos + word_sec *2 *(pm_set['sub']-1) +(pm_set['word']-1)*2  #The position occupied by the synchronous word, number is 1, so -1
                )
        #According to Blen, obtain the mask value
        bits= (1 << pm_set['blen']) -1
        #According to the BOUT, the mask is moved to the corresponding position
        bits <<= pm_set['bout'] - pm_set['blen']
        word &= bits  #获取值
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
    获取参数在arinc717的12bit word中的位置配置
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
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
        param=param.upper() #改大写
        #---find regular parameter----
        tmp=DATA.fra['2']
        tmp=tmp[ tmp.iloc[:,0]==param].copy()  #dataframe
        #print(tmp)
        if len(tmp.index)>0:  #找到记录
            for ii in range( len(tmp.index)):
                tmp2=[  #regular 参数配置
                    tmp.iat[ii,1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit word. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                    tmp.iat[ii,2],   #recordRate, Record frequency (record number/frame)
                    tmp.iat[ii,3],   #subframe, Which subframe is located (1-4)
                    tmp.iat[ii,4],   #word, Several Word (SYNC WORD number as 1) in Subframe
                    tmp.iat[ii,5],   #bitOut, In 12bit, several bits start
                    tmp.iat[ii,6],   #bitLen, A few bits in total
                    tmp.iat[ii,7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits, write writing
                    tmp.iat[ii,12],  #Occurence No
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
                tmp2=[ #Superframe single parameter record
                    tmp.iat[ii,1],   #PART (1,2,3), there will be multiple sets of records, corresponding to multiple 32bit words. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                    tmp.iat[ii,2],   #Period, cycle, every few frames appear once
                    tmp.iat[ii,3],   #Superframe no, corresponding
                    tmp.iat[ii,4],   #Frame, in the first few frames (by superframe counter, find the frame number 1)
                    tmp.iat[ii,5],   #Bitout, in 12bit, the first few bits start
                    tmp.iat[ii,6],   #Bitlen, a few bits in total
                    tmp.iat[ii,7],   #Bitin, write into the 32bits word of Arinc429, start with the number of bits from the first bits
                    tmp.iat[ii,10],  #resolution, Unused
                    ]
                ret4.append(tmp2)
            tmp=DATA.fra['3']
            tmp=tmp[ tmp.iloc[:,0]==superframeNo].copy()  #dataframe
            for ii in range( len(tmp.index)):
                tmp2=[ #superframe 全局配置
                    tmp.iat[ii,0],   #superframe no
                    tmp.iat[ii,1],   #subframe, 位于哪个subframe(1-4)
                    tmp.iat[ii,2],   #word, 在subframe中第几个word(sync word编号为1)
                    tmp.iat[ii,3],   #bitOut, 在12bit中,第几个bit开始(通常=12)
                    tmp.iat[ii,4],   #bitLen, 共几个bits(通常=12)
                    tmp.iat[ii,5],   #superframe counter 1/2, 对应Frame总配置中的第几个counter
                    ]
                ret3.append(tmp2)
                    

    return { '1':
            [  #Frame 总配置, 最多两条记录(表示有两个counter)
                DATA.fra['1'].iat[1,1],  #Word/Sec, 每秒的word数量,即 word/subframe
                DATA.fra['1'].iat[1,2],  #sync length, 同步字长度(bits=12,24,36)
                DATA.fra['1'].iat[1,3],  #sync1, 同步字,前12bits
                DATA.fra['1'].iat[1,4],  #sync2
                DATA.fra['1'].iat[1,5],  #sync3
                DATA.fra['1'].iat[1,6],  #sync4
                DATA.fra['1'].iat[1,7],  #subframe,[superframe counter],每个frame中都有,这4项是counter的位置
                DATA.fra['1'].iat[1,8],  #word,    [superframe counter]
                DATA.fra['1'].iat[1,9],  #bitOut,  [superframe counter]
                DATA.fra['1'].iat[1,10], #bitLen,  [superframe counter]
                DATA.fra['1'].iat[1,11], #Value in 1st frame (0/1), 编号为1的frame,counter的值(counter的最小值)
                ],
             '2':ret2,
             '3':ret3,
             '4':ret4,
            }

def getAIR(reg):
    '''
    Get the configuration of the decoding library corresponding to the tail number.
    Pick out useful, sort it out, return to
       Author: Southern Airlines, llgz@csair.com
    '''
    reg=reg.upper()
    df_flt=AIR.csv(conf.aircraft)
    tmp=df_flt[ df_flt.iloc[:,0]==reg].copy()  #dataframe
    if len(tmp.index)>0:  #找到记录
        return [tmp.iat[0,12],   #dataver
                tmp.iat[0,13],   #dataver
                tmp.iat[0,16],   #recorderType
                tmp.iat[0,16]]   #recorderType
    else:
        return [0,0,0]

def getREG(fname):
    '''
    From the name of the ZIP file, find out the tail number of the machine
       Author: Southern Airlines, llgz@csair.com
    '''
    basename=os.path.basename(fname)
    tmp=basename.strip().split('_',1)
    if len(tmp[0])>6: #787的文件名没有用 _ 分隔
        return tmp[0][:6]
    elif len(tmp[0])>0:
        return tmp[0]
    else:
        return ''

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

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u' Command line tool.')
    print(u' Read raw.dat in WGL, and decode a parameter according to the parameter coding rules.')

    print(sys.argv[0]+' [-h|--help]')
    print('  * (Necessary parameters)')
    print('   -h, --help                 print usage.')
    print(' * -f, --file xxx.wgl.zip     "....wgl.zip" filename')
    print(' * -p, --param alt_std        show "ALT_STD" param. Automatically all uppercase.')
    print('   --paramlist                list all param name.')
    print('   -w xxx.csv            Parameter writing file"xxx.csv"')
    print('   -w xxx.csv.gz         Parameter writing file"xxx.csv.gz"')
    print(u'\n               Author: Southern Airlines, llgz@csair.com ')
    print(u' I think this project is helpful to you. Please send me an email and make me happy.')
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

