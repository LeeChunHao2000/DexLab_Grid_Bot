import time

import base58
from pyserum.connection import conn
from pyserum.enums import OrderType, Side
from pyserum.market import Market
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.client import Token

from DexLab.client import Client


class GridStrategy(object):
    def __init__(
            self, upper: float, lower: float, amount: float, grid: int,
            pair: str, base: str, quote: str, owner: str,
            private: str):
        """
        :params upper: price up
        :params lower: price down
        :params amount: amount of the order
        :params grid: amount of grid
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
        self.pair = pair
        self.base = base
        self.quote = quote
        self.owner = owner
        self.key = base58.b58decode(private)
        self.payer = Account(self.key[:32])
        self.client = Client('', '')
        self.cc = conn('https://api.mainnet-beta.solana.com/')
        self.market = Market.load(
            self.cc, PublicKey(self.pair),
            program_id=PublicKey(
                '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin'))
        try:
            self.open_acc = self.market.find_open_orders_accounts_for_owner(
                self.payer.public_key())[0].address
        except:
            self.open_acc = ''
        self.base_decimal = self.market.state.base_spl_token_decimals()
        self.quote_decimal = self.market.state.quote_spl_token_decimals()
        print(
            f'Initialize...\n\n'
            f'----parameters----\n\n'
            f'upper: {self.upper}\n'
            f'lower: {self.lower}\n'
            f'amount: {self.amount}\n'
            f'grid: {self.grid}\n'
            f'base decimal: {self.base_decimal}\n'
            f'quote decimal: {self.quote_decimal}\n'
            f'pair: {self.pair}\n'
            f'base: {self.base}\n'
            f'quote: {self.quote}\n'
            f'owner: {self.owner}\n'
            f'open orders account: {self.open_acc}\n'
            f'key: {self.key[:32]}\n\n'
            f'----start----\n'
        )

    def _get_orders(self):
        """
        :return: a dict contains price and client id Ex: {price: client}
        """

        orders = self.market.load_orders_for_owner(PublicKey(self.owner))
        order_table = {}
        for o in orders:
            order_table[o.client_id] = o.info.price
        return order_table

    def _get_last_price(self):
        """
        :return: last price (float)
        """

        return float(
            self.client.get_public_single_market_price(self.pair)['price'])

    def _buy_func(self, price, client_id):
        self.market.place_order(
            payer=PublicKey(self.base),
            owner=self.payer,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            limit_price=price,
            max_quantity=abs(self.amount),
            client_id=client_id,
            opts=TxOpts(skip_preflight=True)
        )
        print(
            f'Client ID: {client_id}; Price {price}; Amount: {self.amount}; Open: BUY')

    def _sell_func(self, price, client_id):
        self.market.place_order(
            payer=PublicKey(self.quote),
            owner=self.payer,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            limit_price=price,
            max_quantity=abs(self.amount),
            client_id=client_id,
            opts=TxOpts(skip_preflight=True)
        )
        print(
            f'Client ID: {client_id}; Price {price}; Amount: {self.amount}; Open: SELL')

    def cancel_order(self, client_id):
        """
        :return: a dict contains tx_hash and id
        """
        self.open_acc = self.market.find_open_orders_accounts_for_owner(
            self.payer.public_key())[0].address
        return self.market.cancel_order_by_client_id(
            self.payer, PublicKey(self.open_acc),
            client_id, TxOpts(skip_preflight=True))

    def cancel_pending(self):
        order_table = self._get_orders()
        for o in order_table.keys():
            self.cancel_order(o)

    def on_exit(self):
        if True:
            print(
                f'----Exit----\n\n'
                f'Closing all open orders...\n'
            )
            self.cancel_pending()
        print('----Success----')

    def update_order(self, order_table, distance, last_prcie):
        for i in range(self.grid):
            if (i + 1) not in order_table:
                if (self.lower + i * distance) < last_prcie:
                    #self._buy_func(round((self.lower + i * distance), self.base_decimal), i + 1)
                    print(
                        f'Client ID: {i + 1}; Price {round((self.lower + i * distance), self.base_decimal)}; Amount: {self.amount}; Open: BUY')
                elif (self.lower + i * distance) > last_prcie:
                    #self._sell_func(round((self.lower + i * distance), self.quote_decimal), i + 1)
                    print(
                        f'Client ID: {i + 1}; Price {round((self.lower + i * distance), self.quote_decimal)}; Amount: {self.amount}; Open: SELL')

    def griding(self):
        """
        Main Logic
        """
        
        distance = (self.upper - self.lower) / self.grid
        order_table = self._get_orders()
        last_prcie = self._get_last_price()
        print(f'Current Price: {last_prcie}\n')
        print('----place orders----')
        self.update_order(order_table, distance, last_prcie)


# Worker Example
# it can be replaced by other worker services

strategy = GridStrategy(
    3, 1, 10, 10, 'E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo',
    'E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo',
    'E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo',
    'E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo',
    '')
while True:
    strategy.griding()
    time.sleep(60)
