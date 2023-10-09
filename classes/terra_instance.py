#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from constants.constants import (
    CHAIN_DATA,
    GAS_ADJUSTMENT
)

from terra_classic_sdk.client.lcd import LCDClient
    
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
    