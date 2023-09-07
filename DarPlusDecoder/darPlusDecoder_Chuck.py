from datetime import datetime
import csv
import json
import re

class darPlusDecoder:  

    def __init__(self, filepath, filename, framepath):
        self.full_filename = filepath + filename
        self.darplus_parameters = self.GetParametersJson()
        #self.dataversion = self.GetDataVer(self.Split_acReg_From_Filename(filename))
        self.data = self.load_darplus_file()
        self.acReg = self.Split_acReg_From_Filename(filename)
        self.darplus_results = []

    def GetParametersJson(self):
        # Read JSON data from file
        with open('FlightDataDecode_Chuck/DarPlusDecoder/darplus_parameters.json', 'r') as f:
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

    def decode_darplus429_lineid_label(self, darplus_lineid, darplus_label):
        for line in self.data:
            strip_line=line.strip('\r\n //')
            split_line = strip_line.split(',')

            if darplus_lineid == split_line[1] and darplus_label == split_line[2]:
                epoch_time = split_line[0]
                darplus_word = int(split_line[5],16) #convert hex to decimal for bitwise operations  
                darplus_word_string = split_line[5]  
                # if darplus_word_string == '1ABECE':
                #     print('1ABECE')

                darplus_parameters = self.get_parameters_lineid_label(darplus_lineid, darplus_label)
                if darplus_parameters is not None:
                    for param in darplus_parameters:
                       # if param['TYPE'] == 'DISCREET':
                            result = self.darplus429_decode(darplus_word, param)

                            export = self.export_darplus_results(int(epoch_time),param['NAME'], result)
                            export.update({'extra': darplus_word_string}) #Debugging

                            self.darplus_results.append(export)      
    def decode_darplus429(self):
        for line in self.data:
            strip_line=line.strip('\r\n //')
            split_line = strip_line.split(',')

            epoch_time = split_line[0]
            if epoch_time == 'timestamp':
                continue
            darplus_lineid = split_line[1]
            darplus_429label = split_line[2]
            darplus_A717label = split_line[4]
            darplus_word = int(split_line[5],16) #convert hex to decimal for bitwise operations  
            darplus_word_string = split_line[5]  
            # if darplus_word_string == '1ABECE':
            #     print('1ABECE')
            if darplus_429label is not '':
                darplus_parameters = self.get_parameters_lineid_label(darplus_lineid, darplus_429label)
                if darplus_parameters is not None:
                    for param in darplus_parameters:
                        result = self.darplus429_decode(darplus_word, param)

                        export = self.export_darplus_results(int(epoch_time),param['NAME'], result)
                        export.update({'extra': darplus_word_string}) #Debugging

                        self.darplus_results.append(export)     
             
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
                if darplus_lineid == "1": 
                        if darplus_parameter == "DTG": #429 label 1
                            #result = self.decode_label_205(split_line)
                            par_set = {}
                            par_set['type'] = "BCD"
                            par_set['signBit'] = 0
                            par_set['part'] = []
                            par_set['pos'] = 21
                            par_set['blen'] = 19
                            par_set['Resol'] = 0.1
                            Testresult = self.arinc429_BCD_decode(darplus_word, par_set)
                            self.darplus_results.append(self.export_darplus_results(int(epoch_time), Testresult, darplus_parameter)) 
                        if darplus_parameter == "APP_TYPE": #429 label 271
                            #result = self.decode_label_205(split_line)
                            par_set = {}
                            par_set['type'] = "BCD"
                            par_set['signBit'] = 0
                            par_set['part'] = []
                            par_set['pos'] = 21
                            par_set['blen'] = 19
                            par_set['Resol'] = 0.1
                            Testresult = self.arinc429_BCD_decode(darplus_word, par_set)
                            self.darplus_results.append(self.export_darplus_results(int(epoch_time), Testresult, darplus_parameter))               
                elif darplus_lineid == '8': #lineid 8
                    if darplus_parameter == "APU_EGT": #429 label 175
                        par_set = self.icd.getPAR(darplus_parameter)
                        par_set['pos'] -= 8 #subtract 8 because darplus payload does not include label bits
                        result = self.arinc429_BNR_decode(darplus_word , par_set)
                        self.darplus_results.append(self.export_darplus_results(int(epoch_time), result, darplus_parameter))
                    if darplus_parameter == "SDAC": #429 label 2
                        par_set = self.icd.getPAR(darplus_parameter)
                        par_set['pos'] -= 8 #subtract 8 because darplus payload does not include label bits
                        result = self.arinc429_BNR_decode(darplus_word , par_set)
                        self.darplus_results.append(self.export_darplus_results(int(epoch_time), result, darplus_parameter))
   
    def export_darplus_results(self, epoch_time, darplus_parameter, darplus_result):
        return {
                    'tailnumber':self.acReg,
                    'time' :self.convert_epoch_to_utc(epoch_time),
                    'label':darplus_parameter,
                    'data': darplus_result
                    }
    def get_parameters_lineid_label(self, darplus_lineid, darplus_label):
        # Try to retrieve the label number
        #if lineid == '1' and darplus_429label == "1":
         #    print('lineid 18')
        if darplus_label is not '':
            try:
                parameters = self.darplus_parameters['LineId'][darplus_lineid]['Label'][darplus_label]['Parameter']
                return parameters

            except KeyError as e:
                return None
                print(f"KeyError: The key {e} does not exist.")

            except json.JSONDecodeError:
                print("JSONDecodeError: Invalid JSON format.")

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            return None

    def get_label_from_lineid(self, lineid, darplus_429label, darplus_A717label):
        # Try to retrieve the label number
        #if lineid == '1' and darplus_429label == "1":
         #    print('lineid 18')
        if darplus_429label is not '':
            try:
                labels = self.darplus_labels['DataFrame'][self.dataversion]['LineId'][lineid][0]['Frame']
                # Loop through the keys and values to find the desired value
                for key, value in labels.items():
                    if value == darplus_429label:
                        return key
            except KeyError:
                return None
        elif darplus_A717label is not '':
            try:
                labels = self.darplus_labels['DataFrame'][self.dataversion]['LineId'][lineid][0]['Frame']
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
        value = ( word >> ((conf['pos']) - conf['blen']) ) & bits # darplus payload does not include label, so subtracting 8 bits from position 

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
                value *= float(conf['Resol'][6:])  #trims text off resoltion in PAR file
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
    def darplus429_decode(self, darplus_word, parameter):
        #According to Blen, obtain the mask value
        #It shifts the binary 1 to the left by blen bits and then subtracts 1 to create a mask of 1s of blen length.
        bitmask = (1 << parameter['BLEN']) -1
        #Move the value to the right (move to BIT0) and get the value
        #It performs a right shift to move the specified section to the least significant bit positions and then uses bitwise AND with the bitmask (bits) to isolate the desired section.
        #Using bitwise AND with a mask is a common technique for isolating specific bits in a binary number. The reason it works is due to the properties of the AND operation:
        #value = ( darplus_word >> ((parameter['MSB']-8) - parameter['BLEN']) ) & bitmask # darplus payload does not include label, so subtracting 8 bits from position 
        value = (darplus_word >> (parameter['LSB'] - 9)) & bitmask #Second way to doing this using LSB vice MSB .. subtracting 9 because darplus payload does not include label bits
        # if value==1:
        #     print('value = 1')
        #Symbol
        #The two's complement is a standard way to represent negative integers in binary.
        if parameter['SIGNBIT']>0:  #This checks sign bit and uses two's complement
            bitmask = 1 << (parameter['SIGNBIT']-1)  #Bit bit number starts from 1, so -1
            #The bitwise AND (&) operation between word and bits checks whether the sign bit is set in the word. 
            #If the result is non-zero, that means the sign bit is set, indicating a negative number.
            if darplus_word & bitmask:
                #If the number is negative, you convert it to its two's complement representation by subtracting 2**conf['blen'] (which is equivalent to 1 << conf['blen']). 
                #The -= operator modifies value in-place.
                value -= 1 << parameter['BLEN']
        #Resolution
        if 'RESOL' in parameter:
                value *= float(parameter['RESOL'])

        if 'VALUE' in parameter:
            for key, description in parameter['VALUE'].items():
                if key == str(value):
                    return description
            
        return value
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