#!/usr/bin/python2

import sys
from optparse import OptionParser
from bisect import bisect_right

from coinunifier.wallet.factory import load_wallet

##
## Process arguments
##

USAGE = ''''
% free_simple_unify.py [OPTIONS] KIND THRESHOLD ADDRESS AMOUNT

  KIND: kind of coin (e.g. bitcoin, litecoin, ...)
  THRESHOLD: threshold amount
  ADDRESS: address to send coins
  AMOUNT: amount to send (should be greater than or equal to soft_dust_limit)'''

DESCRIPTION = \
    'Make a free transaction with sub-THRESHOLD coins and a least' \
    ' large-amount-and-high-priority coin. Then, send AMOUNT to the ADDRESS' \
    ' by using the inputs and deposit the change. This script is useful to' \
    ' unify sub-threshold coins into one without fee.'

optparser = OptionParser(USAGE, description=DESCRIPTION)
optparser.add_option('', '--no-dry-run',
                     action='store_false', dest='dryrun', default=True,
                     help='Broadcast a transaction to nodes')
(opts, args) = optparser.parse_args()

if len(args) != 4:
    optparser.error("Incorrect number of arguments.")

kind = args[0]
theta = int(float(args[1]) * 10**8)
address = args[2]
amount = int(float(args[3]) * 10**8)


##
## Functions
##

def coins2inputs(coins):
    res = []
    for c in coins:
        res.append({"txid": c['txid'], "vout": c['vout']})
    return res

# Unify sub-threshold coins to a large-amount-and-high-priority coin
#
# O(n log n)
def free_simple_unify(wallet, coins):
    n = len(coins)

    remain = wallet.free_tx_size-1 - wallet.base_size - 2*wallet.output_size
    maxin = min(n, int(remain / wallet.input_size))

    coins.sort(key=lambda x: x['amount'])
    pos = bisect_right([c['amount'] for c in coins], theta)
    pos = min(pos, maxin-1)
    size = wallet.base_size + (pos+1)*wallet.input_size + 2*wallet.output_size

    total = 0
    prio = 0
    for i in range(0, pos):
        total += coins[i]['amount']
        prio += coins[i]['prio']
    index = -1

    for i in range(pos, n):
        if (total+coins[i]['amount'] >= 2*wallet.soft_dust_limit and
            prio+coins[i]['prio'] >= wallet.prio_threshold*size):
            index = i
            break

    # No large coin found
    if index == -1:
        print('No large coin found')
        return

    res = coins[0:pos]
    res.append(coins[index])
    inputs = coins2inputs(res)

    if opts.dryrun:
        print('Inputs (confirmations amount)')
        for c in res:
            print('  %6d  %.8f' % (c['confirmations'],
                                   float(c['amount']) / 10**8))

        wallet.show_send_info(inputs, address, amount)
        print('Add --no-dry-run option to proceed')
    else:
        print(wallet.send(inputs, address, amount))


##
## Main
##

wallet = load_wallet(kind)
wallet.connect()

if amount < wallet.soft_dust_limit:
    print('AMOUNT should be at least %.8f for free unify' %
           (float(wallet.soft_dust_limit) / 10**8))
    sys.exit(1)

free_simple_unify(wallet, wallet.unspent_coins())
