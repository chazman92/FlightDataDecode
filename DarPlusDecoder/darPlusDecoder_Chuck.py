from datetime import datetime
import csv


class darPlusDecoder:  

    def __init__(self, filepath, filename):
        self.full_filename = filepath + filename
        self.data = self.loadfile()
        self.tailnumber = self.Split_Tailnumber_From_Filename(filename)
        self.darplus_results = []
        #self.icd = self.loadicd()
    
    def Split_Tailnumber_From_Filename(self, filename):
     parts = filename.split('_')
     return parts[0]
    
    #load darPlus File
    def loadfile(self):
        with open(self.full_filename, 'r') as f:
            data = f.readlines()
        return data

    #load ICD File
    def loadicd(self):
        icd = ICD()
        icdPath = '/workspaces/FlightDataDecode/DarPlusDecoder/ICD_Chuck.icd'
        icd.Load(FileDir= icdPath)
        return icd
    
    #decode darPlus File
    def read_darplus(self):
        for line in self.data:
            strip_line=line.strip('\r\n //')
            split_line = strip_line.split(',')
            if split_line[0] == 'timestamp':
                continue
            if split_line[1] == '9': #lineid 9
                if split_line[2] == '205': #429 label 205
                    result = self.decode_label_205(split_line)
                    self.darplus_results.append(result)
                continue
            # if split_line[2] == '111':
            #     result = self.decode_label_110(split_line)
            # if split_line[2] == '120':
            #     continue
            # if split_line[2] == '121':
            #     continue
 
    #convert Unix Epoch to UTC
    def convert_epoch_to_utc(self, epoch):
        epoch_time_in_seconds = epoch / 1000.0
        return datetime.utcfromtimestamp(epoch_time_in_seconds).strftime('%Y-%m-%d %H:%M:%S')
    
    #decode label 205 lineid 9
    def decode_label_205(self, payload):
        binary_range = 65536
        engineering_range = 4.096
        #hex_string = payload[5]
        #truncated_hex = hex_string[1:-1] #in 429 example only bits 28-13 are used representing the middle hex number
        #int_number = int(truncated_hex, 16)
        extracted_decimal = self.extract_429_bits_from_hex(payload[5], 13, 28)
        mach = extracted_decimal * (engineering_range / binary_range)
        return {
                    'tailnumber':self.tailnumber,
                    'time' :self.convert_epoch_to_utc(int(payload[0])),
                    'label':'Mach',
                    'data': round(mach, 4)
                    }
    

    def extract_429_bits_from_hex(self, hex_num, start_bit, end_bit):
        # Step 1: Convert hex to binary
        bin_num = bin(int(hex_num, 16))[2:]
        padded_bin_num = bin_num.zfill(24)

        # Step 2: Extract specific bits
        extracted_bits = padded_bin_num[-(end_bit-9):-(start_bit-9)] # -9 because we are only using the middle 16 bits of the 24 bit hex number

        # Step 3: Convert the extracted bits back to decimal
        decimal_result = int(extracted_bits, 2)
            
        return decimal_result

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

class Frame:

    _SSM_Table=("Failure Warning",
                "Functional Test",
                "Not Computed Data",
                "Normal Operation")

    _LogicalFrame : dict = {}
    _BinaryWord   : str

    def _CheckIntegrity(self,
                       Frame) -> int:
        oneCount : int = 0
        if len(Frame) != 32:
            return 1
        for bit in Frame:
            if (bit != '0' and bit != '1'):
                return 2
            if (bit == '1'):
                oneCount +=1
        if oneCount % 2 == 0:
            return 3
        return 0

    def Decode(self,
               Frame,
               ICD = None,
               Channel : str = "") -> Exception:
        Label  : str
        Fields : list
        self._LogicalFrame.clear()
        FirstCheck = self._CheckIntegrity(Frame)
        if FirstCheck != 0:
            self._LogicalFrame = {}
            return Exception(FirstCheck)
        Tmpstr=Frame[24:32]
        Label = oct(int(Tmpstr[::-1],2))
        self._LogicalFrame["LABEL"]=Label
        SSM = Frame[1:3]
        self._LogicalFrame["SSM"]=self._SSM_Table[int(SSM,2)]
        SDI = Frame[22:24]
        self._LogicalFrame["SDI"]=SDI
        PAYLOAD=Frame[3:22]
        self._LogicalFrame["PAYLOAD"]=PAYLOAD
        if (ICD == None):
            return Exception(0)
        if not ICD.Valid:
            return Exception(0)
        if Channel not in ICD._ChannelList:
            return Exception(6)
        Key = Channel + ';' + Label[2::]
        if not ICD.FindKey(Key):
            return Exception(7)
        Fields = ICD._Content[Key]
        if Fields[0].SDI[0:2] == 'XX':
            self._AttachSDI()
        FieldDict = self._ParsePayload(Fields)
        self._LogicalFrame.update(FieldDict)
        return Exception(0)

    def GetLogicalData(self) -> dict:
        return self._LogicalFrame

    def _AttachSDI(self):
        self._LogicalFrame["PAYLOAD"] += self._LogicalFrame["SDI"]
        self._LogicalFrame["SDI"] = "Extended label"

    def _ParsePayload(self,
                      DataFields : list) -> dict:
        FieldDict = dict()
        for field in DataFields:
            if field.Encoding == "BNR":
                FieldDict[field.Name] = self._DecodeBNR(MSB      = field.MSB,
                                                        LSB      = field.LSB,
                                                        DataType = field.Type,
                                                        Resolution = field.Resolution)
            elif field.Encoding == "ENUM":
                FieldDict[field.Name] = self._DecodeENUM(MSB      = field.MSB,
                                                         LSB      = field.LSB,
                                                         EnumVal  = field.Type)
        return FieldDict

    def _DecodeBNR(self,
                   MSB : int,
                   LSB : int,
                   DataType : str,
                   Resolution : float = 0.0) -> str:
        payload     : str = self._LogicalFrame["PAYLOAD"]
        RightBound  = 32 - MSB - 3
        LeftBound   = 32 - LSB - 3 + 1
        LogicalData : str = ""
        if DataType == "INT": #signed integer 2's complement
            SignBitVal  = -int(payload[RightBound])*pow(2,(len(payload)-1))
            OtherBits   = int(payload[RightBound+1:LeftBound],base = 2)
            LogicalData = SignBitVal + OtherBits
        elif DataType == "UINT": #unsigned integer
            LogicalData = int(payload[RightBound:LeftBound],base = 2)
        elif DataType == "FLOAT": #floating point signed number
            SignBitVal  = -int(payload[RightBound])*pow(2,(len(payload)-1))
            OtherBits   = int(payload[RightBound+1:LeftBound],base = 2)
            LogicalData = SignBitVal + OtherBits
            LogicalData = LogicalData * Resolution
        else:
            pass
        return str(LogicalData)

    def _DecodeENUM(self,
                    MSB : int,
                    LSB : int,
                    EnumVal : str) -> str:
        payload     : str = self._LogicalFrame["PAYLOAD"]
        RightBound  = 32 - MSB - 3
        LeftBound   = 32 - LSB - 3 + 1
        LogicalData : str = ""
        EnumList = EnumVal.split(sep=',')
        Selector = int(payload[RightBound:LeftBound],base = 2)
        if Selector > len(EnumList):
            return "ENUM OUT OF BOUND"
        LogicalData = EnumList[Selector]
        return LogicalData

