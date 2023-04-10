# Arinc717 Directory

### renew   
* Completion of finishing. 2022-02
* The routine used is `test_myqar.py`.
* It is expected that it will not be updated in the future. 2022-02



### illustrate   
** The program for this directory is a file used to decode Arinc 717 Aligned format. **
ArinC 717 Aligned file is organized from the Arinc 717 file. Main two things,
* Find 12 bits word and save it to 16 bits (2 bytes). The 4 BITS that can be made up at a high level can set some states as needed. For example, the current frame is supplemented.
* According to the synchronous word, if the source file has a deficient frame/leakage frame, use an empty frame to make up. In order to decod, the parameter position can be directly calculated without scanning files.


All python3 libraries used in Python3
  * `Import CSV`
  * `From IO Import Stringio`
  * `Import gzip`
  * `Import OS, Sys, Getopt`
  * `Import Zipfile`


When writing, Python-3.9.2 is used. Import package is a built-in or built-in package of Python-3.9.2.
Test OK in python-3.6.8.
Theoretically, all Python-3.x can run.

These programs require configuration files in the VEC directory. (Model coding specifications, or parameter coding rules)
For the source of the configuration file, please see the readme in the [VEC directory] (https://github.com/osnosn/flightAdatadecode/min/arinc717/vec).

The PY script in this directory can run as the command line program.
Running directly will help.
`` `
$ ./Test_myqar.py -h
Usage:
   Command line tool.
 Read the raw.dat in WGL, and decode a parameter according to the parameter coding rules.
./Test_myqar.py [-h |-Help]
   * (Necessary parameters)
   -H, -Help proprint usage.
 * -F, --file xxx.wgl.zip ".... wgl.zip" filename
 * -P, -Param Alt_Std Show "Alt_Std" Param. Automatic all capital.
   -Paramlist list all paras name.
   -W xxx.csv parameter write file "xxx.csv"
   -W xxx.csv.gz parameter write the file "xxx.csv.gz"
`` `

### other  
* I think this project is helpful to you, please click on the stars, leave a saying, or send me an email to me, and make me happy.
  If you think this project is helpful to you, click a Star, or Leave a message, or see me an email to make me happy.


