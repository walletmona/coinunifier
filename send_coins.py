#!/usr/bin/python2

from optparse import OptionParser
import json

from jsonrpc import ServiceProxy

from config import Config

##
## Process arguments
##

USAGE = '''
% send_coins.py [OPTIONS] KIND INPUTS ADDRESS AMOUNT

  KIND: kind of coin (e.g. bitcoin, litecoin, ...)
  INPUTS: input coins in JSON format: [{"txid":txid,"vout":n},...]
  ADDRESS: address to send coins
  AMOUNT: amount to send'''

DESCRIPTION = 'Send AMOUNT to the ADDRESS by using INPUTS.' \
    ' Fee is calculated as well as reference implementations.' \
    ' Transaction is broadcasted only if --no-dry-run option is specified.'

optparser = OptionParser(USAGE, description=DESCRIPTION)
optparser.add_option('', '--no-dry-run',
                     action='store_false', dest='dryrun', default=True,
                     help='Broadcast a transaction to nodes')
(opts, args) = optparser.parse_args()

if len(args) != 4:
    optparser.error('Incorrect number of arguments.')

kind = args[0]
inputs = json.loads(args[1])
address = args[2]
amount = int(float(args[3]) * 10**8)

config = Config(kind)


##
## Main
##

## Deprecate after official supports for getrawchangeaddress in major coins
def get_change_address(proxy):
    groups = proxy.listaddressgroupings()
    for group in groups:
        for entry in group:
            if len(entry) == 3:
                ## maybe with account
                continue
            elif len(entry) == 2:
                res = proxy.validateaddress(entry[0])
                if 'account' not in res:
                    return entry[0]
            else:
                raise RuntimeError('never reach')
    return proxy.getnewaddress()


proxy = ServiceProxy('http://%s:%s@%s:%d/' % (config.RPC_USER, config.RPC_PASS,
                                              config.RPC_HOST, config.RPC_PORT))

chgaddress = get_change_address(proxy)

tmp = {address: float(amount) / 10**8, chgaddress: 1e-8}
raw = proxy.createrawtransaction(inputs, tmp)
size = len(raw) / 2

## ref: wallet.cpp CWallet::CreateTransaction
total = 0
prio = 0
for inp in inputs:
    raw = proxy.getrawtransaction(inp['txid'])
    tx = proxy.decoderawtransaction(raw)
    value = tx['vout'][inp['vout']]['value']
    conf = proxy.gettransaction(inp['txid'])['confirmations']

    total += int(value * 10**8)
    prio += int(value * 10**8) * conf
prio = int(prio / size)

payfee = config.PAY_TX_FEE * (1 + int(size / 1000))

minfee = config.MIN_TX_FEE * (1 + int(size / 1000))
if prio >= config.PRIO_THRESHOLD and size < config.FREE_TX_SIZE:
    minfee = 0
if amount < config.OUTPUT_THRESHOLD:
    minfee += config.MIN_TX_FEE
if total-amount-minfee < config.OUTPUT_THRESHOLD:
    minfee += config.MIN_TX_FEE

fee = max(payfee, minfee)

change = total - amount - fee

if change <= 0:
    raise RuntimeError('Insufficient inputs: change = %f' %
                        (float(change) / 10**8))

if opts.dryrun:
    print('Total amount: %f' % (float(total) / 10**8))
    print('Send: %f to %s' % (float(amount) / 10**8, address))
    print('Change: %f to %s' % (float(change) / 10**8, chgaddress))
    print('Fee: %f' % (float(fee) / 10**8))
    print('Size: %d bytes' % size)
    print('Priority: %d' % prio)
    print('Add --no-dry-run option to proceed')
else:
    out = {address: float(amount) / 10**8, chgaddress: float(change) / 10**8}
    raw = proxy.createrawtransaction(inputs, out)
    signed = proxy.signrawtransaction(raw)
    if not signed['complete']:
        raise RuntimeError('signatures are missing')
    txid = proxy.sendrawtransaction(signed['hex'])
    print(txid)
