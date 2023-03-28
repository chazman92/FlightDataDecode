import struct
import sys
import argparse
#usage python qar_arinc429_reader.py my_qar_file.qar
 
def read_arinc_words(qar_file):
    with open(qar_file, 'rb') as file:
        while True:
            word_data = file.read(4)
            if not word_data:
                break

            word = struct.unpack('>I', word_data)[0]
            yield word

def main():
    #parser = argparse.ArgumentParser(description='Read ARINC 429 words from an Airbus QAR file.')
    #parser.add_argument('qar_file', metavar='QAR_FILE', help='The QAR file to read from.')
    #args = parser.parse_args()

    #Hardcode File Path
    qar_file_path = 'ARINC429Chuck/DataFrames/N2002J-REC25038.DAT'

    #for arinc_word in read_arinc_words(args.qar_file): #commented out args file path line
    for arinc_word in read_arinc_words(qar_file_path):
        print(hex(arinc_word), bin(arinc_word))

if __name__ == '__main__':
    main()
