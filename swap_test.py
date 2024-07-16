#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import base64
import json
import math
import sqlite3

from classes.common import (
    check_database,
    check_version,
    divide_raw_balance,
    get_user_choice,
)

from constants.constants import (
    DB_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT_SWAPS,
    USER_ACTION_QUIT,
    ULUNA,
    UOSMO,
    UUSD,
)

from classes.delegation_transaction import DelegationTransaction
from classes.governance import Governance
from classes.send_transaction import SendTransaction
from classes.swap_transaction import SwapTransaction
from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.withdrawal_transaction import WithdrawalTransaction
from classes.transaction_core import TransactionResult
from classes.liquidity_transaction import LiquidityTransaction
from terra_classic_sdk.core.fee import Fee

from terra_classic_sdk.core.broadcast import (
    BlockTxBroadcastResult,
    TxLog
)

#from hashlib import sha256

from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins

def main():
        
    # for i in range(2000):
    #     test = f'transfer/channel-{i}/cosmos'.encode('utf-8')
    #     hashed =  sha256(test).hexdigest()
    #     if hashed.upper() == '27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2':
    #         print ('found on channel', i)
    #         print (hashed)
    #         exit
    #exit()
    
    #coin_list:Coins  = Coins.from_str('123456789uluna,1234uusd')
    
    # test:Coins = Coins()
    # coin1:Coin = Coin.from_data({'amount': '123456789', 'denom': 'uluna'})
    # coin2:Coin = Coin.from_data({'amount': '999', 'denom': 'uusd'})
    # #print ('coin:', coin)
    # test:Coins.add() = Coins.from_proto([coin1, coin2])
    # #est:Coins.add(coin)
    # #coin:Coin = Coin.from_data({'amount': '999', 'denom': 'uusd'})
    # #test:Coins.add(coin)

    # #print ('coin:', coin)

    # for x in test:
    #     print (x.amount, x.denom)

    # #for coin in coin_list:
    # #    if coin.denom == ULUNA:
    # #        test = Coins(coin)
            
    # print ('coins:', test)
    # exit()

    # Check if there is a new version we should be using
    check_version()
    check_database()
    # Get the user wallets
    wallets = UserWallets()
    user_wallets = wallets.loadUserWallets()

    if user_wallets is None:  
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    if len(user_wallets) > 0:
        print (f'You can make swaps on the following wallets:')

        wallet, answer = wallets.getUserSinglechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    
    # # List all the coins in this wallet, with the amounts available:
    # print ('\nWhat coin do you want to swap FROM?')
    # coin_count:int = 0
    # for coin in wallet.balances:
    #     if coin in FULL_COIN_LOOKUP:
    #         coin_count += 1

    # coin_from, answer, null_value = wallet.getCoinSelection("Select a coin number 1 - " + str(coin_count) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances)

    # if answer == USER_ACTION_QUIT:
    #     print (' 🛑 Exiting...\n')
    #     exit()

    # available_balance:float = wallet.formatUluna(wallet.balances[coin_from], coin_from)
    # print (f'This coin has a maximum of {available_balance} {FULL_COIN_LOOKUP[coin_from]} available.')
    # swap_uluna = wallet.getUserNumber("How much do you want to swap? (Or type 'Q' to quit) ", {'max_number': float(available_balance), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': coin_from})

    # if swap_uluna == USER_ACTION_QUIT:
    #     print (' 🛑 Exiting...\n')
    #     exit()

    # print ('\nWhat coin do you want to swap TO?')
    # coin_to, answer, estimated_amount = wallet.getCoinSelection("Select a coin number 1 - " + str(len(FULL_COIN_LOOKUP)) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances, False, {'denom':coin_from, 'amount':swap_uluna})

    # if answer == USER_ACTION_QUIT:
    #     print (' 🛑 Exiting...\n')
    #     exit()

    # estimated_amount = str(("%.6f" % (estimated_amount)).rstrip('0').rstrip('.'))

    # WITHDRAWALS:
    # withdrawal_tx = WithdrawalTransaction().create(seed = wallet.seed, delegator_address = wallet.address, validator_address = 'terra18kdk2kf8uvzs5gghky23hv4q7wdnk0ff2k83wt')
    # # Assign the details:
    # withdrawal_tx.balances           = wallet.balances
    # withdrawal_tx.wallet_denom       = wallet.denom

    # withdrawal_tx.height = 16375494
    # withdrawal_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=1932357, gas_used=555346 , height = withdrawal_tx.height, txhash='F9AD4AE979D134EDCFBB6F19148BC82459A437E6945C06CE4776D136B312B795')

    # transaction_result:TransactionResult = withdrawal_tx.findTransaction()

    # print (f' ✅ Received amount: ')
    # received_coin:Coin
    # for received_coin in transaction_result.result_received:
    #     print ('    * ' + wallet.formatUluna(received_coin.amount, received_coin.denom, True))
    # print (f' ✅ Tx Hash: {transaction_result.broadcast_result.txhash}')

    # # DELEGATE AMOUNT
    # delegation_tx = DelegationTransaction().create(seed = wallet.seed)
    # # Assign the details:
    # delegation_tx.balances           = wallet.balances
    # delegation_tx.wallet_denom       = wallet.denom

    # height = 16440598
    # delegation_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=1581418, gas_used=460805 , height = height, txhash='37FC908BA67060F300BD989FEDC09B0339D6C6E94A2A697E151C8A1592BFA5B2')

    # transaction_result:TransactionResult = delegation_tx.findTransaction()

    # print (f' ✅ Received amount: ')
    # received_coin:Coin
    # for received_coin in transaction_result.result_received:
    #     print ('    * ' + wallet.formatUluna(received_coin.amount, received_coin.denom, True))
    # print (f' ✅ Tx Hash: {transaction_result.broadcast_result.txhash}')

    # # GOVERNANCE VOTE:
    # governance_tx = DelegationTransaction().create(seed = wallet.seed)
    # # Assign the details:
    # governance_tx.proposal_id = 9999
    # governance_tx.user_vote   = 1
    # governance_tx.memo        = 'this is a test'

    
    # height = 16455704
    # governance_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=189914, gas_used=74140 , height = height, txhash='A2A5434EA5C84C2BAA38A2531C246885B3BFC5D7C488A44E4FB5AB72D0664CBA')

    # transaction_result:TransactionResult = governance_tx.findTransaction()

    # if governance_tx.result_received is not None:
    #     print (f' ✅ Tx Hash: {governance_tx.broadcast_result.txhash}')
    
    # LIQUIDITY TRANSACTION

    
    # liquidity_tx = LiquidityTransaction().create(seed = wallet.seed, denom=UOSMO)
    
    # height = 13629178
    # liquidity_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=427453, gas_used=146225, height = height, txhash='AE0471E11C5FA7ABF524215577A816A765D81BAE9AAA22EFC27F0E587F58AE44')
    # transaction_result:TransactionResult = liquidity_tx.findTransaction()
    # transaction_result.wallet_denom = wallet.denom
    # transaction_result.showResults()
    
    # print ('pool id:', swap_tx.pool_id)
    # print ('result sent:', swap_tx.result_sent)
    # print ('denom:', swap_tx.liquidity_denom)

    # print (f' ✅ Withdrawn amount from pool #{swap_tx.pool_id}: {float(swap_tx.amount_out) * 100}%')
    # print (f' ✅ Received coins: ')
    # received_coin:Coin
    # for received_coin in swap_tx.result_received:
    #     print ('    * ' + wallet.formatUluna(received_coin.amount, received_coin.denom, True))
    # print (f' ✅ Tx Hash: {swap_tx.broadcast_result.txhash}')

    # if swap_tx.result_sent is not None:
    #    print (f' ✅ Swapped amount: {wallet.formatUluna(swap_tx.result_sent, swap_tx.swap_denom)} {FULL_COIN_LOOKUP[swap_tx.swap_denom]}')
    #    #print (f' ✅ Sent amount into pool #{swap_tx.pool_id}: {wallet.formatUluna(swap_tx.result_sent.amount, swap_tx.liquidity_denom)} {FULL_COIN_LOOKUP[swap_tx.liquidity_denom]}')
    #    print (f' ✅ Joined amount: {swap_tx.result_received.amount} shares')
    # print (f' ✅ Received amount: {wallet.formatUluna(swap_tx.result_received.amount, swap_tx.swap_request_denom)} {FULL_COIN_LOOKUP[swap_tx.swap_request_denom]}')
    #print (f' ✅ Received amounts: ')
    #received_coin:Coin
    #for received_coin in swap_tx.result_received:
    #   print (wallet.formatUluna(received_coin.amount, received_coin.denom, True))
    #print (f' ✅ Tx Hash: {swap_tx.broadcast_result.txhash}')

    #### CONFIRM TRANSACTION TEST
    #test = UserWallet().create(name = 'test', address = 'osmo19qqt7ndwkpx7dkwcaa0uq6xsf8t4kf64nv3kzp')
    #test.confirmTxReceipt('terra1em3qvwh0y6zd63pjmdppy3ztj0c6vyg6ek2rh9', 'FCF76633FF417CCC5AF6848877A92799B5DFD48E359D5AABE65706CBFC260DFF')
        
    #test = UserWallet().create(name = 'test', address = 'terra18dyxga35fwgnfkf83jgmpylg8j6yceyymlmqxh')
    #test.confirmTxReceipt('terra18dyxga35fwgnfkf83jgmpylg8j6yceyymlmqxh', '378AD2255FCBFC1AAC4C7E1D6B4E8A70E91736A3B3DBB547D991B76C2F38837F')

    #### SEND TEST
    #test = UserWallet().create(name='test', address='osmo19qqt7ndwkpx7dkwcaa0uq6xsf8t4kf64nv3kzp')
    
    # send_tx = SendTransaction().create(seed=wallet.seed, denom=ULUNA)
    # height = 16884910
    # hash='5E8810B77D0C92D363EC61FC3E34A2A88FD61E8AC5B3D62913A422CB33A06361'
    # gas_wanted=1000000
    # gas_used=327666
    # send_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=gas_wanted, gas_used=gas_used, height = height, txhash=hash)
    # transaction_result:TransactionResult = send_tx.findTransaction()
    # transaction_result.wallet_denom = wallet.denom
    # transaction_result.showResults()


    # liquidity_tx = LiquidityTransaction().create(seed = wallet.seed, denom=UOSMO)
    
    # height = 13629178
    # liquidity_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=427453, gas_used=146225, height = height, txhash='AE0471E11C5FA7ABF524215577A816A765D81BAE9AAA22EFC27F0E587F58AE44')
    # transaction_result:TransactionResult = liquidity_tx.findTransaction()
    # transaction_result.wallet_denom = wallet.denom
    # transaction_result.showResults()


    #### SWAP TEST
    swap_tx = SwapTransaction().create(seed = wallet.seed, denom=ULUNA)
    height = 17067740
    hash = '876DFC1EF1DBD869B55ECD9ECE22A1283B10D72335E785086F0D209367BE8CB8'
    gas_wanted = 1000000
    gas_used = 222710

    swap_tx.swap_denom = ULUNA
    swap_tx.swap_amount = 1000 * 1000000
    swap_tx.swap_request_denom = UUSD
    swap_tx.fee = Fee(gas_limit = 1000000, amount = Coins({Coin(ULUNA, 45 * 1000000)}))

    swap_tx.broadcast_result = BlockTxBroadcastResult(logs= '', raw_log = '', gas_wanted=gas_wanted, gas_used=gas_used, height = height, txhash=hash)
    transaction_result:TransactionResult = swap_tx.findTransaction()
    transaction_result.wallet_denom = wallet.denom

    transaction_result.wallet_denom      = wallet.denom

    # If this was successful, then log the trade
    swap_tx.logTrade(wallet, transaction_result)

    transaction_result.showResults()

    


    exit()
    

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()