#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    get_user_choice,
    get_user_number,
    get_user_text,
    isPercentage,
    UserConfig,
    Wallets,
    Wallet
)

import utility_constants

from terra_classic_sdk.core.coin import Coin

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
                #lunc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uluna'], False))).rstrip('0').rstrip('.')
                lunc_str = wallet.formatUluna(wallet.balances['uluna'], False)
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if 'uusd' in wallet.balances:
                #ustc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uusd'], False))).rstrip('0').rstrip('.')
                ustc_str = wallet.formatUluna(wallet.balances['uusd'], False)
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
            
        if answer == utility_constants.USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == utility_constants.USER_ACTION_QUIT:
            break

    # Get the first (and only) validator from the list
    for item in wallets_to_use:
        user_wallet = wallets_to_use[item]
        break
    
    return user_wallet, answer

def get_coin_selection(question:str, coins:dict, estimation_against:dict = None, wallet:Wallet = False) -> str | str | float:
    """
    Return a selected coin based on the provided list.
    """
    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Coin'))
    label_widths.append(len('Balance'))

    print ('estimation against:', estimation_against)

    if estimation_against is not None:
        label_widths.append(len('Estimation'))
        swaps_tx = wallet.swap().create()

    wallet:Wallet = Wallet()
    coin_list = []
    coin_values = {}
    coin_list.append('')

    for coin in coins:
        coin_list.append(coin)

        if coin in utility_constants.FULL_COIN_LOOKUP:
            coin_name = utility_constants.FULL_COIN_LOOKUP[coin]
            if len(str(coin_name)) > label_widths[1]:
                label_widths[1] = len(str(coin_name))

            coin_val = wallet.formatUluna(coins[coin])

            if len(str(coin_val)) > label_widths[2]:
                label_widths[2] = len(str(coin_val))

            if estimation_against is not None:
                swaps_tx.swap_amount = int(estimation_against['amount'])
                swaps_tx.swap_denom =  estimation_against['denom']

                swaps_tx.swap_request_denom = coin

                if coin != estimation_against['denom']:
                    estimated_result:Coin = swaps_tx.swapRate()
                else:
                    estimated_result:Coin = Coin(estimation_against['denom'], 1 * utility_constants.COIN_DIVISOR)

                estimated_value:str = wallet.formatUluna(estimated_result.amount)

                coin_values[coin] = estimated_value
                
                if len(str(estimated_value)) > label_widths[3]:
                    label_widths[3] = len(str(estimated_value))

    padding_str = ' ' * 100

    header_string = ' Number |'
    if label_widths[1] > len('Coin'):
        header_string += ' Coin' + padding_str[0:label_widths[1] - len('Coin')] + ' |'
    else:
        header_string += ' Coin |'

    if label_widths[2] > len('Balance'):
        header_string += ' Balance ' + padding_str[0:label_widths[2] - len('Balance')] + '|'
    else:
        header_string += ' Balance |'

    if estimation_against is not None:
        if label_widths[3] > len('Estimation'):
            header_string += ' Estimation ' + padding_str[0:label_widths[3] - len('Estimation')] + '|'
        else:
            header_string += ' Estimation |'

    horizontal_spacer = '-' * len(header_string)

    coin_to_use:str = None
    returned_estimation: float = None    
    answer:str = False

    while True:
        count:int = 0

        print (horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for coin in coins:
            count += 1
            
            if coin_to_use == coin:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]

            if coin in utility_constants.FULL_COIN_LOOKUP:
                coin_name = utility_constants.FULL_COIN_LOOKUP[coin]
                if label_widths[1] > len(coin_name):
                    coin_name_str = coin_name + padding_str[0:label_widths[1] - len(coin_name)]
                else:
                    coin_name_str = coin_name

                coin_val = wallet.formatUluna(coins[coin])

                if label_widths[2] > len(str(coin_val)):
                    balance_str = coin_val + padding_str[0:label_widths[2] - len(coin_val)]
                else:
                    balance_str = coin_val

                if estimation_against is None:
                    print (f"{count_str}{glyph} | {coin_name_str} | {balance_str}")
                else:
                    estimated_str =  float(coin_values[coin])
                    estimated_str = str(("%.6f" % (estimated_str)).rstrip('0').rstrip('.'))
                    print (f"{count_str}{glyph} | {coin_name_str} | {balance_str} | {estimated_str}")
    
        print (horizontal_spacer + '\n')

        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) > 0 and int(answer) <= count:
            coin_to_use = coin_list[int(answer)]
            if estimation_against is not None:
                returned_estimation = coin_values[coin_to_use]
            
        if answer == utility_constants.USER_ACTION_CONTINUE:
            if coin_to_use is not None:
                break
            else:
                print ('\nPlease select a coin first.\n')

        if answer == utility_constants.USER_ACTION_QUIT:
            break

    
    return coin_to_use, answer, returned_estimation

