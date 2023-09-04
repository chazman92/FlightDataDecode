import Get_param_from_arinc717_aligned_717Chuck as A717

def main():
    myDAR=A717.ARINC717(FPATH, FNAME)
    #param = getOriginDestination(myDAR)
    #param = getAircraftID(myDAR)
    #param = getPresentPosition(myDAR)
    #param = getFlightID(myDAR)
    param = getParameter(myDAR, "MACH")
    print (param)
    #print(param[0], param[len(param)-1])

def getParameter(myDAR, param):
    Param = myDAR.get_param(param)
    return  Param

def getFlightID(myDAR,):
    FLINUM1 = myDAR.get_param('FLINUM1')
    FLINUM2 = myDAR.get_param('FLINUM2')
    FLINUM3 = myDAR.get_param('FLINUM3')
    FLINUM4 = myDAR.get_param('FLINUM4')
    return FLINUM1[0]["v"][::-1] + FLINUM2[0]["v"][::-1] + FLINUM3[0]["v"][::-1] + FLINUM4[0]["v"][::-1]

def getPresentPosition(myDAR,):
    LATP = myDAR.get_param('LATP')
    LONP = myDAR.get_param('LONP')

    return str(LATP[0]["v"]) + " " + str(LONP[0]["v"])

def getAircraftID(myDAR,):
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
    FPATH='/home/vscode/FlightDataDecode_Chuck/DataFrames/'
    #FNAME='N703JB-REC25134.DAT' #DAT Filename
    #FNAME='N2002J-REC25038.DAT'
    FNAME='N988JT_Sept3_LAXJFK/N988JT_20230904_065837.vdr'
    #FNAME='N639JB-DAR_REC23868.DAT'
    #FNAME='N805JB-QAR_REC00159.DAT'
    main()