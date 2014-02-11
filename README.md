coinunifier
===========

coinunifier provides utility Python scripts to unify divisional coins based on Bitcoin protocol.

Installation
------------

Required external libraries:
* [python-bitcoinrpc](https://github.com/jgarzik/python-bitcoinrpc "python-bitcoinrpc")

Install with:

    python setup.py install

Script Usage
------------

Two scripts are installed:
* `send_coins.py` sends coin with specified inputs
* `unify_coins_simple.py` unifies divisional coins with a large-amount and high-priority coin without fee

Run with `--help` for more detail.

Usage examples:

    # Sends 0.001 monacoins to the ADDRESS by using the INPUTS
    # (like '[{"txid":...,"vout":...},...]'). Calculates Fee as well as
    # reference implementations and gives the change.
    send_coins.py monacoin INPUTS ADDRESS 0.001

    # Run with --no-dry-run to broadcast the transaction
    send_coins.py --no-dry-run monacoin INPUTS ADDRESS 0.001

    # Makes a free transaction with as many sub-threshold monacoins (< 0.123)
    # as possible. Sends 0.001 monacoin to the ADDRESS by using this inputs
    # and gives the change (unified coin).
    unify_coins_simple.py monacoin 0.123 ADDRESS 0.001

    # Run with --no-dry-run to broadcast the transaction
    unify_coins_simple.py --no-dry-run monacoin 0.123 ADDRESS 0.001


License
---------

Copyright (c) 2014 WalletMona.com
