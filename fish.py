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
import base58

class GridStrategy(object):
    def __init__(self, upper, lower, amount, grid, pair, base, quote, owner, private):
        print ("Initialize...")
        self.upper = upper
        self.lower = lower
        self.amount = amount
        self.grid = grid
        self.pair = pair
        self.base = base
        self.quote = quote
        self.owner = owner
        self.key = base58.b58decode(self.private)
        self.payer = Account(key[:32])
        self.cc = conn("https://api.mainnet-beta.solana.com/")
        self.client = Client('', '')
        self.market = Market.load(self.cc, PublicKey(self.pair), program_id=PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"))

    def getOrder(self):
        """
        把orders整理成dict, index為price, value為orderid
        """
        orders = market.load_orders_for_owner(PublicKey(self.owner))
        for order in orders:
            print("Order id: %d, Client id: %d, Size: %f, Price: %f, Side: %s." % (
                order.order_id, order.client_id, order.info.size, order.info.price, order.side))

    def getLastPrice(self):
        return self.client.get_public_single_market_price(self.pair)['price']

    def buyFunc(self, price)
        """
        下買單
        """
        tx_sig = market.place_order(
            payer=PublicKey(self.quote),
            owner=payer,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            limit_price=10,
            max_quantity=0.1,
            client_id=1000 + 2,
            opts = TxOpts(skip_preflight=True)
        )
        print(tx_sig)

    def sellFunc(self, price)
        """
        下賣單
        """
        tx_sig = market.place_order(
            payer=PublicKey(self.quote),
            owner=payer,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            limit_price=10,
            max_quantity=0.1,
            client_id=1000 + 2,
            opts = TxOpts(skip_preflight=True)
        )
        print(tx_sig)

    def cancelPending(self):
        """
        取消所有掛單
        """
        ret = False
        while True:
            if ret:
                Sleep(Interval)
            orders = _C(self.ex.GetOrders)
            if len(orders) == 0:
                break
            for o in orders:
                self.ex.CancelOrder(o.Id, o)
            ret = True
        return ret

    def onexit():
        """
        執行取消所有掛單
        """
        if CancelAllWS:
            Log("正在退出, 嚐試取消所有掛單")
            self.cancelPending()
        Log("策略成功停止")
        Log(_C(self.ex.GetAccount))

    def griding(self, orgAccount):
        """
        組合上面Func
        """
        account = _C(self.ex.GetAccount)
        Log(account)
        InitAccount = account
        if IsVirtual() != True:
            if IsCoinBase:
                LogProfit(account.Stocks + account.FrozenStocks)
            else:
                LogProfit(account.Balance + account.FrozenBalance)
        ticker = _C(self.ex.GetTicker)
        amount = _N(AmountOnce)
        FirstPrice = PriceDown
        fishTable = {}
        uuidTable = {}
        needStocks = 0
        actualNeedStocks = 0
        notEnough = False
        canNum = 0
        BuyFirst = OpType == 0
    
        accountStocks = account.Stocks if IsCoinBase and IsFuture else account.Balance

        currentPrice = ticker.Sell
        for idx in range(AllNum):
            price = _N(FirstPrice + (idx * PriceGrid) if BuyFirst else FirstPrice - (idx * PriceGrid))
            price = min(currentPrice, price)
            if IsFuture:
                if IsCoinBase:
                    needStocks += (100 * amount) / price / MarginLevel
                else:
                    needStocks += amount * price * MarginLevel / 100
            else:
                needStocks += amount * price
            if (_N(needStocks) <= _N(accountStocks)):
                actualNeedStocks = needStocks
                canNum = canNum + 1
            else:
                notEnough = True
            fishTable[idx] = self.STATE_WAIT_OPEN
            uuidTable[idx] = -1

        if notEnough and CheckMoney == True:
            Log("帳戶餘額", accountStocks, ", 不足以支撐整個網格的運行，網格運行至少需要", needStocks)
            return False
        else:
            Log("帳戶餘額", accountStocks, ", 網格運行需要占用資金", needStocks, "格子數", canNum)
        
        OpenFunc = self.buyFunc if BuyFirst else self.SellFunc
        CoverFunc = self.SellFunc if BuyFirst else self.buyFunc
        preMsg = ""
        profitMax = 0
        count = 0
        while True:
            if self.cs:
                self.cs.runOnce()
            
            if count > 0 and count % 100 == 0:
                count = 1
                account = _C(self.ex.GetAccount)
                if IsVirtual() != True:
                    if IsCoinBase:
                        LogProfit(account.Stocks + account.FrozenStocks)
                    else:
                        LogProfit(account.Balance + account.FrozenBalance)
            msg = ""
            records = _C(self.ex.GetRecords, PERIOD_M1)
            length = len(records)
            lowPrice = min(records[length - 1]['Low'], records[length - 2]['Low'])
            highPrice = max(records[length - 1]['High'], records[length - 2]['High'])
            orderRange = self.getOrderRange(lowPrice, highPrice, canNum)
            # 初始化買入網格的时候是否全部買入上方的格子
            if count == 0 and BuyUpGrid:
                orderRange[1] = canNum - 1
            
            # 獲取未成交訂單
            orders = _C(self.ex.GetOrders)
            ticker = _C(self.ex.GetTicker)
            for idx in range(orderRange[0], orderRange[1]):
                openPrice = _N(FirstPrice + (idx * PriceGrid) if BuyFirst else FirstPrice - (idx * PriceGrid))
                coverPrice = _N(openPrice + PriceGrid if BuyFirst else openPrice - PriceGrid)
                openPrice = min(ticker.Sell, openPrice) if BuyFirst else max(ticker.Sell, openPrice)
                state = fishTable[idx]
                fishId = uuidTable[idx]
                order = self.getOrder(orders, fishId)
                if fishId != -1:
                    if (not order):
                        order = self.ex.GetOrder(fishId)
                        if (not order):
                            Log("獲取訂單訊息失敗, ID: ", fishId)
                            continue
                    if (order.Status == ORDER_STATE_PENDING):
                        continue

                # 訂單成交，掛賣單。走到這裡說明委託單都已經成交了
                if state == self.STATE_WAIT_COVER:
                    if IsFuture:
                        self.ex.SetDirection("closebuy" if BuyFirst else "closesell")
                    coverId = CoverFunc(coverPrice, amount)
                    #Log("賣出的格子是", idx, "開倉價格", openPrice, "目標價格", coverPrice) 
                    if coverId:
                        fishTable[idx] = self.STATE_WAIT_CLOSE
                        uuidTable[idx] = coverId
                elif state == self.STATE_WAIT_OPEN or state == self.STATE_WAIT_CLOSE:
                    if IsFuture:
                        self.ex.SetDirection("buy" if BuyFirst else "sell")
                    openId = OpenFunc(openPrice, amount)
                    Sleep(200)
                    if openId:
                        fishTable[idx] = self.STATE_WAIT_COVER
                        uuidTable[idx] = openId
                        #Log("掛單的格子是", idx, "開倉價格", openPrice, "目標價格", coverPrice, "訂單號", openId) 
                        if state == self.STATE_WAIT_CLOSE:
                            self.ProfitCount += 1
            Sleep(CheckInterval)
            count += 1
        return True
        
def main():
    Grid = GridStrategy(0, 100, 100, 'E14BKBhDWD4EuTkWj1ooZezesGxMW8LPCps4W5PuzZJo', '9SJPYhxEx5w7Xqg8G1nkhnr1hVWrnon7ptCaxkG95s3K', '38PvJgFjQ1rJdykymcG7pURko95sxyn5QvaDgop4qH1U', 'AQBqATwRqbU8odBL3RCFovzLbHR13MuoF2v53QpmjEV3')
    print (Grid.getLastPrice())
