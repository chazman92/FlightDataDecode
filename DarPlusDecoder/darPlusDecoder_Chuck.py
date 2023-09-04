from datetime import datetime

import csv
import json
import re


class darPlusDecoder:  

    def __init__(self, filepath, filename, framepath):
        self.full_filename = filepath + filename
        self.darplus_labels = self.GetDataVerJson()
        self.dataversion = self.GetDataVer(self.Split_acReg_From_Filename(filename))
        self.data = self.load_darplus_file()
        self.acReg = self.Split_acReg_From_Filename(filename)
        self.darplus_results = []
        self.icd = self.loadicd(framepath)

    def GetDataVerJson(self):
        # Read JSON data from file
        with open('FlightDataDecode_Chuck/DarPlusDecoder/darplus_dataframes.json', 'r') as f:
            data = json.load(f)
        return data
    
    def GetDataVer(self, acReg):
        '''
        Get the dataver of the current file
        '''

        for frame_id, frame_data in self.darplus_labels['DataFrame'].items():
            if acReg in frame_data['aircraftReg']:
                return frame_id
        return ''   
    def Split_acReg_From_Filename(self, filename):
        pattern = r'N\d+[A-Z]*'
        match = re.search(pattern, filename)

        if match:
            aircraft_identifier = match.group()
            return aircraft_identifier
        else:
            print("No match found.")
            return ''
    
    #load darPlus File
    def load_darplus_file(self):
        with open(self.full_filename, 'r') as f:
            data = f.readlines()
        return data

    #load ICD File
    def loadicd(self, framepath):
        icd = ICD(framepath, self.dataversion)
        return icd
    
    #decode darPlus File
    def decode_darplus(self):
        for line in self.data:
            strip_line=line.strip('\r\n //')
            split_line = strip_line.split(',')

            epoch_time = split_line[0]
            darplus_lineid = split_line[1]
            darplus_429label = split_line[2]
            darplus_A717label = split_line[4]
            try:
                darplus_word = int(split_line[5],16) #convert hex to decimal for bitwise operations
            except ValueError:
                continue

            if epoch_time == 'timestamp':
                continue
            darplus_parameter = self.get_label_from_lineid(darplus_lineid, darplus_429label, darplus_A717label)
            if darplus_parameter is not None:
                if darplus_lineid == '9': #lineid 9
                    if darplus_parameter == "MACH": #429 label 205
                        result = self.decode_label_205(split_line)
                        self.darplus_results.append(self.export_darplus_results(int(epoch_time), result, darplus_parameter))
                    continue
                elif darplus_lineid == '18': #A717 Biphase
                        param_set = self.get_param_spec(darplus_parameter) #get the FRA file data for the parameter
                        par_set = self.icd.getPAR(darplus_parameter)
                        A429word = self.get_darplus_arinc429(param_set, darplus_word)
                        result = self.arinc429_BNR_decode(A429word, par_set)
                        self.darplus_results.append(self.export_darplus_results(int(epoch_time), result, darplus_parameter))

    def export_darplus_results(self, epoch_time, darplus_result, darplus_parameter):
        return {
                    'tailnumber':self.acReg,
                    'time' :self.convert_epoch_to_utc(epoch_time),
                    'label':darplus_parameter,
                    'data': round(darplus_result, 4)
                    }

    def decode_label_205(self, payload):
        binary_range = 65536
        engineering_range = 4.096
        #hex_string = payload[5]
        #truncated_hex = hex_string[1:-1] #in 429 example only bits 28-13 are used representing the middle hex number
        #int_number = int(truncated_hex, 16)
        extracted_decimal = self.extract_429_bits_from_hex(payload[5], 13, 28)
        mach = extracted_decimal * (engineering_range / binary_range)
        return mach

    def get_label_from_lineid(self, lineid, darplus_429label, darplus_A717label):
        # Try to retrieve the label number
        # if lineid == '18' and darplus_A717label == "206":
        #     print('lineid 18')
        if darplus_429label is not '':
            try:
                labels = self.darplus_labels['DataFrame'][self.dataversion]['LineId'][lineid][0]['Parameters'].keys()
                if len(labels) ==1 :
                    return list(labels)[0]
            except KeyError:
                return None
        elif darplus_A717label is not '':
            try:
                labels = self.darplus_labels['DataFrame'][self.dataversion]['LineId'][lineid][0]['Parameters']
                # Loop through the keys and values to find the desired value
                for key, value in labels.items():
                    if value == darplus_A717label:
                        return key
                
            except KeyError as e:
                print(f"KeyError: The key {e} does not exist.")

            except json.JSONDecodeError:
                print("JSONDecodeError: Invalid JSON format.")

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            except KeyError:
                return None
        else:
            return None



    def extract_429_bits_from_hex(self, hex_num, start_bit, end_bit):
        # Step 1: Convert hex to binary
        bin_num = bin(int(hex_num, 16))[2:]
        padded_bin_num = bin_num.zfill(24)

        # Step 2: Extract specific bits
        extracted_bits = padded_bin_num[-(end_bit-9):-(start_bit-9)] # -9 because we are only using the middle 16 bits of the 24 bit hex number

        # Step 3: Convert the extracted bits back to decimal
        decimal_result = int(extracted_bits, 2)
            
        return decimal_result
    def convert_epoch_to_utc(self, epoch):
        epoch_time_in_seconds = epoch / 1000.0
        return datetime.utcfromtimestamp(epoch_time_in_seconds).strftime('%Y-%m-%d %H:%M:%S')
    def write_dict_to_csv(self, data, file_name):
        # Automatically determine the field names (keys in the dictionaries)
        fields = data[0].keys() if data else []
        
        # Open the file in write mode
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            
            # Write the header
            writer.writeheader()
            
            # Write the data
            writer.writerows(data)

    def get_param_spec(self, parameter):
        fra = self.icd.getFRA(parameter)
        #par = self.icd.getPAR(parameter)
        if len(fra)<1:
            print('Empty dataVer.',flush=True)
            return []
        if len(fra['2'])<1 and len(fra['4'])<1:
            print('Parameter not found.',flush=True)
            return []

        if len(fra['2'])>0:
            param_set=self.getDataFrameSet(fra['2'], fra['1'][0])

        return param_set
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
        return p_set
    def get_darplus_arinc429(self, param_set, darplus_word):
        '''
        needs input param_set that includes all parts of the parameter
        '''
        #darplus_word = 0xE9 #testing hardcoded darplus word
        value=0
        pre_id=0
        for part_set in param_set:
            word = darplus_word #using the same darplus word to recompile all parts of A429
            #According to Blen, obtain the mask value
            bits= (1 << part_set['blen']) -1
            #According to BOUT, the mask is moved to the corresponding position
            bits <<= part_set['bout'] - part_set['blen']
            word &= bits  #Obtain
            #Move the value to the target location
            move=part_set['bin'] - part_set['bout']
            if move>0:
                word <<= move
            elif move<0:
                word >>= -1 * move
            value |= word
        return value
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
        #It shifts the binary 1 to the left by blen bits and then subtracts 1 to create a mask of 1s of blen length.
        bits= (1 << conf['blen']) -1
        #Move the value to the right (move to BIT0) and get the value
        #It performs a right shift to move the specified section to the least significant bit positions and then uses bitwise AND with the bitmask (bits) to isolate the desired section.
        #Using bitwise AND with a mask is a common technique for isolating specific bits in a binary number. The reason it works is due to the properties of the AND operation:
        value = ( word >> (conf['pos'] - conf['blen']) ) & bits

        #Symbol
        #The two's complement is a standard way to represent negative integers in binary.
        if conf['signBit']>0:  #This checks sign bit and uses two's complement
            bits = 1 << (conf['signBit']-1)  #Bit bit number starts from 1, so -1
            #The bitwise AND (&) operation between word and bits checks whether the sign bit is set in the word. 
            #If the result is non-zero, that means the sign bit is set, indicating a negative number.
            if word & bits:
                #If the number is negative, you convert it to its two's complement representation by subtracting 2**conf['blen'] (which is equivalent to 1 << conf['blen']). 
                #The -= operator modifies value in-place.
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

