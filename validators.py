#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from datetime import datetime

from constants.constants import (
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

from classes.delegation_transaction import delegate_to_validator, undelegate_from_validator, switch_validator
from classes.transaction_core import TransactionResult
from classes.wallets import UserWallets
from classes.validators import Validators

from terra_classic_sdk.core.coin import Coin

def main():
    
    # Check if there is a new version we should be using
    check_version()

    # Get the user wallets
    wallets      = UserWallets()
    user_wallets = wallets.loadUserWallets(get_delegations = True)

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
    print (' (D)  Delegate to a validator')
    print (' (U)  Undelegate coins from a validator')
    print (' (S)  Switch validators')
    print (' (L)  List undelegations in progress')
    print (' (Q)  Quit')
    print ('')

    user_action = get_user_choice(' ❓ Pick an option: ', [
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

    # Not required for listing undelegations, but no harm having it here:
    delegations:dict = wallet.delegations

    if user_action == USER_ACTION_VALIDATOR_DELEGATE:

        if ULUNA not in wallet.balances or wallet.balances[ULUNA] == 0:
            print (' 🛑 This wallet has no LUNC available to delegate.\n')
            exit()

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
        delegated_uluna:int = int(wallet.getUserNumber('How much are you delegating? ', {'max_number': float(wallet.formatUluna(wallet.balances[ULUNA], ULUNA)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': True, 'target_denom': ULUNA}))
                
        if delegated_uluna == 0:
            print (' 🛑 Delegated amount is zero, exiting...\n')
            exit()

        print (f"You are about to delegate {wallet.formatUluna(delegated_uluna, ULUNA, True)} to {user_validator['moniker']}.")
        complete_transaction = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Delegating {wallet.formatUluna(delegated_uluna, ULUNA, True)}...')
        
        delegated_coin:Coin = wallet.createCoin(delegated_uluna, ULUNA)
        transaction_result:TransactionResult = delegate_to_validator(wallet, user_validator['operator_address'], delegated_coin)
        transaction_result.showResults()

    if user_action == USER_ACTION_VALIDATOR_UNDELEGATE:
        print (f'Select a validator to undelegate from:')

        # Get the validators currently being used
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        if len(filter_list) == 0:
            print (' 🛑 This wallet has no active validators with delegations.\n')
            exit()

        user_validator, answer = validators.getValidatorSingleChoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        available_undelegation_uluna:int = delegations[user_validator['moniker']]['balance_amount']

        print (f"The {wallet.name} wallet has {wallet.formatUluna(available_undelegation_uluna, ULUNA, True)} available to be undelegated.")
        print (f"NOTE: You can send the entire value of this delegation by typing '100%' - no minimum amount will be retained.")
        undelegated_uluna:str = wallet.getUserNumber('How much are you undelegating? ', {'max_number': float(wallet.formatUluna(available_undelegation_uluna, ULUNA, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': ULUNA})
        
        print (f"You are about to undelegate {wallet.formatUluna(undelegated_uluna, ULUNA, True)} from {user_validator['moniker']}.")
        print (' 🛎️  Undelegated funds will not be available for 21 days.')
        complete_transaction = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Undelegating {wallet.formatUluna(undelegated_uluna, ULUNA, True)}...')

        undelegated_coin:Coin = wallet.createCoin(undelegated_uluna, ULUNA)
        transaction_result:TransactionResult = undelegate_from_validator(wallet, user_validator['operator_address'], undelegated_coin)
        transaction_result.showResults()

    if user_action == USER_ACTION_VALIDATOR_SWITCH:
        # Get the validators currently being used
        
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        if len(filter_list) == 0:
            print (' 🛑 This wallet has no active validators with delegations.\n')
            exit()

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
        complete_transaction = get_user_choice(' ❓ Do you want to continue? (y/n) ', [])

        if complete_transaction == False:
            print (' 🛑 Exiting...\n')
            exit()
        
        print (f'Redelegating {wallet.formatUluna(switched_uluna, ULUNA, True)}...')
  
        delegated_coin:Coin = wallet.createCoin(switched_uluna, ULUNA)
        transaction_result:TransactionResult = switch_validator(wallet, to_validator['operator_address'], from_validator['operator_address'], delegated_coin)
        transaction_result.showResults()
    
    if user_action == USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS:
        
        # Get the validator list and the undelegations in progress
        validator_list:dict = validators.validators_by_address
        undelegations:dict  = wallet.undelegations
        
        today:datetime = datetime.now().astimezone()

        print ('')

        if len (undelegations) > 0:
            for undelegation in undelegations:
                if undelegation == UBASE:
                    print ('BASE')
                    for entry in undelegations[undelegation]['entries']:
                        # At 9:10pm 21st Feb, I undelegated 2 BASE
                        #Tx hash: 3061B90D40749DB73DB4DC735BDDDD5F5A1680E2100D5DEDD319FB7F23DD5875
                        finish_day = datetime.strptime(entry['completion_time'], '%d/%m/%Y').astimezone()
                        days_until = (finish_day - today).days + 1

                        print (f"{wallet.formatUluna(entry['balance'], UBASE, True)} becomes available in {days_until} days (midnight UTC on {finish_day.year}-{finish_day.month}-{finish_day.day})")
                else:
                    print (validator_list[undelegations[undelegation]['validator_address']]['moniker'])
                    for entry in undelegations[undelegation]['entries']:

                        finish_day = entry['completion_time']
                        days_until = (finish_day - today).days

                        print (f"{wallet.formatUluna(entry['balance'], ULUNA, True)} becomes available in {days_until} days ({finish_day})")
                
        else:
            print ('No undelegations are currently in progress')
                
        print ('')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()