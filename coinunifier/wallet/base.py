
import ConfigParser
import StringIO

from jsonrpc import ServiceProxy

TMP_SECTION = '__tmp__'

class WalletBase:

    def __init__(self, pay_tx_fee, min_tx_fee,
                 prio_threshold, soft_dust_limit, free_tx_size):
        self.proxy = None
        self.pay_tx_fee = pay_tx_fee
        self.min_tx_fee = min_tx_fee
        self.prio_threshold = prio_threshold
        self.soft_dust_limit = soft_dust_limit
        self.free_tx_size = free_tx_size

    def set_size(self, base_size, input_size, output_size):
        self.base_size = base_size
        self.input_size = input_size
        self.output_size = output_size

    def load_config(self, config_path):
        # trick to load a config file without sections
        con = open(config_path, 'r').read()
        dummy_fp = StringIO.StringIO(("[%s]\n" % TMP_SECTION) + con)
        config = ConfigParser.ConfigParser()
        config.readfp(dummy_fp)

        ## utility function
        def get_conf(key, default=None):
            if config.has_option(TMP_SECTION, key):
                return config.get(TMP_SECTION, key)
            return default

        self.rpc_user = get_conf('rpcuser')
        self.rpc_pass = get_conf('rpcpassword')
        self.rpc_port = int(get_conf('rpcport'))
        self.rpc_host = get_conf('rpcconnect', '127.0.0.1')

        if config.has_option(TMP_SECTION, 'paytxfee'):
            self.pay_tx_fee = int(float(get_conf('paytxfee')) * 10**8)
        if config.has_option(TMP_SECTION, 'mintxfee'):
            self.min_tx_fee = int(float(get_conf('mintxfee')) * 10**8)

    def connect(self):
        self.proxy = ServiceProxy('http://%s:%s@%s:%d/' %
                                   (self.rpc_user, self.rpc_pass,
                                    self.rpc_host, self.rpc_port))

    def get_size(self, inputs, outputs):
        raw = self.proxy.createrawtransaction(inputs, outputs)
        return len(raw) / 2

    ## Deprecate after official supports for getrawchangeaddress in major coins
    def get_change_address(self):
        groups = self.proxy.listaddressgroupings()
        for group in groups:
            for entry in group:
                if len(entry) == 3:
                    ## maybe with account
                    continue
                elif len(entry) == 2:
                    res = self.proxy.validateaddress(entry[0])
                    if 'account' not in res:
                        return entry[0]
                else:
                    raise RuntimeError('never reach')
        return self.proxy.getnewaddress()

    ## ref: wallet.cpp CWallet::CreateTransaction
    def calculate(self, inputs, address, amount, chgaddress):
        tmp = {address: float(amount) / 10**8, chgaddress: 1 }
        size = self.get_size(inputs, tmp)

        total = 0
        prio = 0
        for inp in inputs:
            raw = self.proxy.getrawtransaction(inp['txid'])
            tx = self.proxy.decoderawtransaction(raw)
            value = tx['vout'][inp['vout']]['value']
            conf = self.proxy.gettransaction(inp['txid'])['confirmations']

            total += int(value * 10**8)
            prio += int(value * 10**8) * conf
        prio = int(prio / size)

        payfee = self.pay_tx_fee * (1 + int(size / 1000))

        minfee = self.min_tx_fee * (1 + int(size / 1000))
        if prio >= self.prio_threshold and size < self.free_tx_size:
            minfee = 0
        if amount < self.soft_dust_limit:
            minfee += self.min_tx_fee
        if total-amount-minfee < self.soft_dust_limit:
            minfee += self.min_tx_fee
        fee = max(payfee, minfee)

        change = total - amount - fee

        if change <= 0:
            raise RuntimeError('Insufficient inputs: change = %f' %
                               (float(change) / 10**8))

        return { 'total': total, 'fee': fee, 'change': change,
                  'size': size, 'prio': prio }

    def send(self, inputs, address, amount):
        chgaddress = self.get_change_address()
        res = self.calculate(inputs, address, amount, chgaddress)
        outputs = { address: float(amount) / 10**8,
                    chgaddress: float(res['change']) / 10**8 }

        raw = self.proxy.createrawtransaction(inputs, outputs)
        signed = self.proxy.signrawtransaction(raw)
        if not signed['complete']:
            raise RuntimeError('signatures are missing')
        return self.proxy.sendrawtransaction(signed['hex'])

    def show_send_info(self, inputs, address, amount):
        chgaddress = self.get_change_address()
        res = self.calculate(inputs, address, amount, chgaddress)

        print('Total amount: %f' % (float(res['total']) / 10**8))
        print('Send: %f to %s' % (float(amount) / 10**8, address))
        print('Change: %f to %s' % (float(res['change']) / 10**8, chgaddress))
        print('Fee: %f' % (float(res['fee']) / 10**8))
        print('Size: %d bytes' % res['size'])
        print('Priority: %d' % res['prio'])

    def unspent_coins(self):
        coins = self.proxy.listunspent(6)
        for c in coins:
            c['amount'] = int(c['amount'] * 10**8)
            c['prio'] = c['amount'] * c['confirmations']
        return coins
