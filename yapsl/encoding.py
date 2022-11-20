import binascii

# This code is heavily based on the following answer by John La Roovy:
# https://stackoverflow.com/a/2453027/916672

_gsm = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
        "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
_ext = ("````````````````````^```````````````````{}`````\\````````````[~]`"
        "|````````````````````````````````````€``````````````````````````")

def gsm_encode(plaintext):

    # encode
    res = ""
    for c in plaintext:
        idx = _gsm.find(c);
        if idx != -1:
            res += chr(idx)
            continue
        idx = _ext.find(c)
        if idx != -1:
            res += chr(27) + chr(idx)

    # pack 7 bit to bytes with 8 bits (quick and dirty)
    data = []
    prev = None
    for c in res:
        bits = bin(ord(c)).lstrip('0b')
        bits = '0' * (7 - len(bits)) + bits
        if prev is None:
            prev = bits
        else:
            # fill the left side of the previous N bits with the new bits
            n = 8 - len(prev)
            prev = bits[-n:] + prev
            bits = bits[:-n]
            if len(prev) == 8:
                # we have one full byte: store it
                data.append(prev)
                prev = bits
    if prev is not None and len(prev) > 0:
        # padding for the very last byte
        if len(prev) > 1:
            prev = '0' * (8 - len(prev)) + prev
        else:
            # if 7 bits of the last byte are empty, we have to fill in 0x0D (all zeros would result in @)
            prev = '0001101' + prev
        data.append(prev)
    res = ""

    # convert all bits in a nice hex-string
    for c in data:
        res += f'{int(c, 2):02X}'

    return res

