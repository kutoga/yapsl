# yapsl

yapsl (Yet Another Python Sms Library) allows to send SMS from python by using a local connected modem (e.g. Huawei E220).
It's required that the PIN is already entered (or that no PIN is used at all). If that's not the case, the library
will raise an exception.

## Usage

```python
from yapsl import SmsType, SmsGateway

gw = SmsGateway('/dev/ttyUSB0', verbose=False) # verbose=True is mostly for debugging purposes:
                                               # it'll show the complete communication with the modem
                                               # (plus some more logs)

# Optional: It's possible to check if the modem is connected to a network (this is as well always done when sending an SMS)
if not gw.is_connected():
    print("Not connected!")
    print("Auto select network")
    gw.auto_select_network()
    sleep(60)

# send an ordinary SMS
gw.send('0786391538', 'this is a test message')

# send a "flash"-SMS (this is usually a popup and by default these SMS are not stored)
gw.send('0786391538', 'this is a test message', flash=True)

# send a silent SMS (text wont be shown: this is just some kind of 'ping')
gw.send('0786391538', 'this is a test message', type=SmsType.TYPE_0)

# send a replaceable SMS (note there exist only 7 of these replaceable SMS)
gw.send('0786391538', '3...', type=SmsType.REPLACE_TYPE_1)

# replace the previous sent SMS (a few times)
gw.send('0786391538', '2...', type=SmsType.REPLACE_TYPE_1)
gw.send('0786391538', '1...', type=SmsType.REPLACE_TYPE_1)
gw.send('0786391538', 'Hey:D', type=SmsType.REPLACE_TYPE_1)

```

## TODO

- [ ] Allow it to get the 'sms-received-confirmations' in python