class ICD:
    #<timestamp>,<line id>,<label>,<subframe>,<word>,<value><LF>
    class DataField:
        Name       : str
        LineId   : str
        Label        : int
        Subframe        : int
        Word        : str

        def __init__(self,
                     Name,
                     Encoding,
                     MSB,
                     LSB,
                     SDI,
                     Type,
                     Resolution = 0) -> None:
            self.Name       = Name
            self.Encoding   = Encoding
            self.MSB        = MSB
            self.LSB        = LSB
            self.SDI        = SDI
            self.Type       = Type
            self.Resolution = Resolution

    _LineIdList  = [1,2,3,4,5,6]
    _Content      = {}
    Valid  : bool = False

    def __init__(self) -> None:
        pass

    def GetLineIdList(self) -> list:
        return self._LineIdList
#
    def Load(self,
             FileDir : str) -> Exception:
        TmpLine = [str]
        self.Valid   = False
        try:
            ICDfile=open(FileDir)
        except:
            return Exception(4)

        for line in ICDfile:
            if line[0] == '#':
                continue
            TmpLine=str.split(line,sep=';')
            if len(TmpLine) <= 1:
                return Exception(5)
            LineId = TmpLine[1]
            Label   = TmpLine[2]
            Key     = LineId + ';' + Label
            if LineId not in self._LineIdList:
                self._ChannelList.append(LineId)
            if TmpLine[7] == "":
                TmpLine[7] = 0.0
            TmpField = self.DataField(Name       = TmpLine[0],
                                      Encoding   = TmpLine[3],
                                      MSB        = int(TmpLine[4]),
                                      LSB        = int(TmpLine[5]),
                                      Type       = TmpLine[6],
                                      SDI        = TmpLine[8],
                                      Resolution = float(TmpLine[7]))
            if Key not in self._Content:
                self._Content[Key] = list()
            self._Content[Key].append(TmpField)
        ICDfile.close()
        self._ChannelList.sort()
        self.Valid = True
        return Exception(0)

    def FindKey(self,
                Key : str = "") -> bool:
        if Key in self._Content:
            return True
        else:
            return False

    def ExtractKey(self,
                   Key : str) -> list:
        return self._Content[Key]

    def Invalidate(self):
        self.Valid = False
        self._ChannelList.clear()
        self._Content.clear()

class Exception:
    title   : str
    message : str
    Code    : int

    def __init__(self,Code : int = 0) -> None:
        self.Code = Code
        if   Code == 0:
            self.title   = "No errors"
            self.message = "Execution exited normally"
        elif Code == 1:
            self.title   = "ARINC Frame"
            self.message = "ARINC Frame is not 32 bits long"
        elif Code == 2:
            self.title   = "ARINC Frame"
            self.message = "ARINC Frame is not binary"
        elif Code == 3:
            self.title   = "ARINC Frame"
            self.message = "ARINC Frame must have odd parity"
        elif Code == 4:
            self.title   = "ICD file"
            self.message = "Unable to open ICD file"
        elif Code == 5:
            self.title   = "ICD file"
            self.message = "Invalid ICD file"
        elif Code == 6:
            self.title   = "ARINC Channel"
            self.message = "Provided invalid ARINC Channel"
        elif Code == 7:
            self.title   = "ARINC label"
            self.message = "ARINC label not found in ICD"
        else:
            self.title   = "Unknown exception"
            self.message = "Unknown exception"
        if   Code != 0:
            self.message += "\nError code: " + str(Code)

# if __name__ == "__main__":
#     print("ARINC429 library by RossWorks.")
#     print("Please refer to documentation to learn how to use this library")