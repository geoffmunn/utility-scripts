#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cryptocode
from datetime import datetime, tzinfo
from dateutil.tz import tz
from hashlib import sha256
import json
import math
import requests
import sqlite3
import time
import yaml

import traceback

from classes.common import (
    coin_list,
    divide_raw_balance,
    getPrecision,
    isDigit,
    multiply_raw_balance,
)
    
from constants.constants import (
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    UBASE,
    WITHDRAWAL_REMAINDER,
)

#from classes.delegations import Delegations
from classes.delegation_transaction import DelegationTransaction
from classes.send_transaction import SendTransaction
from classes.withdrawal_transaction import WithdrawalTransaction
from classes.swap_transaction import SwapTransaction
from classes.terra_instance import TerraInstance
from classes.undelegations import Undelegations

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.distribution import Rewards
from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.bank import MsgSend
from terra_classic_sdk.core.broadcast import BlockTxBroadcastResult
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.distribution.msgs import MsgWithdrawDelegatorReward
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.ibc import Height
from terra_classic_sdk.core.ibc_transfer import MsgTransfer
from terra_classic_sdk.core.market.msgs import MsgSwap
from terra_classic_sdk.core.osmosis import MsgSwapExactAmountIn, Pool, PoolAsset
from terra_classic_sdk.core.staking import (
    MsgBeginRedelegate,
    MsgDelegate,
    MsgUndelegate,
    UnbondingDelegation
)
from terra_classic_sdk.core.staking.data.delegation import Delegation
from terra_classic_sdk.core.staking.data.validator import Validator
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.core.wasm.msgs import MsgExecuteContract
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey
    
# class Delegations():

#     def __init__(self):
#         self.delegations:dict = {}

#     def __iter_result__(self, terra:LCDClient, delegator:Delegation) -> dict:
#         """
#         An internal function which returns a dict object with validator details.
#         """

#         # Get the basic details about the delegator and validator etc
#         delegator_address:str       = delegator.delegation.delegator_address
#         validator_address:str       = delegator.delegation.validator_address
#         validator_details:Validator = terra.staking.validator(validator_address)
#         validator_name:str          = validator_details.description.moniker
#         validator_commission:float  = float(validator_details.commission.commission_rates.rate)
        
#         # Get the delegated amount:
#         balance_denom:str    = delegator.balance.denom
#         balance_amount:float = delegator.balance.amount

#         # Get any rewards
#         rewards:Rewards   = terra.distribution.rewards(delegator_address)
#         reward_coins:dict = coin_list(rewards.rewards[validator_address], {})
        
#         # Make the commission human-readable
#         validator_commission = round(validator_commission * 100, 2)

#         # Set up the object with the details we're interested in
#         if balance_amount > 0:
#             self.delegations[validator_name] = {'balance_amount': balance_amount, 'balance_denom': balance_denom, 'commission': validator_commission, 'delegator': delegator_address, 'rewards': reward_coins, 'validator': validator_address,  'validator_name': validator_name}
        
#     #def create(self, wallet_address:str) -> dict:
#     def create(self, wallet) -> dict:
#         """
#         Create a dictionary of information about the delegations on this wallet.
#         It may contain more than one validator.
#         """

#         #wallet:Wallet = Wallet()
#         #prefix = wallet.getPrefix(wallet_address)
#         prefix = wallet.prefix
#         if prefix == 'terra':
#             if len(self.delegations) == 0:
#                 # Defaults to uluna/terra
#                 terra = TerraInstance().create()

#                 pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
#                 try:
#                     result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

#                     delegator:Delegation 
#                     for delegator in result:
#                         self.__iter_result__(terra, delegator)

#                     while pagination['next_key'] is not None:

#                         pagOpt.key         = pagination['next_key']
#                         result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

#                         delegator:Delegation 
#                         for delegator in result:
#                             self.__iter_result__(terra, delegator)
#                 except:
#                     print (' 🛎️  Network error: delegations could not be retrieved.')

#         return self.delegations
    
