import os,sys
import darPlusDecoder_Chuck as DARPLUS

def main():
    myDarPlus = DARPLUS.darPlusDecoder(FPATH, FNAME, FRAMEPATH)
    myDarPlus.decode_darplus()
    myDarPlus.write_dict_to_csv(myDarPlus.darplus_results, 'results.csv')

if __name__=='__main__':
    FRAMEPATH='/home/vscode/FlightDataDecode_Chuck/DataFrames/'
    FPATH='/home/vscode/FlightDataDecode_Chuck/DataFrames/'
    FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_065835.darplus' #Darplus Filename
    #FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_113416.darplus' #End of Flight

    if os.path.isfile(FPATH+FNAME)==False:
            print(FNAME,'Not a file')
            exit()

    main()