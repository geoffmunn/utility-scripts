#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from hashlib import sha256
import json
import math
import sqlite3
from sqlite3 import Cursor, Connection

from constants.constants import (
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_DATA,
    DB_FILE_NAME,
    GAS_ADJUSTMENT_OSMOSIS,
    GAS_ADJUSTMENT_SWAPS,
    MIN_OSMO_GAS,
    OFFCHAIN_COINS,
    TERRASWAP_UKRW_TO_ULUNA_ADDRESS,
    TERRASWAP_ULUNA_TO_UUSD_ADDRESS,
    TERRASWAP_UUSD_TO_ULUNA_ADDRESS,
    UBASE,
    UKRW,
    ULUNA,
    UOSMO,
    UUSD
)

from classes.common import (
    divide_raw_balance,
    getPrecision,
    multiply_raw_balance
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
        self.max_spread:float       = 0.01
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
        """

        belief_price:float = 0

        if self.contract is not None:
            try:
                if self.swap_denom != UBASE and self.swap_request_denom != UBASE:
                    contract_swaps:list = [ULUNA, UKRW, UUSD]
                    # Contract swaps must be on the columbus-5 chain
                    if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
                        if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:
                            # Get the pool details
                            parts:dict          = {}
                            result = self.terra.wasm.contract_query(self.contract, {"pool": {}})
                            if 'native_token' in result['assets'][0]['info']:
                                parts[result['assets'][0]['info']['native_token']['denom']] = int(result['assets'][0]['amount'])

                            parts[result['assets'][1]['info']['native_token']['denom']] = int(result['assets'][1]['amount'])

                            belief_price:float = parts[self.swap_denom] / parts[self.swap_request_denom]
                        
                else:
                    # UBASE does something different
                    if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
                        result           = self.terra.wasm.contract_query(self.contract, {"curve_info": {}})
                        spot_price:float = float(result['spot_price'])

                        if self.swap_request_denom == UBASE:
                            belief_price:float = divide_raw_balance((spot_price * 1.053), UBASE)
                        else:
                            belief_price:float = divide_raw_balance((spot_price - (spot_price * 0.048)), UBASE)

            except Exception as err:
                print (' 🛑 A connection error has occurred:')
                print (err)
                return None
           
        self.belief_price = round(belief_price, 18)

        return self.belief_price
    
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

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        return self
    
    def marketSimulate(self):
        """
        Simulate a market swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.transaction    = None
        self.sequence       = self.current_wallet.sequence()

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

    def marketSwap(self):
        """
        Make a market swap with the information we have so far.
        If fee is None then it will be a simulation.
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
    
    def getRoute(self, denom_in:str, denom_out:str, initial_amount:float):
        """
        Get the recommended route for this this swap combination.
        We will pick the lowest fee while still having a good level of liquidity
        """

        path_query:str      = "SELECT pool.pool_id, denom, readable_denom, swap_fee FROM pool INNER JOIN asset ON pool.pool_id=asset.pool_id WHERE pool.pool_id IN (SELECT pool_id FROM asset WHERE readable_denom = ?) AND readable_denom=? ORDER BY swap_fee ASC;"
        liquidity_query:str = "SELECT readable_denom, amount FROM asset WHERE pool_id = ?;"

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
                    origin_liquidity = row2
                    
                if row2[0] == denom_out:
                    exit_liquidity = row2
                    exit_liquidity_value:float = divide_raw_balance(exit_liquidity[1], denom_out) * float(self.prices[CHAIN_DATA[denom_out]['coingecko_id']]['usd'])

            #print (f'pool id: {row[0]}')
            #print (f'origin liquidity: ({denom_in}) = {origin_liquidity}')
            #print (f'exit liquidity: ({denom_out}) = {exit_liquidity}')
            #print ('converted liquidity:', divide_raw_balance(exit_liquidity[1], denom_out))
            #print ('value:', self.prices[CHAIN_DATA[denom_out]['coingecko_id']]['usd'])
            #print (f'exit liquidity value: {exit_liquidity_value}')
            
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
    
    def isOffChainSwap(self):
        """
        Figure out if this swap is based on off-chain (non-terra) coins.
        You can swap from lunc to osmo from columbus-5, and swap lunc to wBTC on osmosis-1
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

    def offChainSimulate(self):
        """
        Simulate an offchain swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.prices         = None
        self.transaction    = None
        self.sequence       = self.current_wallet.sequence()
        
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
                    print ('Exiting...')    
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
        fee_multiplier:float = GAS_ADJUSTMENT_OSMOSIS
        
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

            from_precision:int   = getPrecision(current_denom)
            target_precision:int = getPrecision(token_out_denom)

            if from_precision != target_precision:
                base_amount:float = divide_raw_balance(base_amount, current_denom)
            
            # Only multiply if the token out demo has a higher precision
            if target_precision < from_precision:
                base_amount:float = multiply_raw_balance(base_amount, token_out_denom)

            # deduct the swap fee:
            #print ('pool:', self.osmosisPoolByID(route['pool_id']))
            swap_fee:float = float(self.osmosisPoolByID(route['pool_id']).pool_params.swap_fee)

            #print ('swap fee:', swap_fee)
            # Deduct the swap fee
            base_amount_minus_swap_fee:float = float(base_amount) * (1 - swap_fee)

            # Deduct the slippage
            base_amount_minus_swap_fee = float(base_amount_minus_swap_fee * (1 - max_spread))

            # Now we have the new denom and the new value
            prev_denom:str       = current_denom
            current_denom:str    = token_out_denom        
            current_amount:float = base_amount_minus_swap_fee
            precision:int        = getPrecision(token_out_denom)

        from_precision:int   = getPrecision(prev_denom)
        target_precision:int = getPrecision(current_denom)
                    
        if target_precision > from_precision:
            current_amount = multiply_raw_balance(current_amount, current_denom)
            
        # Finish off the final value and store it:
        precision:int  = getPrecision(current_denom)
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

            return True
        else:
            return False

    def offChainSwap(self):
        """
        Make an offchain swap with the information we have so far.
        Currently we only support MsgSwapExactAmountIn via the GAMM module.

        If fee is None then it will be a simulation.
        """

        try:
            #print ('sender prefix:', self.sender_prefix)
            #print ('swap denom:', self.swap_denom)
            #chain = self.getChainByDenom(self.swap_denom)
            #chain = CHAIN_DATA[self.wallet_denom]
            #prefix = chain['prefix']
            #print ('prefix:', prefix)
            #channel_id = CHAIN_IDS[prefix]['ibc_channel']
            channel_id = CHAIN_DATA[self.wallet_denom]['ibc_channels'][self.swap_denom]
            
            #print ('channel id:', channel_id)
            #print (f'hash: transfer/{channel_id}/{self.swap_denom}')
            #print ('hash result:', sha256(f'transfer/{channel_id}/{self.swap_denom}'.encode('utf-8')).hexdigest().upper())
            #print ('should look like this:', IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['token_in'])
            #print ('should look like this: ibc/57AA1A70A4BC9769C525EBF6386F7A21536E04A79D62E1981EFCEF9428EBB205')
            
            if self.swap_denom != 'uosmo':
                coin_denom = 'ibc/' + sha256(f'transfer/{channel_id}/{self.swap_denom}'.encode('utf-8')).hexdigest().upper()
            else:
                coin_denom = 'uosmo'

            #print ('we will be using', coin_denom)

            token_in:Coin = Coin(coin_denom, self.swap_amount)

            #old:Coin = Coin(IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['token_in'], self.swap_amount)
            #print (f"old coin: {self.swap_denom}/{self.swap_request_denom} returns {IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['token_in']}")
            #print ('old denom:', old.denom)

            #token_in:Coin = Coin(IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['token_in'], self.swap_amount)

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
                #gas_adjustment = IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['gas_adjustment'],
                gas_adjustment = 1.5,
                msgs           = [tx_msg],
                sequence       = self.sequence
            )

            #print (self.terra.chain_id)
            #print (self.terra.url)
            #print ('options:')
            #print (options)

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
        """

        result:Pool = None

        if pool_id not in self.osmosis_pools:
            # Get this pool:
            pool:pool = self.terra.pool.osmosis_pool(pool_id)
            # Save it in the publicly available object:
            self.osmosis_pools[pool.id] = pool

            # Return this result
            result = pool        
            
        return result

    
    def setContract(self) -> bool:
        """
        Depending on what the 'from' denom is and the 'to' denom, change the contract endpoint.

        If this is going to use a market swap, then we don't need a contract.
        """
        
        use_market_swap:bool = True
        self.contract        = None
        contract_swaps:list  = [ULUNA, UKRW, UUSD, UBASE]

        if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:
            use_market_swap = False

            if self.swap_denom == ULUNA:
                if self.swap_request_denom == UUSD:
                    self.contract = TERRASWAP_ULUNA_TO_UUSD_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UBASE:
                    self.contract = BASE_SMART_CONTRACT_ADDRESS

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

            if self.swap_denom == UBASE:
                if self.swap_request_denom == ULUNA:
                    self.contract = BASE_SMART_CONTRACT_ADDRESS

        self.use_market_swap = use_market_swap

        return use_market_swap
      
    def simulate(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        THIS IS ONLY FOR USTC <-> LUNC SWAPS
        The fee details are saved so the actual delegation will work.

        Outputs:
        self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
        self.tax - the tax component
        self.fee_deductables - the amount we need to deduct off the transferred amount

        """

        # Reset these values in case this is a re-used object:
        self.account_number = self.current_wallet.account_number()
        self.fee            = None
        self.gas_limit      = 'auto'
        self.ibc_routes     = []
        self.min_out        = None
        self.prices         = None
        self.transaction    = None
        self.sequence       = self.current_wallet.sequence()

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
            if self.swap_denom == UBASE:
                self.tax = None
            else:
                self.tax = int(math.ceil(self.swap_amount * float(self.tax_rate['tax_rate'])))

            # Build a fee object
            if fee_denom == ULUNA and self.swap_denom == ULUNA:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            if self.swap_denom == UBASE:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
            else:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.swap_denom, int(self.tax))})

            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.swap_denom:
                self.fee_deductables = int(fee_amount + self.tax)
            elif fee_denom == ULUNA and self.swap_denom == UUSD:
                self.fee_deductables = int(self.tax)
            elif fee_denom == ULUNA and self.swap_denom == UBASE:
                self.fee_deductables = 0
            #elif fee_denom == UKUJI and self.swap_denom == UUSD:
            #    self.fee_deductables = int(self.tax)
            else:
                if self.tax is not None:
                    self.fee_deductables = int(self.tax * 2)
                else:
                    self.fee_deductables = None

            return True
        else:
            return False
    
    def swap(self) -> bool:
        """
        Make a swap with the information we have so far.
        If fee is None then it will be a simulation.
        """

        if self.belief_price is not None:
            
            if self.fee is not None:
                fee_amount:list = self.fee.amount.to_list()
                fee_coin:Coin   = fee_amount[0]
                fee_denom:str   = fee_coin.denom
            else:
                fee_denom:str   = UUSD

            if fee_denom in self.balances:
                swap_amount = self.swap_amount

                if self.tax is not None:
                   if self.fee_deductables is not None:
                       if int(swap_amount + self.fee_deductables) > int(self.balances[self.swap_denom]):
                           swap_amount = int(swap_amount - self.fee_deductables)

                if self.swap_denom == ULUNA and self.swap_request_denom == UBASE:
                    # We are swapping LUNC for BASE
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
                            "buy": {"affiliate": ""}
                        },
                        coins       = Coins(str(swap_amount) + self.swap_denom)
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 500000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom == UBASE:
                    # We are swapping BASE back to ULUNA
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
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
                else:
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
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
                        coins = Coins(str(swap_amount) + self.swap_denom)
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
        Returns a float value of the amount
        """
        
        estimated_amount:float = None
        is_offchain_swap:bool  = self.isOffChainSwap()

        if self.use_market_swap == False and is_offchain_swap == False:

            if self.swap_denom == UBASE:
                if self.swap_request_denom == ULUNA:
                    swap_price       = self.beliefPrice()
                    estimated_amount = float(self.swap_amount * swap_price)
                
            else:
                # This will cover nearly all swap pairs:
                swap_price = self.beliefPrice()
                if swap_price is not None and swap_price > 0:
                    estimated_amount = float(self.swap_amount / swap_price)
                    
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
                    estimated_amount = swap_details.amount
                except Exception as err:
                    #print (f'An error occured getting prices for swapping {self.swap_denom} to {self.swap_request_denom}')
                    #print (err)
                    pass

                
        return estimated_amount
