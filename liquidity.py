#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_database,
    check_version,
    get_precision,
    get_user_choice,
    is_percentage
)

from constants.constants import (
    CHAIN_DATA,
    EXIT_POOL,
    FULL_COIN_LOOKUP,
    JOIN_POOL,
    ULUNA,
    UOSMO,
    USER_ACTION_QUIT,
)

# https://www.reddit.com/r/CryptoCurrency/comments/1al52up/is_being_a_lp_liquidity_provider_actually/

from classes.wallet import UserParameters
from classes.wallets import UserWallets
from classes.liquidity_transaction import LiquidityTransaction, join_liquidity_pool, exit_liquidity_pool
from classes.transaction_core import TransactionResult

from terra_classic_sdk.core.coin import Coin

def main():

    # Check if there is a new version we should be using
    check_version()
    check_database()

    # Get the user wallets
    wallets           = UserWallets()
    user_wallets:dict = wallets.loadUserWallets(filter = [CHAIN_DATA[UOSMO]['bech32_prefix']])

    if len(user_wallets) > 0:
        print (f'You can join or exit liquidity pools on the following wallets:')

        wallet, answer = wallets.getUserSinglechoice(f"Select a wallet number 1 - {str(len(user_wallets))}, 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    denom:str = ULUNA

    print ('\n 🕐  Loading pool list, please wait...')
    
    # Create the send tx object
    liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)

    # Get the pool off the user
    user_pool, answer = liquidity_tx.getPoolSelection('Enter the pool number you want to use, (X) to continue, or (Q) to quit: ', wallet)

    # Update the liquidity object with the details so we can get the pool assets
    liquidity_tx.pools        = wallet.pools
    liquidity_tx.wallet       = wallet
    liquidity_tx.wallet_denom = wallet.denom
    liquidity_tx.pool_id      = user_pool

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # Are we joining aliquidity pool, or exiting?
    print ('')
    join_or_exit = get_user_choice(' ❓ Do you want to join (J) a liquidity pool, exit a pool(E), or quit this process (Q)? ', [JOIN_POOL, EXIT_POOL, USER_ACTION_QUIT])

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    amount_out:float = None
    amount_in:int    = None

    if join_or_exit == JOIN_POOL:
        print (f"\nThe {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom], denom)} {FULL_COIN_LOOKUP[denom]}\n")
        print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")

        user_params:UserParameters      = UserParameters()
        user_params.max_number          = float(wallet.formatUluna(wallet.balances[denom], denom, False))
        user_params.percentages_allowed = True
        user_params.target_amount       = wallet.formatUluna(wallet.balances[denom], denom)
        user_params.target_denom        = denom
        
        amount_in:int = wallet.getUserNumber('How much are you sending (Q to quit)? ', user_params)
        
        if amount_in == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        print (f'You are about to add {wallet.formatUluna(amount_in, denom)} {FULL_COIN_LOOKUP[denom]} to Pool #{user_pool}.')
        transaction_result:TransactionResult = join_liquidity_pool(wallet, user_pool, amount_in, True)
    else:
        # This is the exit pool logic
        # Get the assets for the summary list
        pool_assets:dict  = liquidity_tx.getPoolAssets()
        asset_values:dict = liquidity_tx.getAssetValues(pool_assets)
        total_value:float = 0

        print ('This pool holds:\n')
        for asset_denom in pool_assets:
            print (' *  ' + str(round(pool_assets[asset_denom] / (10 ** get_precision(asset_denom)), 2)) + ' ' + FULL_COIN_LOOKUP[asset_denom] + ' $' + str(round(asset_values[asset_denom],2)))
            total_value += asset_values[asset_denom]

        total_value = round(total_value, 2)

        print ('')
        print (f'    Total value: ${total_value}')

        print ('\nHow much do you want to withdraw?')
        print ('You can type a percentage (eg 50%), or an exact amount of LUNC.')

        user_params:UserParameters      = UserParameters()
        user_params.convert_percentages = False
        user_params.max_number          = float(pool_assets[ULUNA]/ (10 ** get_precision(ULUNA)))
        user_params.percentages_allowed = True
        user_params.target_amount       = wallet.formatUluna(wallet.balances[denom], denom)
        user_params.target_denom        = denom

        user_withdrawal:str = wallet.getUserNumber('How much LUNC are you withdrawing (Q to quit)? ', user_params)
        
        if user_withdrawal == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        if is_percentage(user_withdrawal):
            amount_out:float   = float(user_withdrawal[:-1]) / 100
            uluna_amount:float = round(pool_assets[ULUNA] * amount_out, 2)
        else:
            # If this is a precise amount, we need to convert this into a percentage of the total amount of LUNC   
            amount_out:float   = round(int(float(user_withdrawal)) / int(pool_assets[ULUNA]), 2)
            uluna_amount:float = float(user_withdrawal)

        print (f'You are about to withdraw {wallet.formatUluna(uluna_amount, denom)} LUNC ({round(int(uluna_amount) / int(pool_assets[ULUNA]) * 100, 2)}%) from Pool #{user_pool}.')
        transaction_result:TransactionResult = exit_liquidity_pool(wallet, user_pool, amount_out, True)

    transaction_result.showResults()

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()