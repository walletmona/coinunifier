
from coinunifier.wallet.litecoin import LitecoinWallet
from coinunifier.wallet.monacoin import MonacoinWallet

def load_wallet(kind):
    if kind == 'litecoin': return LitecoinWallet()
    if kind == 'monacoin': return MonacoinWallet()
    raise ArgumentError('No support for %s wallet' % (kind))
