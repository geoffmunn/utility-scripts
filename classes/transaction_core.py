#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from __future__ import annotations

import json
import requests
import sqlite3
import time

from hashlib import sha256
from sqlite3 import Cursor, Connection

from classes.common import (
    divide_raw_balance,
    get_precision
)

from constants.constants import (
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_DATA,
    DB_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_PRICE_URI,
    GRDX,
    GRDX_SMART_CONTRACT_ADDRESS,
    SEARCH_RETRY_COUNT,
    UBASE,
    ULUNA,
    UUSD
)

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.tx import TxInfo, Tx
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.broadcast import BlockTxBroadcastResult, TxLog
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee

class TransactionCore():
    """
    The core class for all transactions.
    """

    def __init__(self):
        
        self.account_number:int                      = None
        self.balances:dict                           = {}
        self.broadcast_result:BlockTxBroadcastResult = None
        self.cached_traces:dict                      = {}
        self.current_wallet:Wallet                   = None # The generated wallet based on the provided details
        self.fee:Fee                                 = None
        self.gas_list:json                           = None
        self.gas_price_url:str                       = None
        self.ibc_routes:list                         = None # Only used by swaps
        self.prices:dict                             = None
        self.sequence:int                            = None
        self.tax_rate:json                           = None
        self.terra:LCDClient                         = None
        self.transaction:Tx                          = None
        self.wallet_denom:str                        = None # Used so we can identify the chain that this transaction is using

        # Initialise the basic variables:
        self.gas_price_url = GAS_PRICE_URI
        # The gas list and tax rate values will be updated when the class is properly created
        
    def broadcast(self) -> TransactionResult:
        """
        A core broadcast function for all transactions.
        It will wait until the transaction shows up in the search function before finishing.

        @params:
            - None

        @return: the transaction result as an object
        """

        # Set up the basic transaction result object
        transaction_result:TransactionResult = TransactionResult()

        try:
            transaction_result.broadcast_result = self.terra.tx.broadcast_sync(self.transaction)
            self.broadcast_result = transaction_result.broadcast_result
        except Exception as err:
            transaction_result.message          = ' 🛑 A broadcast error occurred.'
            transaction_result.log              = err
            transaction_result.broadcast_result = None

        if transaction_result.broadcast_result is not None:
            
            # We need the code to determine if we proceed or not
            code:int = None
            try:
                code = transaction_result.broadcast_result.code
            except:
                transaction_result.message = 'Error getting the code attribute.'
                
            if code is not None and code != 0:
                # Send this back for a retry with a higher gas adjustment value
                return transaction_result
            else:
                # Find the transaction on the network and return the result
                try:
                    transaction_result:TransactionResult = self.findTransaction()

                    if transaction_result.transaction_confirmed == True:
                        transaction_result.message = 'This transaction should be visible in your wallet now.'
                    else:
                        transaction_result.message = 'The transaction did not appear. Future transactions might fail due to a lack of expected funds.'
                except Exception as err:
                   transaction_result.message = 'An unexpected error occurred when broadcasting.'
                   transaction_result.log     = err
                 
        return transaction_result
    
    def cachePrices(self) -> bool:
        """
        Load all the coin prices into a dictionary we can use later.

        @params:
            - None

        @return: True
        """

        retry_count:int  = 0
        retry:bool       = True
        
        if self.prices is None:
            while retry == True:
                try:
                    # Get all the prices we are interested in and cache them so we don't get rate limited by Coingecko
                    id_str:str = ''
                    for denom in CHAIN_DATA:
                        id_str += CHAIN_DATA[denom]['coingecko_id'] + ','

                    uri:str     = 'https://api.coingecko.com/api/v3/simple/price'
                    params:dict = {  
                        'ids': id_str,
                        'vs_currencies': 'USD'
                    }

                    self.prices = requests.get(uri, params = params).json()

                    # Exit this loop
                    retry = False
                    break

                except Exception as err:
                    retry_count += 1
                    if retry_count == 10:
                        print (' 🛑 Error getting coin prices')
                        print (err)

                        retry = False
                        exit()
                    else:
                        time.sleep(1)

        return True
            
    def calculateFee(self, requested_fee:Fee, specific_denom:str = '', convert_to_ibc:bool = False) -> Fee:
        """
        Calculate the fee based on the provided information and what coins are available.
        This function prefers to pay in minor coins first, followed by uluna, and then ustc.

        If desired, the fee can specifically be uusd.

        convert_to_ibc only applies to the ULUNA value, if it is available.

        @params:
            - requested_fee: the fee object that was returned in the simulation
            - specific_denom: a specific denom to return the fee in
            - convert_to_ibc: convert the denom to and IBC value if required

        @return: a fully complete Fee object
        """

        other_coin_list:list      = []
        has_uluna:int             = 0
        has_uusd:int              = 0
        specific_denom_amount:int = 0

        coin:Coin
        for coin in requested_fee.amount:
            if coin.denom in self.balances and int(self.balances[coin.denom]) >= int(coin.amount):

                if coin.denom == UUSD:
                    has_uusd = coin.amount
                elif coin.denom == ULUNA:
                    has_uluna = coin.amount
                else:
                    other_coin_list.append(coin)

                if coin.denom == specific_denom:
                    specific_denom_amount = coin.amount

        if has_uluna > 0 or has_uusd > 0 or len(other_coin_list) > 0:
            
            if len(other_coin_list) > 0:
                requested_fee.amount = Coins({Coin(other_coin_list[0].denom, other_coin_list[0].amount)})
            elif has_uluna > 0:
                requested_fee.amount = Coins({Coin(ULUNA, has_uluna)})
            else:
                requested_fee.amount = Coins({Coin(UUSD, has_uusd)})

            # Override the calculations if we've been told to use uusd or something else
            if convert_to_ibc == True:
                # NOTE: this assumes there is enough ULUNA to cover the fee
                ibc_channel:str      = CHAIN_DATA[self.wallet_denom]['ibc_channels'][ULUNA]
                ibc_value:str        = self.IBCfromDenom(ibc_channel, ULUNA)
                requested_fee.amount = Coins({Coin(ibc_value, has_uluna)})
            else:
                if specific_denom != '':
                    requested_fee.amount = Coins({Coin(specific_denom, specific_denom_amount)})
        else:
            print ('Not enough funds to pay for this transaction!')

        return requested_fee

    def denomTrace(self, ibc_address:str) -> str:
        """
        Based on the wallet prefix, get the IBC denom trace details for this IBC address.
        This is a slow process, so we do two things:
        First, check the cached results in memory.
        Second, check the database.
        Third, go and get the actual result.

        @params:
            - ibc_address: the IBC address we want to convert to readable form
            
        @return: a human-readable version of the IBC value
        """

        # First, if this is not even an IBC address, then return the original value:
        if ibc_address[0:4].lower() != 'ibc/':
            return ibc_address

        # We will use the uri as the key, just to make sure there are no collisions
        value:str      = ibc_address[4:]
        chain_name:str = CHAIN_DATA[self.wallet_denom]['cosmos_name']
        uri:str        = f'https://rest.cosmos.directory/{chain_name}/ibc/apps/transfer/v1/denom_traces/{value}'
        result:str     = ''

        # Now check the cached traces:
        if uri not in self.cached_traces:
            # Now check the database:

            get_ibc_query    = "SELECT readable_denom FROM ibc_denoms WHERE ibc_denom=?;"
            insert_ibc_denom = "INSERT INTO ibc_denoms (ibc_denom, readable_denom) VALUES (?, ?);"

            # Get the database results
            conn:Connection = sqlite3.connect(DB_FILE_NAME)
            cursor:Cursor   = conn.execute(get_ibc_query, [uri])
            row:list        = cursor.fetchone()

            if row is None:
                # Go and get this denom trace:

                retry_count:int = 0
                retry:bool      = True

                while retry == True:
                    try:
                        trace_result:json = requests.get(uri).json()
                    
                        if 'denom_trace' in trace_result:
                            # Return this result
                            result = trace_result['denom_trace']['base_denom']
                            
                            # Add this IBC value and readable version into the database:
                            cursor:Cursor = conn.execute(insert_ibc_denom, [uri, result])
                            conn.commit()

                            # Store this result for future requests
                            self.cached_traces[uri] = result
                            
                            break
                        else:
                            break
                    except Exception as err:
                        retry_count += 1
                        if retry_count == 10:
                            print (f'Denom trace error for {uri}:')
                            print (err)
                            retry  = False
                            result = ''
                            break
                        else:
                            time.sleep(1)
            else:
                # This IBC entry is in the database
                result = row[0]

                # Update the cache so we don't have to do this again
                self.cached_traces[uri] = result
        else:
            # Return what we already have
            result = self.cached_traces[uri]

        return result
        
    def findTransaction(self) -> TransactionResult:
        """
        Do a search for any transaction with the current tx hash.
        If it can't be found within 10 attempts, then give up.

        @params:
            - None
            
        @return: a TransactionResult object
        """

        retry_count:int                      = 0
        transaction_result:TransactionResult = TransactionResult()
        
        # Set up the default values:
        transaction_result.transaction_confirmed = False

        # Put the broadcast result here - the displayed hash comes from this
        transaction_result.broadcast_result = self.broadcast_result

        print (f'\n 🔎︎ Looking for the TX hash...')
        while True:
            # We will be the current height - 1 just in case it rolled over just as we started the search
            block_height:int = int(self.terra.tendermint.block_info()['block']['header']['height']) - 1

            # Build the transaction search object:
            result:dict = self.terra.tx.search([
                ("message.sender", self.current_wallet.key.acc_address),
                ("message.recipient", self.current_wallet.key.acc_address),
                ('tx.hash', transaction_result.broadcast_result.txhash),
                ('tx.height', block_height)
            ])

            if result is not None:
                if len(result['txs']) > 0:

                    info:TxInfo = result['txs'][0]

                    if info.logs is not None and len(info.logs) > 0:
                        log:TxLog   = info.logs[0]
                        
                        if 'message' in log.events_by_type:
                            # Governance votes
                            if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'governance':
                                transaction_result.result_sent     = None
                                transaction_result.result_received = None
                                transaction_result.log_found       = True

                            # Staking/Unstaking
                            if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'staking':
                                transaction_result.result_sent = None

                                # Unstaking will return a bunch of random coins, but we only want the uluna coin
                                coin_list:Coins = Coins.from_str(log.events_by_type['coin_spent']['amount'][0])
                                coin:Coin
                                for coin in coin_list:
                                    if coin.denom == ULUNA:
                                        transaction_result.result_received = Coins.from_proto([coin])
                                        break

                                transaction_result.log_found = True

                            # Validator rewards
                            if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'distribution':
                                transaction_result.result_sent = None

                                # Unstaking will return a bunch of random coins, but we only want uluna and uust
                                coin_list:Coins  = Coins.from_str(log.events_by_type['coin_spent']['amount'][0])
                                
                                coin:Coin
                                filtered_list:list = []
                                for coin in coin_list:
                                    if coin.denom in [ULUNA, UUSD]:
                                        filtered_list.append(coin)
                                
                                transaction_result.result_received = Coins.from_proto(filtered_list)
                                transaction_result.log_found = True

                            # Osmosis swaps
                            if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'gamm':
                                if 'pool_exited' in log.events_by_type:
                                    # This is an exit pool request
                                    transaction_result.result_sent     = None
                                    transaction_result.result_received = Coins.from_str(log.events_by_type['pool_exited']['tokens_out'][0])
                                    transaction_result.log_found       = True
                                else:
                                    # For some reason, wBTC -> LUNC swaps have an empty string so we'll fix that
                                    amount = log.events_by_type['coin_spent']['amount'][0]
                                    if amount == '':
                                        amount = '0uluna'

                                    transaction_result.result_sent     = Coin.from_str(amount)
                                    transaction_result.result_received = Coins.from_proto([Coin.from_str(log.events_by_type['coin_received']['amount'][-1])])
                                    transaction_result.log_found       = True

                            # Send to Osmosis
                            if 'module' in log.events_by_type['message'] and 'transfer' in log.events_by_type['message']['module']:
                                transaction_result.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                                transaction_result.result_received = Coins.from_proto([Coin.from_str(log.events_by_type['coin_received']['amount'][-1])])
                                transaction_result.log_found       = True

                            # Send to on-chain address
                            if 'module' in log.events_by_type['message'] and 'bank' in log.events_by_type['message']['module']:
                                transaction_result.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                                transaction_result.result_received = Coins.from_proto([Coin.from_str(log.events_by_type['coin_received']['amount'][-1])])
                                transaction_result.log_found       = True
                        
                        if 'wasm' in log.events_by_type:
                            # Standard swaps ('LUNC -> USTC'):
                            if 'action' in log.events_by_type['wasm'] and log.events_by_type['wasm']['action'][0] == 'swap':
                                transaction_result.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                                transaction_result.result_received = Coins.from_proto([Coin.from_str(log.events_by_type['coin_received']['amount'][-1])])
                                transaction_result.log_found       = True

                            # Send transactions
                            if 'action' in log.events_by_type['wasm'] and log.events_by_type['wasm']['action'][0] == 'transfer':
                                transaction_result.result_sent     = Coin.from_str(f"{log.events_by_type['wasm']['amount'][0]}{self.denom}")
                                transaction_result.result_received = Coins.from_proto([Coin.from_str(f"{log.events_by_type['wasm']['amount'][0]}{self.denom}")])
                                transaction_result.log_found       = True

                            # Base swaps/undelegations
                            if '_contract_address' in log.events_by_type['wasm'] and log.events_by_type['wasm']['_contract_address'][0] == BASE_SMART_CONTRACT_ADDRESS:
                                transaction_result.result_sent = None
                                if log.events_by_type['wasm']['action'][0] == 'buy':
                                    transaction_result.result_received = Coins.from_proto([Coin.from_data({'amount': log.events_by_type['wasm']['BASE Minted:'][0], 'denom': UBASE})])
                                else:
                                    # Assumes swaps back from BASE -> LUNC
                                    transaction_result.result_received = Coins.from_proto([Coin.from_data({'amount': log.events_by_type['wasm']['Net Unstake:'][0], 'denom': ULUNA})])
                                
                                transaction_result.log_found = True

                            # GRDX swaps (will override the standard swaps detection done earlier)
                            if '_contract_address' in log.events_by_type['wasm'] and GRDX_SMART_CONTRACT_ADDRESS in log.events_by_type['wasm']['_contract_address']:
                                transaction_result.result_sent     = Coin.from_data({'amount': log.events_by_type['wasm']['offer_amount'][0], 'denom': log.events_by_type['wasm']['offer_asset'][0]})
                                transaction_result.result_received = Coins.from_proto([Coin.from_data({'amount': log.events_by_type['wasm']['return_amount'][0], 'denom': GRDX})])
                                transaction_result.log_found       = True

                        if transaction_result.log_found == False:
                            print ('\n@TODO: events by type not returned, please check the results:')
                            print (log)

                    if result['txs'][0].code == 0:
                        print ('\n ⭐ Found the hash!')
                        time.sleep(1)
                        transaction_result.transaction_confirmed = True
                        break
                    elif result['txs'][0].code == 6:
                            # Denom not found on chain
                            transaction_result.code     = result['txs'][0].code
                            transaction_result.log      = info.rawlog
                            transaction_result.is_error = True
                            break
                    else:
                        #result['txs'][0].code == 5:
                        transaction_result.code     = result['txs'][0].code
                        transaction_result.log      = info.rawlog
                        transaction_result.is_error = True
                        break
            else:
                print ('    No result object returned, trying again...')
                
            retry_count += 1

            if retry_count <= SEARCH_RETRY_COUNT:
                print (f'    Search attempt {retry_count}/{SEARCH_RETRY_COUNT}')
                time.sleep(1)
            else:
                break

        # Return the completed transaction result
        return transaction_result

    def gasList(self) -> json:
        """
        Make a JSON request for the gas prices, and store it against this LCD client instance.
        This returns a full list of gas tokens, in JSON format:
        {'uluna': '28.325', 'usdr': '0.52469', 'uusd': '0.75', 'ukrw': '850.0', 'umnt': '2142.855', 'ueur': '0.625', 'ucny': '4.9', 'ujpy': '81.85', 'ugbp': '0.55', 'uinr': '54.4', 'ucad': '0.95', 'uchf': '0.7', 'uaud': '0.95', 'usgd': '1.0', 'uthb': '23.1', 'usek': '6.25', 'unok': '6.25', 'udkk': '4.5', 'uidr': '10900.0', 'uphp': '38.0', 'uhkd': '5.85', 'umyr': '3.0', 'utwd': '20.0'}

        If you only want gas in a particular coin, then pass the gas item like this: {'uluna': self.gas_list['uluna']}

        @params:
            - None
            
        @return: a json object with the relevant gas prices
        """

        if self.gas_list is None:
            try:
                if self.gas_price_url is not None:
                    gas_list:json = requests.get(self.gas_price_url).json()
                    if 'uluna' in gas_list:
                        self.gas_list = gas_list
                    else:
                        self.gas_list = None
                        print (f' 🛑 Gas prices not returned from {self.gas_price_url}')
                        
                else:
                    print (' 🛑 No gas price URL set at self.gas_price_url')
                    self.gas_list = None
            except:
                print (' 🛑 Error getting gas prices')
                print (requests.get(self.gas_price_url).content)

        return self.gas_list
    
    def getPrices(self, from_denom:str, to_denom:str) -> json:
        """
        Get the current USD prices for two different coins.
        From: swap_denom
        To: request_denom

        If the prices aren't present already, we'll go and get them.

        @params:
            - from_denom: coin #1, typically the coin we're swapping from
            - to_denom: coin #2, the coin we're swapping to
            
        @return: a json object with the prices for both coins
        """

        from_price:float = None
        to_price:float   = None

        if self.prices is None:
            self.cachePrices()

        if from_denom != False and to_denom != False:
            from_id:dict = CHAIN_DATA[from_denom]
            to_id:dict   = CHAIN_DATA[to_denom]

        from_price:float = self.prices[from_id['coingecko_id']]['usd']
        to_price:float   = self.prices[to_id['coingecko_id']]['usd']
        
        return {'from':from_price, 'to': to_price}
        
    def IBCfromDenom(self, channel_id:str, denom:str) -> str:
        """
        Based on the provided denom and the source channel, figure out the IBC value

        @params:
            - channel_id: the channel ID, obtained from the CHAIN_DATA list
            - denom: the denom that we want to convert into IBC form
            
        @return: a json object with the prices for both coins
        """

        ibc_value:str = ''
        ibc_value     = sha256(f'transfer/{channel_id}/{denom}'.encode('utf-8')).hexdigest().upper()
        ibc_result    = 'ibc/' + ibc_value

        return ibc_result

    def readableFee(self) -> str:
        """
        Return a description of the fee for the current transaction.
        If the IBC routes have been populated (ie, this is a swap) then show them too.

        @params:
            - None
            
        @return: a string explaining what's happening
        """
        
        routes:list = self.ibc_routes
        if routes is not None and len(routes) > 0:
            route_messages:list = []
            max_length:int      = 0

            # We need this just for readability purposes
            current_denom:str = FULL_COIN_LOOKUP[self.swap_denom]
            for route in routes:

                denom:str    = FULL_COIN_LOOKUP[self.denomTrace(route['token_out_denom'])]
                swap_fee:str = str(route['swap_fee'] * 100) + '%'
                msg          = f"Converting {current_denom} to {denom} (#{route['pool_id']}) with a swap fee of {swap_fee}."

                route_messages.append(msg)
                if len(msg) > max_length:
                    max_length = len(msg)

                current_denom = denom

            first:bool = True
            print ('\n')
            print ('*' * max_length)
            for route_message in route_messages:
                if first == False:
                    print (' ' * (int(max_length / 2) - 3),'⇩')
                print (route_message)

                first = False

            print ('*' * max_length,'\n')

        fee_string:str = ''
        if self.fee is not None and self.fee.amount is not None:
            fee_coins:Coins = self.fee.amount

            # Build a human-readable fee description:
            fee_string:str = ' 🪙 The fee is '
            first:bool     = True
            for fee_coin in fee_coins.to_list():

                amount:float   = divide_raw_balance(fee_coin.amount, fee_coin.denom)
                amount_str:str = ("%.6f" % (amount)).rstrip('0').rstrip('.')

                # Get the readable denom if this is an IBC token
                denom:str = self.denomTrace(fee_coin.denom)

                if denom in FULL_COIN_LOOKUP:
                    denom = FULL_COIN_LOOKUP[denom]
                    
                if first == False:
                    fee_string += ', and ' + amount_str + ' ' + denom
                else:
                    fee_string += amount_str + ' ' + denom

                first = False

        return fee_string
    
    def taxRate(self) -> float:
        """
        Query the terra treasury object for the current tax rate.
        We are not caching it so that tax changes will be automatically picked up.

        If this is not a columbus-5 (Luna Classic) chain, then assume the tax rate is zero.

        @params:
            - None
            
        @return: the tax rate as a float number
        """

        if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
            self.tax_rate = float(self.terra.treasury.tax_rate())
        else:
            self.tax_rate = 0

        return self.tax_rate
