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
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    GAS_PRICE_URI,
    SEARCH_RETRY_COUNT,
    TAX_RATE_URI,
    ULUNA,
    UUSD
)

from classes.wallet import UserWallet

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.tx import (
    Tx
)
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.broadcast import BlockTxBroadcastResult
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
        self.fee:Fee                                 = None
        self.gas_list:json                           = None
        self.gas_price_url:str                       = None
        self.height:int                              = None
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
                ibc_value = 'ibc/' + sha256(f'transfer/{self.source_channel}/{self.denom}'.encode('utf-8')).hexdigest().upper()
                requested_fee.amount = Coins({Coin(ibc_value, has_uluna)})
            else:
                if specific_denom != '':
                    requested_fee.amount = Coins({Coin(specific_denom, specific_denom_amount)})
        else:
            print ('Not enough funds to pay for this transaction!')

        return requested_fee

    def findTransaction(self) -> bool:
        """
        Do a search for any transaction with the current tx hash.
        If it can't be found within 10 attempts, then give up.
        """

        # Store the current block here - needed for transaction searches
        self.height = self.terra.tendermint.block_info()['block']['header']['height']

        transaction_found:bool = False

        result:dict = self.terra.tx.search([
            ("message.sender", self.current_wallet.key.acc_address),
            ("message.recipient", self.current_wallet.key.acc_address),
            ('tx.hash', self.broadcast_result.txhash),
            ('tx.height', self.height)
        ])

        retry_count = 0
        while True:
            if len(result['txs']) > 0:
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
                print ('Tx hash not found, giving it another go')
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
                    self.gas_list = gas_list
                else:
                    print (' 🛑 No gas price URL set at self.gas_price_url')
                    exit()
            except:
                print (' 🛑 Error getting gas prices')
                print (requests.get(self.gas_price_url).content)
                exit()

        return self.gas_list
    
    def getPrices(self, from_denom:str, to_denom:str) -> json:
        """
        Get the current USD prices for two different coins.
        From: swap_denom
        To: request_denom

        If the link doesn't work, we'll try 10 times
        """

        retry_count:int  = 0
        retry:bool       = True
        prices:json      = {}
        from_price:float = None
        to_price:float   = None

        # Get the chains that we are using
        from_id:dict = CHAIN_DATA[from_denom]
        to_id:dict   = CHAIN_DATA[to_denom]

        if from_id != False and to_id != False:
            while retry == True:
                try:
                    uri:str = f"https://api-indexer.keplr.app/v1/price?ids={from_id['keplr_name']},{to_id['keplr_name']}&vs_currencies=usd"
                    prices:json = requests.get(uri).json()

                    # Exit the loop if this hasn't returned an error
                    retry = False

                except Exception as err:
                    retry_count += 1
                    if retry_count == 10:
                        print (' 🛑 Error getting coin prices')
                        print (err)

                        retry = False
                        exit()
                    else:
                        time.sleep(1)

            from_price:float = prices[from_id['keplr_name']]['usd']
            to_price:float   = prices[to_id['keplr_name']]['usd']
        
        return {'from':from_price, 'to': to_price}
        
    def readableFee(self) -> str:
        """
        Return a description of the fee for the current transaction.
        """
        
        fee_string:str = ''
        if self.fee is not None and self.fee.amount is not None:
            fee_coins:Coins = self.fee.amount

            # Build a human-readable fee description:
            fee_string = 'The fee is '
            first      = True
            for fee_coin in fee_coins.to_list():

                amount = divide_raw_balance(fee_coin.amount, fee_coin.denom)
                amount = ("%.6f" % (amount)).rstrip('0').rstrip('.')

                wallet = UserWallet()
                wallet.address = self.sender_address
                wallet.denom = self.wallet_denom

                ibc_denom = wallet.denomTrace(fee_coin.denom)

                if ibc_denom == False:
                    denom  = FULL_COIN_LOOKUP[fee_coin.denom]
                else:
                    denom = FULL_COIN_LOOKUP[ibc_denom['base_denom']]

                if first == False:
                    fee_string += ', and ' + str(amount) + ' ' + denom
                else:
                    fee_string += str(amount) + ' ' + denom

                first = False

        return fee_string
    
    def taxRate(self) -> json:
        """
        Make a JSON request for the tax rate, and store it against this LCD client instance.
        """

        if self.tax_rate is None:

            try:
                tax_rate:json = requests.get(TAX_RATE_URI).json()
                self.tax_rate = tax_rate
            except:
                print (' 🛑 Error getting the tax rate')
                print (requests.get(self.gas_price_url).content)
                exit()

        return self.tax_rate