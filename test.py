from nacl import public
from pyserum.connection import conn
from pyserum.enums import OrderType, Side
from pyserum.market import Market
from pyserum.open_orders_account import *
from solana.account import Account
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.client import Token
import base58
import time

private_key = base58.b58decode("")

payer = Account(private_key[:32])
cc = conn("https://api.mainnet-beta.solana.com/")

market_address = PublicKey("E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo") # Address for market

market = Market.load(cc, market_address, program_id=PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"))

tx_sig = market.place_order(
    payer=PublicKey("38PvJgFjQ1rJdykymcG7pURko95sxyn5QvaDgop4qH1U"),
    owner=payer,
    side=Side.SELL,
    order_type=OrderType.LIMIT,
    limit_price=8,
    max_quantity=1,
    client_id=8,
    opts = TxOpts(skip_preflight=True)
)
print(tx_sig)

# print (1)
# time.sleep(10)
# print (2)

# orders = market.load_orders_for_owner(PublicKey('AQBqATwRqbU8odBL3RCFovzLbHR13MuoF2v53QpmjEV3'))

# print (orders)
# print ("Bid Orders:")
# for order in orders:
#     if str(order.side) == 'Side.BUY':
#         print("Order id: %d, Client id: %d, Size: %f, Price: %f, Side: %s." % (
#             order.order_id, order.client_id, order.info.size, order.info.price, order.side))

# print ('\n')

# print ("Ask Orders:")
# for order in orders:
#     if str(order.side) == 'Side.SELL':
#         print("Order id: %d, Client id: %d, Size: %f, Price: %f, Side: %s." % (
#             order.order_id, order.client_id, order.info.size, order.info.price, order.side))

# from DexLab.client import Client

# client = Client('', '')

# print (client.get_public_single_market_price('E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo'))
# print (client.get_public_single_market_trades('E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo'))