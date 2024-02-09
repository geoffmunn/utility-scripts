#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_database,
    check_version,
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
    join_or_exit = get_user_choice(' ❓ Do you want to join (J) a liquidity pool, exit a pool(E), or quit this process (Q)? ', [JOIN_POOL, EXIT_POOL, USER_ACTION_QUIT])

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    amount_out:float = None
    amount_in:int    = None

    if join_or_exit == JOIN_POOL:
        print (f"\nThe {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom], denom)} {FULL_COIN_LOOKUP[denom]}\n")
        print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")

        amount_in:int = wallet.getUserNumber('How much are you sending? ', {'max_number': float(wallet.formatUluna(wallet.balances[denom], denom, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': denom})
        #liquidity_tx.amount_in = uluna_amount
        
        liquidity_coin:Coin = wallet.createCoin(denom, amount_in)
        coin_amount:float   = wallet.formatUluna(liquidity_coin.amount, liquidity_coin.denom)

    else:
        # This is the exit pool logic
        # Get the assets for the summary list
        pool_assets:dict  = liquidity_tx.getPoolAssets()
        asset_values:dict = liquidity_tx.getAssetValues(pool_assets)
        total_value:float = 0

        print ('This pool holds:\n')
        for asset_denom in pool_assets:
            print (' *  ' + str(round(pool_assets[asset_denom], 2)) + ' ' + FULL_COIN_LOOKUP[asset_denom] + ' $' + str(round(asset_values[asset_denom],2)))
            total_value += asset_values[asset_denom]

        total_value = round(total_value, 2)

        print ('')
        print (f'    Total value: ${total_value}')

        print ('\nHow much do you want to withdraw?')
        print ('You can type a percentage (eg 50%), or an exact amount of LUNC.')

        user_withdrawal:str = wallet.getUserNumber('How much LUNC are you withdrawing? ', {'max_number': float(pool_assets[ULUNA]), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': False, 'keep_minimum': False, 'target_denom': ULUNA})
        
        if is_percentage(user_withdrawal):
            amount_out:float  = float(user_withdrawal[:-1]) / 100
            coin_amount:float = round(pool_assets[ULUNA] * amount_out, 2)
        else:
            # If this is a precise amount, we need to convert this into a percentage of the total amount of LUNC   
            coin_amount:float = wallet.formatUluna(user_withdrawal, ULUNA)
            amount_out:float  = round(int(coin_amount) / int(pool_assets[ULUNA]), 2)

        #liquidity_coin:Coin = wallet.createCoin(denom, amount_out)
        #liquidity_tx.amount_out = amount_out
        
    #swap_coin:Coin = wallet.createCoin(coin_from, swap_uluna)
    #transaction_result:TransactionResult = swap_coins(wallet, swap_coin, coin_to, estimated_amount, True)
    
    if join_or_exit == JOIN_POOL:
        print (f'You are about to add {wallet.formatUluna(amount_in, denom)} {FULL_COIN_LOOKUP[denom]} to Pool #{user_pool}.')
        transaction_result:TransactionResult = join_liquidity_pool(wallet, user_pool, amount_in, True)
    else:
        print (f'You are about to withdraw {coin_amount} LUNC ({round(int(coin_amount) / int(pool_assets[ULUNA]) * 100, 2)}%) from Pool #{user_pool}.')
        
        transaction_result:TransactionResult = exit_liquidity_pool(wallet, user_pool, amount_out, True)

    transaction_result.showResults()

    # # Populate it with the details we have so far:
    # liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)
    # liquidity_tx.amount_in = uluna_amount
    # liquidity_tx.amount_out = amount_out
    # liquidity_tx.balances        = wallet.balances
    # liquidity_tx.pool_id         = user_pool
    # liquidity_tx.pools           = wallet.pools
    # liquidity_tx.sender_address  = wallet.address
    # liquidity_tx.source_channel  = CHAIN_DATA[wallet.denom]['ibc_channels'][ULUNA]
    # liquidity_tx.wallet          = wallet
    # liquidity_tx.wallet_denom    = wallet.denom

    # #denom, answer, null_value = wallet.getCoinSelection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)

    # #if answer == USER_ACTION_QUIT:
    # #    print (' 🛑 Exiting...\n')
    # #    exit()

    # # Populate it with remaining required details:
    # liquidity_tx.liquidity_denom  = denom
    
    # # Simulate it
    # if join_or_exit == JOIN_POOL:
    #     result:bool = liquidity_tx.joinSimulate()
    # else:
    #     result:bool = liquidity_tx.exitSimulate()
    
    # if result == True:

    #     if join_or_exit == JOIN_POOL:
    #         print (f'You are about to add {wallet.formatUluna(uluna_amount, denom)} {FULL_COIN_LOOKUP[denom]} to Pool #{liquidity_tx.pool_id}.')
    #     else:
    #         print (f'You are about to withdraw {coin_amount} LUNC ({round(int(coin_amount) / int(pool_assets[ULUNA]) * 100, 2)}%) from Pool #{liquidity_tx.pool_id}.')

    #     print (liquidity_tx.readableFee())

    #     user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

    #     if user_choice == False:
    #         print (' 🛑 Exiting...\n')
    #         exit()

    #     # Now we know what the fee is, we can do it again and finalise it
    #     if join_or_exit == JOIN_POOL:
    #         result:bool = liquidity_tx.joinPool()
    #     else:
    #         result:bool = liquidity_tx.exitPool()
            
    #     if result == True:
            
    #         liquidity_tx.broadcast()

    #         if liquidity_tx.broadcast_result is not None and liquidity_tx.broadcast_result.code == 32:
    #             while True:
    #                 print (' 🛎️  Boosting sequence number and trying again...')

    #                 liquidity_tx.sequence = liquidity_tx.sequence + 1
                    
    #                 if join_or_exit == JOIN_POOL:
    #                     liquidity_tx.joinSimulate()
    #                     liquidity_tx.joinPool()
    #                 else:
    #                     liquidity_tx.exitSimulate()
    #                     liquidity_tx.exitPool()

    #                 liquidity_tx.broadcast()

    #                 if liquidity_tx is None:
    #                     break

    #                 # Code 32 = account sequence mismatch
    #                 if liquidity_tx.broadcast_result.code != 32:
    #                     break

    #         if liquidity_tx.broadcast_result is None or liquidity_tx.broadcast_result.is_tx_error():
    #             if liquidity_tx.broadcast_result is None:
    #                 print (' 🛎️  The liquidity transaction failed, no broadcast object was returned.')
    #             else:
    #                 print (' 🛎️  The liquidity transaction failed, an error occurred:')
    #                 if liquidity_tx.broadcast_result.raw_log is not None:
    #                     print (f' 🛎️  Error code {liquidity_tx.broadcast_result.code}')
    #                     print (f' 🛎️  {liquidity_tx.broadcast_result.raw_log}')
    #                 else:
    #                     print ('No broadcast log was available.')
    #         else:
    #             if liquidity_tx.result_received is not None:
    #                 if join_or_exit == JOIN_POOL:
    #                     print (f' ✅ Sent amount into pool #{liquidity_tx.pool_id}: {wallet.formatUluna(liquidity_tx.result_sent.amount, liquidity_tx.liquidity_denom)} {FULL_COIN_LOOKUP[liquidity_tx.liquidity_denom]}')
    #                     print (f' ✅ Joined amount: {liquidity_tx.result_received.amount} shares')
    #                 else:
    #                     print (f' ✅ Withdrawn amount from pool #{liquidity_tx.pool_id}: {float(liquidity_tx.amount_out) * 100}%')
    #                     print (f' ✅ Received coins: ')
    #                     received_coin:Coin
    #                     for received_coin in liquidity_tx.result_received:
    #                         print ('    * ' + wallet.formatUluna(received_coin.amount, received_coin.denom, True))
                    
    #                 print (f' ✅ Tx Hash: {liquidity_tx.broadcast_result.txhash}')

    #     else:
    #         print (' 🛎️  The liquidity transaction could not be completed')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()