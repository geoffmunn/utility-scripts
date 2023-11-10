#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_version,
    get_user_choice,
    multiply_raw_balance
)

from constants.constants import (
    TERRASWAP_UUSD_TO_ULUNA_ADDRESS,
    ULUNA,
    USER_ACTION_ALL,
    USER_ACTION_DELEGATE,
    USER_ACTION_QUIT,
    USER_ACTION_SWAP,
    USER_ACTION_SWAP_DELEGATE,
    USER_ACTION_WITHDRAW,
    USER_ACTION_WITHDRAW_DELEGATE,
    UUSD,
    WITHDRAWAL_REMAINDER
)

from classes.delegation_transaction import DelegationTransaction
from classes.swap_transaction import SwapTransaction
from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.withdrawal_transaction import WithdrawalTransaction
    
def main():
    
    # Check if there is a new version we should be using
    check_version()

    # Get the user wallets
    wallets = UserWallets()
    user_wallets = wallets.loadUserWallets()

    # Get the desired actions
    print ('\nWhat action do you want to take?\n')
    print ('  (W)  Withdraw rewards')
    print ('  (S)  Swap coins')
    print ('  (D)  Delegate')
    print ('  (A)  All of the above')
    print ('  (WD) Withdraw & Delegate')
    print ('  (SD) Swap & Delegate')
    print ('  (Q)  Quit\n')

    user_action = get_user_choice('Pick an option: ', [
        USER_ACTION_WITHDRAW,
        USER_ACTION_SWAP,
        USER_ACTION_DELEGATE,
        USER_ACTION_ALL,
        USER_ACTION_WITHDRAW_DELEGATE,
        USER_ACTION_SWAP_DELEGATE,
        USER_ACTION_QUIT
    ])

    if user_action == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getDelegations()
        wallet.getBalances()

    action_string = ''
    if user_action == USER_ACTION_WITHDRAW:
        action_string = 'withdraw rewards'
    if user_action == USER_ACTION_SWAP:
        action_string = 'swap USTC for LUNC'
    if user_action == USER_ACTION_DELEGATE:
        action_string = 'delegate all available funds'
    if user_action == USER_ACTION_WITHDRAW_DELEGATE:
        action_string = 'withdraw rewards and delegate everything'
    if user_action == USER_ACTION_SWAP_DELEGATE:
        action_string = 'swap USTC for LUNC and delegate everything'
    if user_action == USER_ACTION_ALL:
        action_string = 'withdraw rewards, swap USTC for LUNC, and then delegate everything'

    if action_string == '':
        print (' 🛑 No recognised action to complete, exiting...')
        exit()

    if len(user_wallets) > 0:
        print (f'You can {action_string} on the following wallets:')

        user_wallets,answer = wallets.getUserMultiChoice(f"Select a wallet number 1 - {str(len(user_wallets))}, or 'A' to add all of them, 'C' to clear the list, 'X' to continue, or 'Q' to quit: ", {'display': 'balances'})

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    print (f'\nYou are about to {action_string} on the following wallets:\n')
    for wallet_name in user_wallets:
        print (f' * {wallet_name}')

    continue_action = get_user_choice('\nDo you want to continue? (y/n) ', [])
    if continue_action == False:
        print (' 🛑 Exiting...\n')
        exit()

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        
        print ('####################################')
        print (f'Accessing the {wallet.name} wallet...')

        delegations:dict = wallet.delegations
        for validator in delegations:

            if ULUNA in delegations[validator]['rewards']:
                print ('\n------------------------------------')
                print (f"The {delegations[validator]['validator_name']} validator has a {delegations[validator]['commission']}% commission.")

                if user_action in [USER_ACTION_WITHDRAW, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_ALL]:

                    print ('Starting withdrawals...')

                    uluna_reward:int = delegations[validator]['rewards'][ULUNA]

                    # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                    if uluna_reward > multiply_raw_balance(1, ULUNA):
                        print (f'Withdrawing {wallet.formatUluna(uluna_reward, ULUNA, False)} rewards')

                        # Update the balances so we know what we have to pay the fee with
                        wallet.getBalances()
                        
                        # Set up the withdrawal object
                        withdrawal_tx = WithdrawalTransaction().create(seed = wallet.seed, delegator_address = delegations[validator]['delegator'], validator_address = delegations[validator]['validator'])

                        # We need to populate some details
                        withdrawal_tx.balances       = wallet.balances
                        withdrawal_tx.sender_address = wallet.address
                        withdrawal_tx.sender_prefix  = wallet.getPrefix(wallet.address)
                        withdrawal_tx.wallet_denom   = wallet.denom

                        # Simulate it
                        result = withdrawal_tx.simulate()

                        if result == True:

                            print (withdrawal_tx.readableFee())

                            # Now we know what the fee is, we can do it again and finalise it
                            result = withdrawal_tx.withdraw()

                            if result == True:
                                withdrawal_tx.broadcast()
                            
                                if withdrawal_tx.broadcast_result is not None and withdrawal_tx.broadcast_result.code == 32:
                                    while True:
                                        print (' 🛎️  Boosting sequence number and trying again...')

                                        withdrawal_tx.sequence = withdrawal_tx.sequence + 1
                                        
                                        withdrawal_tx.simulate()
                                        withdrawal_tx.withdraw()
                                        withdrawal_tx.broadcast()

                                        if withdrawal_tx is None:
                                            break

                                        # Code 32 = account sequence mismatch
                                        if withdrawal_tx.broadcast_result.code != 32:
                                            break
                                        
                                if withdrawal_tx.broadcast_result is None or withdrawal_tx.broadcast_result.is_tx_error():
                                    if withdrawal_tx.broadcast_result is None:
                                        print (' 🛎️  The withdrawal transaction failed, no broadcast object was returned.')
                                    else:
                                        print (' 🛎️  The withdrawal failed, an error occurred:')
                                        print (f' 🛎️  {withdrawal_tx.broadcast_result.raw_log}')
                            
                                else:
                                    print (f' ✅ Withdrawn amount: {wallet.formatUluna(uluna_reward, ULUNA, True)}')
                                    print (f' ✅ Tx Hash: {withdrawal_tx.broadcast_result.txhash}')
                        else:
                            print (' 🛎️  The withdrawal could not be completed')
                    else:
                        print (' 🛎️  The amount of LUNC in this wallet does not exceed the withdrawal threshold')

            # Swap any uusd coins for uluna
            if user_action in [USER_ACTION_SWAP, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:

                print ('\n------------------------------------')
                print ('Starting swaps...')

                # Update the balances so we know we have the correct amount
                wallet.getBalances(wallet.createCoin(UUSD, wallet.balances[UUSD]))
                
                # We are only supporting swaps with uusd (USTC) at the moment
                if 'uusd' in wallet.balances:
                    swap_amount = wallet.balances['uusd']

                    if swap_amount > 0:
                        print (f'Swapping {wallet.formatUluna(swap_amount, UUSD, False)} USTC for LUNC')

                        # Set up the basic swap object
                        swap_tx = SwapTransaction().create(seed = wallet.seed, denom = ULUNA)

                        # Populate the basic details.
                        swap_tx.balances       = wallet.balances
                        swap_tx.contract       = TERRASWAP_UUSD_TO_ULUNA_ADDRESS
                        swap_tx.sender_address = wallet.address
                        swap_tx.sender_prefix  = wallet.getPrefix(wallet.address)
                        swap_tx.swap_amount    = swap_amount
                        swap_tx.swap_denom     = UUSD
                        #swap_tx.contract      = ASTROPORT_UUSD_TO_ULUNA_ADDRESS
                        swap_tx.wallet_denom   = wallet.denom

                        # Simulate it so we can get the fee
                        result = swap_tx.simulate()

                        if result == True:
                        
                            print (swap_tx.readableFee())
                            
                            result = swap_tx.swap()

                            if result == True:
                                swap_tx.broadcast()

                                if swap_tx.broadcast_result is not None and swap_tx.broadcast_result.code == 32:
                                    while True:
                                        print (' 🛎️  Boosting sequence number and trying again...')

                                        swap_tx.sequence = swap_tx.sequence + 1

                                        swap_tx.simulate()
                                        swap_tx.swap()
                                        swap_tx.broadcast()

                                        if swap_tx is None:
                                            break

                                        # Code 32 = account sequence mismatch
                                        if swap_tx.broadcast_result.code != 32:
                                            break
                                        
                                if swap_tx.broadcast_result is None or swap_tx.broadcast_result.is_tx_error():
                                    if swap_tx.broadcast_result is None:
                                        print (' 🛎️  The swap transaction failed, no broadcast object was returned.')
                                    else:
                                        print (' 🛎️ The swap failed, an error occurred:')
                                        print (f' 🛎️  {swap_tx.broadcast_result.raw_log}')
                            
                                else:
                                    print (f' ✅ Swap successfully completed')
                                    print (f' ✅ Tx Hash: {swap_tx.broadcast_result.txhash}')
                            else:
                                print (' 🛎️  Swap transaction could not be completed')
                    else:
                        print (' 🛎️  Swap amount is not greater than zero')
                else:
                    print (' 🛎️  No UST in the wallet to swap!')

            # Redelegate anything we might have
            if user_action in [USER_ACTION_DELEGATE, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
            
                print ('\n------------------------------------')
                print ('Starting delegations...')

                # Update the balances after having done withdrawals and swaps
                wallet.getBalances(wallet.createCoin(ULUNA, wallet.balances[ULUNA]))
                
                # Only proceed if this is an active validator with a non-zero balance
                if delegations[validator]['balance_amount'] > 0:
                    if ULUNA in wallet.balances:     
                        uluna_balance = int(wallet.balances[ULUNA])
                        
                        # Adjust this so we have the desired amount still remaining
                        delegated_uluna = int(uluna_balance - multiply_raw_balance(WITHDRAWAL_REMAINDER, ULUNA))

                        print (f'About to delegate {delegated_uluna}...')
                        
                        if delegated_uluna > 0 and delegated_uluna <= wallet.balances[ULUNA]:
                            print (f'Delegating {wallet.formatUluna(delegated_uluna, ULUNA, True)}')

                            # Create the delegation object
                            delegation_tx = DelegationTransaction().create(seed = wallet.seed, denom = ULUNA)

                            # Assign the details:
                            delegation_tx.balances = wallet.balances
                            delegation_tx.delegator_address = delegations[validator]['delegator']
                            delegation_tx.validator_address = delegations[validator]['validator']
                            delegation_tx.delegated_uluna   = delegated_uluna
                            delegation_tx.sender_address    = wallet.address
                            delegation_tx.sender_prefix     = wallet.getPrefix(wallet.address)
                            delegation_tx.wallet_denom      = wallet.denom
                            
                            # Simulate it
                            result = delegation_tx.simulate(delegation_tx.delegate)

                            if result == True:
                                    
                                print (delegation_tx.readableFee())
                                
                                # Now we know what the fee is, we can do it again and finalise it
                                result = delegation_tx.delegate()
                                
                                if result == True:
                                    delegation_tx.broadcast()

                                    if delegation_tx.broadcast_result is not None and delegation_tx.broadcast_result.code == 32:
                                        while True:
                                            print (' 🛎️  Boosting sequence number and trying again...')

                                            delegation_tx.sequence = delegation_tx.sequence + 1

                                            delegation_tx.simulate()
                                            delegation_tx.swap()
                                            delegation_tx.broadcast()

                                            if delegation_tx is None:
                                                break

                                            # Code 32 = account sequence mismatch
                                            if delegation_tx.broadcast_result.code != 32:
                                                break
                                        
                                    if delegation_tx.broadcast_result is None or delegation_tx.broadcast_result.is_tx_error():
                                        if delegation_tx.broadcast_result is None:
                                            print (' 🛎️  The delegation transaction failed, no broadcast object was returned.')
                                        else:
                                            print (' 🛎️ The delegation failed, an error occurred:')
                                            print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                                    else:
                                        print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, ULUNA, True)}')
                                        print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
                                else:
                                    print (' 🛎️  The delegation could not be completed')
                            else:
                                print ('🛎️  The delegation could not be completed')
                        else:
                            if delegated_uluna <= 0:
                                print (' 🛎️  Delegation error: the delegated amount is not greater than zero')
                            else:
                                print (f' 🛎️  Delegation error: the delegated amount of {wallet.formatUluna(delegated_uluna, ULUNA, True)} exceeds the available amount of {wallet.formatUluna(uluna_balance, ULUNA, True)}')
                    else:
                        print (' 🛎️  No LUNC to delegate!')
                else:
                    print (f' 🛎️  Skipping, the {validator} validator does not seem to be active!')

            print (' 💯 All actions on this validator are complete.')
            print ('------------------------------------')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()