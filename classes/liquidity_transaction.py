#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from hashlib import sha256
import sqlite3
from sqlite3 import Cursor, Connection

from constants.constants import (
    CHAIN_DATA,
    DB_FILE_NAME,
    OSMOSIS_LIQUIDITIY_SPREAD,
    ULUNA,
)

#from classes.common import (
#    divide_raw_balance,
#    getPrecision,
#    multiply_raw_balance
#)

from classes.terra_instance import TerraInstance    
from classes.transaction_core import TransactionCore

from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

from terra_classic_sdk.core.osmosis import MsgJoinPool, MsgJoinSwapExternAmountIn, PoolAsset

class LiquidityTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(LiquidityTransaction, self).__init__(*args, **kwargs)

        self.gas_limit:str        = 'auto'
        self.liquidity_amount:int = None
        self.liquidity_denom:str  = None
        self.max_spread:float     = OSMOSIS_LIQUIDITIY_SPREAD
        self.pool_id:int          = None
        self.sender_address:str   = ''
        self.sender_prefix:str    = ''
        self.share_out_amount:int = None
        self.source_channel:str   = None
        self.token_in_coin:dict   = None
        
    def calcShareOutAmount(self, coin:Coin) -> int:
        """
        Calculate the share_out_amount value based on the pool and provided coin.
        This only works with a single coin liquidity investment.
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
        pool:list = self.terra.pool.osmosis_pool(self.pool_id)

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

    def simulate(self):
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

            self.fee = self.calculateFee(requested_fee, ULUNA, convert_to_ibc=True)

            return True

        else:
            return False

    def joinPool(self):
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
                        print (' 🛑 An unexpected error occurred in the liquidity function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the liquidity function:')
                    print (err)
                    
                    break

            self.transaction = tx

            return True
        except Exception as err:
           print (' 🛑 An unexpected error occurred in the liquidity function:')
           print (err)
           return False
