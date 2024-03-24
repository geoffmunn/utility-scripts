#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import copy

from constants.constants import (
    BASIC_COIN_LOOKUP,
    FULL_COIN_LOOKUP,
    ULUNA
)

from classes.common import (
    check_database,
    check_version,
    divide_raw_balance,
    get_user_choice
)

from classes.wallets import UserWallets
from classes.wallet import UserWallet

def main():
    
    # Check if there is a new version we should be using
    check_version()
    check_database()

    # Get the user wallets. We'll be getting the balances futher on down.
    user_wallets:dict = UserWallets().loadUserWallets(get_balances = False)
    
    if len(user_wallets) == 0:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    just_main_coins:bool = get_user_choice(' ❓ Show just LUNC and USTC? (y/n) ', [])

    if just_main_coins == True:
        coin_lookup = BASIC_COIN_LOOKUP
        print ('\n 🕐 Getting the balances for just LUNC and USTC in your wallets, please wait...')
    else:
        coin_lookup = FULL_COIN_LOOKUP
        print ('\n 🕐 Getting the balances for all coins in your wallets, please wait...')

    balance_coins = {}
    label_widths  = []

    # These are the default widths of the first 4 columns
    # We need to go through each validator find its name and width
    label_widths.append(len('Coin'))
    label_widths.append(len('Wallet'))
    label_widths.append(len('Value'))
    label_widths.append(len('Available'))
    label_widths.append(len('Delegated'))

    # First, create a template of all the validators
    validator_template:dict = {'Available': '', 'Delegated': ''}

    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        delegations:dict  = wallet.getDelegations()

        if delegations is not None:
            for validator in delegations:
                if validator not in validator_template:
                    if int(delegations[validator]['balance_amount']) > 0 and len(delegations[validator]['rewards']) > 0:

                        validator_template.update({validator: ''})

                        # The default width is zero until we find out what the maximum width/value is:
                        label_widths.append(0)

    # Then, get all the coins we'll be charting (column 1)
    coin_denoms:list = []

    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getBalances()

        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        for denom in wallet.balances:
            raw_amount:float   = divide_raw_balance(wallet.balances[denom], denom)
            denom:str          = wallet.denomTrace(denom)
            if just_main_coins == True and denom in BASIC_COIN_LOOKUP: 
                if denom not in coin_denoms:
                    coin_denoms.append(denom)
            elif just_main_coins == False:
                if denom not in coin_denoms:
                    coin_denoms.append(denom)
            
        for denom in wallet.balances:
            
            raw_amount:float = divide_raw_balance(wallet.balances[denom], denom)
            denom:str        = wallet.denomTrace(denom)

            amount:str = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

            if float(amount) > 0:

                if denom in coin_lookup:
                    coin_denom = copy.deepcopy(coin_lookup[denom])

                    if len(coin_denom) > label_widths[0]:
                        label_widths[0] = len(coin_denom)

                    if coin_denom not in balance_coins:
                        balance_coins[coin_denom] = {}

                    if wallet_name not in balance_coins[coin_denom]:
                        balance_coins[coin_denom].update({wallet_name: validator_template})
                
                    cur_vals:dict = copy.deepcopy(balance_coins[coin_denom][wallet_name])
                    cur_vals.update({'Available': amount})
                    
                    if len(str(amount)) > label_widths[3]:
                        label_widths[3] = len(str(amount))

                    # Get the total number of delegations here and populate label_widths[3]
                    cur_wallets:dict = copy.deepcopy(balance_coins[coin_denom])
                    cur_wallets.update({wallet_name: cur_vals})

                    balance_coins.update({coin_denom: cur_wallets})

        # Get the delegations on this wallet
        delegations:dict = wallet.delegations

        # Keep track of the current delegated amount
        delegated_amount:float = 0
        if delegations is not None:
            for validator in delegations:
                for denom in delegations[validator]['rewards']:

                    if denom == ULUNA:
                        raw_amount        = divide_raw_balance(delegations[validator]['balance_amount'], denom)
                        delegated_amount += float(("%.6f" % (raw_amount)).rstrip('0').rstrip('.'))

                    raw_amount:float = divide_raw_balance(delegations[validator]['rewards'][denom], denom)
                    amount:str       = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

                    if denom in coin_lookup:
                        if float(amount) > 0:

                            coin_denom = copy.deepcopy(coin_lookup[denom])

                            if coin_denom not in balance_coins:
                                balance_coins[coin_denom] = {}

                            if wallet_name not in balance_coins[coin_denom]:
                                balance_coins[coin_denom].update({wallet_name: validator_template})
                                
                            cur_vals:dict = copy.deepcopy(balance_coins[coin_denom][wallet_name])

                            if denom == ULUNA:
                                cur_vals.update({'Delegated': delegated_amount})
                            else:
                                cur_vals.update({'Delegated': ''})
                                
                            cur_vals.update({validator: amount})
                            
                            cur_wallets:dict = copy.deepcopy(balance_coins[coin_denom])
                            cur_wallets.update({wallet_name: cur_vals})

                            balance_coins.update({coin_denom: cur_wallets})

                            # Find the validator column that this applies to:
                            val_count = 0
                            for val_name in validator_template:
                                if val_name == validator:
                                    if len(str(amount)) > label_widths[3 + val_count]:
                                        label_widths[3 + val_count] = len(str(amount))
                                    break
                                val_count += 1

                            # Update the delegation column width:
                            if len(str(delegated_amount)) > label_widths[4]:
                                label_widths[4] = len(str(delegated_amount))

    # Go and get all the prices in one request:
    coin_prices:dict = wallet.getCoinPrice(coin_denoms)

    # Figure out the biggest total
    for coin_type in balance_coins:
        for wallet_name in balance_coins[coin_type]:
            
            denom_total:float = 0
            if balance_coins[coin_type][wallet_name]['Available'] != '':
                denom_total = float(balance_coins[coin_type][wallet_name]['Available'])
            if balance_coins[coin_type][wallet_name]['Delegated'] != '':
                denom_total += float(balance_coins[coin_type][wallet_name]['Delegated'])
            
            # Get this coin's technical name (ie, uluna)
            this_coin:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(coin_type)]

            if this_coin in coin_prices:
                # Get the formatted value
                denom_value:str = "${:,.2f}".format((denom_total) * coin_prices[this_coin])

                if len(denom_value) > label_widths[2]:
                    label_widths[2] = len(denom_value)

    padding_str:str = ' ' * 100

    if label_widths[0] > len('Coin'):
        header_string = ' Coin' + padding_str[0:label_widths[0] - len('Coin')] + ' |'
    else:
        header_string = ' Coin |'

    if label_widths[1] > len('Wallet'):
        header_string += ' Wallet ' + padding_str[0:label_widths[1] - len('Wallet')] + '|'
    else:
        header_string += ' Wallet |'

    if label_widths[2] > len('Value'):
        header_string += ' Value ' + padding_str[0:label_widths[2] - len('Value')] + '|'
    else:
        header_string += ' Value |'

    val_count:int = 1
    for validator in validator_template:
        if label_widths[2 + val_count] >= len(validator):
            header_string += ' ' + validator + ' ' + padding_str[0:label_widths[2 + val_count] - len(validator)] + '|'
        else:
            header_string += ' ' + validator[0:label_widths[2 + val_count] - len(validator)] + ' |' 

        val_count += 1

    horizontal_spacer:str = '-' * len(header_string)

    # Sort the balance coins into alphabetical order    
    sorted_coins:dict = dict(sorted(balance_coins.items()))

    body_string:str = ''
    for coin_type in sorted_coins:

        current_coin =  ' ' + coin_type + padding_str[0:label_widths[0] - len(coin_type)] + ' |'
        body_string += current_coin

        first:bool = True
        for wallet_name in balance_coins[coin_type]:
            if first == True:
                body_string += ' ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'
            else:
                body_string += padding_str[0:len(current_coin) - 1] + '| ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'

            # Get this coin's technical name (ie, uluna)
            this_coin:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(coin_type)]

            # Add up the total amount we have for this wallet
            denom_total:float = 0
            if balance_coins[coin_type][wallet_name]['Available'] != '':
                denom_total = float(balance_coins[coin_type][wallet_name]['Available'])
            if balance_coins[coin_type][wallet_name]['Delegated'] != '':
                denom_total += float(balance_coins[coin_type][wallet_name]['Delegated'])

            # Format it nicely
            if this_coin in coin_prices:
                denom_value:str = "${:,.2f}".format((denom_total) * coin_prices[this_coin])
            else:
                denom_value:str = '---'

            body_string += ' ' + ((denom_value + padding_str)[0:label_widths[2]]) + ' |'
            
            val_count:int = 1
            for validator in balance_coins[coin_type][wallet_name]:
                body_string += ' ' +  (((str(balance_coins[coin_type][wallet_name][validator])) + padding_str)[0:label_widths[2 + val_count]]) + ' |'
                val_count += 1

            body_string += '\n'

            first = False

        body_string += horizontal_spacer + '\n'

    print ('\n')
    print (horizontal_spacer)
    print (header_string)
    print (horizontal_spacer)
    print (body_string)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()