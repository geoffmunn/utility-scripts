#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import requests
import time
from hashlib import sha256

from classes.common import (
    divide_raw_balance
)

from constants.constants import (
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    GAS_PRICE_URI,
    SEARCH_RETRY_COUNT,
    UBASE,
    ULUNA,
    UUSD
)

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.tx import (
    Tx,
    TxInfo
)
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.broadcast import (
    BlockTxBroadcastResult,
    TxLog
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.tx import Tx

class TransactionCore():
    """
    The core class for all transactions.
    """

    def __init__(self):
        
        self.account_number:int                      = None
        self.balances:dict                           = {}
        self.broadcast_result:BlockTxBroadcastResult = None
        self.current_wallet:Wallet                   = None # The generated wallet based on the provided details
        self.denom_traces:dict                       = {}
        self.fee:Fee                                 = None
        self.gas_list:json                           = None
        self.gas_price_url:str                       = None
        self.height:int                              = None
        self.ibc_routes:list                         = None # Only used by swaps
        self.prices:dict                             = None
        self.result_received:Coin                    = None
        self.result_sent:Coin                        = None
        self.sequence:int                            = None
        self.tax_rate:json                           = None
        self.terra:LCDClient                         = None
        self.transaction:Tx                          = None
        self.wallet_denom:str                        = None # Used so we can identify the chain that this transaction is using

        # Initialise the basic variables:
        self.gas_price_url = GAS_PRICE_URI
        # The gas list and tax rate values will be updated when the class is properly created
        
    def broadcast(self) -> BlockTxBroadcastResult:
        """
        A core broadcast function for all transactions.
        It will wait until the transaction shows up in the search function before finishing.
        """

        try:
            result:BlockTxBroadcastResult = self.terra.tx.broadcast(self.transaction)    
        except Exception as err:
            print (' 🛑 A broadcast error occurred.')
            print (err)
            result:BlockTxBroadcastResult = None

        self.broadcast_result:BlockTxBroadcastResult = result

        if result is not None:
            code:int = None

            try:
                code = self.broadcast_result.code
            except:
                print ('Error getting the code attribute')
            
            if code is not None and code != 0:
                # Send this back for a retry with a higher gas adjustment value
                return self.broadcast_result
            else:
                # Find the transaction on the network and return the result
                try:
                    transaction_confirmed = self.findTransaction()

                    if transaction_confirmed == True:
                        print ('This transaction should be visible in your wallet now.')
                    else:
                        print ('The transaction did not appear. Future transactions might fail due to a lack of expected funds.')
                except Exception as err:
                    print ('An unexpected error occurred when broadcasting:')
                    print (err)

        return self.broadcast_result
    
    def cachePrices(self):
        """
        Load all the coin prices into a dictionary we can use later
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

        convert_to_ibc only applies to the ULUNA value, if it is available
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
                ibc_channel = CHAIN_DATA[self.wallet_denom]['ibc_channels'][ULUNA]
                ibc_value = 'ibc/' + sha256(f"transfer/{ibc_channel}/{ULUNA}".encode('utf-8')).hexdigest().upper()
                requested_fee.amount = Coins({Coin(ibc_value, has_uluna)})
            else:
                if specific_denom != '':
                    requested_fee.amount = Coins({Coin(specific_denom, specific_denom_amount)})
        else:
            print ('Not enough funds to pay for this transaction!')

        return requested_fee

    def denomTrace(self, ibc_address:str):
        """
        Based on the wallet denomination, get the IBC denom trace details for this IBC address
        """
        
        result:list = []

        if ibc_address[0:4] == 'ibc/':
            
            value      = ibc_address[4:]
            chain_name = CHAIN_DATA[self.wallet_denom]['cosmos_name']
            uri:str    = f'https://rest.cosmos.directory/{chain_name}/ibc/apps/transfer/v1/denom_traces/{value}'

            if uri not in self.denom_traces:

                retry_count:int = 0
                retry:bool      = True

                while retry == True:
                    try:
                        trace_result:json = requests.get(uri).json()
                    
                        if 'denom_trace' in trace_result:
                            # Store this result for future requests
                            self.denom_traces[uri] = trace_result['denom_trace']
                            # Return this result
                            result = trace_result['denom_trace']
                            break
                        else:
                            break
                    except Exception as err:
                        print (f'Denom trace error for {uri}:')
                        print (err)

                        retry_count += 1
                        if retry_count == 10:
                            retry = False
                            break
                        else:
                            time.sleep(1)
            else:
                result = self.denom_traces[uri]
        
        if len(result) == 0:
            return ibc_address # Not an IBC address we could resolve
        else:
            return result['base_denom']
        
    def findTransaction(self) -> bool:
        """
        Do a search for any transaction with the current tx hash.
        If it can't be found within 10 attempts, then give up.
        """

        # Store the current block here - needed for transaction searches
        retry_count = 0
        while True:
            self.height:int = int(self.terra.tendermint.block_info()['block']['header']['height']) - 1

            transaction_found:bool = False

            result:dict = self.terra.tx.search([
                ("message.sender", self.current_wallet.key.acc_address),
                ("message.recipient", self.current_wallet.key.acc_address),
                ('tx.hash', self.broadcast_result.txhash),
                ('tx.height', self.height)
            ])

            if len(result['txs']) > 0:

                info:TxInfo = result['txs'][0]
                log:TxLog   = info.logs[0]
                
                log_found:bool = False
                
                if 'message' in log.events_by_type:
                    # Governance votes
                    if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'governance':
                        self.result_sent     = None
                        self.result_received = None
                        log_found = True
                    # Staking/Unstaking
                    if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'staking':
                        self.result_sent = None
                        coin_list:Coins  = Coins.from_str(log.events_by_type['coin_spent']['amount'][0])
                        # Unstaking will return a bunch of random coins, but we only want the uluna coin
                        coin:Coin
                        for coin in coin_list:
                            if coin.denom == ULUNA:
                                self.result_received = coin
                                break
                        log_found = True

                    # Validator rewards
                    if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'distribution':
                        self.result_sent = None
                        coin_list:Coins  = Coins.from_str(log.events_by_type['coin_spent']['amount'][0])
                        # Unstaking will return a bunch of random coins, but we only want the uluna coin
                        coin:Coin
                        for coin in coin_list:
                            if coin.denom == ULUNA:
                                self.result_received = coin
                                break
                        
                        log_found = True

                    # Osmosis swaps
                    if 'module' in log.events_by_type['message'] and log.events_by_type['message']['module'][0] == 'gamm':
                        self.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                        self.result_received = Coin.from_str(log.events_by_type['coin_received']['amount'][-1])
                        log_found = True

                    # Send to Osmosis
                    if 'module' in log.events_by_type['message'] and 'transfer' in log.events_by_type['message']['module']:
                        self.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                        self.result_received = Coin.from_str(log.events_by_type['coin_received']['amount'][-1])
                        log_found = True
                
                if 'wasm' in log.events_by_type:
                    # Standard swaps ('LUNC -> USTC'):
                    if 'action' in log.events_by_type['wasm'] and log.events_by_type['wasm']['action'][0] == 'swap':
                        self.result_sent     = Coin.from_str(log.events_by_type['coin_spent']['amount'][0])
                        self.result_received = Coin.from_str(log.events_by_type['coin_received']['amount'][-1])
                        log_found = True

                    # Send transactions
                    if 'action' in log.events_by_type['wasm'] and log.events_by_type['wasm']['action'][0] == 'transfer':
                        self.result_sent     = Coin.from_str(f"{log.events_by_type['wasm']['amount'][0]}{self.denom}")
                        self.result_received = Coin.from_str(f"{log.events_by_type['wasm']['amount'][0]}{self.denom}")
                        log_found = True

                    # Base swaps/undelegations
                    if '_contract_address' in log.events_by_type['wasm'] and log.events_by_type['wasm']['_contract_address'][0] == BASE_SMART_CONTRACT_ADDRESS:
                        self.result_sent = None
                        if log.events_by_type['wasm']['action'][0] == 'buy':
                            self.result_received = Coin.from_data({'amount': log.events_by_type['wasm']['BASE Minted:'][0], 'denom': UBASE})
                        else:
                            # Assumes swaps back from BASE -> LUNC
                            self.result_received = Coin.from_data({'amount': log.events_by_type['wasm']['Net Unstake:'][0], 'denom': ULUNA})
                        log_found = True


                if log_found == False:
                    print ('@TODO: events by type not returned, please check the results:')
                    print (log)

                if result['txs'][0].code == 0:
                    print ('Found the hash!')
                    time.sleep(1)
                    transaction_found = True
                    break
                if result['txs'][0].code == 5:
                    print (' 🛑 A transaction error occurred.')
                    transaction_found = False
                    break

            retry_count += 1

            if retry_count <= SEARCH_RETRY_COUNT:
                print (f'Tx hash not found... attempt {retry_count}/{SEARCH_RETRY_COUNT}')
                time.sleep(1)
            else:
                break

        return transaction_found

    def gasList(self) -> json:
        """
        Make a JSON request for the gas prices, and store it against this LCD client instance.
        This returns a full list of gas tokens, in JSON format:
        {'uluna': '28.325', 'usdr': '0.52469', 'uusd': '0.75', 'ukrw': '850.0', 'umnt': '2142.855', 'ueur': '0.625', 'ucny': '4.9', 'ujpy': '81.85', 'ugbp': '0.55', 'uinr': '54.4', 'ucad': '0.95', 'uchf': '0.7', 'uaud': '0.95', 'usgd': '1.0', 'uthb': '23.1', 'usek': '6.25', 'unok': '6.25', 'udkk': '4.5', 'uidr': '10900.0', 'uphp': '38.0', 'uhkd': '5.85', 'umyr': '3.0', 'utwd': '20.0'}

        If you only want gas in a particular coin, then pass the gas item like this: {'uluna': self.gas_list['uluna']}
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
        
    def readableFee(self) -> str:
        """
        Return a description of the fee for the current transaction.
        If the IBC routes have been populated (ie, this is a swap)l then show them too.
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
            fee_string:str = 'The fee is '
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
    
    def taxRate(self) -> json:
        """
        Query the terra treasury object for the current tax rate.
        We are not caching it so that tax changes will be automatically picked up.

        If this is not a columbus-5 (Luna Classic) chain, then assume the tax rate is zero.
        """

        if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
            self.tax_rate = float(self.terra.treasury.tax_rate())
        else:
            self.tax_rate = 0

        return self.tax_rate