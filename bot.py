from nacl import public
from pyserum.connection import conn
from pyserum.enums import OrderType, Side
from pyserum.market import Market
from pyserum.open_orders_account import *
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.client import Token
from DexLab.client import Client
import base58, time

class GridStrategy(object):
    def __init__(self, upper, lower, amount, grid, interval, pair, base, quote, owner, private):
        """
        :params upper: price up
        :params lower: price down
        :params amount: amount of the order
        :params grid: amount of grid
        :params interval: check interval
        :params pair: dexlab trading pair address
        :params base: youur base coin address for trading
        :params quote: your quote coin address for trading
        :params owner: your solana wallet address
        :params private: your private key for pay the transaction gas
        """

        self.upper = upper
        self.lower = lower
        self.amount = amount
        self.grid = grid
        self.interval = interval
        self.pair = pair
        self.base = base
        self.quote = quote
        self.owner = owner
        self.key = base58.b58decode(private)
        self.payer = Account(self.key[:32])
        self.cc = conn('https://api.mainnet-beta.solana.com/')
        self.client = Client('', '')
        self.market = Market.load(self.cc, PublicKey(self.pair), program_id=PublicKey('9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin'))
        try:
            self.openAcc = self.market.find_open_orders_accounts_for_owner(self.payer.public_key())[0].address
        except:
            self.openAcc = ''
        self.baseDecimal = self.market.state.base_spl_token_decimals()
        self.quoteDecimal = self.market.state.quote_spl_token_decimals()
        print (
            f'Initialize...\n\n'
            f'----parameters----\n\n'
            f'upper: {self.upper}\n'
            f'lower: {self.lower}\n'
            f'amount: {self.amount}\n'
            f'grid: {self.grid}\n'
            f'pair: {self.pair}\n'
            f'base: {self.base}\n'
            f'quote: {self.quote}\n'
            f'owner: {self.owner}\n'
            f'open orders account: {self.openAcc}\n'
            f'key: {self.key[:32]}\n\n'
            f'----start----\n'
        )

    def getOrders(self):
        """
        :return: a dict contains price and client id Ex: {price: client}
        """

        orders = self.market.load_orders_for_owner(PublicKey(self.owner))
        orderTable = {}
        for o in orders:
            orderTable[o.client_id] = o.info.price
        return orderTable

    def getLastPrice(self):
        """
        :return: last price (float)
        """

        return float(self.client.get_public_single_market_price(self.pair)['price'])

    def buyFunc(self, price, clientId):
        self.market.place_order(
            payer=PublicKey(self.base),
            owner=self.payer,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            limit_price=price,
            max_quantity=abs(self.amount),
            client_id=clientId,
            opts = TxOpts(skip_preflight=True)
        )
        print(f'Client ID: {clientId}; Price {price}; Amount: {self.amount}; Open: BUY')

    def sellFunc(self, price, clientId):
        self.market.place_order(
            payer=PublicKey(self.quote),
            owner=self.payer,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            limit_price=price,
            max_quantity=abs(self.amount),
            client_id=clientId,
            opts = TxOpts(skip_preflight=True)
        )
        print(f'Client ID: {clientId}; Price {price}; Amount: {self.amount}; Open: SELL')

    def cancelOrder(self, clientId):
        """
        :return: a dict contains tx_hash and id
        """
        self.openAcc = self.market.find_open_orders_accounts_for_owner(self.payer.public_key())[0].address
        return self.market.cancel_order_by_client_id(self.payer, PublicKey(self.openAcc), clientId, TxOpts(skip_preflight=True))

    def cancelPending(self):
        orderTable = self.getOrders()
        for o in orderTable.keys():
            self.cancelOrder(o)
            
    def onExit(self):
        if True:
            print (
                f'----Exit----\n\n'
                f'Closing all open orders...\n'
            )
            self.cancelPending()
        print ('----Success----')

    def griding(self):
        """
        組合上面Func
        """
        
        # firstBuy

        distance = (self.upper - self.lower) / self.grid

        Buy = self.buyFunc
        Sell = self.sellFunc

        while True:
            orderTable = self.getOrders()
            lastPrcie = self.getLastPrice()
            for i in range(self.grid):
                if (i + 1) not in orderTable:
                    if (self.lower + i * distance) < lastPrcie:
                        #Buy(round((self.lower + i * distance), self.baseDecimal), i + 1)
                        print ('Buy', i + 1, round((self.lower + i * distance), self.baseDecimal))
                    elif (self.lower + i * distance) > lastPrcie:
                        #Sell(round((self.lower + i * distance), self.quoteDecimal), i + 1)
                        print ('Sell', i + 1, round((self.lower + i * distance), self.quoteDecimal))
            time.sleep(self.interval)