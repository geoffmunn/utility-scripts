#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
from getpass import getpass

from utility_classes import (
    Validators,
    Wallets,
    Wallet
)

import utility_constants

from terra_sdk.core.coin import Coin
from terra_sdk.core.coins import Coins

def strtobool (val):
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Returns -1 if
    'val' is anything else.
    """

    val = val.lower()
    if val in ('y', 'yes', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'false', 'off', '0'):
        return False
    else:
        #raise ValueError("invalid truth value %r" % (val,))
        return -1
    
def get_user_choice(question:str, yes_choices:list, no_choices:list) -> str|bool:
    """
    Get the user selection for a prompt and convert it to a standard value.
    """

    while True:    
        answer = input(question).lower()
        if answer in yes_choices or answer in no_choices:
            break
    
    booly = strtobool(answer)
    if  booly== -1:
        result = answer
    else:
        result = booly

    return result

def get_user_number(question:str, max_number:int) -> int:
    """
    Get ther user input - must be a number.
    """ 
    
    while True:    
        answer = input(question).strip(' ')
        if answer.isdigit():

            if int(answer) > 0 and int(answer) <= max_number:
                break

    return int(answer)

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

        if len(str(user_wallets[wallet_name].balances['uluna'])) > label_widths[2]:
            label_widths[2] = len(str(user_wallets[wallet_name].balances['uluna']))

        if len(str(user_wallets[wallet_name].balances['uusd'])) > label_widths[3]:
            label_widths[3] = len(str(user_wallets[wallet_name].balances['uusd']))

    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1]-len('Wallet name')] + ' '
    else:
        header_string +=  ' Wallet name '

    if label_widths[2] > len('LUNC'):
        header_string += '| LUNC ' + padding_str[0:label_widths[2]-len('LUNC')] + ' '
    else:
        header_string += '| LUNC '

    if label_widths[3] > len('USTC'):
        header_string += '| USTC'  + padding_str[0:label_widths[3]-len('USTC')] + ' '
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
            lunc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uluna'], False))).rstrip('0').rstrip('.')
            ustc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uusd'], False))).rstrip('0').rstrip('.')
            
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

def get_validator_singlechoice(question:str, validators:dict) -> dict|str:
    """
    Get a single user selection from a list.
    This is a custom function because the options are specific to this list.
    """

    # Get the longest validator name:
    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Validator name'))
    label_widths.append(len('Commission'))
    label_widths.append(len('Voting power'))

    for validator_name in validators:
        if len(validator_name) > label_widths[1]:
            label_widths[1] = len(validator_name)

    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Validator name'):
        header_string +=  ' Commission | Voting power | Validator name' + padding_str[0:label_widths[1]-len('Validator name')]
    else:
        header_string +=  ' Commission | Voting power | Validator name'

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
            count += 1
            validator_numbers[count] = validators[validator_name]
                
            if validator_name in validators_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            voting_power = str(round(validators[validator_name]['voting_power'],2)) + '%'
            commission = str(validators[validator_name]['commission']) + '%'

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            validator_name_str = ' ' + validator_name + padding_str[0:label_widths[1] - len(validator_name)]             
            commission_str = commission + padding_str[0:label_widths[2] - len(commission)]
            voting_power_str = ' ' + voting_power + padding_str[0:label_widths[3] - len(voting_power)]

            print (f"{count_str}{glyph} | {commission_str} |{voting_power_str} |{validator_name_str}")

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
        break;

    return user_validator, answer

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

def main():


    #DONE: step 1: select one wallet (show balances against wallet)
    #step 2: select (delegate, undelegate, switch)
    #step 2.1: delegate:
    #DONE: step 2.1.1: select one validator
    #step 2.1.2: select amount to delegate
    #step 2.2: undelegate:
    #step 2.2.1 select one validator
    #step 2.2.2 confirm that undelegation is required
    #step 2.3: switch
    #step 2.3.1: select current validator
    #step 2.3.2: select new validator
    #step 2.3.3: confirm that switch is required


    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    try:
        with open(utility_constants.CONFIG_FILE_NAME, 'r') as file:
            user_config = yaml.safe_load(file)
    except :
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...\n')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    #wallet_obj = Wallets().ac(user_config, decrypt_password)

    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You have these wallets available:')

        wallet,answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # Get the desired actions
    print ('\nWhat action do you want to take?')
    print ('  (D)  Delegate to a validator')
    print ('  (U)  Undelegate all coins from a validator')
    print ('  (S)  Switch validators')
    print ('  (Q)  Quit')
    
    user_action = get_user_choice('', ['d', 'u', 's', 'q'], [])

    if user_action == 'q':
        print (' 🛑 Exiting...')
        exit()

    print ('\nGetting available validators - please wait...')

    validators = Validators()
    validators.create()

    sorted_validators = validators.sorted_validators

    if len(sorted_validators) == 0:
        print (' 🛑 No validators could be retrieved - perhaps there are network issues?')
        exit()

    if user_action == utility_constants.USER_ACTION_VALIDATOR_DELEGATE:

        print (f'Select a validator to delegate to:')

        user_validator, answer = get_validator_singlechoice("Select a validator number 1 - " + str(len(sorted_validators)) + ", 'X' to continue', or 'Q' to quit: ", sorted_validators)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()

        print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances['uluna'], True)}")
        delegated_lunc:int = get_user_number('How much are you delegating? ', int(wallet.formatUluna(wallet.balances['uluna'], False)))
        delegated_uluna:int = delegated_lunc * utility_constants.COIN_DIVISOR

        print (f'Delegating {delegated_lunc}...')
        
        delegation_tx = wallet.delegate().create(wallet.address, user_validator['operator_address'])

        # Simulate it
        result = delegation_tx.simulate(delegated_uluna)

        if result == True:
                
            print (delegation_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = delegation_tx.delegate(delegated_uluna)
            
            exit()
            if result == True:
                delegation_tx.broadcast()
            
                if delegation_tx.broadcast_result.is_tx_error():
                    print (' 🛎️ The delegation failed, an error occurred:')
                    print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                    print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The deleggation could not be completed')
        else:
            print ('🛎️  The delegation could not be completed')
    #print (user_validator)
    #for validator in validators:
    #    if validators[validator]['is_jailed'] == False:
    #        print(validator, validators[validator]['voting_power'])


    exit()
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    try:
        with open(utility_constants.CONFIG_FILE_NAME, 'r') as file:
            user_config = yaml.safe_load(file)
    except :
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    if len(user_wallets) > 0:
        print (f'You can send LUNC on the following wallets:')

        user_wallets,answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        
    #     print ('####################################')
    #     print (f'Accessing the {wallet.name} wallet...')

    #     # Update the balances after having done withdrawals and swaps
    #     wallet.getBalances()

    #     if 'uluna' in wallet.balances:
    #         # Adjust this so we have the desired amount still remaining
    #         uluna_amount = int(lunc_amount) * utility_constants.COIN_DIVISOR

    #         if uluna_amount > 0 and uluna_amount <= (wallet.balances['uluna'] - (utility_constants.WITHDRAWAL_REMAINDER * utility_constants.COIN_DIVISOR)):
    #             print (f'Sending {wallet.formatUluna(uluna_amount, True)}')

    #             send_tx = wallet.send().create()

    #             # Simulate it
    #             result = send_tx.simulate(recipient_address, uluna_amount, memo)

    #             if result == True:
                    
    #                 print (send_tx.readableFee())
                        
    #                 exit()
    #                 # Now we know what the fee is, we can do it again and finalise it
    #                 result = send_tx.send()
                    
    #                 if result == True:
    #                     send_tx.broadcast()
                    
    #                     if send_tx.broadcast_result.is_tx_error():
    #                         print (' 🛎️  The send transaction failed, an error occurred:')
    #                         print (f' 🛎️  {send_tx.broadcast_result.raw_log}')
    #                     else:
    #                         print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, True)}')
    #                         print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
    #                 else:
    #                     print (' 🛎️  The send transaction could not be completed')
    #             else:
    #                 print (' 🛎️  The send transaction could not be completed')
                    
    #         else:
    #             print (' 🛎️  Sending error: Not enough LUNC will be left in the account to cover fees')
            
    # print (' 💯 Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()