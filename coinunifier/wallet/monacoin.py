
import os

from coinunifier.wallet.base import WalletBase

DEFAULT_PAY_TX_FEE = int(0 * 10**8)
DEFAULT_MIN_TX_FEE = int(0.001 * 10**8)

PRIO_THRESHOLD = int(10**8 * 960 / 250)
DUST_SOFT_LIMIT = int(10**8 * 0.001)

FREE_TX_SIZE = 1000

INPUT_SIZE = 41
OUTPUT_SIZE = 34
BASE_SIZE = 10

DEFAULT_CONFIG_PATH = os.path.expanduser('~/.monacoin/monacoin.conf')

class MonacoinWallet(WalletBase):

    def __init__(self):
        WalletBase.__init__(self, DEFAULT_PAY_TX_FEE, DEFAULT_MIN_TX_FEE,
                            PRIO_THRESHOLD, DUST_SOFT_LIMIT, FREE_TX_SIZE)

        self.set_size(BASE_SIZE, INPUT_SIZE, OUTPUT_SIZE)

        self.load_config(DEFAULT_CONFIG_PATH)
