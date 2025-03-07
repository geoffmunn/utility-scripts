#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from __future__ import annotations

import base64
import json
import math
import sqlite3

from sqlite3 import Cursor, Connection

from constants.constants import (
    CHAIN_DATA,
    DB_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT_OSMOSIS,
    GAS_ADJUSTMENT_SWAPS,
    GRDX,
    GRDX_SMART_CONTRACT_ADDRESS,
    MAX_SPREAD,
    MIN_OSMO_GAS,
    NON_ULUNA_COINS,
    OFFCHAIN_COINS,
    OSMOSIS_FEE_MULTIPLIER,
    TERRAPORT_SWAP_ADDRESS,
    TERRASWAP_GRDX_TO_LUNC_ADDRESS,
    TERRASWAP_UKRW_TO_ULUNA_ADDRESS,
    TERRASWAP_ULUNA_TO_UUSD_ADDRESS,
    TERRASWAP_UUSD_TO_ULUNA_ADDRESS,
    UBASE,
    UCANDY,
    UCREMAT,
    UELON,
    UKRW,
    ULENNY,
    ULUNA,
    UOSMO,
    URAKOFF,
    UUSD
)

from classes.common import (
    divide_raw_balance,
    get_precision,
    get_user_choice,
    multiply_raw_balance
)

from classes.terra_instance import TerraInstance    
from classes.transaction_core import TransactionCore, TransactionResult

from terra_classic_sdk.client.lcd.api.tx import CreateTxOptions, Tx
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.market.msgs import MsgSwap
from terra_classic_sdk.core.osmosis import MsgSwapExactAmountIn, Pool
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.core.wasm.msgs import MsgExecuteContract
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey
        
class SwapTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(SwapTransaction, self).__init__(*args, **kwargs)

        self.belief_price           = None
        self.contract               = None
        self.fee_deductables:float  = None
        self.gas_limit:str          = 'auto'
        self.max_spread:float       = MAX_SPREAD
        self.min_out:int            = None
        self.osmosis_pools:dict     = {}
        self.recipient_address:str  = ''
        self.recipient_prefix:str   = ''
        self.sender_address:str     = ''
        self.sender_prefix:str      = ''
        self.swap_amount:int        = None
        self.swap_denom:str         = None
        self.swap_request_denom:str = None
        self.tax:float              = None
        self.use_market_swap:bool   = False

    def beliefPrice(self) -> float:
        """
        Figure out the belief price for this swap.
        
        @params:
            - None

        @return: a price that we use to calculate the swap amount with
        """
            
        belief_price:float = 0

        if self.contract is not None:
            try:
                # Contract swaps must be on the columbus-5 chain
                #if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
                contract_swaps:list = [GRDX, ULUNA, UKRW, UUSD]
                if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:
                    parts:dict = {}
                    # Get the pool details
                    result = self.terra.wasm.contract_query(self.contract, {"pool": {}})
                    if 'native_token' in result['assets'][0]['info']:
                        parts[result['assets'][0]['info']['native_token']['denom']] = int(result['assets'][0]['amount'])
                    else:
                        # GRDX:
                        if result['assets'][0]['info']['token']['contract_addr'] == TERRASWAP_GRDX_TO_LUNC_ADDRESS:
                            parts[GRDX] = int(result['assets'][0]['amount'])
                        
                    parts[result['assets'][1]['info']['native_token']['denom']] = int(result['assets'][1]['amount'])

                    # if self.swap_denom == GRDX and self.swap_request_denom == ULUNA:
                    #     belief_price:float = parts[self.swap_request_denom] / parts[self.swap_denom]
                    # else:
                    #     # Everything except GRDX -> ULUNA goes here:
                    #     belief_price:float = parts[self.swap_denom] / parts[self.swap_request_denom]
                    if self.swap_denom == ULUNA:
                        belief_price:float = parts[self.swap_denom] / parts[self.swap_request_denom]
                    else:
                        belief_price:float = parts[self.swap_request_denom] / parts[self.swap_denom]
                else:
                    # UBASE does something different
                    if self.swap_denom == UBASE or self.swap_request_denom == UBASE:
                        result           = self.terra.wasm.contract_query(self.contract, {"curve_info": {}})
                        spot_price:float = float(result['spot_price'])
                        if self.swap_request_denom == UBASE:
                            belief_price:float = divide_raw_balance((spot_price * 1.053), UBASE)
                        else:
                            belief_price:float = divide_raw_balance((spot_price - (spot_price * 0.048)), UBASE)
                    elif self.swap_denom in NON_ULUNA_COINS.values() or self.swap_request_denom in NON_ULUNA_COINS.values():
                        # These are all Terraport swaps. Anything else must have been done prior to this point
                        if self.swap_denom in NON_ULUNA_COINS.values():
                            contract_address = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_denom)])
                            
                        elif self.swap_request_denom in NON_ULUNA_COINS.values():
                            contract_address = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_request_denom)])
                            
                        slip_rate: int = 1
                        if self.swap_denom == ULUNA:
                            result = self.terra.wasm.contract_query(TERRAPORT_SWAP_ADDRESS, {"simulate_swap_operations":{"offer_amount":"1000000","operations":[{"terra_port":{"offer_asset_info":{"native_token":{"denom":"uluna"}},"ask_asset_info":{"token":{"contract_addr":contract_address}}}}]}})   
                        else:
                            slip_rate = 0.95
                            result = self.terra.wasm.contract_query(TERRAPORT_SWAP_ADDRESS, {"reverse_simulate_swap_operations":{"ask_amount":"1000000","operations":[{"terra_port":{"offer_asset_info":{"native_token":{"denom":"uluna"}},"ask_asset_info":{"token":{"contract_addr":contract_address}}}}]}})

                        belief_price:float = float(result['amount']) / (10 ** get_precision(ULUNA))

                        belief_price = belief_price * slip_rate
                    
            except Exception as err:
                return None
           
        self.belief_price = round(belief_price, 18)

        return self.belief_price
    
    def create(self, seed:str, denom:str = 'uluna') -> SwapTransaction:
        """
        Create a swap object and set it up with the provided details.
        
        @params:
            - seed: the wallet seed so we can create the wallet
            - denom: what denomination are we swapping from?

        @return: self
        """

        # Create the terra instance
        self.terra = TerraInstance().create(denom)

        # Create the wallet based on the calculated key
        prefix              = CHAIN_DATA[denom]['bech32_prefix']
        current_wallet_key  = MnemonicKey(mnemonic = seed, prefix = prefix)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        # if self.gas_list is None:
        #     return False
        # else:
        return self
    
    def marketSimulate(self) -> bool:
        """
        Simulate a market swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        
        @params:
            - None

        @return: bool
        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.transaction    = None
        #self.sequence       = self.current_wallet.sequence()

        if self.getSequenceNumber() == False:
            return False

        # Bump up the gas adjustment - it needs to be higher for swaps it turns out
        self.terra.gas_adjustment = float(GAS_ADJUSTMENT_SWAPS)

        #Perform the swap as a simulation, with no fee details
        self.marketSwap()
        
        # Get the transaction result
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            self.fee = self.calculateFee(requested_fee)

            return True
        else:
            return False

    def marketSwap(self) -> bool:
        """
        Make a market swap with the information we have so far.
        If fee is None then it will be a simulation.
        
        @params:
            - None

        @return: bool
        """

        try:
            tx:Tx = None

            tx_msg = MsgSwap(
                trader     = self.current_wallet.key.acc_address,
                offer_coin = Coin(self.swap_denom, self.swap_amount),
                ask_denom  = self.swap_request_denom
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
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print ('An unexpected error occurred in the market swap function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the market swap function:')
                    print (err)
                    break

            self.transaction = tx

            return True
        except Exception as err:
            print (' 🛑 An unexpected error occurred in the market swap function:')
            print (err)
            return False
    
    def getRoute(self, denom_in:str, denom_out:str, initial_amount:float) -> dict:
        """
        Get the recommended route for this this swap combination.
        We will pick the lowest fee while still having a good level of liquidity.
        
        @params:
            - denom_in: the denomination we are starting with
            - denom_out: the denomination we want
            - initial_amount: the amount we want to swap

        @return: a dictionary containing the recommended route details
        """

        path_query:str      = "SELECT pool.pool_id, token_denom, token_readable_denom, pool_swap_fee FROM pool INNER JOIN asset ON pool.pool_id=asset.pool_id WHERE pool.pool_id IN (SELECT pool_id FROM asset WHERE token_readable_denom = ?) AND token_readable_denom=? ORDER BY pool_swap_fee ASC;"
        liquidity_query:str = "SELECT token_readable_denom, token_amount FROM asset WHERE pool_id = ?;"

        conn:Connection = sqlite3.connect(DB_FILE_NAME)
        cursor:Cursor   = conn.execute(path_query, [denom_in, denom_out])
        rows:list       = cursor.fetchall()

        # This is the base option we will be returning
        current_option:dict = {'pool_id': None, 'denom': None, 'swap_fee': 1}

        self.cachePrices()

        # Go and check for single pool swaps. The origin is swap_denom and the exit is swap_request_denom
        for row in rows:
            cursor.execute(liquidity_query, (row[0],))

            origin_liquidity:list = []
            exit_liquidity:list   = []
            for row2 in cursor.fetchall():
                if row2[0] == denom_in:
                    origin_liquidity:list = row2
                    
                if row2[0] == denom_out:
                    exit_liquidity:list        = row2
                    exit_liquidity_value:float = divide_raw_balance(exit_liquidity[1], denom_out) * float(self.prices[CHAIN_DATA[denom_out]['coingecko_id']]['usd'])

            # Now we have the origin and exit options, check that the liquidity amounts are sufficient
            swap_amount:float = initial_amount
            if origin_liquidity[1] > float(swap_amount * 10) and exit_liquidity_value >= 100:
                prices:json       = self.getPrices(denom_in, denom_out)
                swap_amount:float = (initial_amount * float(prices['from']) / float(prices['to']))

                swap_amount = multiply_raw_balance(divide_raw_balance(swap_amount, denom_in), denom_out)
                if exit_liquidity[1] > float(swap_amount * 10):
                    if row[3] < current_option['swap_fee']:
                        current_option['pool_id']         = row[0]
                        current_option['token_out_denom'] = row[1]
                        current_option['denom']           = row[2]
                        current_option['swap_fee']        = row[3]
                        current_option['swap_amount']     = swap_amount
                
        return current_option
    
    def isOffChainSwap(self) -> bool:
        """
        Figure out if this swap is based on off-chain (non-terra) coins.
        You can swap from lunc to osmo from columbus-5, and swap lunc to wBTC on osmosis-1
        
        @params:
            - None

        @return: true or false if this is offChain or not
        """

        if self.swap_request_denom in OFFCHAIN_COINS or self.swap_denom in OFFCHAIN_COINS:
            is_offchain_swap:bool = True
        else:
            is_offchain_swap:bool = False

        # Overrides for some instances:
        if self.swap_denom == ULUNA and self.swap_request_denom == UUSD and self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
            is_offchain_swap = False

        if self.swap_denom == UUSD and self.swap_request_denom == ULUNA and self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
            is_offchain_swap = False

        return is_offchain_swap
    
    def logTrade(self, wallet, transaction_result:TransactionResult, log_trade_params:dict) -> int:
        """
        Put the details of this swap into the database.

        @params:
            - wallet: the current wallet that this trade is applied to
            - transaction_result: the result we're getting trade details from

        @return: the ID of the database row we've added
        """

        if transaction_result.is_error == False:

            insert_trade_query:str = "INSERT INTO trades (wallet_name, coin_from, amount_from, price_from, coin_to, amount_to, price_to, fees, exit_profit, exit_loss, tx_hash, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,'OPEN');"

            wallet_name:str = wallet.name
            coin_from:str   = self.swap_denom
            amount_from:int = self.swap_amount
            tx_hash:str     = transaction_result.broadcast_result.txhash

            if coin_from not in NON_ULUNA_COINS.values():
                price_from:float = float(wallet.getCoinPrice([coin_from])[coin_from])
            else:
                price_from:float = 0
                
            coin_to:str = self.swap_request_denom

            # Some coins won't return a price because they're not on coingecko:
            if coin_to not in NON_ULUNA_COINS.values():
                price_to:float = float(wallet.getCoinPrice([coin_to])[coin_to])
            else:
                price_to:float = 0

            # Get the received coin from the results
            received_coin:Coin
            amount_to:int = 0

            if transaction_result.result_received is not None:
                for received_coin in transaction_result.result_received:
                    readable_denom = wallet.denomTrace(received_coin.denom)

                    if readable_denom in NON_ULUNA_COINS:
                        readable_denom = NON_ULUNA_COINS[readable_denom]

                    if readable_denom == coin_to:
                        amount_to:int = received_coin.amount
            else:
                print ('no result received:')
                print (transaction_result)
                
            fees:dict = {}

            fee_coins:Coins = self.fee.amount
            for fee_coin in fee_coins.to_list():

                amount:float   = divide_raw_balance(fee_coin.amount, fee_coin.denom)
                amount_str:str = ("%.6f" % (amount)).rstrip('0').rstrip('.')

                # Get the readable denom if this is an IBC token
                denom:str = self.denomTrace(fee_coin.denom)

                if denom in FULL_COIN_LOOKUP:
                    denom = FULL_COIN_LOOKUP[denom]
                    
                fees[denom] = amount_str
            
            if 'exit_profit' in log_trade_params and 'exit_loss' in log_trade_params:
                exit_profit:float = log_trade_params['exit_profit']
                exit_loss:float   = -abs(float(log_trade_params['exit_loss']))

                conn   = sqlite3.connect(DB_FILE_NAME)
                cursor = conn.cursor()
                cursor.execute(insert_trade_query, [wallet_name, coin_from, amount_from, price_from, coin_to, amount_to, price_to, json.dumps(fees), exit_profit, exit_loss, tx_hash])
                
                new_id = cursor.lastrowid

                conn.commit()

                return new_id
            else:
                return 0
            
        else:
            return 0

    def offChainSimulate(self) -> bool:
        """
        Simulate an offchain swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        
        @params:
            - None

        @return: bool
        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.prices         = None
        self.transaction    = None
        #self.sequence       = self.current_wallet.sequence()
        if self.getSequenceNumber() == False:
            return False
        
        current_option = self.getRoute(self.swap_denom, self.swap_request_denom, self.swap_amount)

        if current_option['pool_id'] is None:
            # Now we have to try OSMO jumps
            current_option1 = self.getRoute(self.swap_denom, UOSMO, self.swap_amount)
            current_option2 = self.getRoute(UOSMO, self.swap_request_denom, current_option1['swap_amount'])

            if current_option2['pool_id'] is None:
                current_option1 = self.getRoute(self.swap_denom, UUSD, self.swap_amount)
                current_option2 = self.getRoute(UUSD, self.swap_request_denom, current_option1['swap_amount'])

                if current_option2['pool_id'] is None: 
                    print (' 🛑 No pool could be found that supported this swap pair.')
                    print ('\n 🛑 Exiting...\n')
                    exit()

            routes = [
                {
                    "pool_id": str(current_option1['pool_id']),
                    "token_out_denom": current_option1['token_out_denom'],
                    'swap_fee': float(current_option1['swap_fee'])
                },
                {
                    "pool_id": str(current_option2['pool_id']),
                    "token_out_denom": current_option2['token_out_denom'],
                    'swap_fee': float(current_option2['swap_fee'])
                },
            ]
        else:
            # We have a candidate pool to use in a single transfer

            routes = [{
                'pool_id': str(current_option['pool_id']),
                'token_out_denom': current_option['token_out_denom'],
                'swap_fee': float(current_option['swap_fee'])
            }]

        self.ibc_routes = routes

        max_spread:float = self.max_spread
        
        # Figure out the minimum expected coins for this swap:
        fee_multiplier:float = OSMOSIS_FEE_MULTIPLIER
        
        current_amount:int = self.swap_amount
        current_denom:str  = self.swap_denom

        # For each route:
        # Step 1: convert the current coin to the base price
        # Step 2: deduct swap fee
        # Step 3: deduct slippage
        for route in self.ibc_routes:

            # Get the token we want to swap to (what we expect to end up with for this route)
            #print ('we need the token out denom from this route:', route)
            token_out_denom = route['token_out_denom']
            token_out_denom = self.denomTrace(token_out_denom)
            
            #print ('token out denom:', token_out_denom)
            # Get the prices for the current denom and the output denom
            coin_prices:json = self.getPrices(current_denom, token_out_denom)
            
            # Get the initial base price (no fee deductions)
            base_amount = (current_amount * coin_prices['from']) / coin_prices['to']

            #step 1: run price conversion
            #step 2: divide by $eth precision
            #Step 3: multiple by Cosmo precision
            #step 4: round to cosmo precision

            from_precision:int   = get_precision(current_denom)
            target_precision:int = get_precision(token_out_denom)

            if from_precision != target_precision:
                base_amount:float = divide_raw_balance(base_amount, current_denom)
            
            # Only multiply if the token out demo has a higher precision
            if target_precision < from_precision:
                base_amount:float = multiply_raw_balance(base_amount, token_out_denom)

            # deduct the swap fee:
            #print ('pool:', self.osmosisPoolByID(route['pool_id']))
            try:
                swap_fee:float = float(self.osmosisPoolByID(route['pool_id']).pool_params.swap_fee)
            except Exception as err:
                # Something went wrong, we'll abandon this attempt
                return False
            
            #print ('swap fee:', swap_fee)
            # Deduct the swap fee
            base_amount_minus_swap_fee:float = float(base_amount) * (1 - swap_fee)

            # Deduct the slippage
            base_amount_minus_swap_fee = float(base_amount_minus_swap_fee * (1 - max_spread))

            # Now we have the new denom and the new value
            prev_denom:str       = current_denom
            current_denom:str    = token_out_denom        
            current_amount:float = base_amount_minus_swap_fee
            precision:int        = get_precision(token_out_denom)

        from_precision:int   = get_precision(prev_denom)
        target_precision:int = get_precision(current_denom)
                    
        if target_precision > from_precision:
            current_amount = multiply_raw_balance(current_amount, current_denom)
            
        # Finish off the final value and store it:
        precision:int  = get_precision(current_denom)
        current_amount = round(current_amount, precision)
        self.min_out   = math.floor(current_amount)
        
        self.offChainSwap()

        # Get the transaction result
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # Get the fee details, but we'll need to make some modifications
            self.fee:Fee  = self.calculateFee(requested_fee)
            fee_coin:Coin = self.fee.amount.to_list()[0]
            
            # We'll take the returned fee and use that as the gas limit
            self.gas_limit = self.fee.gas_limit
            
            # Now calculate the actual fee
            #(0.007264 * 0.424455) / 0.00006641 = 43.7972496474
            min_uosmo_gas:float = MIN_OSMO_GAS
            uosmo_fee:float     = min_uosmo_gas * float(self.gas_limit)

            # Calculate the LUNC fee
            # (osmosis amount * osmosis unit cost) / lunc price
            # For the calculation to work, the 'to' value always needs to be the usomo price

            from_denom:str = UOSMO
            to_denom:str   = ULUNA

            # Get the current prices
            prices:json = self.getPrices(from_denom, to_denom)
            
            # OSMO -> LUNC:
            fee_amount:float = float((uosmo_fee * prices['from']) / prices['to'])
            fee_amount       = fee_amount * fee_multiplier
            fee_denom:str    = fee_coin.denom
            fee_denom:str    = 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0'

            # Create the coin object
            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            # This will be used by the swap function next time we call it
            self.fee.amount = new_coin

            # If the fee denom is the same as what we're swapping, then we need to deduct this
            if fee_coin.denom == self.swap_denom:
                self.fee_deductables = int(fee_amount)
                
            return True
        else:
            return False

    def offChainSwap(self) -> bool:
        """
        Make an offchain swap with the information we have so far.
        Currently we only support MsgSwapExactAmountIn via the GAMM module.

        If fee is None then it will be a simulation.
        
        @params:
            - None

        @return: bool
        """

        #print ('old swap amount: ', self.swap_amount)

        if self.fee_deductables is not None:
            if int(self.swap_amount + self.fee_deductables) > int(self.balances[self.swap_denom]):
                self.swap_amount = int(self.swap_amount - self.fee_deductables)
            
        try:
            channel_id = CHAIN_DATA[self.wallet_denom]['ibc_channels'][self.swap_denom]
            
            if self.swap_denom != UOSMO:
                coin_denom = self.IBCfromDenom(channel_id, self.swap_denom)
            else:
                coin_denom = UOSMO

            token_in:Coin = Coin(coin_denom, self.swap_amount)

            tx_msg = MsgSwapExactAmountIn(
                sender               = self.sender_address,
                routes               = self.ibc_routes,
                token_in             = str(token_in),
                token_out_min_amount = str(self.min_out)
            )

            options = CreateTxOptions(
                account_number = self.account_number,
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_adjustment = GAS_ADJUSTMENT_OSMOSIS,
                msgs           = [tx_msg],
                sequence       = self.sequence
            )

            tx:Tx = self.current_wallet.create_and_sign_tx(options)
            
            self.transaction = tx

            return True
        except Exception as err:
            print (' 🛑 An unexpected error occurred in the off-chain swap function:')
            print (err)
            return False

    def osmosisPoolByID(self, pool_id:int) -> Pool:
        """
        Get the pool details for the provided pool id.
        Save them in memory so we can access individual details and discover the best paths.

        @params:
            - pool_id: the Pool ID that we want to get info on

        @return: a Pool object matching the provided ID
        """

        result:Pool = None

        if pool_id not in self.osmosis_pools:
            # Get this pool:
            try:
                pool:Pool = self.terra.pool.osmosis_pool(pool_id)
                # Save it in the publicly available object:
                self.osmosis_pools[pool.id] = pool

                # Return this result
                result = pool 
            except Exception as err:
                print (' 🛑 An unexpected error occurred in the osmosisPoolByID swap function:')
                print (err)
        else:
            result = self.osmosis_pools[pool_id]

        return result

    
    def setContract(self) -> bool:
        """
        Depending on what the 'from' denom is and the 'to' denom, change the contract endpoint.

        If this is going to use a market swap, then we don't need a contract.

        @params:
            - None

        @return: True/False on can we use the market swap function?
        """
        
        use_market_swap:bool = True
        self.contract        = None
        contract_swaps:list  = list(NON_ULUNA_COINS.values()) + [ULUNA, UKRW, UUSD]

        if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:
            use_market_swap = False

            if self.swap_denom == ULUNA and self.swap_request_denom != ULUNA:
                if self.swap_request_denom == UUSD:
                    self.contract = TERRASWAP_ULUNA_TO_UUSD_ADDRESS
                elif self.swap_request_denom == UKRW:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                else:
                    self.contract = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_request_denom)])

            if self.swap_denom == UUSD:
                if self.swap_request_denom == ULUNA:
                    self.contract = TERRASWAP_UUSD_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = None
                    use_market_swap = True

            if self.swap_denom == UKRW:
                if self.swap_request_denom == ULUNA:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UUSD:
                    self.contract = None
                    use_market_swap = True

            if self.swap_denom in NON_ULUNA_COINS.values():
                if self.swap_request_denom == ULUNA:
                    self.contract = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_denom)])

        self.use_market_swap = use_market_swap

        return use_market_swap
      
    def simulate(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        THIS IS ONLY FOR USTC <-> LUNC SWAPS
        The fee details are saved so the actual delegation will work.

        Outputs:
            - self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
            - self.tax - the tax component
            - self.fee_deductables - the amount we need to deduct off the transferred amount

        @params:
            - None

        @return: bool
        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.prices         = None
        self.transaction    = None
        #self.sequence       = self.current_wallet.sequence()

        if self.getSequenceNumber() == False:
            return False
        
        self.belief_price   = self.beliefPrice()
        
        # Perform the swap as a simulation, with no fee details
        self.swap()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:

            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee, ULUNA)

            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            # Calculate the tax portion 
            # if self.swap_denom in NON_ULUNA_COINS.values():
            #     self.tax = None
            # else:
            #     self.tax = int(math.ceil(self.swap_amount * float(self.tax_rate)))
            self.tax = 0

            # Build a fee object
            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            # if fee_denom == ULUNA and self.swap_denom == ULUNA:
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            # if  self.swap_denom in NON_ULUNA_COINS.values():
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
            # else:
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.swap_denom, int(self.tax))})

            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.swap_denom:
                # self.fee_deductables = int(fee_amount + self.tax)
                self.fee_deductables = int(fee_amount)

            # elif fee_denom == ULUNA and self.swap_denom == UUSD:
            #     self.fee_deductables = int(self.tax)
            # elif fee_denom == ULUNA and self.swap_denom in NON_ULUNA_COINS.values():
            #     self.fee_deductables = 0
            # else:
            #     if self.tax is not None:
            #         self.fee_deductables = int(self.tax * 2)
            #     else:
            #         self.fee_deductables = None

            return True
        else:
            return False
    
    def swap(self) -> bool:
        """
        Make a swap with the information we have so far.
        If fee is None then it will be a simulation.

        @params:
            - None

        @return: bool
        """

        non_uluna_coins:list = [UCANDY, UCREMAT, UELON, ULENNY, URAKOFF]

        if self.fee_deductables is not None:
            if int(self.swap_amount + self.fee_deductables) > int(self.balances[self.swap_denom]):
                self.swap_amount = int(self.swap_amount - self.fee_deductables)
            
        if self.belief_price is not None:
            
            if self.fee is not None:
                fee_amount:list = self.fee.amount.to_list()
                fee_coin:Coin   = fee_amount[0]
                fee_denom:str   = fee_coin.denom
            else:
                fee_denom:str   = ULUNA

            if fee_denom in self.balances:
                swap_amount = self.swap_amount

                #if self.tax is not None:
                if self.fee_deductables is not None:
                    if int(swap_amount + self.fee_deductables) > int(self.balances[self.swap_denom]):
                        swap_amount = int(swap_amount - self.fee_deductables)

                if self.swap_denom == ULUNA and self.swap_request_denom == UBASE:
                    # We are swapping LUNC for BASE
                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = self.contract,
                        msg      = {
                            "buy": {"affiliate": ""}
                        },
                        coins    = Coins(str(swap_amount) + self.swap_denom)
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 500000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom == ULUNA and self.swap_request_denom in non_uluna_coins:
                    # We are swapping ULUNA to a Terraport contract
                    contract_address = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_request_denom)])

                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = TERRAPORT_SWAP_ADDRESS,
                        msg =
                            {
                            "execute_swap_operations": {
                                "operations": [
                                {
                                    "terra_port": {
                                    "offer_asset_info": {
                                        "native_token": {
                                        "denom": "uluna"
                                        }
                                    },
                                    "ask_asset_info": {
                                        "token": {
                                        "contract_addr": contract_address
                                        }
                                    }
                                    }
                                }
                                ]
                            }
                        },
                        coins    = Coins(str(swap_amount) + self.swap_denom)
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 1000000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom in non_uluna_coins and self.swap_request_denom == ULUNA:
                    # These are all swaps on the Terraport address
                    contract_address = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.swap_denom)])
                    
                    encoded_msg = base64.b64encode(bytes(str('{"execute_swap_operations":{"operations":[{"terra_port":{"offer_asset_info":{"token":{"contract_addr":"' + contract_address + '"}},"ask_asset_info":{"native_token":{"denom":"uluna"}}}}]}}'), 'utf-8'))
                    encoded_msg = encoded_msg.decode("utf-8")

                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = contract_address,
                        msg = 
                            {
                            "send": {
                                "contract": TERRAPORT_SWAP_ADDRESS,
                                "amount": str(swap_amount),
                                "msg": encoded_msg
                            }
                        },
                        coins    = []
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 1000000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom == UBASE:
                    # We are swapping BASE back to ULUNA
                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = self.contract,
                        msg      = {
                            "burn": {"amount": str(swap_amount)}
                        }
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 500000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom == GRDX:
                    encoded_msg = base64.b64encode(bytes(str('{"swap":{"max_spread": "' + str(MAX_SPREAD) + '","belief_price": "' + str(self.belief_price) + '"}}'), 'utf-8'))
                    encoded_msg = encoded_msg.decode("utf-8")

                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = TERRASWAP_GRDX_TO_LUNC_ADDRESS,
                        msg      = {'send': {'amount': str(swap_amount), 'contract': GRDX_SMART_CONTRACT_ADDRESS,'msg': encoded_msg}}
                    )

                    options = CreateTxOptions(
                        fee            = self.fee,
                        gas            = 1000000,
                        gas_prices     = {'uluna': self.gas_list['uluna']},
                        gas_adjustment = GAS_ADJUSTMENT_SWAPS,
                        msgs           = [tx_msg],
                        sequence       = self.sequence,
                    )

                else:
                    tx_msg = MsgExecuteContract(
                        sender   = self.current_wallet.key.acc_address,
                        contract = self.contract,
                        msg      = {
                            'swap': {
                                'belief_price': str(self.belief_price),
                                'max_spread': str(self.max_spread),
                                'offer_asset': {
                                    'amount': str(swap_amount),
                                    'info': {
                                        'native_token': {
                                            'denom': self.swap_denom
                                        }
                                    }
                                },
                            }
                        },
                        coins    = Coins(str(swap_amount) + self.swap_denom)
                    )

                    options = CreateTxOptions(
                        fee            = self.fee,
                        gas            = 1000000,
                        gas_prices     = self.gas_list,
                        gas_adjustment = 3.6,
                        msgs           = [tx_msg],
                        sequence       = self.sequence,
                    )

                # If we are swapping from lunc to usdt then we need a different fee structure
                if self.swap_denom == ULUNA and self.swap_request_denom == UUSD:
                    options.fee_denoms = [ULUNA]
                    options.gas_prices = {ULUNA: self.gas_list[ULUNA]}

                tx:Tx = None
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
                        print (' 🛑 An unexpected error occurred in the swap function:')
                        print (err)
                        break
                    except Exception as err:
                        print (' 🛑 An unexpected error occurred in the swap function:')
                        print (err)
                        break

                self.transaction = tx

                return True
            else:
                return False
        else:
            print ('No belief price calculated - did you run the simulation first?')
            return False
  
    def swapRate(self) -> float:
        """
        Get the swap rate based on the provided details.
        Returns a float value of the amount.

        @params:
            - None

        @return: the swap rate
        """
        
        estimated_amount:float = None
        is_offchain_swap:bool  = self.isOffChainSwap()

        if self.use_market_swap == False and is_offchain_swap == False:
            if self.swap_denom == UBASE:
                if self.swap_request_denom == ULUNA:
                    swap_price       = self.beliefPrice()
                    estimated_amount = float(self.swap_amount * swap_price)
            elif self.swap_denom == GRDX:
                if self.swap_request_denom == ULUNA:
                    swap_price       = self.beliefPrice()
                    estimated_amount = float(self.swap_amount * swap_price)
            elif self.swap_request_denom in NON_ULUNA_COINS.values() and self.swap_denom == ULUNA:
                swap_price       = self.beliefPrice()
                if swap_price is not None:
                    if self.swap_request_denom == UBASE or self.swap_request_denom == GRDX:
                        estimated_amount = float(self.swap_amount / swap_price)
                    else:
                        estimated_amount = float(self.swap_amount * swap_price)
            else:
                # This will cover nearly all other swap pairs:
                # eg: rakoff -> LUNC
                swap_price = self.beliefPrice()
                if swap_price is not None and swap_price > 0:
                    # Rakoff definitely needs to multiply
                    if self.swap_request_denom == UUSD:
                        estimated_amount = float(self.swap_amount / swap_price)
                    else:    
                        estimated_amount = float(self.swap_amount * swap_price)
                    
        else:
            if self.swap_denom in OFFCHAIN_COINS + [ULUNA] and self.swap_request_denom in OFFCHAIN_COINS + [ULUNA]:
                # Calculate the amount of OSMO (or whatever) we'll be getting:
                # (lunc amount * lunc unit cost) / osmo price
                if self.wallet_denom in CHAIN_DATA and self.swap_request_denom in CHAIN_DATA[self.wallet_denom]['ibc_channels']:
                    prices:json            = self.getPrices(self.swap_denom, self.swap_request_denom)
                    estimated_amount:float = (self.swap_amount * float(prices['from']) / float(prices['to']))
            else:
                # Market swaps between mntc -> ukrw etc
                # NOTE: DOES NOT WORK AT THE MOMENT DUE TO A CHAIN CHANGE
                try:
                    swap_details:Coin = self.terra.market.swap_rate(Coin(self.swap_denom, self.swap_amount), self.swap_request_denom)
                    estimated_amount  = swap_details.amount
                except Exception as err:
                    #print (f'An error occured getting prices for swapping {self.swap_denom} to {self.swap_request_denom}')
                    #print (err)
                    pass
                
        #print (self.swap_denom, ' to ', self.swap_request_denom, ' = ', estimated_amount)
        return estimated_amount