class TransactionResult(TransactionCore):
    """
    Holds the details of the transaction result.
    We're moving the results into a separate class so it's cleaner.
    """

    def __init__(self, *args, **kwargs):
        
        super(TransactionResult, self).__init__(*args, **kwargs)

        self.broadcast_result:BlockTxBroadcastResult = None
        self.code:int                                = None
        self.is_error:bool                           = False
        self.label:str                               = ''       # For display purposes, it will be something like 'Sent amount', or 'Delegated amount'
        self.log:str                                 = None
        self.log_found:bool                          = False
        self.message:str                             = ''
        self.result_received:Coins                   = None     # Even if we only get one coin, we'll treat it as a list of coins
        self.result_sent:Coin                        = None
        self.transacted_amount:str                   = None     # This holds the sent/delegated/whatever amount. It has already been through the formatUluna function.
        self.transaction_confirmed:bool              = None

    def formatCoin(self, coin:Coin, add_suffix:bool = False) -> str:
        """
        Format the coin into a human-readable string.

        @params:
            - coin: a Coin object holding the amount and denom
            - add_suffix: if True, then the denom is added to the string

        @return a human-readable string of the provided coin
        """

        denom:str = self.denomTrace(coin.denom)
        if denom in FULL_COIN_LOOKUP:
            precision:int = get_precision(denom)
            lunc:float    = round(float(divide_raw_balance(coin.amount, denom)), precision)

            target:str = '%.' + str(precision) + 'f'
            lunc:str   = (target % (lunc)).rstrip('0').rstrip('.')

            if add_suffix:
                lunc = str(lunc) + ' ' + FULL_COIN_LOOKUP[denom]
        else:
            lunc:float = coin.amount
            if add_suffix:
                if denom[0:len('gamm/pool')] == 'gamm/pool':
                    denom_bits:list = denom.split('/')
                    lunc = str(lunc) + ' shares in pool ' + str(denom_bits[2])

        return str(lunc)
    
    def showResults(self) -> bool:
        """
        Show the results of the transaction result.

        @params:
            - none

        @return: True
        """

        if self.transaction_confirmed == True:
            print ('')
            if self.transacted_amount is not None:
                print (f' ✅ {self.label}: {self.transacted_amount}')
            elif self.label != '':
                print (f' ✅ {self.label}')

            if self.result_received is not None:
                print (f' ✅ Received amount: ')
                received_coin:Coin
                for received_coin in self.result_received:
                    print ('    * ' + str(self.formatCoin(received_coin, True)))
                    
            print (f' ✅ Tx Hash: {self.broadcast_result.txhash}')
            print ('\n')
        else:
            print (f'{self.message}')
            print (f' 🛎️  Error code {self.code}')
            if self.log is not None:
                print (f' 🛎️  {self.log}')

        return True