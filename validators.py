#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    check_version,
    get_user_choice,
    get_user_number,
    UBASE,
    ULUNA,
    UUSD,
    UserConfig,
    Validators,
    Wallets,
    Wallet
)

from datetime import datetime, timezone

#import utility_constants
from utility_constants import (
    GAS_ADJUSTMENT_INCREMENT,
    MAX_GAS_ADJUSTMENT,
    MAX_VALIDATOR_COUNT,
    USER_ACTION_ALL,
    USER_ACTION_CLEAR,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    USER_ACTION_VALIDATOR_DELEGATE,
    USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS,
    USER_ACTION_VALIDATOR_UNDELEGATE,
    USER_ACTION_VALIDATOR_SWITCH,
    WITHDRAWAL_REMAINDER
)

def get_user_multichoice(question:str, user_wallets:dict):
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
            
        if answer == USER_ACTION_CLEAR:
            wallets_to_use = {}
        
        if answer == USER_ACTION_ALL:
            wallets_to_use = {}
            for wallet_name in user_wallets:
                wallets_to_use[wallet_name] = user_wallets[wallet_name]

        if answer == USER_ACTION_CONTINUE:
            break

        if answer == USER_ACTION_QUIT:
            break

    return wallets_to_use, answer

def get_user_singlechoice(question:str, user_wallets:dict):
    """
    Get a single user selection from a list.
    This is a custom function because the options are specific to this list.
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))
    label_widths.append(len('LUNC'))
    label_widths.append(len('USTC'))
    label_widths.append(len('Delegations'))
    label_widths.append(len('Undelegations'))

    for wallet_name in user_wallets:

        wallet:Wallet = user_wallets[wallet_name]

        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        if ULUNA in wallet.balances:
            uluna_val = wallet.formatUluna(wallet.balances[ULUNA], ULUNA)
        else:
            uluna_val = ''
            
        if UUSD in wallet.balances:
            ustc_val = wallet.formatUluna(wallet.balances[UUSD], UUSD)
        else:
            ustc_val = ''

        if len(str(uluna_val)) > label_widths[2]:
            label_widths[2] = len(str(uluna_val))

        if len(str(ustc_val)) > label_widths[3]:
            label_widths[3] = len(str(ustc_val))

        # Calculate the delegations and undelegations
        delegations = wallet.getDelegations()

        if delegations is not None:
            for delegation in delegations:
                if len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False))) > label_widths[4]:
                    label_widths[4] = len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False)))

        undelegations = wallet.getUndelegations()
        for undelegation in undelegations:
            if len(str(wallet.formatUluna(undelegations[undelegation]['balance_amount'], ULUNA, False))) > label_widths[5]:
                label_widths[5] = len(str(wallet.formatUluna(undelegations[undelegation]['balance_amount'], ULUNA, False)))

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

    if label_widths[4] > len('Delegations'):
        header_string += '| Delegations'  + padding_str[0:label_widths[4] - len('Delegations')] + ' '
    else:
        header_string += '| Delegations '

    if label_widths[5] > len('Undelegations'):
        header_string += '| Undelegations'  + padding_str[0:label_widths[5] - len('Undelegations')] + ' '
    else:
        header_string += '| Undelegations '

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

            if ULUNA in wallet.balances:
                lunc_str = wallet.formatUluna(wallet.balances[ULUNA], ULUNA, False)
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if UUSD in wallet.balances:
                ustc_str = wallet.formatUluna(wallet.balances[UUSD], UUSD, False)
            else:
                ustc_str = ' '

            ustc_str = ustc_str + padding_str[0:label_widths[3] - len(ustc_str)]

            delegations_balance:float   = 0
            undelegations_balance:float = 0
            delegations_str:str = ''
            undelegations_str:str = ''

            delegations   = wallet.getDelegations()
            undelegations = wallet.getUndelegations()
            
            if delegations is not None:
                for delegation in delegations:
                    delegations_balance += int(delegations[delegation]['balance_amount'])

            delegations_str = str(wallet.formatUluna(delegations_balance, ULUNA, False))
            delegations_str = delegations_str + padding_str[0:label_widths[4] - len(delegations_str)]

            for undelegation in undelegations:
                undelegations_balance += float(undelegations[undelegation]['balance_amount'])
                
            undelegations_str = str(wallet.formatUluna(undelegations_balance, ULUNA, False))
            undelegations_str = undelegations_str + padding_str[0:label_widths[5] - len(undelegations_str)]

            print (f"{count_str}{glyph} | {wallet_name_str} | {lunc_str} | {ustc_str} | {delegations_str} | {undelegations_str}")
            
        print (horizontal_spacer + '\n')

        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use = {}

            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) validator from the list
    for item in wallets_to_use:
        user_wallet = wallets_to_use[item]
        break
    
    return user_wallet, answer

def get_validator_singlechoice(question:str, validators:dict, filter_list:list, delegations:dict):
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
        if len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False))) > label_widths[3]:
            label_widths[3] = len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False)))

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
                    delegated_lunc = wallet.formatUluna(delegations[validator_name]['balance_amount'], ULUNA, False)
                    delegated = ' ' + str(delegated_lunc) + padding_str[0:label_widths[3] - len(str(delegated_lunc))]
                else:
                    delegated = ' ' + padding_str[0:label_widths[3]]

                validator_name_str = ' ' + validator_name + padding_str[0:label_widths[4] - len(validator_name)]

                print (f"{count_str}{glyph} | {commission_str} |{voting_power_str} |{delegated} |{validator_name_str}")

                if count == MAX_VALIDATOR_COUNT:
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

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) validator from the list
    for item in validators_to_use:
        user_validator = validators_to_use[item]
        break

    return user_validator, answer

#def remove_exponent(num):
#    return num.to_integral() if num == num.to_integral() else num.normalize()

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

    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    if decrypt_password == '':
        print (' 🛑 Exiting...\n')
        exit()

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
        exit()

    print ('Decrypting and validating wallets - please wait...\n')

    # Create the wallet object based on the user config file
    wallet_obj       = Wallets().create(user_config, decrypt_password)
    decrypt_password = None

    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()
        wallet.getDelegations()

    if len(user_wallets) > 0:
        print (f'You have these wallets available:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue, or 'Q' to quit: ", user_wallets)

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

    delegations = wallet.getDelegations()

    if user_action == USER_ACTION_VALIDATOR_DELEGATE:

        print (f'Select a validator to delegate to:')

        max_number:int = len(sorted_validators)
        if max_number > MAX_VALIDATOR_COUNT:
            max_number = MAX_VALIDATOR_COUNT

        user_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(max_number) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, [], delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[ULUNA], ULUNA, True)}")
        print (f"NOTE: A minimum amount of {WITHDRAWAL_REMAINDER} LUNC will be retained for future transactions.")
        delegated_uluna:float = get_user_number('How much are you delegating? ', {'max_number': float(wallet.formatUluna(wallet.balances[ULUNA], ULUNA)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': True})
                
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

        user_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        available_undelegation_uluna:int = delegations[user_validator['moniker']]['balance_amount']

        print (f"The {wallet.name} wallet has {wallet.formatUluna(available_undelegation_uluna, ULUNA, True)} available to be undelegated.")
        print (f"NOTE: You can send the entire value of this delegation by typing '100%' - no minimum amount will be retained.")
        undelegated_uluna:str = get_user_number('How much are you undelegating? ', {'max_number': float(wallet.formatUluna(available_undelegation_uluna, ULUNA, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False})
        
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
        from_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(filter_list)) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, filter_list, delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'Select a validator to delegate switch TO:')
        max_number:int = len(sorted_validators)
        if max_number > MAX_VALIDATOR_COUNT:
            max_number = MAX_VALIDATOR_COUNT

        to_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(max_number) + ", 'X' to continue, or 'Q' to quit: ", sorted_validators, [], delegations)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
        
        total_delegated_uluna = delegations[from_validator['moniker']]['balance_amount']
        print (f"The {from_validator['moniker']} wallet holds {wallet.formatUluna(total_delegated_uluna, ULUNA, True)}")
        print (f"NOTE: You can switch the entire value of this delegation by typing '100%' - no minimum amount will be retained.")
        switched_uluna:float = get_user_number('How much are you switching? ', {'max_number': float(wallet.formatUluna(total_delegated_uluna, ULUNA, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': ULUNA})
        
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
        today = datetime.now()

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