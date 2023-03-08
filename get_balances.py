#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import copy
import yaml
import requests
import json
import cryptocode
import time

from getpass import getpass

from utility_classes import (
    Wallets,
    Wallet
)

import utility_constants

coin_lookup = {
    'uaud': 'AUT',
    'ucad': 'CAT',
    'uchf': 'CHT',
    'ucny': 'CNT',
    'udkk': 'DKT',
    'ueur': 'EUT',
    'ugbp': 'GBT',
    'uhkd': 'HKT',
    'uidr': 'IDT',
    'uinr': 'INT',
    'ujpy': 'JPT',
    'ukrw': 'KRT',
    'uluna': 'LUNC',
    'umnt': 'MNT',
    'umyr': 'MYT',
    'unok': 'NOT',
    'uphp': 'PHT',
    'usdr': 'SDT',
    'usek': 'SET',
    'usgd': 'SGT',
    'uthb': 'THT',
    'utwd': 'TWT',
    'uusd': 'UST'
}

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

    if len(user_wallets) == 0:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # Now start doing stuff

    balance_coins = {}

    # Token   Wallet  Current CryptoPlant Gingko  Garuda  TerraCVita
    # Lunc    lunc1   100     1000
    #         lunc2   100     2000
    #         lunc3   100     1500
    #         lunc4   100     4000
    #         onyx                                1000
    #         toxic                       2000
    #         terra                                       2000
    

    # {
    #     'AUT': {
    #         'Lunc Original': {
    #             'wallet': 0.001, 
    #             'CryptoPlant': '', 
    #             'Garuda Nodes  🇮🇩': '',
    #             'Ginkou': '', 
    #             'TerraCVita 🌎 0% fee': ''}}, 'CAT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'CHT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'CNT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'DKT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'EUT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'GBT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'HKT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'IDT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'INT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'JPT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'KRT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'LUNC': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'MNT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'MYT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'NOT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'PHT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'SDT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'SET': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'THT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'TWT': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}, 'UST': {'Lunc Original': {'wallet': 0.001, 'CryptoPlant': '', 'Garuda Nodes  🇮🇩': '', 'Ginkou': '', 'TerraCVita 🌎 0% fee': ''}}}


    # First, create a template of all the validators
    validator_template:dict = {'wallet': 0}
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        
        delegations = wallet.getDelegations()

        for validator in delegations:
            validator_template.update({validator: ''})


    # First, get all the coins we'll be charting (column 1)

    label_widths = []

    label_widths.append(len(' Coin '))
    label_widths.append(len(' Wallet '))

    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        for denom in wallet.balances:
            amount = float(wallet.balances[denom]) / utility_constants.COIN_DIVISOR
            
            if amount > 0:

                if denom in coin_lookup:
                    coin_denom = copy.deepcopy(coin_lookup[denom])

                    if len(coin_denom) > label_widths[0]:
                        label_widths[0] = len(coin_denom)

                    if coin_denom not in balance_coins:
                        balance_coins[coin_denom] = {}

                    if wallet_name not in balance_coins[coin_denom]:
                        balance_coins[coin_denom].update({wallet_name: validator_template})
                
                    cur_vals:dict = balance_coins[coin_denom][wallet_name]
                    cur_vals.update({'wallet': amount})
                    
                    # if len(str(amount)) > current_label_width:
                    #     current_label_width = len(str(amount))

                    cur_wallets:dict = balance_coins[coin_denom]
                    cur_wallets.update({wallet_name: copy.deepcopy(cur_vals)})

                    balance_coins.update({coin_denom: copy.deepcopy(cur_wallets)})

        delegations = wallet.getDelegations()
        for validator in delegations:
            #print (f'rewards on {validator}:', delegations[validator]['rewards'])
            for denom in delegations[validator]['rewards']:
                amount = round(float(delegations[validator]['rewards'][denom]) / utility_constants.COIN_DIVISOR, 3)

                if denom in coin_lookup:

                    if amount > 0:

                        coin_denom = copy.deepcopy(coin_lookup[denom])

                        if coin_denom not in balance_coins:
                            balance_coins[coin_denom] = {}

                        if wallet_name not in balance_coins[coin_denom]:
                            balance_coins[coin_denom].update({wallet_name: validator_template})
                            
                        cur_vals:dict = balance_coins[coin_denom][wallet_name]
                        cur_vals.update({validator: amount})
                        
                        cur_wallets:dict = balance_coins[coin_denom]
                        cur_wallets.update({wallet_name: copy.deepcopy(cur_vals)})

                        #print (f'updating {coin_denom}')
                        balance_coins.update({coin_denom: copy.deepcopy(cur_wallets)})

    
    print ('----------')

    padding_str = '                                           '

    #wallet_column_title = (' Wallet' + padding_str)[0:wallet_label_width]
    #current_column_title = (' Current' + padding_str)[0:current_label_width]
    if label_widths[0] > len('Coin'):
        header_string = ' Coin' + padding_str[0:label_widths[0]-len(' Coin ')] + '|'
    else:
        header_string = ' Coin |'

    if label_widths[1] > len('Wallet'):
        header_string += ' Wallet ' + padding_str[0:label_widths[1]-len(' Wallet ')] + '|'
    else:
        header_string += ' Wallet |'

    #header_string = f' Coin |{wallet_column_title}| Current'
    header_string += ' Current '

    for validator in validator_template:
        header_string += ('\t' + validator)

    body_string = ''
    for coin_type in balance_coins:

        current_coin =  ' ' + coin_type + padding_str[0:label_widths[0]-len('Coin ')] + '|'

        body_string += current_coin

        first = True
        for wallet_name in balance_coins[coin_type]:
            if first == True:
                body_string += ' ' + ((wallet_name + padding_str)[0:label_widths[1]])
            else:
                body_string += padding_str[0:len(current_coin) - 1] + '| ' + ((wallet_name + padding_str)[0:label_widths[1]])


            for validator in balance_coins[coin_type][wallet_name]:
                body_string += ('\t' + str(balance_coins[coin_type][wallet_name][validator]))

            body_string += '\n'

            first = False

    print (header_string)
    print (body_string)
    
    #print (Token   Wallet  Current CryptoPlant Gingko  Garuda  TerraCVita)
    #print (balance_coins)
    

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()