def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
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
        print (f'You can make swaps on the following wallets:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == utility_constants.USER_ACTION_QUIT:
            print (' 🛑 Exiting...')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.")
        exit()

    # List all the coins in this wallet, with the amounts available:
    print ('What coin do you want to swap FROM?')
    coin_from, answer, null_value = get_coin_selection("Select a coin number 1 - " + str(len(wallet.balances)) + ", 'X' to continue', or 'Q' to quit: ", wallet.balances)

    if answer == utility_constants.USER_ACTION_QUIT:
        print (' 🛑 Exiting...')
        exit()

    available_balance:float = float(wallet.formatUluna(wallet.balances[coin_from]))
    print (f'This coin has a maximum of {available_balance} {utility_constants.FULL_COIN_LOOKUP[coin_from]} available.')
    swap_uluna = get_user_number('How much do you want to swap? ', {'max_number': available_balance, 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False})

    print ('What coin do you want to swap TO?')
    coin_to, answer, estimated_amount = get_coin_selection("Select a coin number 1 - " + str(len(wallet.balances)) + ", 'X' to continue', or 'Q' to quit: ", wallet.balances, {'denom':coin_from, 'amount':swap_uluna}, wallet)

    if answer == utility_constants.USER_ACTION_QUIT:
        print (' 🛑 Exiting...')
        exit()

    print (f'You will be swapping {wallet.formatUluna(swap_uluna, False)} {utility_constants.FULL_COIN_LOOKUP[coin_from]} for approximately {estimated_amount} {utility_constants.FULL_COIN_LOOKUP[coin_to]}')
    complete_transaction = get_user_choice('Do you want to continue? (y/n) ', [])

    if complete_transaction == False:
        print (" 🛑 Exiting...")
        exit()

    # Create the swap object
    swaps_tx = wallet.swap().create()

    # Assign the details:
    swaps_tx.swap_amount = int(swap_uluna)
    swaps_tx.swap_denom = coin_from
    swaps_tx.swap_request_denom = coin_to

    result = swaps_tx.marketSimulate()
    if result == True:
        print (swaps_tx.readableFee())
        exit()
        result = swaps_tx.marketSwap()

        if result == True:
            swaps_tx.broadcast()
        
            if swaps_tx.broadcast_result.code == 11:
                while True:
                    print (' 🛎️  Increasing the gas adjustment fee and trying again')
                    swaps_tx.terra.gas_adjustment += utility_constants.GAS_ADJUSTMENT_INCREMENT
                    print (f' 🛎️  Gas adjustment value is now {swaps_tx.terra.gas_adjustment}')
                    swaps_tx.marketSimulate()
                    print (swaps_tx.readableFee())
                    swaps_tx.marketSwap()
                    swaps_tx.broadcast()

                    if swaps_tx.broadcast_result.code != 11:
                        break

                    if swaps_tx.terra.gas_adjustment >= utility_constants.MAX_GAS_ADJUSTMENT:
                        break

            if swaps_tx.broadcast_result.is_tx_error():
                print (' 🛎️  The send transaction failed, an error occurred:')
                print (f' 🛎️  {swaps_tx.broadcast_result.raw_log}')
            else:
                print (f' ✅ Sent amount: {wallet.formatUluna(swaps_tx.swap_amount, False)}')
                print (f' ✅ Tx Hash: {swaps_tx.broadcast_result.txhash}')
        else:
            print (' 🛎️  The swap transaction could not be completed')
            
    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()