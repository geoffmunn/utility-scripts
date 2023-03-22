#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
from getpass import getpass

from utility_classes import (
    UserConfig,
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

def isDigit(x):
    """
    A better method for identifying digits. This one can handle decimal places.
    """

    try:
        float(x)
        return True
    except ValueError:
        return False
    
def get_user_number(question:str, max_number:float) -> int:
    """
    Get ther user input - must be a number.
    """ 
    
    while True:    
        answer = input(question).strip(' ')
        if isDigit(answer):

            if float(answer) > 0 and float(answer) <= max_number:
                break
            elif float(answer) <= 0:
                print (f' 🛎️  The transfer amount must be greater than zero')
            elif float(answer) > max_number:
                print (f' 🛎️  The transfer amount must be less than {max_number}')

    return float(answer)

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
            lunc_str = wallet.formatUluna(wallet.balances['uluna'], False)
            ustc_str = wallet.formatUluna(wallet.balances['uusd'], False)
            
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
        break
    
    return user_wallet, answer

def get_user_text(question:str, max_length:int) -> str:
    """
    Get a text string from the user - must be less than a definied length
    """

    while True:    
        answer = input(question).strip(' ')

        if len(answer) > max_length:
            print (f' 🛎️  The length must be less than {max_length}')
        else:
            break

    return str(answer)

def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You can send LUNC on the following wallets:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # If we're sending LUNC then we need a few more details:
    recipient_address:str = input('What is the address you are sending to? ')

    # Get the balances
    #Ewallet.getBalances()

    print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances['uluna'], True)}")
    
    lunc_amount:int       = get_user_number('How much are you sending? ', float(wallet.formatUluna(wallet.balances['uluna'], False)))
    memo:str              = get_user_text('Provide a memo (optional): ', 255)

    # Now start doing stuff
    print (f'\nAccessing the {wallet.name} wallet...')

    if 'uluna' in wallet.balances:
        # Adjust this so we have the desired amount still remaining
        uluna_amount = int(lunc_amount) * utility_constants.COIN_DIVISOR

        if uluna_amount > 0 and uluna_amount <= (wallet.balances['uluna'] - (utility_constants.WITHDRAWAL_REMAINDER * utility_constants.COIN_DIVISOR)):
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
                
                    if send_tx.broadcast_result.code == 11:
                        while True:
                            print (' 🛎️  Increasing the gas adjustment fee and trying again')
                            send_tx.terra.gas_adjustment += 0.5
                            send_tx.simulate(recipient_address, uluna_amount, memo)
                            print (send_tx.readableFee())
                            send_tx.send()
                            send_tx.broadcast()

                            if send_tx.broadcast_result.code != 11:
                                break

                            if send_tx.terra.gas_adjustment >= utility_constants.MAX_GAS_ADJUSTMENT:
                                break

                    if send_tx.broadcast_result.is_tx_error():
                        print (' 🛎️  The send transaction failed, an error occurred:')
                        print (f' 🛎️  {send_tx.broadcast_result.raw_log}')
                    else:
                        print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, True)}')
                        print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
                else:
                    print (' 🛎️  The send transaction could not be completed')
            else:
                print (' 🛎️  The send transaction could not be completed')
                
        else:
            print (' 🛎️  Sending error: Not enough LUNC will be left in the account to cover fees')
            
    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()