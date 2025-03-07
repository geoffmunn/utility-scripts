#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from __future__ import annotations

import math
import time

from classes.common import (
    get_user_choice
)

from constants.constants import (
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    GRDX,
    NON_ULUNA_COINS,
    SEARCH_RETRY_COUNT,
    TERRASWAP_GRDX_TO_LUNC_ADDRESS,
    ULUNA,
    UOSMO,
    UUSD
)

from classes.terra_instance import TerraInstance
from classes.transaction_core import TransactionCore, TransactionResult
from classes.wallet import UserWallet

from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.core.bank import MsgSend
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.ibc import Height
from terra_classic_sdk.core.ibc_transfer import MsgTransfer
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.core.wasm.msgs import MsgExecuteContract
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

class SendTransaction(TransactionCore):
    def __init__(self, *args, **kwargs):

        super(SendTransaction, self).__init__(*args, **kwargs)

        self.amount:int            = 0
        self.block_height:int      = None
        self.denom:str             = ''
        self.fee:Fee               = None
        self.fee_deductables:float = None
        self.gas_limit:str         = 'auto'
        self.is_ibc_transfer:bool  = False
        self.is_on_chain:bool      = True
        self.memo:str              = ''
        self.receiving_denom:str   = ''
        self.recipient_address:str = None
        self.recipient_prefix:str  = ''
        self.revision_number:int   = None
        self.sender_address:str    = None
        self.sender_prefix:str     = ''
        self.source_channel:str    = None
        self.tax:float             = None

    def create(self, seed:str, denom:str = 'uluna') -> SendTransaction:
        """
        Create a send object and set it up with the provided details.
        
        @params:
            - seed: the wallet seed so we can create the wallet
            - denom: what denomination are we sending? It will usually be LUNC

        @return: self
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

    def send(self) -> bool:
        """
        Complete a send transaction with the information we have so far.
        If fee is None then it will be a simulation.
        The fee denomination must be uluna - it is the only one we are supporting.
        
        @params:
            - None

        @return: True/False depending on if the transaction succeeded
        """

        send_amount = int(self.amount)

        if self.fee_deductables is not None:
            if int(send_amount + self.tax) > int(self.balances[self.denom]):
                send_amount = int(send_amount - self.fee_deductables)

        try:
            tx:Tx = None

            if self.denom in NON_ULUNA_COINS.values():
                if self.denom == GRDX:
                    contract_address = TERRASWAP_GRDX_TO_LUNC_ADDRESS
                else:
                    contract_address = (list(NON_ULUNA_COINS.keys())[list(NON_ULUNA_COINS.values()).index(self.denom)])

                msg = MsgExecuteContract(
                    sender      = self.current_wallet.key.acc_address,
                    contract    = contract_address,
                    msg = {
                        "transfer": {
                            "amount": str(send_amount),
                            "recipient": self.recipient_address
                        }
                    }
                )

            else:
                msg = MsgSend(
                    from_address = self.current_wallet.key.acc_address,
                    to_address   = self.recipient_address,
                    amount       = Coins(str(int(send_amount)) + self.denom)
                )

            options = CreateTxOptions(
                account_number = self.account_number,
                fee            = self.fee,
                fee_denoms     = ['uluna'],
                gas            = str(self.gas_limit),
                gas_prices     = self.gas_list,
                memo           = self.memo,
                msgs           = [msg],
                sequence       = self.sequence
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
                        print (' 🛑 An unexpected error occurred in the on-chain send function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the on-chain send function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except Exception as err:
            print (' 🛑 An unexpected error occurred in the on-chain send function:')
            print (err)
            return False
        
    def sendOffchain(self) -> bool:
        """
        Complete a send transaction with the information we have so far.
        If fee is None then it will be a simulation.
        
        @params:
            - None

        @return: True/False depending on if the transaction succeeded
        """

        send_amount = int(self.amount)

        if self.fee_deductables is not None:
            if int(send_amount + self.tax) > int(self.balances[self.denom]):
                send_amount = int(send_amount - self.fee_deductables)

        try:
            tx:Tx = None

            if self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
                revision_number = 1
            else:
                revision_number = 6

            if self.denom != self.wallet_denom:
                send_denom = self.IBCfromDenom(self.source_channel, self.denom)

                token = {
                    "amount": str(send_amount),
                    "denom": send_denom
                }
            else:
                token = Coin(self.denom, send_amount)

            msg = MsgTransfer(
                source_port       = 'transfer',
                source_channel    = self.source_channel,
                token             = token,
                sender            = self.sender_address,
                receiver          = self.recipient_address,
                timeout_height    = Height(revision_number = revision_number, revision_height = self.block_height),
                timeout_timestamp = 0
            )
                                
            options = CreateTxOptions(
                account_number = str(self.account_number),
                sequence       = str(self.sequence),
                msgs           = [msg],
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = self.gas_list
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
                        print (' 🛑 An unexpected error occurred in the off-chain send function:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 An unexpected error occurred in the off-chain send function:')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        except Exception as err:
            print (' 🛑 An unexpected error occurred in the off-chain send function:')
            print (err)
            return False
    
    def simulate(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.

        Outputs:
        self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
        self.tax - the tax component
        self.fee_deductables - the amount we need to deduct off the transferred amount
        
        @params:
            - None

        @return: True/False depending on if the transaction succeeded
        """

        # Reset these values in case this is a re-used object:
        self.account_number  = self.current_wallet.account_number()
        self.fee             = None
        self.fee_deductables = None
        self.prices          = None
        self.tax             = None
        #self.sequence        = self.current_wallet.sequence()
        if self.getSequenceNumber() == False:
            return False

        # If the send amount denom is NOT the native denom of the chain, then convert it to the IBC value
        # Eg, send LUNC on Osmosis -> Osmosis
        if self.terra.chain_id == CHAIN_DATA[UOSMO]['chain_id'] and self.denom != UOSMO:
            self.denom = self.IBCfromDenom(self.source_channel, self.denom)

        # Perform the swap as a simulation, with no fee details
        self.send()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            #if wallet.terra.chain_id == CHAIN_DATA[wallet.getDenomByPrefix(send_tx.recipient_prefix)]['chain_id']:
            
            self.fee = self.calculateFee(requested_fee = requested_fee, specific_denom = ULUNA, convert_to_ibc = self.is_ibc_transfer)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom
        
            # Calculate the tax portion.
            # The tax is now calculated by the chain, no need for any alterations now.
            self.tax = 0
            
            # if self.denom in NON_ULUNA_COINS.values():
            #     # No taxes for BASE and GRDX transfers
            #     self.tax = 0
            # else:
            #     self.tax = int(math.ceil(self.amount * float(self.tax_rate)))

            # Build a fee object
            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            # if fee_denom == ULUNA and self.denom == ULUNA:
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            # elif self.denom in NON_ULUNA_COINS.values():
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
            # else:
            #     new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.denom, int(self.tax))})

            # If the chain is Osmosis then adjust the fee amount    
            if self.terra.chain_id != CHAIN_DATA[ULUNA]['chain_id']:
                fee_amount = fee_amount * 1.2

                # Change the denom to an IBC version
                fee_denom = self.IBCfromDenom(self.source_channel, fee_denom)

                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Fee deductibles are the total cost of this transaction.
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.denom:
                # If the fee denom is the same as what we're paying the tax in, then combine the two
                self.fee_deductables = int(fee_amount)

            # if self.tax > 0:
            #     if fee_denom == self.denom:
            #         # If the fee denom is the same as what we're paying the tax in, then combine the two
            #         self.fee_deductables = int(fee_amount + self.tax)
            #     elif fee_denom == ULUNA and self.denom == UUSD:
            #         # If this is UUSD transfer then the deductible is just the tax
            #         self.fee_deductables = int(self.tax)
            #     else:
            #         # Everything else incurs a 2x tax (@TODO give exmaples)
            #         self.fee_deductables = int(self.tax * 2)

            return True
        else:
            return False
        
    def simulateOffchain(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.

        Outputs:
        self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
        self.tax - the tax component
        self.fee_deductables - the amount we need to deduct off the transferred amount
        
        @params:
            - None

        @return: True/False depending on if the transaction succeeded
        """

        # Reset these values in case this is a re-used object:
        self.account_number  = self.current_wallet.account_number()
        self.fee             = None
        self.fee_deductables = None
        self.prices          = None
        self.tax             = None
        #self.sequence        = self.current_wallet.sequence()

        if self.getSequenceNumber() == False:
            return False

        #self.gas_limit = '241946'
        # Set a specific gas limit because 'auto' is too high
        self.gas_limit = '250000'
        
        #self.gas_limit = '200000'
        # Perform the swap as a simulation, with no fee details
        self.sendOffchain()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            
            # If we are sending from an offChain network, then the fee needs to be converted to IBC values
            if self.terra.chain_id != CHAIN_DATA[ULUNA]['chain_id']:
                self.fee = self.calculateFee(requested_fee, ULUNA, True)
            else:
                self.fee = self.calculateFee(requested_fee, ULUNA)    

            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
        
            self.tax = 0
            
            # For osmosis-1 transfers, we need to adjust the fee:
            fee_amount    = fee_amount * 1.2
            fee_denom:str = fee_bit.denom

            # Create the coin object
            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            # This will be used by the swap function next time we call it
            self.fee.amount = new_coin

            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            self.fee_deductables = int(fee_amount)
            
            return True
        else:
            return False
        
def send_transaction(wallet:UserWallet, recipient_address:str, send_coin:Coin, memo:str = '', silent_mode:bool = False) -> TransactionResult:
    """
    A wrapper function for workflows and wallet management.
    This lets the user send a LUNC or USTC amount to supported address.
    This could be a terra, osmo, or an IBC destination.
    The wrapper function adds any error messages depending on the results that got returned.
    
    @params:
      - wallet: a fully complete wallet object
      - recipient: the address of the recipient in question
      - send_coin: a fully complete Coin object. We get the amount and denom from this
      - memo: optional text to include
      - prompt_user: do we want to pause for user confirmation?

    @return: a TransactionResult object
    """

    transaction_result:TransactionResult = TransactionResult()

    send_tx = SendTransaction().create(wallet.seed, wallet.denom)
        
    # Populate it with required details:
    send_tx.balances          = wallet.balances
    send_tx.recipient_address = recipient_address
    send_tx.recipient_prefix  = wallet.getPrefix(recipient_address)
    send_tx.sender_address    = wallet.address
    send_tx.sender_prefix     = wallet.getPrefix(wallet.address)
    send_tx.silent_mode       = silent_mode
    send_tx.wallet_denom      = wallet.denom
    
    # Based on the recipient prefix, get the receiving denomination
    send_tx.receiving_denom   = wallet.getDenomByPrefix(send_tx.recipient_prefix)

    # If the chain ID of the wallet and the recipient prefix native chain are then same, then it's an on-chain tx
    #if wallet.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id'] and send_tx.recipient_prefix == CHAIN_DATA[ULUNA]['bech32_prefix']:
    if wallet.terra.chain_id == 'columbus-5' and wallet.terra.chain_id == CHAIN_DATA[wallet.getDenomByPrefix(send_tx.recipient_prefix)]['chain_id']:
        send_tx.is_on_chain     = True
        send_tx.revision_number = 1
        # This is required if the chain id is NOT a terra chain (columbus-5).
        # For example, Osmosis transfers require LUNC to be converted into the IBC denom
        if CHAIN_DATA[send_tx.receiving_denom]['chain_id'] != CHAIN_DATA[ULUNA]['chain_id']:
            send_tx.source_channel = CHAIN_DATA[UOSMO]['ibc_channels'][ULUNA]

        send_tx.denom = send_coin.denom

    else:
        send_tx.is_on_chain = False

        send_tx.source_channel = CHAIN_DATA[wallet.denom]['ibc_channels'][send_tx.receiving_denom]
        
        if wallet.terra.chain_id == CHAIN_DATA[UOSMO]['chain_id']:
            send_tx.revision_number = 6
        else:
            send_tx.revision_number = 1

        send_tx.denom = send_coin.denom
    
    # Assign the remaining user provided details:
    send_tx.memo         = memo
    send_tx.amount       = int(send_coin.amount)
    send_tx.block_height = send_tx.terra.tendermint.block_info()['block']['header']['height']
        
    # Simulate it            
    if send_tx.is_on_chain == True:
        send_result = send_tx.simulate()
    else:
        send_result = send_tx.simulateOffchain()
    
    # Now complete it
    if send_result == True:

        if silent_mode == False:
            print ('')
            print(f'  ➜ You are about to send {wallet.formatUluna(send_coin.amount, send_coin.denom)} {FULL_COIN_LOOKUP[send_coin.denom]} to {recipient_address}')
            print (send_tx.readableFee())
            print ('')
            user_choice = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

            if user_choice == False:
                print ('\n 🛑 Exiting...\n')
                exit()
        
        recipient_wallet:UserWallet = UserWallet().create('Recipient wallet', send_tx.recipient_address)
        recipient_wallet.getBalances()

        # Get the recipient current balance before the tx so we can compare it for success
        old_balance:int = 0
        if send_tx.denom in recipient_wallet.balances:
            old_balance = int(recipient_wallet.balances[send_tx.denom])

        # Now we know what the fee is, we can do it again and finalise it
        if send_tx.is_on_chain == True:
            send_result = send_tx.send()
        else:
            send_result = send_tx.sendOffchain()
        
        if send_result == True:
            
            transaction_result:TransactionResult = send_tx.broadcast()

            if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error() or transaction_result.is_error == True:
                transaction_result.is_error = True
                if transaction_result.broadcast_result is None:
                    transaction_result.message = f' 🛎️  The send transaction on {wallet.name} failed, no broadcast object was returned.'
                else:
                    if transaction_result.broadcast_result.raw_log is not None:
                        transaction_result.message = f' 🛎️  The send transaction on {wallet.name} failed, an error occurred.'
                        transaction_result.code    = transaction_result.broadcast_result.code
                        transaction_result.log     = transaction_result.broadcast_result.raw_log
                    else:
                        transaction_result.message = f' 🛎️  No broadcast log on {wallet.name} was available.'
            else:
                # Check that the recipient wallet has been updated
                # To keep things simple, we'll only check for increased balances
                retry_count:int = 0
                if silent_mode == False:
                    print (f'\n 🔎︎ Checking that the recipient has this transaction...')
                while True:
                    recipient_wallet.getBalances()
                    new_balance:int = 0
                    if send_tx.denom in recipient_wallet.balances:
                        new_balance = int(recipient_wallet.balances[send_tx.denom])

                    if new_balance > old_balance:
                        break
                    
                    retry_count += 1

                    if retry_count <= SEARCH_RETRY_COUNT:
                        if silent_mode == False:
                            print (f'    Search attempt {retry_count}/{SEARCH_RETRY_COUNT}')
                        time.sleep(1)
                    else:
                        break


        else:
            transaction_result.message  = f' 🛎️  The send transaction on {wallet.name} could not be completed.'
            transaction_result.is_error = True
    else:
        transaction_result.message  = f' 🛎️  The send transaction on {wallet.name} could not be completed.'
        transaction_result.is_error = True


    # Store the delegated amount for display purposes
    transaction_result.transacted_amount = wallet.formatUluna(send_coin.amount, send_coin.denom, True)
    transaction_result.label             = 'Sent amount'

    return transaction_result