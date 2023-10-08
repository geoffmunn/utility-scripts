#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from constants.constants import (
    CHAIN_DATA,
    GAS_ADJUSTMENT
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
    
class TerraInstance:
    def __init__(self):
        self.gas_adjustment = float(GAS_ADJUSTMENT)
        self.terra          = None
        
    def create(self, denom:str = 'uluna') -> LCDClient:
        """
        Create an LCD client instance and store it in this object.
        """
        
        if denom in CHAIN_DATA:
            self.chain_id = CHAIN_DATA[denom]['chain_id']
            self.url      = CHAIN_DATA[denom]['lcd_urls'][0]
            
            if self.chain_id == 'osmosis-1':
                gas_prices = '1uosmo,1uluna'
            else:
                gas_prices = None

            terra:LCDClient = LCDClient(
                chain_id       = self.chain_id,
                gas_adjustment = float(self.gas_adjustment),
                url            = self.url,
                gas_prices     = gas_prices
            )

            self.terra = terra
        
        return self.terra

    def instance(self) -> LCDClient:
        """
        Return the LCD client instance that we have created.
        """
        return self.terra
    