class ICD:

    def __init__(self,fpath, frame_version):
        self.datapath=fpath
        self.dataver=frame_version
        self.fra=None
        self.par=None
        if len(frame_version)>0:
            self.readFRA()
            self.readPAR()

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
    def readPAR(self):
        'Read PAR configuration'

        if self.par is None:
            self.par=self.read_parameter_file(self.datapath + self.dataver + '.par')
    def read_parameter_file(self, dataver):

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
                        par_conf.append(self.one_PAR(PAR_offset,one_par) )
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
            par_conf.append(self.one_PAR(PAR_offset,one_par) )

        return par_conf       #Return to list
    def one_PAR(self, PAR_offset,one_par):
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
    
    def readFRA(self):
        'Read FRA configuration'
        if self.fra is None:
            self.fra=self.read_frame_file(self.datapath + self.dataver +'.fra')
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
                    #// 4|0Superframe Parameter Name	1Part(1,2 or 3)	2Period Of	3Superframe No	4Frame	5Output Word (Bit Out)	6Output Word (Data Bits)	7Input Raw Data (Bit In)
                    tmp2=[ #superframe Single parameter record
                        tmp[ii][1],   #part(1,2,3),There will be multiple sets of records, corresponding to multiple 32bit words. The same group of up to 3 parts, 3 parts read out separately, write the same 32bit word.
                        tmp[ii][2],   #period of, In the cycle, every few frames appear once
                        tmp[ii][3],   #superframe no, Corresponding to the Superframe No
                        tmp[ii][4],   #Frame,  Located in the first few Frames (by superframe counter, find Frame with number 1)
                        tmp[ii][5],   #bitOut, In 12bit, several bits start
                        tmp[ii][6],   #bitLen, A total of several bits
                        tmp[ii][7],   #bitIn,  Write into ArinC429's 32bits Word, start with several bits
                        #tmp[ii][10],  #resolution, Unused
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
                        #// 3|0Superframe No	1Superframe Word Location (Subframe)	2Superframe Word Location (Word)	3Superframe Word Location (Bit Out)	4Superframe Word Location (Data Bits)
                        tmp2=[ #superframe Global configuration
                            tmp[ii][0],   #superframe no
                            tmp[ii][1],   #subframe,Which subframe is located (1-4)
                            tmp[ii][2],   #word, In Subframe, several Word (SYNC WORD number is 1)
                            tmp[ii][3],   #bitOut, In 12bit, several bits start (usually = 12)
                            tmp[ii][4],   #bitLen, A total of several bits (usually = 12)
                            #tmp[ii][5],   #superframe couter 1/2, Corresponding to the number of counters in the total configuration of Frame
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
                    self.fra['1'][1][11], #JETBLUE this is PEH duration #Value in 1st frame (0/1), The value of the number of the number 1, the value of the counter (the minimum value of the counter)
                    ],
                 '2':ret2,
                 '3':ret3,
                 '4':ret4,
                }
    def read_frame_file(self, dataver):
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

        return fra_conf       #Return to list