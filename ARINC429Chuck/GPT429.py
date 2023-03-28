def decode_arinc429(data):
    # Extract label, SDI, data, and SSM from the 32-bit ARINC 429 word
    label = data & 0xFF
    sdi = (data >> 8) & 0x3
    arinc_data = (data >> 10) & 0xFFFF
    ssm = (data >> 26) & 0x3
    parity = (data >> 28) & 0x1
    sign_status = (data >> 29) & 0x1

    return {
        'Label': label,
        'SDI': sdi,
        'Data': arinc_data,
        'SSM': ssm,
        'Parity': parity,
        'SignStatus': sign_status
    }


def main():
    # Example ARINC 429 data word (32 bits)
    arinc429_word = 0b11111111000011110000000000000000
    #arinc429_word = 0xff0f0000

    decoded_data = decode_arinc429(arinc429_word)
    print("Decoded ARINC 429 data:")
    for key, value in decoded_data.items():
        print(f"{key}: {value}")

if __name__ == '__main__':
    main()
