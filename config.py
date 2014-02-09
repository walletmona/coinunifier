
import os
import ConfigParser
import StringIO

class Config:
    def __init__(self, section_name):
        config = ConfigParser.ConfigParser()
        config.read('coins.cfg')

        if not config.has_section(section_name):
            raise RuntimeError('Config section not found: %s' % section_name)

        ## utility function
        def get_conf(key, default=None):
            if config.has_option(section_name, key):
                return config.get(section_name, key)
            return default

        self.PRIO_THRESHOLD = int(get_conf('priority_threshold'))
        self.OUTPUT_THRESHOLD = int(get_conf('soft_dust_limit'))

        # load coin config
        coin_config = os.path.expanduser(get_conf('config_path'))
        # trick to load a config file without sections
        con = open(coin_config, 'r').read()
        dummy_fp = StringIO.StringIO(("[%s]\n" % section_name) + con)
        config.readfp(dummy_fp)

        self.RPC_USER = get_conf('rpcuser')
        self.RPC_PASS = get_conf('rpcpassword')
        self.RPC_PORT = int(get_conf('rpcport'))
        self.RPC_HOST = get_conf('rpcconnect', '127.0.0.1')
        self.PAY_TX_FEE = int(float(get_conf('paytxfee', 0)) * 10**8)
        self.MIN_TX_FEE = int(float(get_conf('mintxfee', 0.001)) * 10**8)

