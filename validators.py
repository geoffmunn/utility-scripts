#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
from getpass import getpass

from utility_classes import (
    get_user_choice,
    get_user_number,
    isPercentage,
    UserConfig,
    Validators,
    Wallets,
    Wallet
)

import utility_constants

def get_user_multichoice(question:str, user_wallets:dict) -> dict|str:
    """
    Get multiple user selections from a list.
    This is a custom function because the options are specific to this list.
    """

    wallets_to_use = {}
    while True:

        count = 0
        wallet_numbers = {}

        for wallet_name in user_wallets:
            count += 1
            wallet_numbers[count] = user_wallets[wallet_name]
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = ''

            print (f"  ({count}) {glyph} {wallet_name}")
            
        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:
            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == 'c':
            wallets_to_use = {}
        
        if answer == 'a':
            wallets_to_use = {}
            for wallet_name in user_wallets:
                wallets_to_use[wallet_name] = user_wallets[wallet_name]

        if answer == 'x':
            break

        if answer == 'q':
            break

    return wallets_to_use, answer

def get_user_singlechoice(question:str, user_wallets:dict) -> dict|str:
    """
    Get a single user selection from a list.
    This is a custom function because the options are specific to this list.
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))
    label_widths.append(len('LUNC'))
    label_widths.append(len('USTC'))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        if 'uluna' in user_wallets[wallet_name].balances:
            uluna_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances['uluna'])
        else:
            uluna_val = ''
            
        if 'uusd' in user_wallets[wallet_name].balances:
            ustc_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances['uusd'])
        else:
            ustc_val = ''

        if len(str(uluna_val)) > label_widths[2]:
            label_widths[2] = len(str(uluna_val))

        if len(str(ustc_val)) > label_widths[3]:
            label_widths[3] = len(str(ustc_val))

    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
    else:
        header_string +=  ' Wallet name '

    if label_widths[2] > len('LUNC'):
        header_string += '| LUNC' + padding_str[0:label_widths[2] - len('LUNC')] + ' '
    else:
        header_string += '| LUNC '

    if label_widths[3] > len('USTC'):
        header_string += '| USTC'  + padding_str[0:label_widths[3] - len('USTC')] + ' '
    else:
        header_string += '| USTC '

    horizontal_spacer = '-' * len(header_string)

    wallets_to_use = {}
    user_wallet    = {}

    while True:

        count = 0
        wallet_numbers = {}

        print (horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:Wallet  = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]

            if 'uluna' in wallet.balances:
                lunc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uluna'], False))).rstrip('0').rstrip('.')
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if 'uusd' in wallet.balances:
                ustc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uusd'], False))).rstrip('0').rstrip('.')
            else:
                ustc_str = ' '
            
            print (f"{count_str}{glyph} | {wallet_name_str} | {lunc_str} | {ustc_str}")
            
        print (horizontal_spacer + '\n')

        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use = {}

            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == 'x':
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == 'q':
            break

    # Get the first (and only) validator from the list
    for item in wallets_to_use:
        user_wallet = wallets_to_use[item]
        break;
    
    return user_wallet, answer

def get_validator_singlechoice(question:str, validators:dict, filter_list:list, delegations:dict) -> dict|str:
    """
    Get a single user selection from a list.
    This is a custom function because the options are specific to this list.
    """

    # We need a wallet object so we can format LUNC values
    wallet = Wallet()

    # Get the longest validator name:
    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Commission'))
    label_widths.append(len('Voting power'))
    label_widths.append(len('Delegated'))
    label_widths.append(len('Validator name'))

    for delegation in delegations:
        if len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], False))) > label_widths[3]:
            label_widths[3] = len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], False)))

    for validator_name in validators:
        if len(validator_name) > label_widths[4]:
            label_widths[4] = len(validator_name)

    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[3] > len('Delegated'):
        header_string +=  ' Commission | Voting power | Delegated' + padding_str[0:label_widths[3]-len('Delegated')]
    else:
        header_string +=  ' Commission | Voting power | Delegated'

    if label_widths[4] > len('Validator name'):
        header_string +=  ' | Validator name' + padding_str[0:label_widths[4]-len('Validator name')]
    else:
        header_string +=  ' | Validator name'

    horizontal_spacer = '-' * len(header_string)

    validators_to_use = {}
    user_validator    = {}

    while True:

        count = 0
        validator_numbers = {}

        print (horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)
        
        for validator_name in validators:

            if len(filter_list) == 0 or (len(filter_list) > 0 and validator_name in filter_list):
                count += 1
                validator_numbers[count] = validators[validator_name]
                    
                if validator_name in validators_to_use:
                    glyph = '✅'
                else:
                    glyph = '  '

                voting_power = str(round(validators[validator_name]['voting_power'],2)) + '%'
                commission = str(validators[validator_name]['commission']) + '%'

                count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                
                commission_str = commission + padding_str[0:label_widths[1] - len(commission)]

                voting_power_str = ' ' + voting_power + padding_str[0:label_widths[2] - len(voting_power)]

                if validator_name in delegations:
                    delegated_lunc = wallet.formatUluna(delegations[validator_name]['balance_amount'], False)
                    delegated = ' ' + str(delegated_lunc) + padding_str[0:label_widths[3] - len(str(delegated_lunc))]
                else:
                    delegated = ' ' + padding_str[0:label_widths[3]]

                validator_name_str = ' ' + validator_name + padding_str[0:label_widths[4] - len(validator_name)]

                print (f"{count_str}{glyph} | {commission_str} |{voting_power_str} |{delegated} |{validator_name_str}")

                if count == utility_constants.MAX_VALIDATOR_COUNT:
                    break
            
        print (horizontal_spacer + '\n')

        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in validator_numbers:

            validators_to_use = {}

            key = validator_numbers[int(answer)]['moniker']
            if key not in validators_to_use:
                validators_to_use[key] = validator_numbers[int(answer)]
            else:
                validators_to_use.pop(key)
            
        if answer == 'x':
            if len(validators_to_use) > 0:
                break
            else:
                print ('\nPlease select a validator first.\n')

        if answer == 'q':
            break

    # Get the first (and only) validator from the list
    for item in validators_to_use:
        user_validator = validators_to_use[item]
        break

    return user_validator, answer

def remove_exponent(num):
    return num.to_integral() if num == num.to_integral() else num.normalize()

def main():


    #DONE: step 1: select one wallet (show balances against wallet)
    #DONE: step 2: select (delegate, undelegate, switch)
    #DONE: step 2.1: delegate:
    #DONE: step 2.1.1: select one validator
    #DONE: step 2.1.2: select amount to delegate
    #step 2.2: undelegate:
    #step 2.2.1 select one validator
    #step 2.2.2 confirm that undelegation is required
    #DONE: step 2.3: switch
    #DONE: step 2.3.1: select current validator
    #DONE: step 2.3.2: select new validator
    #DONE: step 2.3.3: select amount to switch
    #step 2.3.3: confirm that switch is required


    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...\n')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)

    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You have these wallets available:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.")
        exit()

    # Get the desired actions
    print ('\nWhat action do you want to take?')
    print ('  (D)  Delegate to a validator')
    print ('  (U)  Undelegate all coins from a validator')
    print ('  (S)  Switch validators')
    print ('  (Q)  Quit')
    
    user_action = get_user_choice('', ['d', 'u', 's', 'q'])

    if user_action == 'q':
        print (' 🛑 Exiting...')
        exit()

    print ('\nGetting available validators - please wait...')

    validators = Validators()
    validators.create()

    sorted_validators:dict = validators.sorted_validators

    if len(sorted_validators) == 0:
        print (' 🛑 No validators could be retrieved - perhaps there are network issues?')
        exit()

    if user_action == utility_constants.USER_ACTION_VALIDATOR_DELEGATE:

        print (f'Select a validator to delegate to:')

        user_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(sorted_validators)) + ", 'X' to continue', or 'Q' to quit: ", sorted_validators, [])

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()

        print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances['uluna'], True)}")
        delegated_lunc:int = get_user_number('How much are you delegating? ', {'max_number': int(wallet.formatUluna(wallet.balances['uluna'])), 'min_number': 0, 'percentages_allowed': True})
        
        if isPercentage(delegated_lunc):
            percentage:int = int(str(delegated_lunc).strip(' ')[0:-1]) / 100
            delegated_lunc:int = int((wallet.formatUluna(wallet.balances['uluna'], False) - utility_constants.WITHDRAWAL_REMAINDER) * percentage)
        
        delegated_lunc:int  = int(str(delegated_lunc).replace('.0', ''))
        delegated_uluna:int = int(delegated_lunc * utility_constants.COIN_DIVISOR)
        
        print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}...')
        
        # Create the delegation object
        delegation_tx = wallet.delegate().create()
        
        # Assign the details
        delegation_tx.delegator_address = wallet.address
        delegation_tx.validator_address = user_validator['operator_address']
        delegation_tx.delegated_uluna   = delegated_uluna

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
                        delegation_tx.terra.gas_adjustment += utility_constants.GAS_ADJUSTMENT_INCREMENT
                        print (f' 🛎️  Gas adjustment value is now {delegation_tx.terra.gas_adjustment}')
                        delegation_tx.simulate(delegation_tx.delegate)
                        print (delegation_tx.readableFee())
                        delegation_tx.delegate()
                        delegation_tx.broadcast()

                        if delegation_tx.broadcast_result.code != 11:
                            break

                        if delegation_tx.terra.gas_adjustment >= utility_constants.MAX_GAS_ADJUSTMENT:
                            break
                    
                if delegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The delegation failed, an error occurred:')
                    print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                    print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The delegation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')

    if user_action == utility_constants.USER_ACTION_VALIDATOR_UNDELEGATE:
        print (f'Select a validator to undelegate from:')

        # Get the validators currently being used
        
        delegations:dict = wallet.getDelegations()

        
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        user_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue', or 'Q' to quit: ", sorted_validators, filter_list)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()

        available_undelegation_uluna:int = delegations[user_validator['moniker']]['balance_amount']

        print (f"The {wallet.name} wallet has {wallet.formatUluna(available_undelegation_uluna, True)} available to be undelegated.")
        undelegated_lunc:int = get_user_number('How much are you undelegating? ', {'max_number': float(wallet.formatUluna(wallet.balances['uluna'], False)), 'min_number': 0, 'percentages_allowed': True})
        
        if isPercentage(undelegated_lunc):
            percentage:int = int(str(undelegated_lunc).strip(' ')[0:-1]) / 100
            undelegated_lunc:int = int((wallet.formatUluna(available_undelegation_uluna, False) - utility_constants.WITHDRAWAL_REMAINDER) * percentage)

        print (f'Undelegating {undelegated_lunc}...')

        undelegated_luna:int = undelegated_lunc * utility_constants.COIN_DIVISOR

        print (' 🛎️  Undelegated funds will not be available for 21 days.')
        answer = get_user_choice('Are you sure you want to undelegate from this validator? (y/n) ', [])

        # Start the undelegation process        

        undelegation_tx = wallet.delegate().create(wallet.address, user_validator['operator_address'])

        # Simulate it
        undelegation_tx.delegated_uluna = undelegated_luna
        result = undelegation_tx.simulate(undelegation_tx.undelegate)

        if result == True:
                
            print (delegation_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = delegation_tx.undelegate()

            if result == True:
                delegation_tx.broadcast()
            
                if delegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The delegation failed, an error occurred:')
                    print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                    print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The delegation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')
        
    if user_action == utility_constants.USER_ACTION_VALIDATOR_SWITCH:
        # Get the validators currently being used
        
        delegations:dict = wallet.getDelegations()
        filter_list:list = []

        for validator in delegations:
            filter_list.append(validator)

        print (f'Select a validator to delegate switch FROM:')
        from_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue', or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()

        print (f'Select a validator to delegate switch TO:')
        to_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(sorted_validators)) + ", 'X' to continue', or 'Q' to quit: ", sorted_validators, [], delegations)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()

        print (delegations[from_validator['moniker']]['balance_amount'])

        #print (delegations[from_validator])
        
        print (f"The {from_validator['moniker']} wallet holds {wallet.formatUluna(delegations[from_validator['moniker']]['balance_amount'], True)}")
        delegated_lunc:int = get_user_number('How much are you delegating? ', {'max_number': int(wallet.formatUluna(wallet.balances['uluna'])), 'min_number': 0, 'percentages_allowed': True})

        if isPercentage(delegated_lunc):
            percentage:int = int(str(delegated_lunc).strip(' ')[0:-1]) / 100
            delegated_lunc:int = int((wallet.formatUluna(wallet.balances['uluna'], False) - utility_constants.WITHDRAWAL_REMAINDER) * percentage)
        
        delegated_lunc:int  = int(str(delegated_lunc).replace('.0', ''))
        delegated_uluna:int = int(delegated_lunc * utility_constants.COIN_DIVISOR)
        
        print (f'Redelegating {wallet.formatUluna(delegated_uluna, True)}...')
        
        # Create the delegation object
        delegation_tx = wallet.delegate().create()
        
        # Assign the details
        delegation_tx.delegator_address = wallet.address
        delegation_tx.validator_address = to_validator['operator_address']
        delegation_tx.validator_address_old = from_validator['operator_address']
        delegation_tx.delegated_uluna   = delegated_uluna

        # Simulate it
        result = delegation_tx.simulate(delegation_tx.redelegate)

        if result == True:
                
            print (delegation_tx.readableFee())
            # Now we know what the fee is, we can do it again and finalise it
            result = delegation_tx.redelegate()
            
            if result == True:
                delegation_tx.broadcast()
            
                if delegation_tx.broadcast_result.code == 11:
                    while True:
                        print (' 🛎️  Increasing the gas adjustment fee and trying again')
                        delegation_tx.terra.gas_adjustment += utility_constants.GAS_ADJUSTMENT_INCREMENT
                        print (f' 🛎️  Gas adjustment value is now {delegation_tx.terra.gas_adjustment}')
                        delegation_tx.simulate(delegation_tx.redelegate)
                        print (delegation_tx.readableFee())
                        delegation_tx.redelegate()
                        delegation_tx.broadcast()

                        if delegation_tx.broadcast_result.code != 11:
                            break

                        if delegation_tx.terra.gas_adjustment >= utility_constants.MAX_GAS_ADJUSTMENT:
                            break
                    
                if delegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The delegation failed, an error occurred:')
                    print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                    print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The delegation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')

        #print (from_validator)

        #print (to_validator)
        
    # print (' 💯 Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()