
from jsonrpc import ServiceProxy

class Wallet:
    def __init__(self, pay_tx_fee, min_tx_fee,
                 prio_theta, out_theta, free_tx_size):
        self.proxy = None
        self.pay_tx_fee = pay_tx_fee
        self.min_tx_fee = min_tx_fee
        self.prio_theta = prio_theta
        self.out_theta = out_theta
        self.free_tx_size = free_tx_size

    def connect(self, user, password, host, port):
        self.proxy = ServiceProxy('http://%s:%s@%s:%d/' %
                                   (user, password, host, port))

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
        if prio >= self.prio_theta and size < self.free_tx_size:
            minfee = 0
        if amount < self.out_theta:
            minfee += self.min_tx_fee
        if total-amount-minfee < self.out_theta:
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
