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

class Validators():

    def __init__(self):        
        self.validators:dict            = {}
        self.sorted_validators:dict     = {}
        self.validators_by_address:dict = {}

    def __iter_result__(self, validator:Validator) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about validator
        commission       = validator.commission
        details          = validator.description.details
        identity         = validator.description.identity
        is_jailed        = validator.jailed
        moniker          = validator.description.moniker
        operator_address = validator.operator_address
        status           = validator.status
        token_count      = validator.tokens
        unbonding_time   = validator.unbonding_time
        
        commision_rate   = int(commission.commission_rates.rate * 100)

        self.validators[moniker] = {'commission': commision_rate, 'details': details, 'identity': identity, 'is_jailed': is_jailed, 'moniker': moniker, 'operator_address': operator_address, 'status': status, 'token_count': token_count, 'unbonding_time': unbonding_time, 'voting_power': 0}
        
    def create(self) -> dict:
        """
        Create a dictionary of information about the validators that are available.
        """

        # Defaults to uluna/terra
        terra = TerraInstance().create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        result, pagination       = terra.staking.validators(params = pagOpt)

        validator:Validator
        for validator in result:
            self.__iter_result__(validator)

        while pagination['next_key'] is not None:

            pagOpt.key         = pagination['next_key']
            result, pagination = terra.staking.validators(params = pagOpt)
            
            validator:Validator
            for validator in result:
                self.__iter_result__(validator)

        # Go through each validator and create an ordered list
        sorted_validators:dict = {}

        # Calculate the voting power for each validator:
        coin_total = 0
        for validator in self.validators:
            coin_total += int(self.validators[validator]['token_count'])

        for validator in self.validators:

            moniker = self.validators[validator]['moniker']

            self.validators[validator]['voting_power'] = (int(self.validators[validator]['token_count']) / coin_total) * 100

            key = self.validators[validator]['token_count']
            if key not in sorted_validators:
                sorted_validators[moniker] = {}
            
            current:dict               = sorted_validators[moniker]
            current[moniker]           = self.validators[validator]['voting_power']
            sorted_validators[moniker] = key

        sorted_list:list = sorted(sorted_validators.items(), key=lambda x:x[1], reverse=True)[0:len(sorted_validators)]
        sorted_validators = dict(sorted_list)

        # Populate the sorted list with the actual validators
        for validator in sorted_validators:
            sorted_validators[validator] = self.validators[validator]
            self.validators_by_address[self.validators[validator]['operator_address']] = self.validators[validator]

        self.sorted_validators = sorted_validators

        return self.validators
