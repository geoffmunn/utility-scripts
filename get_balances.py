#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import copy

from getpass import getpass

from utility_classes import (
    check_version,
    get_user_choice,
    UserConfig,
    Wallets,
    Wallet
)

from utility_constants import (
    COIN_DIVISOR,
    BASIC_COIN_LOOKUP,
    FULL_COIN_LOOKUP,
    ULUNA
)

def main():
    
    # Check if there is a new version we should be using
    check_version()

    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    if decrypt_password == '':
        print (' 🛑 Exiting...\n')
        exit()

    just_main_coins:bool = get_user_choice('Show just LUNC and USTC? (y/n) ', [])

    if just_main_coins == True:
        coin_lookup = BASIC_COIN_LOOKUP
    else:
        coin_lookup = FULL_COIN_LOOKUP

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

    if len(user_wallets) == 0:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # Now start doing stuff

    balance_coins = {}
    label_widths  = []

    # These are the default widths of the first 4 columns
    # We need to go through each validator find its name and width
    label_widths.append(len('Coin'))
    label_widths.append(len('Wallet'))
    label_widths.append(len('Available'))
    label_widths.append(len('Delegated'))

    # First, create a template of all the validators
    validator_template:dict = {'Available': '', 'Delegated': ''}

    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        
        delegations:dict = wallet.getDelegations()

        if delegations is not None:
            for validator in delegations:
                
                if validator not in validator_template:
                    if int(delegations[validator]['balance_amount']) > 0 and len(delegations[validator]['rewards']) > 0:
                    #if len(delegations[validator]['rewards']) > 0:

                        validator_template.update({validator: ''})

                        # The default width is zero until we find out what the maximum width/value is:
                        label_widths.append(0)

    # Then, get all the coins we'll be charting (column 1)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

        # Update the wallet name column max width
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        for denom in wallet.balances:            
            ibc_denom = wallet.denomTrace(denom)
            raw_amount = float(wallet.balances[denom]) / COIN_DIVISOR

            if ibc_denom != False:     
                denom = ibc_denom['base_denom']

            amount     = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

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
                    
                    if len(str(amount)) > label_widths[2]:
                        label_widths[2] = len(str(amount))

                    # Get the total number of delegations here and populate label_widths[3]
                    cur_wallets:dict = copy.deepcopy(balance_coins[coin_denom])
                    cur_wallets.update({wallet_name: cur_vals})

                    balance_coins.update({coin_denom: cur_wallets})

        delegations = wallet.getDelegations()
        delegated_amount = 0

        if delegations is not None:
            for validator in delegations:
                for denom in delegations[validator]['rewards']:

                    if denom == ULUNA:
                        raw_amount = delegations[validator]['balance_amount'] / COIN_DIVISOR
                        delegated_amount += float(("%.6f" % (raw_amount)).rstrip('0').rstrip('.'))

                    raw_amount = float(delegations[validator]['rewards'][denom]) / COIN_DIVISOR
                    amount = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

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
                                    if len(str(amount)) > label_widths[2 + val_count]:
                                        label_widths[2 + val_count] = len(str(amount))
                                    break
                                val_count += 1

                            # Update the delegation column width:
                            if len(str(delegated_amount)) > label_widths[3]:
                                label_widths[3] = len(str(delegated_amount))

    padding_str = ' ' * 100

    if label_widths[0] > len('Coin'):
        header_string = ' Coin' + padding_str[0:label_widths[0]-len('Coin')] + ' |'
    else:
        header_string = ' Coin |'

    if label_widths[1] > len('Wallet'):
        header_string += ' Wallet ' + padding_str[0:label_widths[1]-len('Wallet')] + '|'
    else:
        header_string += ' Wallet |'

    val_count = 1
    for validator in validator_template:
        if label_widths[1 + val_count] >= len(validator):
            header_string += ' ' + validator + ' ' + padding_str[0:label_widths[1 + val_count] - len(validator)] + '|'
        else:
            header_string += ' ' + validator[0:label_widths[1 + val_count] - len(validator)] + ' |' 

        val_count += 1

    horizontal_spacer = '-' * len(header_string)

    # Sort the balance coins into alphabetical order    
    sorted_coins = dict(sorted(balance_coins.items()))

    body_string = ''
    for coin_type in sorted_coins:

        current_coin =  ' ' + coin_type + padding_str[0:label_widths[0]-len(coin_type)] + ' |'
        body_string += current_coin

        first = True
        for wallet_name in balance_coins[coin_type]:
            if first == True:
                body_string += ' ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'
            else:
                body_string += padding_str[0:len(current_coin) - 1] + '| ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'

            val_count = 1
            for validator in balance_coins[coin_type][wallet_name]:
                body_string += ' ' +  (((str(balance_coins[coin_type][wallet_name][validator])) + padding_str)[0:label_widths[1 + val_count]]) + ' |'
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