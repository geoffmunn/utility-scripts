#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_version,
    get_precision
)

from constants.constants import (
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    ULUNA,
    UOSMO,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
)

from classes.wallet import UserWallet, UserParameters
from classes.wallets import UserWallets
from classes.send_transaction import send_transaction
from classes.transaction_core import TransactionResult

from terra_classic_sdk.core.coin import Coin

def get_send_to_address(user_wallets:UserWallet) -> list[str, str]:
    """
    Show a simple list address from what is found in the user_config file
    """

    label_widths:list = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)
                
    # Generic string we use for padding purposes
    padding_str:str   = ' ' * 100
    header_string:str = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' | Address                                      '
    else:
        header_string +=  ' Wallet name | Address                                      '

    horizontal_spacer:str = '-' * len(header_string)

    # Create default variables and values
    wallets_to_use:dict   = {}
    user_wallet:dict      = {}
    recipient_address:str = ''

    while True:

        count:int            = 0
        wallet_numbers:dict  = {}
        wallets_by_name:dict = {}

        print ('\n' + horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:UserWallet = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
            wallets_by_name[wallet.name.lower()] = count

            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str    = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]
            wallet_address:str = wallet.address
            
            print (f"{count_str}{glyph} | {wallet_name_str} | {wallet_address}")
            
        print (horizontal_spacer + '\n')

        print ('You can send to an address in your config file by typing the wallet name or number.')
        print ('You can also send to a completely new address by entering the wallet address.\n')

        answer:str = input("What is the address you are sending to? (or type 'X' to continue, or 'Q' to quit) ").lower()
        
        # Check if someone typed the name of a wallet
        if answer in wallets_by_name.keys():
            answer = str(wallets_by_name[answer])
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use:dict = {}

            key:str = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
        else:
            # check if this is an address we support:
            prefix:str = wallet.getPrefix(answer)

            if prefix in wallet.getSupportedPrefixes():
                recipient_address:str = answer
                break
            
        if answer == USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) wallet from the list
    if len(wallets_to_use) > 0:
        for item in wallets_to_use:
            user_wallet:UserWallet = wallets_to_use[item]
            recipient_address:str  = user_wallet.address
            break
    
    return recipient_address, answer

def main():
    
    # Check if there is a new version we should be using
    check_version()

    # Get the user wallets
    wallets           = UserWallets()
    user_wallets:dict = wallets.loadUserWallets()

    #user_wallets:dict = wallets.wallets
    user_addresses:dict = wallets.addresses

    if len(user_wallets) > 0:
        print (f'You can send LUNC, USTC, and minor coins on the following wallets:')

        wallet, answer = wallets.getUserSinglechoice(f"Select a wallet number 1 - {str(len(user_wallets))}, 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    denom, answer, null_value = wallet.getCoinSelection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom], denom)} {FULL_COIN_LOOKUP[denom]}")
    print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")

    user_params:UserParameters      = UserParameters()
    user_params.max_number          = float(wallet.formatUluna(wallet.balances[denom], denom, False))
    user_params.percentages_allowed = True
    user_params.target_amount       = wallet.formatUluna(wallet.balances[denom], denom)
    user_params.target_denom        = denom

    uluna_amount:str  = wallet.getUserNumber('How much are you sending (Q to quit)? ', user_params)

    if uluna_amount == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()
    else:
        uluna_amount = float(uluna_amount)

    uluna_amount = float(uluna_amount) * (10 ** get_precision(denom))
    # Print a list of the addresses in the user_config.yml file:
    recipient_address, answer = get_send_to_address(user_addresses)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # This is what we will be sending
    send_coin:Coin = wallet.createCoin(uluna_amount, denom)

    # NOTE: I'm pretty sure the memo size is int64, but I've capped it at 255 so python doens't panic
    memo:str = wallet.getUserText('Provide a memo (optional): ', 255, True)

    print (f'\n  ➜ Accessing the {wallet.name} wallet...')

    if ULUNA in wallet.balances:
        #print (f'Sending {wallet.formatUluna(send_coin.amount, send_coin.denom)} {FULL_COIN_LOOKUP[send_coin.denom]}')
        
        #recipient_wallet:UserWallet = UserWallet().create('target', recipient_address)
        #recipient_balance = recipient_wallet.getBalances()

        transaction_result:TransactionResult = send_transaction(wallet, recipient_address, send_coin, memo)
        
        # Now check the balance to see if it's arrived at the recipient wallet
        #if send_coin.denom in recipient_balance:
        #    current_balance:int = recipient_balance[send_coin.denom]
        #else:
        #    current_balance:int = 0
            
        #recipient_wallet.getBalances()
        transaction_result.wallet_denom = wallet.denom
        transaction_result.showResults()

    else:
        print (" 🛑 This wallet has no LUNC - you need a small amount to be present to pay for fees.")

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()