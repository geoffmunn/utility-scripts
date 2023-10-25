#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from datetime import datetime

from constants.constants import (
    GAS_ADJUSTMENT_INCREMENT,
    MAX_GAS_ADJUSTMENT,
    MAX_VALIDATOR_COUNT,
    UBASE,
    ULUNA,
    USER_ACTION_QUIT,
    USER_ACTION_VALIDATOR_DELEGATE,
    USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS,
    USER_ACTION_VALIDATOR_UNDELEGATE,
    USER_ACTION_VALIDATOR_SWITCH,
    WITHDRAWAL_REMAINDER
)

from classes.common import (
    check_version,
    get_user_choice,
)

from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.validators import Validators

def main():

    # today = datetime.now()
    # test_date = datetime.strptime('4/23/2023', '%m/%d/%Y')

    # print (today)
    # print (test_date)

    # diff = (test_date-today).days
    # print (diff)
    # exit()

    # Check if there is a new version we should be using
    check_version()

    # Get the user wallets
    wallets      = UserWallets()
    user_wallets = wallets.loadUserWallets()

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getBalances()
        wallet.getDelegations()

    if len(user_wallets) > 0:
        print (f'You have these wallets available:')

        wallet, answer = wallets.getUserSinglechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue, or 'Q' to quit: ", True)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # Get the desired actions
    print ('\nWhat action do you want to take?\n')
    print ('  (D)  Delegate to a validator')
    print ('  (U)  Undelegate coins from a validator')
    print ('  (S)  Switch validators')
    print ('  (L)  List undelegations in progress')
    print ('  (Q)  Quit\n')
    
    user_action = get_user_choice('Pick an option: ', [
        USER_ACTION_VALIDATOR_DELEGATE,
        USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS,
        USER_ACTION_VALIDATOR_UNDELEGATE,
        USER_ACTION_VALIDATOR_SWITCH,
        USER_ACTION_QUIT
    ])

    if user_action == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    print ('\nGetting available validators - please wait...')

    validators = Validators()
    validators.create()

    sorted_validators:dict = validators.sorted_validators

    if len(sorted_validators) == 0:
        print (' 🛑 No validators could be retrieved - perhaps there are network issues?')
        exit()

    delegations:dict = wallet.getDelegations()

    if user_action == USER_ACTION_VALIDATOR_DELEGATE:

        print (f'Select a validator to delegate to:')

        max_number:int = len(sorted_validators)
        if max_number > MAX_VALIDATOR_COUNT:
            max_number = MAX_VALIDATOR_COUNT

        user_validator, answer = validators.getValidatorSingleChoice("Select a validator number 1 - " + str(max_number) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, [], delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[ULUNA], ULUNA, True)}")
        print (f"NOTE: A minimum amount of {WITHDRAWAL_REMAINDER} LUNC will be retained for future transactions.")
        delegated_uluna:float = wallet.getUserNumber('How much are you delegating? ', {'max_number': float(wallet.formatUluna(wallet.balances[ULUNA], ULUNA)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': True})
                
        if delegated_uluna == 0:
            print (' 🛑 Delegated amount is zero, exiting...\n')
            exit()

        print (f"You are about to delegate {wallet.formatUluna(delegated_uluna, ULUNA, True)} to {user_validator['moniker']}.")
        complete_transaction = get_user_choice('Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Delegating {wallet.formatUluna(delegated_uluna, ULUNA, True)}...')
        
        # Create the delegation object
        delegation_tx = wallet.delegate().create()
        
        # Assign the details
        delegation_tx.delegator_address = wallet.address
        delegation_tx.validator_address = user_validator['operator_address']
        delegation_tx.delegated_uluna   = delegated_uluna
        delegation_tx.sender_address    = wallet.address
        delegation_tx.sender_prefix     = wallet.getPrefix(wallet.address)
        delegation_tx.wallet_denom      = wallet.denom

        # Simulate it
        result = delegation_tx.simulate(delegation_tx.delegate)

        if result == True:
                
            print (delegation_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = delegation_tx.delegate()
            
            if result == True:
                delegation_tx.broadcast()
            
                if delegation_tx.broadcast_result.code == 11:
                    while True:
                        print (' 🛎️  Increasing the gas adjustment fee and trying again')
                        delegation_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                        print (f' 🛎️  Gas adjustment value is now {delegation_tx.terra.gas_adjustment}')
                        delegation_tx.simulate(delegation_tx.delegate)
                        print (delegation_tx.readableFee())
                        delegation_tx.delegate()
                        delegation_tx.broadcast()

                        if delegation_tx.broadcast_result.code != 11:
                            break

                        if delegation_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                            break
                    
                if delegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The delegation failed, an error occurred:')
                    print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, ULUNA, True)}')
                    print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The delegation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')

    if user_action == USER_ACTION_VALIDATOR_UNDELEGATE:
        print (f'Select a validator to undelegate from:')

        # Get the validators currently being used
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        user_validator, answer = validators.getValidatorSingleChoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        available_undelegation_uluna:int = delegations[user_validator['moniker']]['balance_amount']

        print (f"The {wallet.name} wallet has {wallet.formatUluna(available_undelegation_uluna, ULUNA, True)} available to be undelegated.")
        print (f"NOTE: You can send the entire value of this delegation by typing '100%' - no minimum amount will be retained.")
        undelegated_uluna:str = wallet.getUserNumber('How much are you undelegating? ', {'max_number': float(wallet.formatUluna(available_undelegation_uluna, ULUNA, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False})
        
        print (f"You are about to undelegate {wallet.formatUluna(undelegated_uluna, ULUNA, True)} from {user_validator['moniker']}.")
        print (' 🛎️  Undelegated funds will not be available for 21 days.')
        complete_transaction = get_user_choice('Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Undelegating {wallet.formatUluna(undelegated_uluna, ULUNA, True)}...')

        # Create the delegation object    
        undelegation_tx = wallet.delegate().create()

        # Assign the details
        undelegation_tx.delegator_address = wallet.address
        undelegation_tx.validator_address = user_validator['operator_address']
        undelegation_tx.delegated_uluna   = undelegated_uluna
        undelegation_tx.wallet_denom      = wallet.denom

        # Simulate it
        result = undelegation_tx.simulate(undelegation_tx.undelegate)

        if result == True:
                
            print (undelegation_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = undelegation_tx.undelegate()

            if result == True:
                undelegation_tx.broadcast()
            
                if undelegation_tx.broadcast_result.code == 11:
                    while True:
                        print (' 🛎️  Increasing the gas adjustment fee and trying again')
                        undelegation_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                        print (f' 🛎️  Gas adjustment value is now {undelegation_tx.terra.gas_adjustment}')
                        undelegation_tx.simulate(undelegation_tx.undelegate)
                        print (undelegation_tx.readableFee())
                        undelegation_tx.undelegate()
                        undelegation_tx.broadcast()

                        if undelegation_tx.broadcast_result.code != 11:
                            break

                        if undelegation_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                            break

                if undelegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The undelegation failed, an error occurred:')
                    print (f' 🛎️  {undelegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Undelegated amount: {wallet.formatUluna(undelegated_uluna, ULUNA, True)}')
                    print (f' ✅ Tx Hash: {undelegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The undelegation could not be completed')
        else:
            print ('🛎️  The undelegation could not be completed')
        
    if user_action == USER_ACTION_VALIDATOR_SWITCH:
        # Get the validators currently being used
        
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        print (f'Select a validator to delegate switch FROM:')
        from_validator, answer = validators.getValidatorSingleChoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Select a validator to delegate switch TO:')
        max_number:int = len(sorted_validators)
        if max_number > MAX_VALIDATOR_COUNT:
            max_number = MAX_VALIDATOR_COUNT

        to_validator, answer = validators.getValidatorSingleChoice("Select a validator number 1 - " + str(max_number) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, [], delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
        
        total_delegated_uluna = delegations[from_validator['moniker']]['balance_amount']
        print (f"The {from_validator['moniker']} wallet holds {wallet.formatUluna(total_delegated_uluna, ULUNA, True)}")
        print (f"NOTE: You can switch the entire value of this delegation by typing '100%' - no minimum amount will be retained.")
        switched_uluna:float = wallet.getUserNumber('How much are you switching? ', {'max_number': float(wallet.formatUluna(total_delegated_uluna, ULUNA, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': ULUNA})
        
        print (f"You are about to switch {wallet.formatUluna(switched_uluna, ULUNA, True)} from {from_validator['moniker']} and move it to {to_validator['moniker']}.")
        complete_transaction = get_user_choice('Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()
        
        print (f'Redelegating {wallet.formatUluna(switched_uluna, ULUNA, True)}...')
  
        # Create the delegation object
        delegation_tx = wallet.delegate().create()
        
        # Assign the details
        delegation_tx.delegator_address     = wallet.address
        delegation_tx.validator_address     = to_validator['operator_address']
        delegation_tx.validator_address_old = from_validator['operator_address']
        delegation_tx.delegated_uluna       = int(switched_uluna)
        delegation_tx.wallet_denom          = wallet.denom
        
        # Simulate it
        result = delegation_tx.simulate(delegation_tx.redelegate)

        if result == True:
                
            print (delegation_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = delegation_tx.redelegate()

            if result == True:
                delegation_tx.broadcast()
            
                if delegation_tx is not None:
                    if delegation_tx.broadcast_result.code == 11:
                        while True:
                            print (' 🛎️  Increasing the gas adjustment fee and trying again')
                            delegation_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                            print (f' 🛎️  Gas adjustment value is now {delegation_tx.terra.gas_adjustment}')
                            delegation_tx.simulate(delegation_tx.redelegate)
                            print (delegation_tx.readableFee())
                            delegation_tx.redelegate()
                            delegation_tx.broadcast()

                            if delegation_tx.broadcast_result.code != 11:
                                break

                            if delegation_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                                break
                        
                    if delegation_tx.broadcast_result.is_tx_error():
                        print (' 🛎️ The delegation failed, an error occurred:')
                        print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                    else:
                        print (f' ✅ Delegated amount: {wallet.formatUluna(switched_uluna, ULUNA, True)}')
                        print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
                else:
                    print (' 🛎️ Please check the validator list to see what the current status is. This transaction returned an error but may have completed.')
            else:
                print (' 🛎️  The delegation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')
    
    if user_action == USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS:
        
        # Get the validator list and the undelegations in progress
        validator_list:dict = validators.validators_by_address
        undelegations:dict  = wallet.getUndelegations()
        
        # Use today's date. 
        today:datetime = datetime.now()

        print ('')

        if len (undelegations) > 0:
            for undelegation in undelegations:
                if undelegation == 'base':
                    print ('BASE')
                else:
                    print (validator_list[undelegations[undelegation]['validator_address']]['moniker'])

                for entry in undelegations[undelegation]['entries']:
                    finish_day = datetime.strptime(entry['completion_time'], '%d/%m/%Y')

                    days_until = (finish_day - today).days

                    print (f"{wallet.formatUluna(entry['balance'], UBASE, True)} becomes available in {days_until} days")
        else:
            print ('No undelegations are currently in progress')
                
        print ('')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()