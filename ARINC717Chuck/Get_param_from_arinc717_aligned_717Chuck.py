#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Decoding a parameter.
Only support ArinC 573/717 Aligned format
------
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
   Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com -- Modified by Chuck Cook ccook@jetblue.com
  --------------------------
'''
The primitive ArinC 573/717 PCM file should be processed first, change 12bits to 16bits storage, and use the empty Frame to make up the missing Frame structure.
 The program will be read in the aligned bit format format.
"""
import os,sys
import read_fra_717Chuck as FRA
import read_par_717Chuck as PAR

class ARINC717():
    '''
   From ArIinc 573/717 Aligned format file, get parameters
    '''
    def __init__(self,fpath, fname):
        '''
      For example variables used to save configuration parameters
        '''
        # self.air=None
        self.datapath= fpath
        self.fra=None
        self.fra_dataver=''
        self.par=None
        self.par_dataver=''
        self.qar=None
        self.qar_filename= ""
        if len(fname)>0:
            self.qar_file(fname)

    def qar_file(self,qar_filename):
        #----------Open the DAR/QAR file-----------
        if self.qar is None or self.qar_filename != qar_filename:
            #read into buffer
            file = open(self.datapath + qar_filename,'rb')
            self.qar=file.read()
            self.qar_filename=qar_filename
            file.close()

        self.readFRA()
        self.readPAR()

    def get_param(self, parameter):
        fra = self.getFRA(parameter)
        par = self.getPAR(parameter)
        if len(fra)<1:
            print('Empty dataVer.',flush=True)
            return []
        if len(fra['2'])<1 and len(fra['4'])<1:
            print('Parameter not found.',flush=True)
            return []

        if len(fra['2'])>0:
            pm_list=self.get_regular(fra,par) #Get a parameter, regular
        else:
            pm_list=self.get_super(fra,par) #Get a parameter, superframe
        return pm_list

    def get_super(self,fra,par):
        '''
        Get the superframe parameter and return to Arinc 429 format
      -------------------------------------
      bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
          |  | SSM |                            DATA field                  | SDI|     label     | 
         _/  \     | MSB -->                                        <-- LSB |    |               | 
        /     \    
       |parity |   
      -------------------------------------  
       Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        #Initialize variables
        word_sec=int(fra['1'][0])
        sync_word_len=int(fra['1'][1])//12  #Event, the number (length) of the synchronous words (length)
        sync1=int(fra['1'][2],16)  #Synchronous word 1
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
                'peh':int(fra['1'][10]),
                # 'bin' :12,
                # 'occur': -1,
                },
                #Counter2 does not read from the configuration file (TODO)
                #{'part':1,}
                ]
        if sync_word_len>1: #If synchronous words> 1 word
            sync1=(sync1 << (12 * (sync_word_len-1))) +1  #Synchronous word for growth
            sync2=(sync2 << (12 * (sync_word_len-1))) +1
            sync3=(sync3 << (12 * (sync_word_len-1))) +1
            sync4=(sync4 << (12 * (sync_word_len-1))) +1

        #----------Parameter configuration-----------
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

        #---------- The arrangement of the parameter configuration, take a period as a big Frame processing -------
        superpm_set=[]
        p_set=[]  #Temporary variables
        last_part=0
        for vv in fra['4']: #All content becomes int
            vv[0]=int(vv[0]) #part
            if vv[0]<=last_part:
                #part=1,2,3 According to part groups
                superpm_set.append(p_set)
                p_set=[]
            last_part=vv[0]
            #frameNo=vv[2]   #The corresponding configuration of Frameno should be found in the super_set, which is simplified here.
            p_set.append({
                'part':vv[0],
                'rate': 1,
                'sub' :super_set['sub'],
                'word':super_set['word'] + (int(vv[3])-1) * word_sec * 4, #subframe + (Frame-1) * word_sec *4
                'bout':int(vv[4]),  #The following two bouts, blen should be set in Super_Set. After obtaining the data, use the configuration here to remove the final bits.
                'blen':int(vv[5]),  #But because the content in Super_Set is 12,12.So the final configuration is used here.
                'bin' :int(vv[6]),
                'occur' : -1,
                'resol': float(vv[7]), #resolution
                'period':int(vv[1]),
                })
        if len(p_set)>0: #Last group
            superpm_set.append(p_set)

        #----------Data Type Warning-----------
        if par['type'].find('BCD')!=0 and \
                par['type'].find('BNR LINEAR (A*X)')!=0 and \
                par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
                par['type'].find('CHARACTER')!=0 and \
                par['type'].find('DISCRETE')!=0 and \
                par['type'].find('PACKED BITS')!=0 and \
                par['type'].find('UTC')!=0 :
            print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) ,flush=True)

        #----------The total data of the original data in the compression file-----------
        ttl_len=len(self.qar)

        #----------Find the starting position-----------
        frame_pos=0  #Frame starts position, byte pointer
        frame_pos=self.find_SYNC1( ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
        if frame_pos > 0:
            print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
        if frame_pos >= ttl_len - sync_word_len *2:
            #No synchronization words were found throughout the file
            print('==>ERR, SYNC not found at end of DATA.',flush=True)
            raise(Exception('ERR,SYNC not found at end of DATA.'))

        period=superpm_set[0][0]['period']   #Simply obtain Period from the first record of the first group

        #----------Calculate the counter_mask-----------
        #Some libraries are increased by 1, n period.Some are increasing 256, a period cycle.
        #Determine MASK according to the counter value in the two Frames.
        frame_counter  = self.get_arinc429( frame_pos, superframe_counter_set, word_sec )
        frame_counter -= self.get_arinc429( frame_pos + word_sec * 4 * 2, superframe_counter_set, word_sec )
        if abs(frame_counter) ==1:
            count_mask = ( 1 << int(pow(period, 0.5)) ) -1  #SQRT: POW (x, 0.5) or (x ** 0.5)
            #count_mask= 0xf
        else:
            count_mask= 0
        #print('counter sep:',frame_counter,period,bin(count_mask) )

        #----------Looking for the starting position of Superframe-----------
        val_first=super_set['counterNo'] #superframe counter 1/2
        if val_first==2: val_first=1  #Counter2 does not read from the configuration (TODO)
        val_first=superframe_counter_set[val_first-1]['v_first']
        pm_sec=0.0   #Parameter of the timeline, seconds number
        frame_pos,sec_add=self.find_FIRST_super( ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
        pm_sec += sec_add  #Add time increment

        #----------Read the parameter-----------
        ii=0    #count
        pm_list=[] #parameter list
        while True:
            #There are several DataVER data, not starting from the file header, only sync1 will find it wrong.It is not ruled out that the middle will be wrong/chaos.
            #So confirm the location of First Frame every time.The actual test was found that there was a synchronous word error, but the Frame interval was correct.
            frame_pos2=frame_pos   #Save the old position
            frame_pos,sec_add=self.find_FIRST_super( ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
            pm_sec += sec_add  #Add time increment
            if frame_pos>=ttl_len -2:
                #-----On the end of the file, exit-----
                break

            for pm_set in superpm_set:
                #Get Anrinc429, the first step should be set with the bout, blen settings in Super_Set, and after obtaining the data, use the configuration in Superpm_Set to remove the final BITS.
                #But because the content in Super_Set is 12,12.So the final configuration is used here.
                value=self.get_arinc429( frame_pos, pm_set, word_sec )  #ARINC 429 format
                value =self.arinc429_decode(value ,par )
                # superpm_set There is a resolution that seems useless.In the AGS configuration, it is said to be automatically calculated and not allowed to change.
                #Try to ride, the data is wrong.
                #if pm_set[0]['resol'] != 0.0 and pm_set[0]['resol'] != 1.0: 
                #    value *= pm_set[0]['resol']

                pm_list.append({'t':round(pm_sec,10),'v':value})
                #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
                #pm_list.append({'t':round(pm_sec,10),'v':value,'c':frame_counter})

            pm_sec += 4.0 * period  #A frame is 4 seconds
            frame_pos += word_sec * 4 * 2 * period   #4Subframe, 2bytes, skipped a period directly, even if there is Frame error/lack in the middle, it doesn't care.
        return pm_list

    def find_FIRST_super(self, ttl_len, frame_pos, word_sec, sync_word_len, sync, val_first, superframe_counter_set, period, count_mask ):
        '''
        Judging the position of the first frame, if not, push 1 frame and find it back.
        According to the content of Superframe_Counter, find the Frame position of the value as FIRST VALUE
           Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        pm_sec=0.0   #The timeline of the parameter, the number of seconds
        while True:
            frame_pos2=frame_pos   #Save the old position
            frame_pos=self.find_SYNC1( ttl_len, frame_pos, word_sec, sync_word_len, sync )  #Determine synchronization words, or continue to find new positions
            if frame_pos>=ttl_len -2:
                #-----Beyond the end of the file, exit-----
                break
            if frame_pos>frame_pos2:
                print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) ,flush=True)
                pm_sec +=4  #If the synchronization is lost, after the synchronization, the time will be added for 4 seconds.(Here we should determine the time according to the skip distance, it is simple and rude here)

            frame_counter=self.get_arinc429( frame_pos, superframe_counter_set, word_sec )
            if count_mask > 0:
                frame_counter &= count_mask
            if frame_counter==val_first:
                #print('Found first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
                break
            else:
                print('NotFound first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) ,flush=True)
                pm_sec += 4.0   #A frame is 4 seconds
                frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes

        return frame_pos, pm_sec  #Return position, time increase

    def get_regular(self,fra,par):
        '''
        Get the regular parameter and return to Arinc 429 Format
      -------------------------------------
      bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
          |  | SSM |                            DATA field                  | SDI|     label     | 
         _/  \     | MSB -->                                        <-- LSB |    |               | 
        /     \    
       |parity |   
      -------------------------------------  
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        #Initialize variables
        word_sec=int(fra['1'][0])
        sync_word_len=int(fra['1'][1])//12  #Event, the number (length) of the synchronous words (length)
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
                'peh':int(fra['1'][10]),
                # 'bin' :12,
                # 'occur': -1,
                }]
        if sync_word_len>1: #If synchronous words> 1 word
            sync1=(sync1 << (12 * (sync_word_len-1))) +1  #Synchronous word for growth
            sync2=(sync2 << (12 * (sync_word_len-1))) +1
            sync3=(sync3 << (12 * (sync_word_len-1))) +1
            sync4=(sync4 << (12 * (sync_word_len-1))) +1

        param_set=self.getDataFrameSet(fra['2'],word_sec)  #Configuration of sorting parameter position records

        #----------Data Type Warning-----------
        #Need to update for Jetblue Parameter files
        if par['type'].find('BCD')!=0 and \
                par['type'].find('BNR LINEAR (A*X)')!=0 and \
                par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
                par['type'].find('CHARACTER')!=0 and \
                par['type'].find('DISCRETE')!=0 and \
                par['type'].find('PACKED BITS')!=0 and \
                par['type'].find('UTC')!=0 :
            print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) ,flush=True)

        #----------The total data in the compressed file-----------
        ttl_len=len(self.qar)

        #----------Find the starting position-----------
        frame_pos=0  #Frame starts position, byte pointer
        frame_pos=self.find_SYNC1( ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
        if frame_pos > 0:
            print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
        if frame_pos >= ttl_len - sync_word_len *2:
            #No synchronization words were found throughout the file
            print('==>ERR, SYNC not found at end of DATA.',flush=True)
            raise(Exception('ERR,SYNC not found at end of DATA.'))

        #----------Read parameter-----------
        ii=0    #count
        pm_list=[] #parameter list
        pm_sec=0.0   #The timeline of the parameter, the number of seconds
        while True:
            #There are several DataVER data, not starting from the file header, only sync1 will find it wrong.It is not ruled out that the middle will be wrong/chaos.
            #So use Self.find_sync1 () every time.The actual test was found that there was a synchronous word error, but the Frame interval was correct.
            frame_pos2=frame_pos   #Save the old position
            frame_pos=self.find_SYNC1( ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )  #Determine synchronization words, or continue to find new position
            if frame_pos>=ttl_len -2:
                #-----Beyond the end of the file, exit-----
                break
            if frame_pos>frame_pos2:
                print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) ,flush=True)
                pm_sec +=4  #If the synchronization is lost, after the synchronization, the time will be added for 4 seconds.(Here we should determine the time according to the skip distance, it is simple and rude here)

            sec_add = 4.0 / len(param_set)  #A frame is 4 seconds
            for pm_set in param_set:
                value=self.get_arinc429( frame_pos, pm_set, word_sec )  #ARINC 429 format
                value =self.arinc429_decode(value ,par )

                pm_list.append({'t':round(pm_sec,10),'v':value})
                #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
                pm_sec += sec_add   #Time shaft accumulation

            frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes
        return pm_list

    def find_SYNC1(self, ttl_len, frame_pos, word_sec, sync_word_len, sync):
        '''
        Determine whether the Frame_POS position meets the characteristics of synchronization.If not satisfied, continue to find the next starting location
        '''
        while frame_pos<ttl_len - sync_word_len *2:  #Find the starting position of Frame
            #----It seems to only judge that the two consecutive synchronous words are correct, it is enough-----
            if self.getWord(frame_pos, sync_word_len) == sync[0] and \
                    self.getWord(frame_pos+word_sec*2,sync_word_len) == sync[1] :
            #if self.getWord(frame_pos, sync_word_len) == sync[0] and \
            #        self.getWord(frame_pos+word_sec*2,sync_word_len) == sync[1] and \
            #        self.getWord(frame_pos+word_sec*4,sync_word_len) == sync[2] and \
            #        self.getWord(frame_pos+word_sec*6,sync_word_len) == sync[3] :
                #print('==>Mark,x%X'%(frame_pos,))
                break
            frame_pos +=1
        return frame_pos

    def getDataFrameSet(self,fra2,word_sec):
        '''
        The configuration of the compilation parameters in the ArIinc717 position (position in 12 bit word)
        If it is not Self-Distant, there will be configuration of each position.Record all the location.
            You need to make up for other subframes according to the Rate value.
            For example: Rate = 4, that is, 1-4Subframe.Rate = 2 is in 1,3 or 2,4Subframe.
        If it is Self-Distant, there is only the configuration of the first position.Based on Rate, make up for all location records and group.
            You need to make up for other Subframe and Word positions according to the Rate value.
            Subframe's complement is the same as above. The interval between Word is to determine the number of records with Word/SEC.Uniformly divided into each subframe.
            Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
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
            #Rate: 1 = 1/4Hz (a Frame record), 2 = 1/2Hz, 4 = 1Hz (a record of each subframe), 8 = 2Hz, 16 = 4Hz, 32 = 8Hz (8 records per subframe have 8 records per subframe.Cure
            p_set.append({
                'part':vv[0],
                'rate':int(vv[1]),
                'sub' :int(vv[2]),
                'word':int(vv[3]),
                'bout':int(vv[4]),
                'blen':int(vv[5]),
                'bin' :int(vv[6]),
                'location' :(vv[7]) if len(vv[7])>0 else '',
                })
        if len(p_set)>0: #Last group
            group_set.append(p_set)

        # --------Printing packet configuration----------
        #print('Packet configuration: len:%d'%(len(group_set) ) )
        #for vv in group_set:
        #    print(vv)

        # --------Based on the Rate Makeup Record-------
        param_set=[]
        frame_rate=group_set[0][0]['rate']
        if frame_rate>4:
            frame_rate=4           #A Frame occupies a few subframes
        subf_sep=4//frame_rate  #Divide
        for subf in range(0,4,subf_sep):  #Make up the subframe, only the Rate supplement based on the first record
            for group in group_set:
                frame_rate=group[0]['rate']
                if frame_rate>4:
                    sub_rate=frame_rate//4  #There are several records in a subframe, which is divided
                else:
                    sub_rate=1
                word_sep=word_sec//sub_rate  #Divide
                for word_rate in range(sub_rate):  #Make up Word, according to the first rate supplement of the group record
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
                            'location':vv['location'],
                            })
                    param_set.append(p_set)
        return param_set

    def arinc429_decode(self,word,conf):
        '''
        PAR may have the Type: 'Constant' 'Discrete' 'Packed Bits'' BITS '' Bnr Linear (A*X) '' Computed on Ground 'Character' 'BCD' BNR Segments (A*X+B) 'UTC'
        Par's actual Type: 'BNR LINEAR (A*X)' 'BNR Segments (A*X+B)' Character '' BCD '' '' Packed Bits' 'Discrete'
            Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        if conf['type'].find('BNR')==0 or \
                conf['type'].find('PACKED BITS')==0:
            return self.arinc429_BNR_decode(word ,conf)
        elif conf['type'].find('BCD')==0 or \
                conf['type'].find('CHARACTER')==0:
            return self.arinc429_BCD_decode(word ,conf)
        elif conf['type'].find('UTC')==0:
            val=self.arinc429_BNR_decode(word ,conf)
            ss= val & 0x3f         #6bits
            mm= (val >>6) & 0x3f   #6bits
            hh= (val >>12) & 0x1f  #5bits
            return '%02d:%02d:%02d' % (hh,mm,ss)
        else:
            return self.arinc429_BNR_decode(word ,conf)

    def arinc429_BCD_decode(self,word,conf):
        '''
        Take the value from the Arinc429 format
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
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        if conf['type']=='CHARACTER':
            if len(conf['part'])>0:
                #Stepically configuration
                value = ''
                for vv in conf['part']:
                    #According to Blen, obtain the mask value
                    bits= (1 << vv['blen']) -1
                    #Move the value to the right (move to BIT0) and get the value
                    tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                    value +=  chr(tmp)
            else:
                #According to BLEN, get the mask value
                bits= (1 << conf['blen']) -1
                #Move the value to the right (move to BIT0) and get the value
                value = ( word >> (conf['pos'] - conf['blen']) ) & bits
                value =  chr(value)
            #print (value)
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
                #Stepically configuration
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

    def arinc429_BNR_decode(self, word,conf):
        '''
        Take the value from the Arinc429 format
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
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
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
            #---- Knowing Packed Bits, UTC, Discrete, you should process it according to BNR ---
            #Other types that cannot be recognized, press BNR by default
            #Here, no need to give an error prompt
            pass
        return value 

    def get_arinc429(self, frame_pos, param_set, word_sec ):
        '''
        According to FRA configuration, obtain 32bit word in the Arinc429 format
        Another: There are multiple different records in the FRA configuration, corresponding to multiple 32bit word (completed)
        BIT position is numbered from 1.Word position is also numbered from 1.The position of synchronization is 1, and the data word is from 2 (assuming that synchronous words only occupy 1Word).
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        value=0
        pre_id=0
        for pm_set in param_set:
            #if pm_set['part']>pre_id:  #There are multiple sets of configuration, only the first group.// The configuration has been sorted, and there is only one group.
            #    pre_id=pm_set['part']
            #else:
            #    break
            word=self.getWord(
                    frame_pos + word_sec *2 *(pm_set['sub']-1) +(pm_set['word']-1)*2  #The position occupied by the synchronous word, the number is 1, so -1
                    )
            #According to Blen, obtain the mask value
            bits= (1 << pm_set['blen']) -1
            #According to BOUT, the mask is moved to the corresponding position
            bits <<= pm_set['bout'] - pm_set['blen']
            word &= bits  #Obtain
            #Move the value to the target location
            move=pm_set['bin'] - pm_set['bout']
            if move>0:
                word <<= move
            elif move<0:
                word >>= -1 * move
            value |= word
        return value

    def getWord(self, pos, word_len=1):
        '''
        Read two bytes and take 12bit as a word.The low position is in front.LittleEndian, Low-Byte First.
        Support 12bits, 24bits, 36bits, 48bits, 60bits
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        buf=self.qar
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

    def readPAR(self):
        'Read PAR configuration'
        dataver=self.dataVer(self.getREG())
        # if isinstance(dataver,(str,float)):
        #     dataver=int(dataver)
        # if str(dataver).startswith('787'):
        #     print('ERR,dataver %s not support.' % (dataver,) ,flush=True)
        #     print('Use "read_frd.py instead.',flush=True)
        #     return
        if self.par is None or self.par_dataver != dataver: #Don't read it repeatedly if you have
            self.par=PAR.read_parameter_file(self.datapath + dataver + '.par')
            self.par_dataver = dataver

    def getPAR(self,param):
        '''
        Get the position configuration of the 32bit word of the parameter in Arinc429
        Pick out useful, sort it out, return
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        self.readPAR()
        if self.par is None or len(self.par)<1:
            return {}
        param=param.upper()  #Remodel
        pm_find=None  #Temporary variables
        for row in self.par:  #Find the first match record, there will only be a record in PAR
            if row[0] == param:
                pm_find=row
                break
        if pm_find is None:
            return {}
        else:
            tmp_part=[]
            if isinstance(pm_find[43], list):
                #If there are multiple parts of the configuration of bits, combine it
                for ii in range(len(pm_find[43])):
                    tmp_part.append({
                            'id'  :int(pm_find[43][ii]),  #DIGIT, sequential labeling
                            'pos' :int(pm_find[44][ii]),  #MSB, starting position
                            'blen':int(pm_find[45][ii]),  #bitlen, databits, data length
                            })
            return {
                    'ssm'    :int(pm_find[5]) if len(pm_find[5])>0 else -1,   #SSM Rule , (0-15)0,4 
                    'signBit':int(pm_find[6]) if len(pm_find[6])>0 else -1,   #bitLen,SignBit  ,Symbol position
                    'pos'   :int(pm_find[7]) if len(pm_find[7])>0 else -1,   #MSB  ,Start position
                    'blen'  :int(pm_find[8]) if len(pm_find[8])>0 else -1,   #bitLen,DataBits ,The total length of the data part
                    'part'    :tmp_part,
                    'type'    :pm_find[2],    #Type(BCD,CHARACTER)
                    'format'  :pm_find[17],    #Display Format Mode (DECIMAL,ASCII)
                    'Resol'   :pm_find[12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                    'A'       :pm_find[36] if pm_find[36] is not None else '',    #Coef A(Res)
                    'B'       :pm_find[37] if pm_find[37] is not None else '',    #Coef b
                    'format'  :pm_find[25],    #Internal Format (Float ,Unsigned or Signed)
                    }

    def readFRA(self):
        'Read FRA configuration'
        dataver=self.dataVer(self.getREG())
        # if isinstance(dataver,(str,float)):
        #     dataver=int(dataver)
        # if str(dataver).startswith('787'):
        #     print('ERR,dataver %s not support.' % (dataver,) ,flush=True)
        #     print('Use "read_frd.py instead.',flush=True)
        #     return
        if self.fra is None or self.fra_dataver != dataver: #Don't read it repeatedly if you have
            self.fra=FRA.read_parameter_file(self.datapath + dataver +'.fra')
            self.fra_dataver = dataver

    def getFRA(self,param):
        '''
        Get the position configuration of the 12bit word of the parameter in Arinc717
        Pick out useful, sort it out, return
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        self.readFRA()
        if self.fra is None:
            return None

        ret2=[]  #for regular
        ret3=[]  #for superframe
        ret4=[]  #for superframe pm
        if len(param)>0:
            param=param.upper() #Remodel
            #---find regular parameter----
            tmp=self.fra['2']
            idx=[]
            ii=0
            for row in tmp: #Find out all the records, one parameter will have multiple records
                if row[0] == param: idx.append(ii)
                ii +=1

            if len(idx)>0:  #Find a record
                for ii in idx:
                    tmp2=[  #regular Parameter configuration
                        tmp[ii][1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit words. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                        tmp[ii][2],   #recordRate,Record frequency (record number/frame)
                        tmp[ii][3],   #subframe, Which subframe is located (1-4)
                        tmp[ii][4],   #word, In Subframe, several Word (SYNC WORD number is 1)
                        tmp[ii][5],   #bitOut, In 12bit, several bits start
                        tmp[ii][6],   #bitLen, A total of several bits
                        tmp[ii][7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits
                        # tmp[ii][12],  #Occurence No
                        tmp[ii][8],   #Location Type(Imposed,Computed)
                        ]
                    ret2.append(tmp2)
            #---find superframe parameter----
            tmp=self.fra['4']
            idx=[]
            ii=0
            for row in tmp: #Find out all the records
                if row[0] == param: idx.append(ii)
                ii +=1

            if len(idx)>0:  #Find a record
                superframeNo=tmp[ idx[0] ][3] #Take the value in the first record found
                for ii in idx:
                    tmp2=[ #superframe Single parameter record
                        tmp[ii][1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit words. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                        tmp[ii][2],   #period, In the cycle, every few frames appear once
                        tmp[ii][3],   #superframe no, Corresponding to the Superframe No
                        tmp[ii][4],   #Frame,  Located in the first few Frames (by superframe counter, find Frame with number 1)
                        tmp[ii][5],   #bitOut, In 12bit, several bits start
                        tmp[ii][6],   #bitLen, A total of several bits
                        tmp[ii][7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits
                        tmp[ii][10],  #resolution, Unused
                        ]
                    ret4.append(tmp2)
                tmp=self.fra['3']
                idx=[]
                ii=0
                for row in tmp: #Find out all the records
                    if row[0] == superframeNo: idx.append(ii)
                    ii +=1

                if len(idx)>0:  #Find the record, usually there must be records
                    for ii in idx:
                        tmp2=[ #superframe Global configuration
                            tmp[ii][0],   #superframe no
                            tmp[ii][1],   #subframe,Which subframe is located (1-4)
                            tmp[ii][2],   #word, In Subframe, several Word (SYNC WORD number is 1)
                            tmp[ii][3],   #bitOut, In 12bit, several bits start (usually = 12)
                            tmp[ii][4],   #bitLen, A total of several bits (usually = 12)
                            tmp[ii][5],   #superframe couter 1/2, Corresponding to the number of counters in the total configuration of Frame
                            ]
                        ret3.append(tmp2)

        return { '1':
                [  #Frame Total configuration, up to two records (indicating two counters)
                    self.fra['1'][1][1],  #Word/Sec, The number per second, the word/subframe
                    self.fra['1'][1][2],  #sync length, Synchronous word length (bits = 12,24,36)
                    self.fra['1'][1][3],  #sync1, Synchronous word, first 12bits
                    self.fra['1'][1][4],  #sync2
                    self.fra['1'][1][5],  #sync3
                    self.fra['1'][1][6],  #sync4
                    self.fra['1'][1][7],  #subframe, [superframe counter],Every frame is available, these 4 items are the position of the counter
                    self.fra['1'][1][8],  #word,     [superframe counter]
                    self.fra['1'][1][9],  #bitOut,   [superframe counter]
                    self.fra['1'][1][10], #bitLen,   [superframe counter]
                    self.fra['1'][1][11], #Value in 1st frame (0/1), The value of the number of the number 1, the value of the counter (the minimum value of the counter)
                    ],
                 '2':ret2,
                 '3':ret3,
                 '4':ret4,
                }

    # def getAIR(self):
    #     '''
    #     Get the configuration of the decoding library corresponding to the tail number.
    #     Pick out useful, sort it out, return
    #        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
    #     '''
    #     reg=self.getREG().upper()
    #     self.readAIR()
    #     idx=0
    #     for row in self.air: #Find a machine tail number
    #         if row[0]==reg: break
    #         idx +=1
    #     if idx<len(self.air):  #Find a record
    #         return [self.air[idx][12], #dataver
    #                 self.air[idx][13], #dataver2
    #                 self.air[idx][16], #recorderType
    #                 self.air[idx][17]] #recorderType2
    #     else:
    #         return [0,0,'','']  #did not find

    # def readAIR(self):
    #     'Read AIR configuration'
    #     if self.air is None:
    #         self.air=AIR.air(conf.aircraft)

    def getREG(self):
        '''
        From the DAT file name, find the tail number of the machine
        Author: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com
        '''
        basename=os.path.basename(self.qar_filename)
        reg=basename.strip().split('-',1)
        if len(reg[0]) > 0:
            return reg[0]
        else:
            return ''
    def paramlist(self):
        '''
        Get all the records of all record parameters, including Regular and Superframe parameters
        '''
        #---regular parameter
        regular_list=[]
        for vv in self.fra['2']:
            regular_list.append(vv[0])
        #---superframe parameter
        super_list=[]
        for vv in self.fra['4']:
            super_list.append(vv[0])
        return regular_list,super_list
    def dataVer(self, acReg):
        '''
        Get the dataver of the current file
        '''
        #list of registrations for each registration number
        #create a list of registrations for each registration number

        dataver5471 = ['N2002J']
        dataver5461 = ['N703JB']
        if acReg in dataver5471:
            return '5471'
        elif acReg in dataver5461:
            return '5461'

        return ''
    def close(self):
        'Clear all configuration and data reserved'
        # self.air=None
        self.fra=None
        self.fra_dataver=-1
        self.par=None
        self.par_dataver=-1
        self.qar=None
        self.qar_filename=''



def usage():
    print()
    print(u'Read the QAR/DAR file and decode a parameter according to the parameter coding rules.')
    print(u'Usage:')

    print('   import Get_param_from_arinc717_aligned as A717')
    print('   qar_file="xxxxxxxxx.DAT"')
    print('   myQAR=A717.ARINC717(qar_file)               #Create examples and open a file')
    print('   regularlist,superlist=myQAR.paramlist()     #List all conventional parameters and superframe parameters, names')
    print('   fra=myQAR.getFRA("ACID1")      #FRA configuration of the parameter')
    print('   par=myQAR.getFRA("ACID1")      #Par configuration of the parameter')
    print('   dataver=myQAR.dataVer()       #Dataver of the file that has been opened')
    print('   myQAR.get_param("ACID1")       #Decoding a parameter')
    print('   myQAR.close()                 #closure')
    print('   myQAR.qar_file(qar_file)      #Open a file again')
    print(u'\nAuthor: Southern Airlines, llgz@csair.com - Modified by Chuck Cook ccook@jetblue.com  Modified by Chuck Cook ccook@jetblue.com')
    print()
    return

if __name__=='__main__':
    # usage()
    FPATH='/workspaces/FlightDataDecode/DataFrames/'
    myQAR=ARINC717(FPATH, 'N2002J-REC25038.DAT')
    #reg = myQAR.getREG()
    # print(myQAR.get_param('ACID3'))
    # myQAR.close()
    exit()
