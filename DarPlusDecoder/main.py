import os,sys
import darPlusDecoder_Chuck as DARPLUS

IcdTable = DARPLUS.ICD()

def main():
    myDarPlus = DARPLUS.darPlusDecoder(FPATH+FNAME)
    myDarPlus.read_darplus()

def LoadICD(FileName):
    ErrorCode = IcdTable.Load(FileDir=FileName)


def ForgetICD():
    IcdTable.Invalidate()

if __name__=='__main__':

    FPATH='/workspaces/FlightDataDecode/DataFrames/'
    FNAME='N737AID_20220907_082446.darplus' #DAT Filename

    if os.path.isfile(FPATH+FNAME)==False:
            print(FNAME,'Not a file')
            exit()

    main()