def swap_coins(wallet, swap_coin:Coin, swap_to_denom:str, estimated_amount:int = 0, silent_mode:bool = False, log_trade:bool = False, log_trade_params:dict = {}):
    """
    A wrapper function for workflows and wallet management.

    This lets the user swap coins between denominations and chains.
    
    This could be a terra, osmo, or an IBC destination.

    The wrapper function adds any error messages depending on the results that got returned.
    
    @params:
      - wallet: a fully complete wallet object
      - swap_coin: a fully complete Coin object. We get the amount and denom from this
      - swap_to_denom: what are we swapping this for?
      - esimated amount: required for display purposes only
      - silent_mode: do we want to pause for user confirmation?
      - log_trade: do we add this to the trade database?
      - log_trade_params: exit and loss thresholds

    @return: a TransactionResult object
    """

    transaction_result:TransactionResult = TransactionResult()

    # Create the swap object
    swap_tx = SwapTransaction().create(seed = wallet.seed, denom = wallet.denom)

    # Assign the details:
    swap_tx.balances           = wallet.balances
    swap_tx.sender_address     = wallet.address
    swap_tx.sender_prefix      = wallet.getPrefix(wallet.address)
    swap_tx.silent_mode        = silent_mode
    swap_tx.swap_amount        = int(swap_coin.amount)
    swap_tx.swap_denom         = swap_coin.denom
    swap_tx.swap_request_denom = swap_to_denom
    swap_tx.wallet_denom       = wallet.denom

    # Bump up the gas adjustment - it needs to be higher for swaps it turns out
    swap_tx.terra.gas_adjustment = float(GAS_ADJUSTMENT_SWAPS)

    # Set the contract based on what we've picked
    # As long as the swap_denom and swap_request_denom values are set, the correct contract should be picked
    use_market_swap:bool  = swap_tx.setContract()
    is_offchain_swap:bool = swap_tx.isOffChainSwap()

    if is_offchain_swap == True:
        # This is an off-chain swap. Something like LUNC(terra)->OSMO or LUNC(Osmosis) -> wETH
        swap_result:bool = swap_tx.offChainSimulate()
        if swap_result == True:
            if silent_mode == False:
                print (f'You will be swapping {wallet.formatUluna(swap_coin.amount, swap_coin.denom, False)} {FULL_COIN_LOOKUP[swap_coin.denom]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[swap_to_denom]}')
                print (swap_tx.readableFee())

                user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

                if user_choice == False:
                    print ('\n 🛑 Exiting...\n')
                    exit()
            
            swap_result:bool = swap_tx.offChainSwap()
    else:
        if use_market_swap == True:
            # uluna -> umnt, uluna -> ujpy etc
            # This is for terra-native swaps ONLY
            swap_result:bool = swap_tx.marketSimulate()
            if swap_result == True:
                if silent_mode == False:
                    print (f'You will be swapping {wallet.formatUluna(swap_coin.amount, swap_coin.denom, False)} {FULL_COIN_LOOKUP[swap_coin.denom]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[swap_to_denom]}')
                    print (swap_tx.readableFee())
                    user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

                    if user_choice == False:
                        print ('\n 🛑 Exiting...\n')
                        exit()
                    
                swap_result:bool = swap_tx.marketSwap()
        else:
            # This is for uluna -> uusd/lenny/grdx swaps ONLY. We use the contract addresses to support this

            swap_result:bool = swap_tx.simulate()
            if swap_result == True:
                if silent_mode == False:
                    print (f'You will be swapping {wallet.formatUluna(swap_coin.amount, swap_coin.denom, False)} {FULL_COIN_LOOKUP[swap_coin.denom]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[swap_to_denom]}')
                    print (swap_tx.readableFee())
                    user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

                    if user_choice == False:
                        print ('\n 🛑 Exiting...\n')
                        exit()
                
                swap_result:bool = swap_tx.swap()
    
    if swap_result == True:
        transaction_result = swap_tx.broadcast()

        # if transaction_result.broadcast_result is not None and transaction_result.broadcast_result.code == 32:
        #     while True:
        #         print (' 🛎️  Boosting sequence number and trying again...')

        #         swap_tx.sequence = swap_tx.sequence + 1
        #         swap_tx.simulate()
        #         print (swap_tx.readableFee())

        #         swap_tx.swap()
        #         transaction_result:TransactionResult = swap_tx.broadcast()

        #         if swap_tx is None:
        #             break

        #         # Code 32 = account sequence mismatch
        #         if transaction_result.broadcast_result.code != 32:
        #             break

        if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error():
            transaction_result.is_error = True
            if transaction_result.broadcast_result is None:
                transaction_result.message  = ' 🛎️  The swap transaction failed, no broadcast object was returned.'
                transaction_result.is_error = True
            else:
                transaction_result.message = ' 🛎️  The swap transaction failed, an error occurred'
                if transaction_result.broadcast_result.raw_log is not None:
                    transaction_result.message  = f' 🛎️  The swap transaction on {wallet.name} failed, an error occurred.'
                    transaction_result.code     = f' 🛎️  Error code {transaction_result.broadcast_result.code}'
                    transaction_result.log      = f' 🛎️  {transaction_result.broadcast_result.raw_log}'
                    transaction_result.is_error = True
                else:
                    transaction_result.message  = f' 🛎️  No broadcast log on {wallet.name} was available.'
                    transaction_result.is_error = True
        
    else:
        transaction_result.message  = ' 🛎️  The swap transaction could not be completed'
        transaction_result.is_error = True

    # Store the delegated amount for display purposes
    transaction_result.transacted_amount = wallet.formatUluna(swap_coin.amount, swap_coin.denom, True)
    transaction_result.label             = 'Swapped amount'
    transaction_result.wallet_denom      = wallet.denom

    if log_trade == True:
        # If this was successful, then log the trade
        transaction_result.trade_id = swap_tx.logTrade(wallet, transaction_result, log_trade_params)

    return transaction_result