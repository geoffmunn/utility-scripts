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

from classes.terra_instance import TerraInstance

# from classes.common import (
#     multiply_raw_balance
# )

from constants.constants import (
    UBASE
)

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
    
class Undelegations(Wallet):

    def __init__(self):
        self.undelegations:dict = {}

    def __iter_result__(self, undelegation:UnbondingDelegation) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str = undelegation.delegator_address
        validator_address:str = undelegation.validator_address
        entries:list          = []

        for entry in undelegation.entries:
            entries.append({'balance': entry.balance, 'completion_time': entry.completion_time.strftime('%m/%d/%Y')})
       
        # Get the total balance from all the entries
        balance_total:int = 0
        for entry in entries:
            balance_total += entry['balance']

        # Set up the object with the details we're interested in
        self.undelegations[validator_address] = {'balance_amount': balance_total, 'delegator_address': delegator_address, 'validator_address': validator_address, 'entries': entries}
 
    def getUbaseUndelegations(self, wallet_address:str) -> list:
        """
        Get the undelegations that are in progress for BASE.

        This returns a list of the active undelegations.
        """

        result:json  = requests.get('https://raw.githubusercontent.com/lbunproject/BASEswap-api-price/main/public/unstaked_plus_hashes.json').json()
        results:list = []
        today        = datetime.now()

        for undelegation in result:
            if datetime.strptime(undelegation['releaseDate'], '%m/%d/%Y') > today:
                if undelegation['sendTo'] == wallet_address:
                    results.append(undelegation)
            else:
                break

        return results
    
    def create(self, wallet_address:str, balances:dict) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        prefix = self.getPrefix(wallet_address)

        if prefix == 'terra':
            if len(self.undelegations) == 0:
                # Defaults to uluna/terra
                terra = TerraInstance().create()

                pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
                try:
                
                    result, pagination = terra.staking.unbonding_delegations(delegator = wallet_address, params = pagOpt)

                    unbonding:UnbondingDelegation
                    for unbonding in result:

                        self.__iter_result__(unbonding)

                    while pagination['next_key'] is not None:

                        pagOpt.key         = pagination['next_key']
                        result, pagination = terra.staking.unbonding_delegations(delegator = wallet_address, params = pagOpt)

                        unbonding:UnbondingDelegation
                        for unbonding in result:
                            self.__iter_result__(unbonding)

                except Exception as err:
                    print (' 🛎️  Network error: undelegations could not be retrieved.')
                    print (err)
                    

        # Get any BASE undelegations currently in progress
        if 'ubase' in balances:
            base_undelegations       = self.getUbaseUndelegations(wallet_address)
            undelegated_amount:float = 0
            entries:list             = []
            
            utc_zone = tz.gettz('UTC')
            base_zone = tz.gettz('US/Eastern')

            for base_item in base_undelegations:
                undelegated_amount += base_item['luncNetReleased']

                # Convert the BASE date to a UTC format
                # First, we need to swap it to a d/m/y format
                release_date_bits = base_item['releaseDate'].split('/')
                release_date      = f"{release_date_bits[1]}/{release_date_bits[0]}/{release_date_bits[2]}" 
                base_time         = datetime.strptime(release_date, '%d/%m/%Y')

                # Now give it the timezone that BASE works in
                base_time = base_time.replace(tzinfo = base_zone)
                # Convert time to UTC
                utc_time = base_time.astimezone(utc_zone)
                # Generate UTC time string
                utc_string = utc_time.strftime('%d/%m/%Y')

                entries.append({'balance': multiply_raw_balance(base_item['luncNetReleased'], UBASE), 'completion_time': utc_string})
            
            self.undelegations['base'] = {'balance_amount': multiply_raw_balance(undelegated_amount, UBASE), 'entries': entries}

        return self.undelegations
