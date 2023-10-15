#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# from classes.common import (
#     CHAIN_DATA
# )

from constants.constants import (
    CHAIN_DATA,
    ULUNA
)

from classes.transaction_core import TransactionCore
from classes.terra_instance import TerraInstance
from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.staking import (
    MsgBeginRedelegate,
    MsgDelegate,
    MsgUndelegate,
)
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

class DelegationTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        self.action:str                = ''
        self.delegator_address:str     = ''
        self.delegated_uluna:int       = 0
        self.sender_address:str        = ''
        self.sender_prefix:str         = ''
        self.validator_address_old:str = ''
        self.validator_address:str     = ''

        super(DelegationTransaction, self).__init__(*args, **kwargs)
        
    def create(self, seed:str, denom:str = 'uluna'):
        """
        Create a delegation object and set it up with the provided details.
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
    
    def delegate(self) -> bool:
        """
        Make a delegation with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msg = MsgDelegate(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address,
                amount            = Coin(ULUNA, self.delegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msg],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    # This is code 32:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print ('An unexpected error occurred in the delegation function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the delegation function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
            return False
        
    def redelegate(self):
        """
        Redelegate funds from one validator to another.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msgRedel = MsgBeginRedelegate(
                validator_dst_address = self.validator_address,
                validator_src_address = self.validator_address_old,
                delegator_address     = self.delegator_address,
                amount                = Coin(ULUNA, self.delegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msgRedel],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
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
                        print ('An unexpected error occurred in the redelegation function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the redelegation function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
            return False 
    
    def simulate(self, action) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        The fee details are saved so the actual delegation will work.
        """

        # Set the fee to be None so it is simulated
        self.fee = None
        if self.sequence is None:
            self.sequence = self.current_wallet.sequence()
        
        # This is a provided function. Depending on the original function, we might be delegating or undelegating
        action()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            self.fee = self.calculateFee(requested_fee)

            return True
        else:
            return False
        
    def undelegate(self):
        """
        Undelegate funds from the provided validator
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msg = MsgUndelegate(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address,
                amount            = Coin(ULUNA, int(self.delegated_uluna))
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msg],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
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
                        print ('An unexpected error occurred in the undelegation function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the undelegation function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
           return False
        
