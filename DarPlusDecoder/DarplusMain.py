import os,sys
import darPlusDecoder_Chuck as DARPLUS

def main():
    myDarPlus = DARPLUS.darPlusDecoder(FPATH, FNAME, FRAMEPATH)
    myDarPlus.decode_darplus429_lineid_label("3", "271")
    #myDarPlus.decode_darplus429()
    #myDarPlus.decode_darplus()
    myDarPlus.write_dict_to_csv(myDarPlus.darplus_results, 'results.csv')

if __name__=='__main__':
    FRAMEPATH='/home/vscode/FlightDataDecode_Chuck/DataFrames/'
    FPATH='/home/vscode/FlightDataDecode_Chuck/DataFrames/'
    FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_065835.darplus' #Beginning of Flight
    #FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_113416.darplus' #Middle of Flight
    #FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_091632.darplus' #End of Flight
    #FNAME='N988JT_20230705_015843.darplus'

    if os.path.isfile(FPATH+FNAME)==False:
            print(FNAME,'Not a file')
            exit()

    main()