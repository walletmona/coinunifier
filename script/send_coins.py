#!/usr/bin/python2

from optparse import OptionParser
import json

from config import Config
from wallet import Wallet

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


##
## Main
##

config = Config(kind)

wallet = Wallet(config.PAY_TX_FEE, config.MIN_TX_FEE, config.PRIO_THRESHOLD,
                config.OUTPUT_THRESHOLD, config.FREE_TX_SIZE)
wallet.connect(config.RPC_USER, config.RPC_PASS,
               config.RPC_HOST, config.RPC_PORT)

if opts.dryrun:
    wallet.show_send_info(inputs, address, amount)
    print('Add --no-dry-run option to proceed')
else:
    print(wallet.send(inputs, address, amount))
