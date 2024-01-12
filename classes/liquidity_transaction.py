#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from hashlib import sha256
from pycoingecko import CoinGeckoAPI

from classes.common import (
    getPrecision
)

from constants.constants import (
    CHAIN_DATA,
    OSMOSIS_FEE_MULTIPLIER,
    OSMOSIS_LIQUIDITIY_SPREAD,
    ULUNA
)

from classes.terra_instance import TerraInstance    
from classes.transaction_core import TransactionCore

from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

from terra_classic_sdk.core.osmosis import MsgJoinPool, MsgJoinSwapExternAmountIn, PoolAsset, MsgExitPool

class LiquidityTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(LiquidityTransaction, self).__init__(*args, **kwargs)

        self.amount_out:float = None
        self.cached_pools:dict    = {}
        self.gas_limit:str        = 'auto'
        #self.liquidity_amount:int = None
        self.liquidity_denom:str  = None
        self.max_spread:float     = OSMOSIS_LIQUIDITIY_SPREAD
        self.pool_id:int          = None
        self.pools:dict           = None    # Provided by the wallet balances
        self.sender_address:str   = ''
        self.sender_prefix:str    = ''
        self.share_in_amount:int  = None
        self.share_out_amount:int = None
        self.source_channel:str   = None
        self.token_in_coin:dict   = None
        self.token_out_coins:list = None
        
    def calcShareInAmount(self) -> int:
        """
        Calculate the share_in_amount value based on the pool and required exit amount.

        This is used for exiting a pool.
        """

        # Step 1: calculate the fraction that the user has of the entire pool:
        pool:list = self.getOsmosisPool(self.pool_id)
        
        total_shares:int = int(pool.total_shares.amount)
        share_fraction:int = int(total_shares / self.pools[self.pool_id])
        print ('total shares:', total_shares)
        print ('my shares:', self.pools[self.pool_id])
        print ('share fraction:', share_fraction)

        # Step 2: now get the actual amount of each asset across this pool:
        
        share_in_amount:int = 0
        asset:PoolAsset
        print ('withdrawal amount:', self.amount_out)
        # Go through each asset
        for asset in pool.pool_assets:
            denom = self.denomTrace(asset.token.denom)
            precision = getPrecision(denom)
            
            #asset_list[asset.token.denom] = int(asset.token.amount) / share_fraction / (10 ** precision)
            print (f'The pool has {asset.token.amount} of {denom}')
            asset_amount = int(asset.token.amount) / share_fraction / (10 ** precision)
            print (f'I have {asset_amount} of {denom}')

            user_amount:float = float(asset_amount * self.amount_out)
            # get the price for this denom
            denom_price = self.getCoinPrice(denom)

            print (f'The user amount is', user_amount)
            
            share_in_amount += user_amount * denom_price * 1000000000000000


        return share_in_amount
        

    def calcShareOutAmount(self, coin:Coin) -> int:
        """
        Calculate the share_out_amount value based on the pool and provided coin.
        This only works with a single coin liquidity investment.

        This is used for joining a pool.
        """

        # const tokenInAmount = new BigNumber(coinsNeeded[i].amount);
        # const totalShare = new BigNumber(poolInfo.totalShares.amount);
        # const totalShareExp = totalShare.shiftedBy(-18);
        # const poolAssetAmount = new BigNumber(token.amount);

        # return tokenInAmount
        #     .multipliedBy(totalShareExp)
        #     .dividedBy(poolAssetAmount)
        #     .shiftedBy(18)
        #     .decimalPlaces(0, BigNumber.ROUND_HALF_UP)
        #     .toString();

        # Get the pool details from the network
        pool:list = self.getOsmosisPool(self.pool_id)
        
        asset:PoolAsset
        for asset in pool.pool_assets:
            if asset.token.denom == coin.denom:
                pool_asset_amount:int = int(asset.token.amount)
                
        shift_val:int         = 10 ** 18
        token_in_amount:float = float(coin.amount)
        total_share_exp:float = float(int(pool.total_shares.amount) / shift_val)

        # This is the basic amount we expect to receive
        share_out_amount:int = ((token_in_amount * total_share_exp) / pool_asset_amount) * shift_val

        return share_out_amount

    def create(self, seed:str, denom:str = 'uluna'):
        """
        Create a swap object and set it up with the provided details.
        """

        # Create the terra instance
        self.terra = TerraInstance().create(denom)

        # Create the wallet based on the calculated key
        prefix              = CHAIN_DATA[denom]['bech32_prefix']
        current_wallet_key  = MnemonicKey(mnemonic = seed, prefix = prefix)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas list
        self.gas_list = self.gasList()

        return self
    
    def exitPool(self):
        """
        Join a pool with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            tx_msg = MsgExitPool(
                pool_id = self.pool_id,
                sender = self.sender_address,
                share_in_amount = str(int(self.share_in_amount)),
                token_out_mins = self.token_out_coins
            )

            options = CreateTxOptions(
                account_number = str(self.account_number),
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = {'uluna': self.gas_list['uluna']},
                msgs           = [tx_msg],
                sequence       = str(self.sequence),
            )
            
            print ('exit options:', options)
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    # if 'account sequence mismatch' in err.message:
                    #     self.sequence    = self.sequence + 1
                    #     options.sequence = self.sequence
                    #     print (' 🛎️  Boosting sequence number')
                    # else:
                    if 'too much slippage' in err.message:
                        self.share_out_amount = round(int(self.share_out_amount) * (1 - OSMOSIS_LIQUIDITIY_SPREAD))
                        tx_msg.share_out_min_amount = str(self.share_out_amount)
                        options.msgs = [tx_msg]
                        #print ('trying again with new share out amount:', self.share_out_amount)
                    else:
                        print (' 🛑 An unexpected error occurred in the exit liquidity function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the exit liquidity function:')
                    print (err)
                    
                    break

            self.transaction = tx

            return True
    
        except Exception as err:
            print (' 🛑 An unexpected error occurred in the exit liquidity function:')
            print (err)
            return False

    def exitSimulate(self):
        """
        Simulate a liquidity deposit so we can get the fee details.

        We primarily need to calculate the share_in_amount and the token_out_mins.
        NOTE: self.amount_out should already be supplied and needs to be a percentage.

        - pool_id: already supplied
        - sender: already supplied
        - share_in_amount is a complicated number - basically the user's share of the total value of the pool.
        - token_out_mins are the actual number of assets for this pool that we are requesting.

        Outputs:
        - self.fee - requested_fee object
        """

        ####
        #         "share_in_amount": "568701660205999",
        #         "token_out_mins": [
        #         {
        #             "amount": "2304780009",
        #             "denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0"
        #         },
        #         {
        #             "amount": "153067",
        #             "denom": "uosmo"
        #         }
        #         ]
        ####
        # Reset these values in case this is a re-used object:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = '1000000'
        self.sequence:int       = self.current_wallet.sequence()

        self.share_in_amount = self.calcShareInAmount()
        self.token_out_coins = self.tokenOutMins()

        # Perform the liquidity action as a simulation, with no fee details
        self.exitPool()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:

            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple

            print ('original requested fee:', requested_fee)
            self.fee = self.calculateFee(requested_fee, ULUNA, convert_to_ibc=True)

            # Adjust the fee to give it a higher amount
            fee_coin_list:list = self.fee.amount.to_list()

            new_fee_coin:Coin = Coin.from_data({'amount': fee_coin_list[0].amount * OSMOSIS_FEE_MULTIPLIER, 'denom': fee_coin_list[0].denom})

            self.fee.amount = Coins.from_proto([new_fee_coin])
            # amount:int = self.fee.amount
            # print ('amount:', amount)
            # print ('denom:', self.fee.denom)

            # adjusted:int = int(amount * 1.5)
            # test:Coins = self.fee.amount
            # for x in test:
            #     print (x.amount)
            #     x.amount = x.amount * 1.5

            # print (test)
            # #amount[0].amount = int(amount[0].amount * 1.5)
            # self.fee.amount = test
            # print ('new fee:')
            # print (self.fee)
            print (self.fee.amount)
            return True

        else:
            return False
        
    def getCoinPrice(self, denom:str) -> float:
        """
        Based on the provided denomination, get the coingecko details.

        It returns the price in US dollars.
        """

        # Create the Coingecko object
        cg = CoinGeckoAPI()

        # Coingecko uses its own denom key, which we store in the chain data constant
        cg_denom:str = CHAIN_DATA[denom]['coingecko_id']

        # We're only supporting USD at the moment
        result = cg.get_price(cg_denom, 'usd')

        return float(result[cg_denom]['usd'])
    
    def getAssetValues(self, assets) -> dict:
        """
        Go through the asset list and retrieve a price for each one
        """

        prices:dict = {}
        for asset_denom in assets:
            prices[asset_denom] = assets[asset_denom] * self.getCoinPrice(asset_denom)

        return prices
    
    def getOsmosisPool(self, pool_id) -> list:
        """
        Get the pool from Osmosis.
        Cache the results so we don't have to do this again.
        """

        if pool_id in self.cached_pools:
            pool:list = self.cached_pools[pool_id]
        else:
            # Get the pool details from the network
            pool:list = self.terra.pool.osmosis_pool(self.pool_id)
            self.cached_pools[pool_id] = pool

        return pool

    def getPoolAssets(self) -> dict:
        """
        Get the assets for the pool, but converted into an actual amount
        """

        pool:list = self.getOsmosisPool(self.pool_id)

        total_shares:int = int(pool.total_shares.amount)
        share_fraction:int = int(total_shares / self.pools[self.pool_id])

        asset_list:dict = {}
    
        # Go through each asset
        asset:PoolAsset
        for asset in pool.pool_assets:
            denom = self.denomTrace(asset.token.denom)
            precision = getPrecision(denom)
            
            asset_list[denom] = int(asset.token.amount) / share_fraction / (10 ** precision)

        return asset_list


    def joinPool(self) -> bool:
        """
        Join a pool with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            tx_msg = MsgJoinSwapExternAmountIn(
                pool_id = self.pool_id,
                sender = self.sender_address,
                share_out_min_amount = str(int(self.share_out_amount)),
                token_in = self.token_in_coin
            )

            options = CreateTxOptions(
                account_number = str(self.account_number),
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = self.gas_list,
                msgs           = [tx_msg],
                sequence       = self.sequence,
            )
            
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    # if 'account sequence mismatch' in err.message:
                    #     self.sequence    = self.sequence + 1
                    #     options.sequence = self.sequence
                    #     print (' 🛎️  Boosting sequence number')
                    # else:
                    if 'too much slippage' in err.message:
                        self.share_out_amount = round(int(self.share_out_amount) * (1 - OSMOSIS_LIQUIDITIY_SPREAD))
                        tx_msg.share_out_min_amount = str(self.share_out_amount)
                        options.msgs = [tx_msg]
                        #print ('trying again with new share out amount:', self.share_out_amount)
                    else:
                        print (' 🛑 An unexpected error occurred in the join liquidity function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the join liquidity function:')
                    print (err)
                    
                    break

            self.transaction = tx

            return True
        except Exception as err:
           print (' 🛑 An unexpected error occurred in the join liquidity function:')
           print (err)
           return False

    def joinSimulate(self) -> bool:
        """
        Simulate a liquidity deposit so we can get the fee details.

        Outputs:
        self.fee - requested_fee object
        """

        # Reset these values in case this is a re-used object:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = 'auto'
        self.sequence:int       = self.current_wallet.sequence()

        liquidity_denom:str = self.IBCfromDenom(self.source_channel, self.liquidity_denom)
        
        token_in_coin:Coin = Coin(liquidity_denom, int(self.liquidity_amount))

        share_out_amount:int = self.calcShareOutAmount(token_in_coin) / 2

        share_out_amount = round(share_out_amount * (1 - self.max_spread))

        token_in_coin = {'amount': int(self.liquidity_amount), 'denom': liquidity_denom}

        self.share_out_amount = share_out_amount
        self.token_in_coin = token_in_coin

        # Perform the liquidity action as a simulation, with no fee details
        self.joinPool()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:

            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple

            print ('original requested fee:', requested_fee)
            self.fee = self.calculateFee(requested_fee, ULUNA, convert_to_ibc=True)

            self.fee.amount = self.fee.amount * 1.5
            print ('calculated fee:', self.fee)
            return True

        else:
            return False

    def tokenOutMins(self) -> dict:
        """
        Given the user-supplied withdrawal amount, what does this translate into for coins in the pool?
        The self.amount_out needs to be a percentage.

        This is used for exiting a pool.
        """

        token_out_list:list = []
        # Step 1: calculate the fraction that the user has of the entire pool:
        pool:list = self.getOsmosisPool(self.pool_id)
        
        total_shares:int = int(pool.total_shares.amount)
        share_fraction:int = int(total_shares / self.pools[self.pool_id])
        print ('total shares:', total_shares)
        print ('my shares:', self.pools[self.pool_id])
        print ('share fraction:', share_fraction)

        # Step 2: now get the actual amount of each asset across this pool:
        
        share_in_amount:int = 0
        asset:PoolAsset
        print ('withdrawal amount:', self.amount_out)
        # Go through each asset
        for asset in pool.pool_assets:
            #denom = self.denomTrace(asset.token.denom)
            #precision = getPrecision(denom)
            
            #asset_list[asset.token.denom] = int(asset.token.amount) / share_fraction / (10 ** precision)
            #print (f'The pool has {asset.token.amount} of {denom}')
            #asset_amount = int(asset.token.amount) / share_fraction / (10 ** precision)
            asset_amount = int(asset.token.amount) / share_fraction
           #print (f'I have {asset_amount} of {denom}')

            user_amount:int = int(asset_amount * self.amount_out)
            
            token_out_list.append(Coin.from_data({'amount': user_amount, 'denom': asset.token.denom}))


        print ('token out list:', token_out_list)
        return token_out_list
    
        # Get the pool details from the network
        # pool:list = self.getOsmosisPool(self.pool_id)

        # asset:PoolAsset
        # asset_list:list = []

        # if isPercentage(lunc_amount):
        #     # Go through each asset and take the desired percentage of each

        #     # First, get the percentage amount from the supplied value
        #     percentage_amount:float = float(lunc_amount[0:-1]) / 100

        #     print ('percentage amount:', percentage_amount)
        #     # Go through each asset
        #     for asset in pool.pool_assets:
        #         #asset_list[asset.token.denom] = int(asset.token.amount) * percentage_amount
        #         print (asset.token.denom, asset.token.amount)
        #         print ( int(int(asset.token.amount) * percentage_amount))
        #         asset_list.append({'amount': int(int(asset.token.amount) * percentage_amount), 'denom': asset.token.denom})
        #         #print (f'{percentage_amount} of {asset.token.amount} ({asset.token.denom}) is', asset_list[asset.token.denom])

        #     print (asset_list)
        # else:
        #     # Convert the lunc amount into uluna:
        #     precision:int = getPrecision(ULUNA)
        #     lunc_amount = lunc_amount * (10 ** precision)

        #     # Go through each asset and find the LUNC asset
        #     for asset in pool.pool_assets:
        #         asset_denom = self.denomTrace(asset.token.denom)
                
        #         # if this is uluna, then figure out the percentage that this number is
        #         if asset_denom == ULUNA:
        #             percentage_amount:float = int(lunc_amount) / int(asset.token.amount)
        #             #print (f'{lunc_amount} as a percentage is {percentage_amount}')
        #         break

        #     # Now go through each asset and build the list:
        #     for asset in pool.pool_assets:
        #         #asset_list[asset.token.denom] = int(asset.token.amount) * percentage_amount
        #         asset_list.append({'amount': int(int(asset.token.amount) * percentage_amount), 'denom': asset.token.denom})
        #         #print (f'{percentage_amount} of {asset.token.amount} ({asset.token.denom}) is', asset_list[asset.token.denom])


        # return asset_list 


