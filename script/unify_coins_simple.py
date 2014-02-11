#!/usr/bin/env python

import sys
from optparse import OptionParser
from bisect import bisect_left, bisect_right

from coinunifier.wallet.factory import load_wallet

##
## Process arguments
##

USAGE = ''''
% unify_coins_simple.py [OPTIONS] KIND THRESHOLD ADDRESS

  KIND: kind of coin (e.g. bitcoin, litecoin, ...)
  THRESHOLD: threshold amount
  ADDRESS: address to send coins'''

DESCRIPTION = \
    'Make a free transaction with sub-THRESHOLD coins and a least' \
    ' large-amount-and-high-priority coin. Then, send minimul amount of' \
    ' coins (== DUST_SOFT_LIMIT) to the ADDRESS by using the inputs and' \
    ' deposit the change. This script is useful to unify sub-threshold coins' \
    ' into one without fee.'

optparser = OptionParser(USAGE, description=DESCRIPTION)
optparser.add_option('', '--no-dry-run',
                     action='store_false', dest='dryrun', default=True,
                     help='Broadcast a transaction to nodes')
(opts, args) = optparser.parse_args()

if len(args) != 3:
    optparser.error("Incorrect number of arguments.")

kind = args[0]
theta = int(float(args[1]) * 10**8)
address = args[2]


##
## Functions
##

def coins2inputs(coins):
    res = []
    for c in coins:
        res.append({"txid": c['txid'], "vout": c['vout']})
    return res

def cumsum(ls):
    res = list(ls) # shallow copy
    for i in range(1, len(res)): res[i] += res[i-1]
    return res

# Unify sub-threshold coins to a large-amount-and-high-priority coin
#
# O(n log n)
def unify_coins_simple(wallet, coins):
    n = len(coins)

    remain = wallet.free_tx_size-1 - wallet.base_size - 2*wallet.output_size
    maxin = min(n, int(remain / wallet.input_size))

    coins.sort(key=lambda x: x['amount'])

    amounts = [c['amount'] for c in coins]
    prios = [c['prio'] for c in coins]

    camounts = cumsum(amounts)
    cprios = cumsum(prios)
    hiprios = list(prios)
    for i in range(len(prios)-1, 0, -1):
        hiprios[i-1] = max(hiprios[i-1], hiprios[i])

    num = min(bisect_right(amounts, theta), maxin-1)
    if num == 0:
        print('No sub-threshold coins found')
        return

    # Determine included sub-threshold coins by binary search in (left, right]
    left = 0
    right = num
    while left < right:
        # use coins in range [0, m) and a large coin
        m = int((left + right + 1) / 2)

        size = wallet.base_size + (m+1)*wallet.input_size + 2*wallet.output_size

        index = bisect_left(amounts, 2*wallet.dust_soft_limit - camounts[m-1],
                            lo=m)

        if cprios[m-1]+hiprios[index] < wallet.prio_threshold*size:
            # decrease size
            right = m-1
        else:
            # increase size
            left = m
    num = left

    if num == 0:
        print('No large coin found')
        return

    size = wallet.base_size + (num+1)*wallet.input_size + 2*wallet.output_size

    # Find a large coin
    index = bisect_left(amounts, 2*wallet.dust_soft_limit - camounts[num-1],
                        lo=num)
    while cprios[num-1]+prios[index] < wallet.prio_threshold*size:
        index += 1

    res = coins[0:num]
    res.append(coins[index])
    inputs = coins2inputs(res)

    if opts.dryrun:
        print('Inputs (confirmations amount)')
        for c in res:
            print('  %6d  %.8f' % (c['confirmations'],
                                   float(c['amount']) / 10**8))

        wallet.show_send_info(inputs, address, wallet.dust_soft_limit)
        print('Add --no-dry-run option to proceed')
    else:
        print(wallet.send(inputs, address, wallet.dust_soft_limit))


##
## Main
##

wallet = load_wallet(kind)
wallet.connect()

unify_coins_simple(wallet, wallet.unspent_coins())
