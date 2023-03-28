# WGL directory

### renew  
* 2022-02 The first update
  -`get_param_from_wgl.py` can finally extract a single record parameter (original value, not converted to use value).
* 2022-02 update again
  -`get_param_from_wgl.py` can obtain the values ​​of parts of the BNR, BCD, Character, and convert it to the use value.
  -The question: UTC type does not seem to be. The rate of the parameters is not processed.
* 2022-02 update again
  -The record format of Arinc 573/717
    -`Get_param_from_wgl.py` can correctly obtain all record parameters (except the super frame parameter). It can handle the values ​​of BNR, BCD, Character, and convert it to the use value.
    -Code parameters can be stored as CSV files.
    -At the corresponding seconds when returning the parameter (starting from 0).
    -Base will decode all the record values ​​according to the Rate value. For example: VRTG is 8 records per second.
    -The record parameters in the record parameters are `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY`. (Some decoding libraries will miss a certain parameter). You can use these parameters to modify the Frame Time.
    -The Question: There is no handling of the superframe. If the parameters are recorded in the super frame, the decoding will fail, or the contents of decoding are wrong.
  -The record format for Arinc 767
    -In the beginning and end of each frame. Find the format of the frame head, and the format of the frame.
* 2022-02 update again
  -The record format for ArinC 573/717: Increases the value of supporting Discrete, Packed Bits, UTC, and type. A total of 7: BCD, BNR Linear, BNR Segments, Character, Discrete, Packed Bits, UTC.
* 2022-02 update again
  -The record format for Arinc 573/717: You can decode all parameters, including regula, superframe parameters.



### illustrate
The PY program in this directory can be used. But it did not reach a complete usable state.
It is a program written in the process of understanding the original raw.dat file of wireless QAR (wqar).
** can currently decode all record parameters. **
If you are interested, please refer to it.

The organic code will be placed in other directory. 【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】   

------------
The PY script in this directory can run as the command line program.
Running directly will help.
`` `
$ ./Get_param_from_wgl.py
Usage:
   Command line tool.
 Read the raw.dat in WGL, and decode a parameter according to the parameter coding rules.
./Get_param_from_wgl.py [-h |-Help]
   * (Necessary parameters)
   -H, -Help proprint usage.
 * -F, --file xxx.wgl.zip ".... wgl.zip" filename
 * -P, -Param Alt_Std Show "Alt_Std" Param. Automatic all capital.
   -Paramlist list all paras name.
   -W xxx.csv parameter write file "xxx.csv"
   -W xxx.csv.gz parameter write the file "xxx.csv.gz"
`` `

There are two empty files in the WGL directory, just give an example to see the name of the file name in the compressed package.
  * `B-1234_20210121132255.wgl.zip`, this is ArinC 717 Aligned
  * `B-123420220102114550m.zip`, this is ArinC 767 format

The contents of these two files are the same.
  * `Get_param_from_arinc717_aligned.py`
  * `Get_param_from_wgl.py`

All python3 libraries used in Python3
  * `Import OS, Sys, Getopt`
  * `From dateTime Import Datetime`
  * `Import Zipfile`
  * `From IO Import bytesio`
  * `From IO Import Stringio`
  * `Import Pandas as PD` decoding, not used, read the AIR configuration file, dependence. Read other configuration files and use it.
  * `Import psutil` decoding, not used
  * `Import Struct` decoding, not used


The Python 3.9.2 version is used. pandas-1.3.4, numpy-1.21.4, PSUTIL-5.9.0, and other bags are Python-3.9.2 built-in or built-in bags.
Test OK in python-3.6.8. pandas-1.0.3, numpy-1.18.2, PSUTIL-5.8.0
Theoretically, all Python-3.x can run.

These programs require configuration files in the VEC directory. (Model coding specifications, or parameter coding rules)
For the source of the configuration file, please see the readme in the [VEC directory] (https://github.com/osnosn/flightAdatadecode/min/wgl/vec).