class Wallet:
    def __init__(self):
        self.address:str               = ''
        #self.allow_swaps:bool          = False
        self.balances:dict             = None
        self.delegateTx                = DelegationTransaction()
        self.delegations:dict          = {}
        self.delegation_details:dict   = None
        self.denom:str                 = ''
        self.denom_traces:dict         = {}
        #self.has_delegations:bool      = False
        self.undelegation_details:dict = None
        self.name:str                  = ''
        self.prefix:str                = ''     # NOTE: might not be used anymore, replaced by self.denom
        self.seed:str                  = ''
        self.sendTx                    = SendTransaction()
        self.swapTx                    = SwapTransaction()
        self.terra:LCDClient           = None
        self.validated: bool           = False
        self.withdrawalTx              = WithdrawalTransaction()
    
    def __iter_result__(self, terra:LCDClient, delegator:Delegation) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str       = delegator.delegation.delegator_address
        validator_address:str       = delegator.delegation.validator_address
        validator_details:Validator = terra.staking.validator(validator_address)
        validator_name:str          = validator_details.description.moniker
        validator_commission:float  = float(validator_details.commission.commission_rates.rate)
        
        # Get the delegated amount:
        balance_denom:str    = delegator.balance.denom
        balance_amount:float = delegator.balance.amount

        # Get any rewards
        rewards:Rewards   = terra.distribution.rewards(delegator_address)
        reward_coins:dict = coin_list(rewards.rewards[validator_address], {})
        
        # Make the commission human-readable
        validator_commission = round(validator_commission * 100, 2)

        # Set up the object with the details we're interested in
        if balance_amount > 0:
            self.delegations[validator_name] = {'balance_amount': balance_amount, 'balance_denom': balance_denom, 'commission': validator_commission, 'delegator': delegator_address, 'rewards': reward_coins, 'validator': validator_address,  'validator_name': validator_name}
        

    # def allowSwaps(self, allow_swaps:bool) -> bool:
    #     """
    #     Update the wallet with the allow_swaps status.
    #     """

    #     self.allow_swaps = allow_swaps
        
    #     return True
    
    def convertPercentage(self, percentage:float, keep_minimum:bool, target_amount:float, target_denom:str):
        """
        A generic helper function to convert a potential percentage into an actual number.
        """

        percentage:float = float(percentage) / 100
        if keep_minimum == True:
            lunc_amount:float = float((target_amount - WITHDRAWAL_REMAINDER) * percentage)
            if lunc_amount < 0:
                lunc_amount = 0
        else:
            lunc_amount:float = float(target_amount) * percentage
            
        lunc_amount:float = float(str(lunc_amount))
        uluna_amount:int  = int(multiply_raw_balance(lunc_amount, target_denom))
        
        return uluna_amount
    
    def create(self, name:str = '', address:str = '', seed:str = '', password:str = '', denom:str = '') -> Wallet:
        """
        Create a wallet object based on the provided details.
        """

        self.name    = name
        self.address = address

        if seed != '' and password != '':
            self.seed = cryptocode.decrypt(seed, password)

        # If a denom wasn't provided, then figure it out based on the prefix and the CHAIN_DATA dict
        if denom == '':
            prefix = self.getPrefix(self.address)
            for chain_key in [*CHAIN_DATA]:
                if CHAIN_DATA[chain_key]['prefix'] == prefix:
                    denom = chain_key

        self.denom = denom
        
        self.terra = TerraInstance().create(denom)

        return self
    
    # def delegate(self):
    #     """
    #     Update the delegate class with the data it needs
    #     It will be created via the create() command
    #     """

    #     self.delegateTx.seed     = self.seed
    #     self.delegateTx.balances = self.balances

    #     return self.delegateTx
    
    def denomTrace(self, ibc_address:str):
        """
        Based on the wallet prefix, get the IBC denom trace details for this IBC address
        """
        
        result:list = []

        if ibc_address[0:4] == 'ibc/':
            
            value      = ibc_address[4:]
            chain_name = CHAIN_DATA[self.denom]['name']
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
            return False
        else:
            return result
    
    def formatUluna(self, uluna:float, denom:str, add_suffix:bool = False):
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        precision:int = getPrecision(denom)
        lunc:float    = round(float(divide_raw_balance(uluna, denom)), precision)

        target = '%.' + str(precision) + 'f'
        lunc   = (target % (lunc)).rstrip('0').rstrip('.')

        if add_suffix:
            lunc = str(lunc) + ' ' + FULL_COIN_LOOKUP[denom]
        
        return lunc
    
    def getBalances(self, clear_cache:bool = False) -> dict:
        """
        Get the balances associated with this wallet.
        """

        if clear_cache == True:
            self.balances = None

        if self.balances is None:
            # Default pagination options
            pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)

            # Get the current balance in this wallet
            balances:dict = {}
            result:Coins
            try:
                result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)

                # Convert the result into a friendly list
                for coin in result:
                    denom_trace = self.denomTrace(coin.denom)
                    if denom_trace == False:
                        balances[coin.denom] = coin.amount
                    else:
                        balances[denom_trace['base_denom']] = coin.amount

                # Go through the pagination (if any)
                while pagination['next_key'] is not None:
                    pagOpt.key         = pagination["next_key"]
                    result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)
                    
                    denom_trace = self.denomTrace(coin.denom)
                    if  denom_trace == False:
                        balances[coin.denom] = coin.amount
                    else:
                        balances[denom_trace['base_denom']] = coin.amount
            except Exception as err:
                print (f'Pagination error for {self.name}:', err)

            # Add the extra coins (Kuji etc)
            if self.terra.chain_id == 'columbus-5':
                #coin_balance = self.terra.wasm.contract_query(KUJI_SMART_CONTACT_ADDRESS, {'balance':{'address':self.address}})
                #if int(coin_balance['balance']) > 0:
                #    balances[UKUJI] = coin_balance['balance']

                coin_balance = self.terra.wasm.contract_query(BASE_SMART_CONTRACT_ADDRESS, {'balance':{'address':self.address}})
                if int(coin_balance['balance']) > 0:
                    balances[UBASE] = coin_balance['balance']

            self.balances = balances

        return self.balances
    
    # def getDelegations(self) -> dict:
    #     """
    #     Get the delegations associated with this wallet address.
    #     The results are cached so if the list is refreshed then it is much quicker.
    #     """
        
    #     if self.has_delegations == True:
    #         if self.delegation_details is None:
    #             self.delegation_details = Delegations().create()

    #     return self.delegation_details
    
    def getDelegations(self) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        try:
            result, pagination = self.terra.staking.delegations(delegator = self.address, params = pagOpt)

            delegator:Delegation 
            for delegator in result:
                self.__iter_result__(self.terra, delegator)

            while pagination['next_key'] is not None:

                pagOpt.key         = pagination['next_key']
                result, pagination = self.terra.staking.delegations(delegator = self.address, params = pagOpt)

                delegator:Delegation 
                for delegator in result:
                    self.__iter_result__(self.terra, delegator)
        except:
            print (' 🛎️  Network error: delegations could not be retrieved.')

        #wallet:Wallet = Wallet()
        #prefix = wallet.getPrefix(wallet_address)
        
        # prefix = wallet.prefix
        # if prefix == 'terra':
        #     if len(self.delegations) == 0:
        #         # Defaults to uluna/terra
        #         terra = TerraInstance().create()

        #         pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        #         try:
        #             result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

        #             delegator:Delegation 
        #             for delegator in result:
        #                 self.__iter_result__(terra, delegator)

        #             while pagination['next_key'] is not None:

        #                 pagOpt.key         = pagination['next_key']
        #                 result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

        #                 delegator:Delegation 
        #                 for delegator in result:
        #                     self.__iter_result__(terra, delegator)
        #         except:
        #             print (' 🛎️  Network error: delegations could not be retrieved.')

        return self.delegations
    
    def getPrefix(self, address:str) -> str:
        """
        Get the first x (usually 4) letters of the address so we can figure out what network it is
        """

        prefix:str = ''
        for char in address:
            if isDigit(char) == False:
                prefix += char
            else:
                break

        return prefix.lower()
    
    def getUndelegations(self) -> dict:
        """
        Get the undelegations associated with this wallet address.
        The results are cached so if the list is refreshed then it is much quicker.
        """

        if self.undelegation_details is None:
            self.undelegation_details = Undelegations().create(self.address, self.balances)

        return self.undelegation_details
    
    def newWallet(self):
        """
        Creates a new wallet and returns the seed and address
        """

        mk            = MnemonicKey()
        wallet:Wallet = self.terra.wallet(mk)
        
        return mk.mnemonic, wallet.key.acc_address

    def send(self):
        """
        Update the send class with the data it needs.
        It will be created via the create() command.
        """

        self.sendTx.seed     = self.seed
        self.sendTx.balances = self.balances

        return self.sendTx
    
    def swap(self):
        """
        Update the swap class with the data it needs.
        It will be created via the create() command.
        """

        self.swapTx.seed     = self.seed
        self.swapTx.balances = self.balances

        return self.swapTx
    
    # def updateDelegation(self, amount:str, threshold:int) -> bool:
    #     """
    #     Update the delegation details with the amount and threshold details.
    #     """

    #     self.delegations = {'delegate': amount, 'threshold': threshold}

    #     return True
    
    def validateAddress(self, address:str) -> bool:
        """
        Check that the provided address actually resolves to a terra wallet.
        This only applies to addresses which look like terra addresses.
        """

        prefix = self.getPrefix(address)

        # If this is an Osmosis address (or something like that) then we'll just accept it
        if prefix != 'terra':
            return True, False
        
        # We'll run some extra checks on terra addresses
        if address != '':
            try:
                result = self.terra.auth.account_info(address)

                # No need to do anything - if it doesn't return an error then it's valid
                return True, False
            
            except LCDResponseError as err:
                if 'decoding bech32 failed' in err.message:
                    return False, False
                if f'account {address} not found' in err.message:
                    return False, True
                else:
                    return False, False
        else:
            return False, False
        
    def validateWallet(self) -> bool:
        """
        Check that the password does actually resolve against any wallets
        
        Go through each wallet and create it based on the password that was provided
        and then check it against the saved address
        If it's not the same, then the password is wrong or the file has been edited.
        """

        try:
            prefix                   = self.getPrefix(self.address)
            generated_wallet_key     = MnemonicKey(mnemonic=self.seed, prefix = prefix)
            generated_wallet         = self.terra.wallet(generated_wallet_key)
            generated_wallet_address = generated_wallet.key.acc_address
            
            if generated_wallet_address == self.address:
                return True
            else:
                return False
        except:
            return False
    
    def withdrawal(self):
        """
        Update the withdrawal class with the data it needs.
        It will be created via the create() command.
        """

        self.withdrawalTx.seed     = self.seed
        self.withdrawalTx.balances = self.balances

        return self.withdrawalTx
    