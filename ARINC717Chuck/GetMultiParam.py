import Get_param_from_arinc717_aligned_717Chuck as A717

def main():
    myDAR=A717.ARINC717(FPATH, FNAME)
    #param = getOriginDestination(myDAR)
    #param = getAircraftID(myDAR)
    param = getFlightDate(myDAR)
    print(param)

def getFlightDate(myDAR):
    DATE = myDAR.get_param('DATE')

    return  DATE

def getAircraftID(myDAR):
    ACID1 = myDAR.get_param('ACID1')
    ACID2 = myDAR.get_param('ACID2')
    ACID3 = myDAR.get_param('ACID3')
    return ACID1[0]["v"][::-1] + ACID2[0]["v"][::-1] + ACID3[0]["v"][::-1]

def getOriginDestination(myDAR):
    ORIGIN1 = myDAR.get_param('ORIGIN1')
    DEST_OR = myDAR.get_param('DEST_OR')
    DEST2 = myDAR.get_param('DEST2')
    return ORIGIN1[0]["v"][::-1] + DEST_OR[0]["v"][::-1] + DEST2[0]["v"][::-1]

if __name__=='__main__':
    FPATH='/workspaces/FlightDataDecode/DataFrames/'
    FNAME='N703JB-REC25134.DAT' #DAT Filename
    #FNAME='N2002J-REC25038.DAT'
    main()