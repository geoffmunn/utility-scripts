#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
from getpass import getpass

from utility_classes import (
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

def get_user_number(question:str) -> int:
    """
    Get ther user input - must be a number.
    """ 
    
    while True:    
        answer = input(question).strip(' ')
        if answer.isdigit():
            break

    return answer

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

            wallets_to_use = {}

            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == 'x':
            break

        if answer == 'q':
            break

    return wallets_to_use, answer

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

    # If we're sending LUNC then we need a few more details:
    recipient_address:str = input('What is the address you are sending to? ')
    lunc_amount:int       = get_user_number('How much are you sending? ')
    memo:str              = input('Provide a memo (optional): ').strip(' ')

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        print ('####################################')
        print (f'Accessing the {wallet.name} wallet...')

        # Update the balances after having done withdrawals and swaps
        wallet.getBalances()

        if 'uluna' in wallet.balances:
            # Adjust this so we have the desired amount still remaining
            uluna_amount = int(lunc_amount) * 1000000

            if uluna_amount > 0 and uluna_amount <= (wallet.balances['uluna'] - (utility_constants.WITHDRAWAL_REMAINDER * 1000000)):
                print (f'Sending {wallet.formatUluna(uluna_amount, True)}')

                send_tx = wallet.send().create()

                # Simulate it
                result = send_tx.simulate(recipient_address, uluna_amount, memo)

                if result == True:
                    
                    print (send_tx.readableFee())
                        
                    # Now we know what the fee is, we can do it again and finalise it
                    result = send_tx.send()
                    
                    if result == True:
                        send_tx.broadcast()
                    
                        if send_tx.broadcast_result.is_tx_error():
                            print (' 🛎️ Send transaction failed, an error occurred')
                            print (send_tx.broadcast_result.raw_log)
                        else:
                            print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, True)}')
                            print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
                    else:
                        print (' 🛎️  The send transaction could not be completed')
                else:
                    print (' 🛎️  The send transaction could not be completed')
                    
            else:
                print (' 🛎️  Sending error: Not enough LUNC will be left in the account to cover fees')
            
    print (' 💯 Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()