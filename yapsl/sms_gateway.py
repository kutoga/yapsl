import os
import json
import alog
import binascii
import time
from enum import Enum
from .encoding import gsm_encode

class SmsType(Enum):
    DEFAULT = 0
    TYPE_0 = 64
    REPLACE_TYPE_1 = 65
    REPLACE_TYPE_2 = 66
    REPLACE_TYPE_3 = 67
    REPLACE_TYPE_4 = 68
    REPLACE_TYPE_5 = 69
    REPLACE_TYPE_6 = 70
    REPLACE_TYPE_7 = 71
    RETURN_CALL_MESSAGE = 95

class SmsGateway:
    MAX_SMS_LEN = 160

    def __init__(self, tty_dev, verbose=False):
        self._verbose = verbose
        self._tty_dev = tty_dev
        self._tty_r = open(self._tty_dev, 'r')
        self._tty_w = open(self._tty_dev, 'w')

    def auto_select_network(self):
        if self._verbose:
            alog.info('Change to text mode')
        self._write('AT+CMGF=1\r\n')
        self._expect_ok()
        if self._verbose:
            alog.info('Enable auto selection for networks')
        self._write('AT+COPS=0\r\n')
        self._expect_ok()

    def is_connected(self):
        if self._verbose:
            alog.info('Change to text mode')
        self._write('AT+CMGF=1\r\n')
        self._expect_ok()
        if self._verbose:
            alog.info('Query connection state')
        self._write('AT+CREG?\r\n')
        self._expect_empty_line()
        res = self._read_line()
        self._expect_ok()
        res_prefix = '+CREG: '
        if not res.startswith(res_prefix):
            raise Exception('Expected a line with the prefix "{res_prefix}", but got this line: {res}')
        n, stat = res[len(res_prefix):].split(',')
        n = int(n)
        stat = int(stat)
        registered_home_nw = 1
        registered_roaming = 5
        connected = stat == registered_home_nw or stat == registered_roaming
        if self._verbose:
            alog.info(f'Modem has a network connection: {connected}')
        return connected

    def is_pin_ready(self):
        if self._verbose:
            alog.info("Check if PIN is ready")
        self._write('AT+CPIN?\r\n')
        self._expect_empty_line()
        ready = self._read_line() == '+CPIN: READY'
        self._expect_ok()
        if self._verbose:
            alog.info(f'PIN is ready: {ready}')
        return ready

    def send(self, receiver, text='', type=SmsType.DEFAULT, flash=False, delivery_report=False):
        if len(text) > SmsGateway.MAX_SMS_LEN:
            raise Exception(f'The maximum length for a SMS is {SmsGateway.MAX_SMS_LEN}, but the given SMS has a length of {len(text)}!')
        if not self.is_pin_ready():
            raise Exception("A PIN is required! Note that this library does not support PIn authentication, so you have to do this before the library is used.")
        if not self.is_connected():
            raise Exception("Network connection is missing")
        # alog.info(f'receiver="{receiver}" text="{text}" type="{type}"')
        # More details are here: https://blog.compass-security.com/2018/10/substitutable-message-service/
        pdu_msg = ''.join([
            '00', # SMS service center nr is not included
            '21' if delivery_report else '01',
            '00', # reference nr: 00 means auto selection
            self._pdu_encode_phone_nr(receiver),
            f'{type.value:02X}',
            '10' if flash else '00', # 7 bit GSM encoding
            f'{len(text):02X}', # length of message
            gsm_encode(text), #'0CC8329BFD065DDF72363904'
            # binascii.hexlify(text.encode('utf8')).decode('utf8')
        ])
        self._send_pdu_cmd(pdu_msg)
        # while True:
        # self._read_line()

    def _pdu_encode_phone_nr(self, nr):
        is_international = nr.startswith('+')
        if is_international:
            nr = nr[1:]

        nr_len = len(nr)
        if len(nr) % 2 == 1:
            nr += 'F' # see: http://subnets.ru/saved/sms_pdu_format.html

        # swap "pairs" of characters. E.g.: 123456... => 214365...
        encoded_nr = ''.join(nr[i * 2:i * 2 + 2][::-1] for i in range(len(nr) // 2))

        return ''.join([
            f'{nr_len:02X}',
            '91' if is_international else '81',
            encoded_nr
        ])

    def _send_pdu_cmd(self, pdu_msg):
        if self._verbose:
            alog.info('Change to PDU mode')
        self._write(f'AT+CMGF=0\r\n')
        self._expect_ok()
        if self._verbose:
            alog.info('Send PDU message')
        self._write(f'AT+CMGS={(len(pdu_msg) - 1) // 2}\r')
        self._expect_empty_line()
        self._write(f'{pdu_msg}\x1a\n')
        self._expect_str('>', False)
        self._expect_empty_line()
        res = self._read_line()
        error_prefix = '+CMS ERROR: '
        if res.startswith(error_prefix):
            error_code = int(res[len(error_prefix):])
            raise Exception(f'Sending sms failed. Error code: {error_code}')
        self._expect_ok()

    def _expect_ok(self, expect_empty_line_before_ok=True):
        return self._expect_str('OK', expect_empty_line_before_ok)

    def _expect_str(self, expected_str, expect_empty_line_before_str=True):
        if expect_empty_line_before_str:
            self._expect_empty_line()
        line = self._read_line()
        if line != expected_str:
            raise Exception(f'Expected "{expected_str}", but got: {repr(line)}')

    def _expect_empty_line(self):
        line = self._read_line()
        if line != '':
            raise Exception(f'Expected an empty line, but got: {repr(line)}')

    def _write(self, data):
        if self._verbose:
            alog.info(f"WRITE: {repr(data)}")
        for c in data:
            self._tty_w.write(c)
            time.sleep(0.01)

    def _read_line(self, strip=True):
        data = self._tty_r.readline()
        if self._verbose:
            alog.info(f"READ: {repr(data)}")
        if strip:
            data = data.strip()
        return data
