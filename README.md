# Flight Data Decode

[FOQA (Flight Operations Quality AsURANCE)]

This project can be used completely. However, the program is not perfect, and individual conditions/logic is not implemented (notes). Read the parameter coding rules (configuration files), and write the database after being sorted. Do not solve multiple parameters at the same time.

This is the test program I wrote in the process of understanding wireless QAR (wqar) the original raw.dat file. ** can currently decode all record parameters. **
These test programs are in [WGL directory] (https://github.com/osnosn/flightdatadecode/tree/main/wgl). They all have detailed annotations. Convenient for you to learn/understand.

** If you want to use it directly, please use the code after finishing. **
The final code after finishing is placed in other directory. 【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】, Note has also been sorted.

### renew  
* [wgl directory] (https://github.com/osnosn/flightdatadecode/tree/main/wgl), test program. For details, look at [Readme] (https://github.com/osNOSN/flightDataDecode/blob/main/wgl/readme.md)
  2022-02 Last update
  -The record format of Arinc 573/717
    -`Get_param_from_wgl.py` can correctly obtain all record parameters. Including Regular, Superframe parameters.
    -Code parameters can be stored as CSV files.
    -The can handle 7: BCD, BNR Linear, BNR Segments, Character, Discrete, Packed Bits, UTC type, and convert it to use value.
    -At the corresponding seconds when returning the parameter (starting from 0).
    -Base will decode all the record values ​​according to the Rate value. For example: VRTG is 8 records per second.
    -The record parameters in the record parameters are `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY`. (Some decoding libraries will lack certain parameters). You can use these parameters to modify the Frame Time.
  -The record format for Arinc 767
    -In the beginning and end of each frame. Find the format of the frame head, and the format of the frame.
* [Arinc717 Directory] (https://github.com/osnosn/flightdatadecode/tree/main/arinc717), program after WGL. For more updates, read the readme in the [ArIinc717 directory] (https://github.com/osnosn/flightdatadecode/blob/arinc717/readme.md)
  * Completion of finishing. 2022-02
  * It is expected that it will not be updated in the future. 2022-02
* [Arinc767 Directory] (https://github.com/osnosn/flightdatadecode/blob/main/wgl/readme.md). For more updates, read the readme in [ArIinc767] (https://github.com/osnosn/flightdatadecode/blob/arinc767/Readme.md)
  * ~~ After the test program is completed, sort it out. 2022-02 ~~
  * The format is not complicated, and the XML definition file should be packaged with the original record file. Unfortunately, XML was removed in the original record file I got. So this program no longer continues to write. 2022-02

### other  
* I think this project is helpful to you, please click on the stars, leave a saying, or send me an email to me, and make me happy.
  If you think this project is helpful to you, click a Star, or Leave a message, or see me an email to make me happy.