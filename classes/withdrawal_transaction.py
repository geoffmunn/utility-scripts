#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from __future__ import annotations

import traceback

from classes.transaction_core import TransactionCore, TransactionResult
from classes.terra_instance import TerraInstance
from classes.wallet import UserWallet

from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)

from terra_classic_sdk.core.distribution.msgs import MsgWithdrawDelegatorReward
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

class WithdrawalTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(WithdrawalTransaction, self).__init__(*args, **kwargs)

        self.delegator_address:str = ''
        self.validator_address:str = ''

    def create(self, seed:str, delegator_address:str, validator_address:str) -> WithdrawalTransaction:
        """
        Create a withdrawal object and set it up with the provided details.
        
        @params:
            - seed: the wallet seed so we can create the wallet
            - delegator_address: usually the wallet address that we are currently using
            - validator_address: the address of the validator we're withdrawing from

        @return: self
        """

        # Create the terra instance
        self.terra = TerraInstance().create()
        
        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        #self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        # Store the delegator and validator addresses
        self.delegator_address:str = delegator_address
        self.validator_address:str = validator_address

        return self
    
    def simulate(self) -> bool:
        """
        Simulate a withdrawal so we can get the fee details.
        The fee details are saved so the actual withdrawal will work.
        
        @params:
            - None

        @return: True/False if the simulation worked.
        """

        # Set the fee to be None so it is simulated
        self.fee      = None
        if self.getSequenceNumber() == False:
            return False
       
                
        self.withdraw()

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
        

    def withdraw(self) -> bool:
        """
        Make a withdrawal with the information we have so far.
        If fee is None then it will be a simulation.
        
        @params:
            - None

        @return: True/False if the withdrawal worked.
        """

        try:
            tx:Tx = None

            msg = MsgWithdrawDelegatorReward(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address
            )
            
            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                #gas_prices = self.gas_list,
                msgs       = [msg]
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
                        print ('An unexpected error occurred in the withdrawal function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the withdrawal function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        except:
            return False
        
def claim_delegation_rewards(wallet:UserWallet, validator_address:str, silent_mode:bool = False) -> TransactionResult:
    """
    A wrapper function for workflows and wallet management.
    This lets the user claim any delegation rewards for the provided validator.
    The wrapper function adds any error messages depending on the results that got returned.

    @note: all rewards are withdrawn, we can't do a partial withdrawal.
    
    @params:
      - wallet: a fully complete wallet object
      - validator_address: the address of the validator in question

    @return: a TransactionResult object
    """

    transaction_result:TransactionResult = TransactionResult()

    # Update the balances so we know what we have available to pay the fee with
    wallet.getBalances()
    
    # Set up the withdrawal object
    withdrawal_tx = WithdrawalTransaction().create(seed = wallet.seed, delegator_address = wallet.address, validator_address = validator_address)

    # We need to populate some details
    withdrawal_tx.balances     = wallet.balances
    withdrawal_tx.silent_mode  = silent_mode
    withdrawal_tx.wallet_denom = wallet.denom
    
    # Simulate it
    withdrawal_result = withdrawal_tx.simulate()

    if withdrawal_result == True:

        if silent_mode == False:
            print (withdrawal_tx.readableFee())

        # Now we know what the fee is, we can do it again and finalise it
        withdrawal_result = withdrawal_tx.withdraw()

        if withdrawal_result == True:
            transaction_result:TransactionResult = withdrawal_tx.broadcast()
        
            # if transaction_result.broadcast_result is not None and transaction_result.broadcast_result.code == 32:
            #     while True:
                    
            #         print (' 🛎️  Boosting sequence number and trying again...')

            #         withdrawal_tx.sequence = withdrawal_tx.sequence + 1
                    
            #         withdrawal_tx.simulate()
            #         withdrawal_tx.withdraw()

            #         transaction_result:TransactionResult = withdrawal_tx.broadcast()

            #         if transaction_result is None:
            #             break

            #         # Code 32 = account sequence mismatch
            #         if transaction_result.broadcast_result.code != 32:
            #             break
                    
            if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error():
                transaction_result.is_error = True
                if transaction_result.broadcast_result is None:
                    transaction_result.message = f' 🛎️ The withdrawal transaction on {wallet.name} failed, no broadcast object was returned.'
                else:
                    if transaction_result.broadcast_result.raw_log is not None:
                        transaction_result.message = f' 🛎️ The withdrawal transaction on {wallet.name} failed, an error occurred:'
                        transaction_result.code    = f' 🛎️ Error code {transaction_result.broadcast_result.code}'
                        transaction_result.log     = f' 🛎️ {transaction_result.broadcast_result.raw_log}'
                    else:
                        transaction_result.message = f' 🛎️ No broadcast log on {wallet.name} was available.'
        
    else:
        transaction_result.message  = f' 🛎️ The withdrawal on {wallet.name} could not be completed.'
        transaction_result.is_error = True

    return transaction_result