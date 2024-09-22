#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from __future__ import annotations

from hashlib import sha256
import sqlite3
from sqlite3 import Cursor, Connection
import time
from terra_classic_sdk.core.osmosis import Pool

from classes.common import (
    get_precision,
    get_user_choice
)

from constants.constants import (
    BUSY_RETRY_COUNT,
    CHAIN_DATA,
    DB_FILE_NAME,
    FULL_COIN_LOOKUP,
    OSMOSIS_FEE_MULTIPLIER,
    OSMOSIS_LIQUIDITIY_SPREAD,
    OSMOSIS_POOL_TAX,
    ULUNA,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT
)

from classes.terra_instance import TerraInstance    
from classes.transaction_core import TransactionCore, TransactionResult
from classes.wallet import UserWallet

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

from terra_classic_sdk.core.osmosis import MsgJoinSwapExternAmountIn, PoolAsset, MsgExitPool

class LiquidityTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(LiquidityTransaction, self).__init__(*args, **kwargs)

        self.amount_out:float     = None  # Used for exiting a pool - supplied by user
        self.amount_in:float      = None  # Used for joining a pool - supplied by user
        self.cached_pools:dict    = {}
        self.gas_limit:str        = 'auto'
        self.max_spread:float     = OSMOSIS_LIQUIDITIY_SPREAD
        self.pool_id:int          = None  # Used by both joining and exiting - supplied by user
        self.pools:dict           = None  # Provided by the wallet balances
        self.sender_address:str   = ''
        self.share_in_amount:int  = None
        self.share_out_amount:int = None
        self.source_channel:str   = None
        self.token_in_coin:dict   = None
        self.token_out_coins:list = None
        self.wallet:UserWallet    = None

    def calcShareInAmount(self) -> int:
        """
        Calculate the share_in_amount value based on the pool and required exit amount.
        This is simply the total number of shares that the user has, multiplied by the percentage.

        NOTE: the amount_out MUST be a percentage decimal value.

        This is used for exiting a pool.

        @params:
            - None

        @return: the number of shares that this transaction will return
        """

        # Get the number of shares that this user has
        user_shares:int = int(self.pools[self.pool_id])

        # Multiply this by the percentage. This is the amount we are removing.
        share_in_amount:int = int(user_shares * self.amount_out)

        return share_in_amount
        
    def calcShareOutAmount(self, coin:Coin) -> int:
        """
        Calculate the share_out_amount value based on the pool and provided coin.
        This only works with a single coin liquidity investment.

        This is used for joining a pool.

        @params:
            - coin: a Coin object with the amount that we are joining with

        @return: the number of shares that this transaction will return
        """

        share_out_amount: int = 0
        # Get the pool details from the network
        pool:Pool = self.getOsmosisPool(self.pool_id)
        
        if pool is not None:
            total_weight:int = int(pool.total_weight)

            # Get the actual amount of this asset in the pool
            divisor:float = 0
            asset:PoolAsset
            for asset in pool.pool_assets:
                if asset.token.denom == coin.denom:
                    pool_asset_amount:int = int(asset.token.amount)
                    divisor:float =  total_weight / int(asset.weight)
                    break
                    
            shift_val:int         = 10 ** 18
            token_in_amount:float = float(coin.amount)
            total_share_exp:float = float(int(pool.total_shares.amount) / shift_val)

            # This is the basic amount we expect to receive
            share_out_amount = (((token_in_amount * total_share_exp) / pool_asset_amount) * shift_val) / divisor

        return share_out_amount

    def create(self, seed:str, denom:str = 'uluna') -> LiquidityTransaction:
        """
        Create a liquidity object and set it up with the provided details.

        @params:
            - seed: the wallet seed so we can create the wallet
            - denom: what denomination are we sending? It will usually be LUNC

        @return: self
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
    
    def exitPool(self) -> bool:
        """
        Join a pool with the information we have so far.
        If fee is None then it will be a simulation.

        @params:
            - None

        @return: true/false depending on if the transaction succeeded
        """

        try:
            tx:Tx = None

            tx_msg = MsgExitPool(
                pool_id         = self.pool_id,
                sender          = self.sender_address,
                share_in_amount = str(int(self.share_in_amount)),
                token_out_mins  = self.token_out_coins
            )

            options = CreateTxOptions(
                account_number = str(self.account_number),
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = {'uluna': self.gas_list['uluna']},
                msgs           = [tx_msg],
                sequence       = str(self.sequence),
            )
            
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'too much slippage' in err.message:
                        # Decreate the share out amount by a bit and try again
                        self.share_out_amount       = round(int(self.share_out_amount) * (1 - OSMOSIS_LIQUIDITIY_SPREAD))
                        tx_msg.share_out_min_amount = str(self.share_out_amount)
                        options.msgs                = [tx_msg]
                        print (f'Trying again with new share_out_amount: {self.share_out_amount}')
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

        @params:
            - None

        @return: true/false depending on if the transaction succeeded
        """

        # Reset these values in case this is a re-used object:
        # try:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = '1000000'
        #self.sequence:int       = self.current_wallet.sequence()
        
        if self.getSequenceNumber() == False:
            return False

        # except Exception as err:
        #     print (' 🛑 An unexpected error occurred in the exitSimulate liquidity function:')
        #     print (err)
        #     return False

        # Calculate the two basic components of this request:
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
            self.fee = self.calculateFee(requested_fee, ULUNA, convert_to_ibc=True)

            # Adjust the fee to give it a higher amount
            fee_coin_list:list = self.fee.amount.to_list()
            new_fee_coin:Coin  = Coin.from_data({'amount': int(fee_coin_list[0].amount * OSMOSIS_FEE_MULTIPLIER), 'denom': fee_coin_list[0].denom})
            self.fee.amount    = Coins.from_proto([new_fee_coin])

            return True

        else:
            return False
        
    def getAssetValues(self, assets:dict) -> dict:
        """
        Go through the asset list and retrieve a price for each one.

        @params:
            - assets: a dictionary of the assets we want prices for

        @return: a dictionary of assets and their prices
        """

        prices:dict = {}
        for asset_denom in assets:
            prices[asset_denom] = (assets[asset_denom] / (10 ** get_precision(asset_denom))) * self.wallet.getCoinPrice([asset_denom])[asset_denom]

        return prices
    
    def getOsmosisPool(self, pool_id) -> Pool:
        """
        Get the pool from Osmosis.
        Cache the results so we don't have to do this again.

        @params:
            - assets: a dictionary of the assets we want prices for

        @return: a dictionary of assets and their prices
        """

        pool:Pool = None

        if pool_id in self.cached_pools:
            pool = self.cached_pools[pool_id]
        else:
            # Get the pool details from the network
            retry_count: int = 0

            while retry_count < BUSY_RETRY_COUNT:
                try:
                    pool:Pool = self.terra.pool.osmosis_pool(pool_id)
                    # Cache this so we don't have to check again
                    self.cached_pools[pool_id] = pool
                    break
                except Exception as err:
                    retry_count += 1
                    print (err)
                    print (f'    The LCD is busy - trying again {retry_count}/{BUSY_RETRY_COUNT}')            

        return pool

    def getPoolAssets(self) -> dict:
        """
        Get the assets for the pool, but converted into an actual amount.
        If this pool does not exist in the wallet pool list, then it will return an empty set.

        @params:
            - None

        @return: a dictionary of assets and amounts for the current pool
        """

        asset_list:dict = {}
        if self.pool_id in self.pools:
            # Get the pool details from the network
            pool:Pool = self.getOsmosisPool(self.pool_id)

            if pool is not None:
                # Calculate the two basic components of this request:
                total_shares:int   = int(pool.total_shares.amount)
                share_fraction:int = int(total_shares / self.pools[self.pool_id])

                # Go through each asset and calculate the actual amount the user has
                asset:PoolAsset
                for asset in pool.pool_assets:
                    denom:str     = self.denomTrace(asset.token.denom)
                    
                    # Add this to the list
                    asset_list[denom] = int(asset.token.amount) / share_fraction

        return asset_list
    
    def getPoolSelection(self, question:str, wallet:UserWallet) -> list[int, str]:
        """
        Return a selected pool based on the provided list.

        @params:
            - question: what question are we prompting the user with?
            - wallet: the wallet we will be using for this transaction

        @return: the selected pool and the answer
        """

        label_widths:list = []

        label_widths.append(len('Number'))
        label_widths.append(len('Pool assets'))
        label_widths.append(len('Liquidity'))
        label_widths.append(len('Your balance'))

        # Create a liquidity object
        liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)

        # Now store the basic details
        liquidity_tx.balances     = wallet.balances
        liquidity_tx.pools        = wallet.pools
        liquidity_tx.wallet       = wallet
        liquidity_tx.wallet_denom = wallet.denom

        pool_balances:dict = {}
        pool_list:dict = liquidity_tx.poolList(ULUNA)

        # Find the correct label widths based on the content
        # We'll store the pool balances so we don't have to do this twice
        for pool_id in pool_list:

            asset_label:str = ''

            # Get the longest pool number:
            if len(str(pool_id)) > label_widths[0]:
                label_widths[0] = len(str(pool_id))

            # Get the maximum width of the asset name column
            for asset in pool_list[pool_id]['assets']:
                asset_label += FULL_COIN_LOOKUP[asset] + '/'
                
            asset_label = asset_label[:-1]
            
            if len(asset_label) > label_widths[1]:
                label_widths[1] = len(asset_label)

            # Now get the maximum width of the liquidity column, when properly formatted
            pool_liquidity = "${:,.2f}".format(pool_list[pool_id]['liquidity'])
            if len(pool_liquidity) > label_widths[2]:
                label_widths[2] = len(pool_liquidity)
            
            # Change the pool ID that this liquidity object uses:
            liquidity_tx.pool_id = pool_id
            
            # Get the asset values
            pool_assets:dict  = liquidity_tx.getPoolAssets()
            asset_values:dict = liquidity_tx.getAssetValues(pool_assets)

            # Calculate the pool balance
            total_value:float = 0
            for asset in asset_values:
                total_value += asset_values[asset]
            user_balance:str = "${:,.2f}".format(total_value)

            # Store this so we don't have to do this again
            pool_balances[pool_id] = user_balance

            if len(user_balance) > int(label_widths[3]):
                label_widths[3] = int(user_balance)
            
        padding_str:str   = ' ' * 100
        header_string:str = ''
        if label_widths[1] > len('Number'):
            header_string += ' Number' + padding_str[0:label_widths[0] - len('Number')] + '   |'
        else:
            header_string += ' Number   |'

        if label_widths[1] > len('Pool assets'):
            header_string += ' Pool assets' + padding_str[0:label_widths[1] - len('Pool assets')] + ' |'
        else:
            header_string += ' Pool assets |'

        if label_widths[2] > len('Liquidity'):
            header_string += ' Liquidity ' + padding_str[0:label_widths[2] - len('Liquidity')] + '|'
        else:
            header_string += ' Liquidity |'

        if label_widths[3] > len('Pool balance'):
            header_string += ' Pool balance ' + padding_str[0:label_widths[3] - len('Pool balance')] + '|'
        else:
            header_string += ' Pool balance '

        horizontal_spacer = '-' * len(header_string)

        pool_to_use:int = None
        answer:str      = False

        while True:

            print ('\n' + horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for pool_id in pool_list:

                if pool_to_use == pool_id:
                    glyph = '✅'
                else:
                    glyph = '  '

                if label_widths[1] > len(str(pool_id)):
                    count_str = ' ' + str(pool_id) + padding_str[0:label_widths[0] - len(str(pool_id))]
                else:
                    count_str = ' ' + str(pool_id)
            
                asset_label:str = ''
                for asset in pool_list[pool_id]['assets']:
                    asset_label += FULL_COIN_LOOKUP[asset] + '/'
                asset_label = asset_label[:-1]

                if label_widths[1] > len(asset_label):
                    asset_label_str = asset_label + padding_str[0:label_widths[1] - len(asset_label)]
                else:
                    asset_label_str = asset_label

                pool_liquidity = "${:,.2f}".format(pool_list[pool_id]['liquidity'])
                if label_widths[2] > len(pool_liquidity):
                    liquidity_str = pool_liquidity + padding_str[0:label_widths[2] - len(pool_liquidity)]
                else:
                    liquidity_str = pool_liquidity

                if label_widths[3] > len(pool_balances[pool_id]):
                    pool_balance_str = pool_balances[pool_id] + padding_str[0:label_widths[3] - len(pool_balances[pool_id])]
                else:
                    pool_balance_str = pool_balances[pool_id]

                print (f"{count_str}{glyph} | {asset_label_str} | {liquidity_str} | {pool_balance_str}")
                
            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            # Check if a coin name was provided:
            if answer.isdigit() and int(answer) in pool_list:
                pool_to_use = int(answer)

            if answer == USER_ACTION_CONTINUE:
                if pool_to_use is not None:
                    break
                else:
                    print ('\nPlease select a pool first.\n')

            if answer == USER_ACTION_QUIT:
                break

        return pool_to_use, answer

    def joinPool(self) -> bool:
        """
        Join a pool with the information we have so far.
        If fee is None then it will be a simulation.

        @params:
            - None

        @return: true/false depending on if the transaction succeeded
        """

        try:
            tx:Tx = None

            tx_msg = MsgJoinSwapExternAmountIn(
                pool_id              = self.pool_id,
                sender               = self.sender_address,
                share_out_min_amount = str(int(self.share_out_amount)),
                token_in             = self.token_in_coin
            )

            options = CreateTxOptions(
                account_number = str(self.account_number),
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = self.gas_list,
                msgs           = [tx_msg],
                sequence       = self.sequence
            )
            
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'too much slippage' in err.message:
                        self.share_out_amount       = round(int(self.share_out_amount) * (1 - OSMOSIS_LIQUIDITIY_SPREAD))
                        tx_msg.share_out_min_amount = str(self.share_out_amount)
                        options.msgs                = [tx_msg]
                        print (f'Trying again with new share_out_amount: {self.share_out_amount}')
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

        @params:
            - None

        @return: true/false depending on if the transaction succeeded
        """
        
        # Reset these values in case this is a re-used object:
        #try:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = 'auto'
        #self.sequence:int       = self.current_wallet.sequence()
        
        if self.getSequenceNumber() == False:
            return False
                
        #except Exception as err:
        #    print (' 🛑 An unexpected error occurred in the joinSimulate liquidity function:')
        #    print (err)
        #    return False
        
        # We are only allowing for LUNC deposits into liquidity pools, but this could technically be any denom
        liquidity_denom:str = self.IBCfromDenom(self.source_channel, ULUNA)
        
        # This is the amount we are adding to the pool
        token_in_coin:Coin = Coin(liquidity_denom, int(float(self.amount_in)))

        # This is the final amount we expect to get
        self.share_out_amount:int = self.calcShareOutAmount(token_in_coin)

        if self.share_out_amount > 0:
            # Reduce it by the spread amount
            self.share_out_amount = round(self.share_out_amount * (1 - self.max_spread))

            # This is the amount we are contributing. It will be resized by the pool depending on the share split of each asset
            token_in_coin      = {'amount': int(float(self.amount_in)), 'denom': liquidity_denom}
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

                # Adjust the fee to give it a higher amount
                fee_coin_list:list = self.fee.amount.to_list()
                new_fee_coin:Coin  = Coin.from_data({'amount': int(fee_coin_list[0].amount * OSMOSIS_FEE_MULTIPLIER), 'denom': fee_coin_list[0].denom})
                self.fee.amount    = Coins.from_proto([new_fee_coin])

                return True
            else:
                return False
        else:
            return False
        
    def poolList(self, liquidity_asset_denom:str) -> dict:
        """
        Get the entire list of pools that match the supplied token as a liquidity asset

        @params:
            - liquidity_asset_denom: the denom we want pools for

        @return: a dict with the pools and the relevant details
        """

        all_pools:str = "SELECT pool_id, token_readable_denom FROM asset WHERE pool_id IN (SELECT pool_id FROM asset WHERE token_readable_denom = ?);"
        
        # Open the database and make the query
        conn:Connection = sqlite3.connect(DB_FILE_NAME)
        cursor:Cursor   = conn.execute(all_pools, [liquidity_asset_denom])
        rows:list       = cursor.fetchall()

        # Go through the database results and get the live liquidity
        pools:dict = {}
        
        for row in rows:
            if row[0] not in pools:
                # If this pool is not in the list, then add it
                pool:Pool = self.getOsmosisPool(row[0])

                if pool is not None:
                    # Based on the assets, get the value of this pool:
                    pool_balance:float = 0
                    valid_pool:bool    = True

                    # To make things faster, we'll query all the denoms in one go:
                    cg_denom_list:list = []

                    pool_asset:PoolAsset
                    for pool_asset in pool.pool_assets:
                        readable_denom:str = self.denomTrace(pool_asset.token.denom)
                        
                        if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
                            readable_denom = 'uluna2'

                        cg_denom_list.append(readable_denom)

                    prices:dict = self.wallet.getCoinPrice(cg_denom_list)

                    # Now we can calculate the balance for each pool
                    for pool_asset in pool.pool_assets:
                        readable_denom:str = self.denomTrace(pool_asset.token.denom)
                        
                        if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
                            readable_denom = 'uluna2'

                        if readable_denom not in CHAIN_DATA:
                            valid_pool = False
                            break

                        asset_amount:float = int(pool_asset.token.amount) / (10 ** get_precision(readable_denom))

                        price:float   = prices[readable_denom]
                        pool_balance += (price * asset_amount)

                    if valid_pool == True:
                        pools[int(row[0])] = {'assets': [], 'liquidity': pool_balance}
                
            # Otherwise, add this new asset to the existing pool
            if int(row[0]) in pools:
                pools[int(row[0])]['assets'].append(row[1])

        return pools
    
    def tokenOutMins(self) -> dict:
        """
        Given the user-supplied withdrawal amount, what does this translate into for coins in the pool?
        The self.amount_out needs to be a percentage.

        This is used for exiting a pool.

        @params:
            - None

        @return: a list with the coins that this transaction will return
        """

        token_out_list:list = []

        # Get the pool details from the network
        pool:Pool = self.getOsmosisPool(self.pool_id)
        
        if pool is not None:
            # Step 1: calculate the fraction that the user has of the entire pool:
            total_shares:int   = int(pool.total_shares.amount)
            share_fraction:int = int(total_shares / self.pools[self.pool_id])
            
            # Step 2: now get the actual amount of each asset across this pool:
            asset:PoolAsset
            # Go through each asset and add it to the list
            for asset in pool.pool_assets:

                # Get the amount of this asset as percentage of the total amount
                asset_amount:float = int(asset.token.amount) / share_fraction

                # This is the actual amount we're removing, minus the pool tax
                user_amount:int = int(int(asset_amount * self.amount_out) * (1 - OSMOSIS_POOL_TAX))
                
                token_out_list.append(Coin.from_data({'amount': user_amount, 'denom': asset.token.denom}))

        return token_out_list
    
def join_liquidity_pool(wallet:UserWallet, pool_id:int, amount_in:int, silent_mode:bool = False) -> TransactionResult:
    """
    A wrapper function for workflows and wallet management.

    This lets the user join a liquidity pool on Osmosis.
    
    The wrapper function adds any error messages depending on the results that got returned.
    
    @params:
      - wallet: a fully complete wallet object
      - pool_id: the pool ID that we want to join
      - amount_in: the amount (LUNC) that we are joining with
      - prompt_user: do we want to pause for user confirmation?

    @return: a TransactionResult object
    """

    transaction_result:TransactionResult = TransactionResult()

    liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)
    liquidity_tx.amount_in      = amount_in
    liquidity_tx.balances       = wallet.balances
    liquidity_tx.pool_id        = pool_id
    liquidity_tx.pools          = wallet.pools
    liquidity_tx.sender_address = wallet.address
    liquidity_tx.silent_mode    = silent_mode
    liquidity_tx.source_channel = CHAIN_DATA[wallet.denom]['ibc_channels'][ULUNA]
    liquidity_tx.wallet         = wallet
    liquidity_tx.wallet_denom   = wallet.denom

    # Simulate it
    liquidity_result:bool = liquidity_tx.joinSimulate()
    
    if liquidity_result == True:

        if silent_mode == False:
            print (liquidity_tx.readableFee())

            user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

            if user_choice == False:
                print (' 🛑 Exiting...\n')
                exit()
        
        # Now we know what the fee is, we can do it again and finalise it
        liquidity_result:bool = liquidity_tx.joinPool()
            
        if liquidity_result == True:
            transaction_result:TransactionResult = liquidity_tx.broadcast()

            # if liquidity_tx.broadcast_result is not None and liquidity_tx.broadcast_result.code == 32:
            #     while True:
            #         print (' 🛎️  Boosting sequence number and trying again...')

            #         liquidity_tx.sequence = liquidity_tx.sequence + 1
                    
            #         liquidity_tx.joinSimulate()
            #         liquidity_tx.joinPool()
                    
            #         liquidity_tx.broadcast()

            #         if liquidity_tx is None:
            #             break

            #         # Code 32 = account sequence mismatch
            #         if liquidity_tx.broadcast_result.code != 32:
            #             break

            if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error():
                transaction_result.is_error = True
                if transaction_result.broadcast_result is None:
                    transaction_result.message = f' 🛎️  The liquidity transaction failed, no broadcast object was returned.'
                else:
                    transaction_result.message = f' 🛎️  The liquidity transaction failed, an error occurred.'
                    if transaction_result.broadcast_result.raw_log is not None:
                        transaction_result.message = f' 🛎️  The liquidity transaction on {wallet.name} failed, an error occurred.'
                        transaction_result.code    = f' 🛎️  Error code {transaction_result.broadcast_result.code}'
                        transaction_result.log     = f' 🛎️  {transaction_result.broadcast_result.raw_log}'
                    else:
                        transaction_result.message = f' 🛎️  No broadcast log on {wallet.name} was available.'  

        else:
            transaction_result.message  = ' 🛎️  The liquidity transaction could not be completed'
            transaction_result.is_error = True

    # Store the delegated amount for display purposes
    transaction_result.transacted_amount = wallet.formatUluna(amount_in, ULUNA, True)
    transaction_result.label             = 'Liquidity addition'
    transaction_result.wallet_denom      = wallet.denom

    return transaction_result

def exit_liquidity_pool(wallet:UserWallet, pool_id:int, amount_out:float, silent_mode:bool = False) -> TransactionResult:
    """
    A wrapper function for workflows and wallet management.

    This lets the user exit a liquidity pool on Osmosis.
    
    The wrapper function adds any error messages depending on the results that got returned.
    
    @params:
      - wallet: a fully complete wallet object
      - pool_id: the pool ID that we want to join
      - amount_out: the amount (percentage) that we are withdrawing
      - prompt_user: do we want to pause for user confirmation?

    @return: a TransactionResult object
    """

    transaction_result:TransactionResult = TransactionResult()

    liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)

    # Populate it with required details:
    liquidity_tx.amount_out     = amount_out
    liquidity_tx.balances       = wallet.balances
    liquidity_tx.pool_id        = pool_id
    liquidity_tx.pools          = wallet.pools
    liquidity_tx.sender_address = wallet.address
    liquidity_tx.silent_mode    = silent_mode
    liquidity_tx.source_channel = CHAIN_DATA[wallet.denom]['ibc_channels'][ULUNA]
    liquidity_tx.wallet         = wallet
    liquidity_tx.wallet_denom   = wallet.denom

    # Simulate it
    liquidity_result:bool = liquidity_tx.exitSimulate()
    
    if liquidity_result == True:
        if silent_mode == False:
            print (liquidity_tx.readableFee())

            user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

            if user_choice == False:
                print (' 🛑 Exiting...\n')
                exit()
        
        # Now we know what the fee is, we can do it again and finalise it
        liquidity_result:bool = liquidity_tx.exitPool()
            
        if liquidity_result == True:
            
            transaction_result:TransactionResult = liquidity_tx.broadcast()

            if liquidity_tx.broadcast_result is not None and transaction_result.broadcast_result is not None and transaction_result.broadcast_result.raw_log == 'Status 429 - Too Many Requests':
                retry_count = 0
                while True:
                    retry_count += 1
                    
                    if retry_count <= BUSY_RETRY_COUNT:
                        if silent_mode == False:
                            print (f'    {transaction_result.broadcast_result.raw_log}, attempt {retry_count}/{BUSY_RETRY_COUNT}')
                        time.sleep(1)
                    else:
                        break
                    
            #     while True:
            #         print (' 🛎️  Boosting sequence number and trying again...')

            #         liquidity_tx.sequence = liquidity_tx.sequence + 1
                    
            #         liquidity_tx.exitSimulate()
            #         liquidity_tx.exitPool()

            #         transaction_result:TransactionResult = liquidity_tx.broadcast()

            #         # Code 32 = account sequence mismatch
            #         if liquidity_tx.broadcast_result.code != 32:
            #             break

            if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error():
                transaction_result.is_error = True
                if transaction_result.broadcast_result is None:
                    transaction_result.message = f' 🛎️  The liquidity transaction failed, no broadcast object was returned.'
                else:
                    transaction_result.message = f' 🛎️  The liquidity transaction failed, an error occurred.'
                    if transaction_result.broadcast_result.raw_log is not None:
                        transaction_result.message = f' 🛎️  The liquidity transaction on {wallet.name} failed, an error occurred.'
                        transaction_result.code    = f' 🛎️  Error code {transaction_result.broadcast_result.code}'
                        transaction_result.log     = f' 🛎️  {transaction_result.broadcast_result.raw_log}'
                    else:
                        transaction_result.message = f' 🛎️  No broadcast log on {wallet.name} was available.'
            
        else:
            transaction_result.message  = f' 🛎️  The liquidity transaction could not be completed'
            transaction_result.is_error = True

    transaction_result.wallet_denom = wallet.denom

    return transaction_result