#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
import time

from getpass import getpass

from utility_classes import (
    Wallets,
    Wallet
)

import utility_constants

def strtobool (val):
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Returns -1 if
    'val' is anything else.
    """

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
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
    
def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the desired actions
    print ('What action do you want to take?')
    print ('  (W)  Withdraw rewards')
    print ('  (S)  Swap coins')
    print ('  (D)  Delegate')
    print ('  (WD) Withdraw & Delegate')
    print ('  (SD) Swap & Delegate')
    print ('  (A)  All of the above')

    user_action = get_user_choice('', ['w', 's', 'd', 'wd', 'sd', 'a'], [])

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

    action_string = ''
    if user_action == utility_constants.USER_ACTION_WITHDRAW:
        action_string = 'withdraw rewards'
    if user_action == utility_constants.USER_ACTION_SWAP:
        action_string = 'swap USTC for LUNC'
    if user_action == utility_constants.USER_ACTION_DELEGATE:
        action_string = 'delegate all available funds'
    if user_action == utility_constants.USER_ACTION_WITHDRAW_DELEGATE:
        action_string = 'withdraw rewards and delegating everything'
    if user_action == utility_constants.USER_ACTION_SWAP_DELEGATE:
        action_string = 'swap USTC for LUNC and delegating everything'
    if user_action == utility_constants.USER_ACTION_ALL:
        action_string = 'withdraw rewards, swap USTC for LUNC, and then delegate everything'

    if action_string == '':
        print (' 🛑 No recognised action to complete, exiting...')
        exit()

    if len(user_wallets) > 0:
        print (f'You can {action_string} on the following wallets:')

        user_wallets,answer = get_user_multichoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", or 'A' to add all of them, 'C' to clear the list, 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        print ('####################################')
        print (f'Accessing the {wallet.name} wallet...')

        delegations = wallet.getDelegations()
        for validator in delegations:

            print ('\n------------------------------------')
            print (f"The {delegations[validator]['validator_name']} validator has a {delegations[validator]['commission']}% commission.")

            if user_action in [utility_constants.USER_ACTION_WITHDRAW, utility_constants.USER_ACTION_WITHDRAW_DELEGATE, utility_constants.USER_ACTION_ALL]:

                print ('Starting withdrawals...')

                uluna_reward:int = delegations[validator]['rewards']['uluna']

                # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                if wallet.formatUluna(uluna_reward, False) > wallet.delegations['threshold']:

                    print (f'Withdrawing {wallet.formatUluna(uluna_reward, False)} rewards')

                    # Update the balances so we know what we have to pay the fee with
                    wallet.getBalances()

                    # Set up the withdrawal object
                    withdrawal_tx = wallet.withdrawal().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                    # Simulate it
                    result = withdrawal_tx.simulate()

                    if result == True:

                        print (withdrawal_tx.readableFee())

                        # Now we know what the fee is, we can do it again and finalise it
                        result = withdrawal_tx.withdraw()

                        if result == True:
                            withdrawal_tx.broadcast()
                        
                            if withdrawal_tx.broadcast_result.is_tx_error():
                                print (' 🛎️  Withdrawal failed, an error occurred')
                                print (withdrawal_tx.broadcast_result.raw_log)
                        
                            else:
                                print (f' ✅ Withdrawn amount: {wallet.formatUluna(uluna_reward, True)}')
                                print (f' ✅ Tx Hash: {withdrawal_tx.broadcast_result.txhash}')
                                time.sleep(10)
                    else:
                        print (' 🛎️  The withdrawal could not be completed')
                else:
                    print (' 🛎️  The amount of LUNC in this wallet does not exceed the withdrawal threshold')

            # Swap any uusd coins for uluna
            if user_action in [utility_constants.USER_ACTION_SWAP, utility_constants.USER_ACTION_SWAP_DELEGATE, utility_constants.USER_ACTION_ALL]:

                if wallet.allow_swaps == True:
                    print ('\n------------------------------------')
                    print ('Starting swaps...')

                    # Update the balances so we know we have the correct amount
                    wallet.getBalances()
                    
                    # We are only supporting swaps with uusd (USTC) at the moment
                    swap_amount = wallet.balances['uusd']

                    if swap_amount > 0:
                        print (f'Swapping {wallet.formatUluna(swap_amount, False)} USTC for LUNC')

                        # Set up the basic swap object
                        swaps_tx = wallet.swap().create()

                        # Simulate it so we can get the fee
                        result = swaps_tx.simulate()

                        if result == True:
                           
                            print (swaps_tx.readableFee())
                            
                            result = swaps_tx.swap()

                            if result == True:

                                swaps_tx.broadcast()

                                if swaps_tx.broadcast_result.is_tx_error():
                                    print (' 🛎️ Swap failed, an error occurred')
                                    print (swaps_tx.broadcast_result.raw_log)
                            
                                else:
                                    print (f' ✅ Swap successfully completed')
                                    print (f' ✅ Tx Hash: {swaps_tx.broadcast_result.txhash}')
                                    time.sleep(10)
                            else:
                                print (' 🛎️  Swap transaction could not be completed')
                    else:
                        print (' 🛎️  Swap amount is not greater than zero')
                else:
                    print ('Swaps not allowed on this wallet')

            # Redelegate anything we might have
            if user_action in [utility_constants.USER_ACTION_DELEGATE, utility_constants.USER_ACTION_WITHDRAW_DELEGATE, utility_constants.USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
                
                # Only delegate if the wallet is configured for delegations
                if 'delegate' in wallet.delegations:       

                    print ('\n------------------------------------')
                    print ('Starting delegations...')

                    # Update the balances after having done withdrawals and swaps
                    wallet.getBalances()

                    if 'uluna' in wallet.balances:     

                        # Figure out how much to delegate based on the user settings
                        uluna_balance = int(wallet.balances['uluna'])
                        
                        if wallet.delegations['delegate'].strip(' ')[-1] == '%':
                            percentage:int = int(wallet.delegations['delegate'].strip(' ')[0:-1]) / 100
                            delegated_uluna:int = int(uluna_balance * percentage)
                        else:
                            delegated_uluna:int = wallet.delegations['delegate'].strip(' ')

                        # Adjust this so we have the desired amount still remaining
                        delegated_uluna = int(delegated_uluna - ((utility_constants.WITHDRAWAL_REMAINDER) * 1000000))

                        if delegated_uluna > 0 and delegated_uluna <= wallet.balances['uluna']:
                            print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}')

                            delegation_tx = wallet.delegate().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                            # Simulate it
                            result = delegation_tx.simulate(delegated_uluna)

                            if result == True:
                                    
                                print (delegation_tx.readableFee())

                                # Now we know what the fee is, we can do it again and finalise it
                                result = delegation_tx.delegate(delegated_uluna)
                                
                                if result == True:
                                    delegation_tx.broadcast()
                                
                                    if delegation_tx.broadcast_result.is_tx_error():
                                        print (' 🛎️ Delegation failed, an error occurred')
                                        print (delegation_tx.broadcast_result.raw_log)
                                    else:
                                        print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                                        print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
                                else:
                                    print (' 🛎️  The deleggation could not be completed')
                            else:
                                print ('🛎️  The delegation could not be completed')
                        else:
                            print (' 🛎️  Delegation error: amount is not greater than zero')
                    else:
                        print (' 🛎️  No LUNC to delegate!')
                else:
                    print ('This wallet is not configured for delegations')

            print (' 💯 All actions on this validator are complete.')
            print ('------------------------------------')

    print (' 💯 Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()