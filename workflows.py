#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import yaml

from os.path import exists

from classes.common import (
#     check_database,
#     check_version,
#     get_user_choice,
    getPrecision,
    isPercentage
)

from constants.constants import (
    FULL_COIN_LOOKUP,
    ULUNA,
    WITHDRAWAL_REMAINDER,
    WORKFLOWS_FILE_NAME,
)

# from classes.delegation_transaction import DelegationTransaction
# from classes.swap_transaction import SwapTransaction
from classes.delegation_transaction import delegate_to_validator
from classes.send_transaction import send_transaction
from classes.swap_transaction import swap_coins
from classes.transaction_core import TransactionResult
from classes.validators import Validators
from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.withdrawal_transaction import claim_delegation_rewards
# from classes.withdrawal_transaction import WithdrawalTransaction
    
from terra_classic_sdk.core.coin import Coin

def check_amount(amount:str, balances:dict, preserve_minimum:bool = False) -> (bool, Coin):
    """
    The amount will be either a percentage or a specific amount.
    If it's a percentage, then ee need to convert this to an actual amount.
    If it's a specific amount, we need to check that we have this amount in the provided balance

    @params:
        - amount: the amount we want to perform an action with. It can be either specific or a percentage, ie: 50% LUNC or 2000 LUNC
        - balances: a dictionary of coins. This can be from the wallet.balances list, or the validator withdrawals
        - include_minimim: if True, then deduct the WITHDRAWAL_REMAINDER value off the available amount

    @return: can we proceed? and converted uluna amount
    """

    amount_ok:bool   = False
    coin_denom:str   = ''
    coin_amount:int  = 0
    coin_result:Coin = None

    # We need a wallet to create coins with
    wallet:UserWallet = UserWallet()

    # Figure out the coin and denom. If no denom can be found, then assume it's ULUNA
    amount_bits:list = amount.split(' ')

    # Get the denom.
    if len(amount_bits) >= 2:
        # @TODO: conjoine everything after the first list item so we can support token names with spaces
        coin_denom:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(amount_bits[1])]
    else:
        # If it's a single item list, then assume it's something like '100%' and then denom is ULUNA
        coin_denom:str = ULUNA

    if coin_denom in balances:
        # Adjust the available balance depending on requirements
        if preserve_minimum == True and coin_denom == ULUNA:
            available_balance:int = int(int(balances[coin_denom]) - (WITHDRAWAL_REMAINDER * (10 ** getPrecision(coin_denom))))
        else:
            available_balance:int = int(balances[coin_denom])

        if available_balance > 0:

            #if len(amount_bits) >= 2:
            if amount_bits[0].isnumeric():
                coin_amount:float = float(amount_bits[0]) * (10 ** getPrecision(coin_denom))
                
            elif isPercentage(amount_bits[0]):
                amount:float      = float(amount_bits[0][0:-1]) / 100
                coin_amount:float = float(available_balance * amount)

            if coin_amount > available_balance:
                amount_ok = False
            else:
                # Create a coin with the final denom and amount
                amount_ok = True
                coin_result = wallet.createCoin(coin_denom, coin_amount)
        else:
            amount_ok = False

    return amount_ok, coin_result

def check_trigger(triggers:list, balances:dict) -> bool:
    """
    Check the 'when' clause. 
    If it's got a balance check, then compare the requirements against the wallet.
    If this is a validator check, then compare the requirements against the available rewards.

    @params:
      - triggers: a list of triggers, which are simple equations to check with. All of them must be true to proceed
      - balances: a dictionary of coins. This can be from the wallet.balances list, or the validator withdrawals

    @return true/false, this step can proceed
    """

    # Check the trigger
    is_triggered:bool = True

    for trigger in triggers:
        #if trigger == 'always':
        #    is_triggered = True
        #else:
        trigger_bits:list = trigger.split(' ')
        if len(trigger_bits) == 3:
            # Should be something like LUNC >= 1000
            coin_denom:str      = str(trigger_bits[0])
            comparison:str      = str(trigger_bits[1])
            target_amount:float = float(trigger_bits[2])

            # Get this coin's technical name (ie, uluna)
            coin_denom:str     = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(coin_denom)]
            coin_balance:float = balances[coin_denom] / (10 ** getPrecision(coin_denom))
            eval_string:str    = f'{coin_balance}{comparison}{target_amount}'

            # Evaluate this string and return the value
            value:bool = eval(eval_string)

            if value == False:
                 is_triggered = False

    return is_triggered

def find_address_in_wallet(wallet_list:dict, user_address:str) -> str:
    """
    Go through the list of wallets to find a match for the user address.
    This might be either a wallet name or an address.

    @params:
        - user_address: wallet name or actual terra/osmo address

    @return: actual terra/osmo address
    """

    result = ''
    wallet:UserWallet
    for wallet_name in wallet_list:
        wallet = wallet_list[wallet_name]
        
        if wallet.name.lower() == user_address.lower():
            result = wallet.address
            break
        if wallet.address.lower() == user_address.lower():
            result = wallet.address
    
    for wallet_name in wallet_list:
        wallet = wallet_list[wallet_name]
        
        if wallet.name.lower() == user_address.lower():
            result = wallet.address
            break
        if wallet.address.lower() == user_address.lower():
            result = wallet.address

    return result

def main():
    
    file_exists = exists(WORKFLOWS_FILE_NAME)

    if file_exists:
        
        # Now open this file and get the contents
        user_workflows:dict = {}
        try:
            with open(WORKFLOWS_FILE_NAME, 'r') as file:
                user_workflows = yaml.safe_load(file)

        except:
               print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
               exit()
    else:
        print (' 🛑 The user_config.yml does not exist - please run configure_user_wallets.py before running this script.')
        exit()
    
    # Get the wallets
    # Get the user wallets. We'll be getting the balances futher on down.
    user_wallets = UserWallets().loadUserWallets(get_balances = False)
    
    if len(user_wallets) == 0:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # Go through each workflow and attach the wallets that they match
    for workflow in user_workflows['workflows']:
        workflow['user_wallets'] = []   
        # Take each wallet in the user config list... 
        for wallet in user_wallets:
            # If this wallet name or address matches what the workflow has asked for, then add it
            for workflow_wallet in workflow['wallets']:
                if workflow_wallet.lower() == user_wallets[wallet].name.lower() or workflow_wallet.lower() == user_wallets[wallet].address.lower():
                    workflow['user_wallets'].append(user_wallets[wallet])
            
    # Now go through each workflow and run the steps
    for workflow in user_workflows['workflows']:

        # Only proceed if we have a wallet attached to this workflow:
        if 'user_wallets' in workflow:

            # Get the relevant wallets from this workflow
            description:str = ''
            if 'description' in workflow:
                description = workflow['description']
                
            wallets:list = workflow['user_wallets']
            steps:list   = workflow['steps']

            print ('')
            print ('#' * len(workflow['name']))
            print (f"# {workflow['name']}")
            if description != '':
                print (f'# {description}')

            # Go through each wallet
            wallet:UserWallet
            for wallet in wallets:
                print ('#')
                print (f'# {wallet.name}')
                print ('#')

                validator_withdrawals:dict = {}  # This keeps track of what we've removed from each validator in this wallet
                # Go through each step
                for step in steps:
                    action = step['action'].lower()

                    print (f'# Performing {action} step...')

                    if action == 'withdraw':
                        
                        # Get an updated list of delegations on this wallet
                        wallet.getDelegations()
                        delegations:dict = wallet.delegations

                        for validator in delegations:
                            # One last check to make sure LUNC is in the reward list
                            if ULUNA in delegations[validator]['rewards']:
                                uluna_reward:int = delegations[validator]['rewards'][ULUNA]

                                # Check that the 'when' clause is triggered
                                # We will pass a dictionary of the validator LUNC rewards that we are expecting
                                is_triggered:bool = check_trigger(step['when'], {ULUNA: uluna_reward})

                                if is_triggered == True:
                                    print (f"Withdrawing rewards from {delegations[validator]['validator_name']}...")
                                    print (f'Withdrawing {wallet.formatUluna(uluna_reward, ULUNA, False)} rewards.')

                                    # Ideally this should get the uluna rewards from the transaction result
                                    # just in case the numbers are different
                                    #if delegations[validator]['validator'] not in validator_withdrawals:
                                    #    validator_withdrawals[delegations[validator]['validator']] = {}
                                    #validator_withdrawals[delegations[validator]['validator']][ULUNA] = uluna_reward

                                    transaction_result:TransactionResult = claim_delegation_rewards(wallet, validator_address = delegations[validator]['validator'])
                                    transaction_result.showResults()
                                    
                                    received_coin:Coin
                                    for received_coin in transaction_result.result_received:
                                        if delegations[validator]['validator'] not in validator_withdrawals:
                                            validator_withdrawals[delegations[validator]['validator']] = {}
                                        validator_withdrawals[delegations[validator]['validator']][received_coin.denom] = received_coin.amount

                                else:
                                    print ("'when' trigger not fired!")
                                    print (f"- when: {step['when']}")
                            else:
                                print ('No LUNC in the validator to withdraw!')

                    if action == 'redelegate':
                        # Check the trigger
                        #print ('validator withdrawals:', validator_withdrawals)
                        for validator in validator_withdrawals:
                            is_triggered = check_trigger(step['when'], validator_withdrawals[validator])
                                
                            if is_triggered == True:
                                #print ('trigger is ok')
                                # We will redelegate an amount based on the 'amount' value, calculated from the returned rewards
                                amount_ok, delegation_coin = check_amount(step['amount'], validator_withdrawals[validator], False)

                                if amount_ok == True:
                                    
                                    transaction_result:TransactionResult = delegate_to_validator(wallet, validator, delegation_coin)
                                    transaction_result.showResults()
                                    
                                else:
                                    print ('Not enough LUNC in the rewards to make this delegation.')
                            else:
                                print ("'when' trigger not fired!")
                                print (f"- when: {step['when']}")
                 
                    if action == 'delegate':
                        # This is going to a specific validator, and is from the wallet balance

                        wallet.getBalances()

                        is_triggered = check_trigger(step['when'], wallet.balances)
                                
                        if is_triggered == True:
                            # We will delegate a specific amount of LUNC from the wallet balance
                            # We only support LUNC for this action                            
                            amount_ok, delegation_coin = check_amount(step['amount'], wallet.balances, True)

                            if amount_ok == True:
                                # Find the validator
                                if 'validator' in step:
                                    # Find the validator details
                                    validators = Validators()
                                    validators.create()
                                    validator_address:str = validators.findValidatorByName(step['validator'])

                                    if validator_address != '':

                                        transaction_result:TransactionResult = delegate_to_validator(wallet, validator_address, delegation_coin)
                                        transaction_result.showResults()
                                                
                                    else:
                                        print ('The validator could not be found, please check the name')

                                else:
                                    print ('No validator specified to delegated to!')
                            else:
                                print ('Not enough LUNC in the rewards to make this delegation.')
                        else:
                            print ("'when' trigger not fired!")
                            print (f"- when: {step['when']}")
                    
                    if action == 'send':
                        # We are sending an amount to a specific address (could be terra or osmo)
                        wallet.getBalances()

                        is_triggered = check_trigger(step['when'], wallet.balances)
                                
                        if is_triggered == True:
                            amount_ok, send_coin = check_amount(step['amount'], wallet.balances, True)

                            if amount_ok == True:
                                # Get the address based on the recipient value
                                # We will restrict recipients to just whats in the address book for safety reasons
                                recipient_address:str = find_address_in_wallet(user_wallets, step['recipient'])

                                if recipient_address != '':
                                    # We should be ok to send at this point

                                    # Memos are optional
                                    memo:str = ''
                                    if 'memo' in step:
                                        memo = step['memo']

                                    transaction_result:TransactionResult = send_transaction(wallet, recipient_address, send_coin, memo, False)
                                    transaction_result.showResults()

                                else:
                                    print ('No valid recipient was included!')
                            else:
                                print ('No valid amount was available in this wallet!')
                        else:
                            print ("'when' trigger not fired!")
                            print (f"- when: {step['when']}")

                    if action == 'swap':

                        # We are sending an amount to a specific address (could be terra or osmo)
                        wallet.getBalances()

                        is_triggered = check_trigger(step['when'], wallet.balances)
                                
                        if is_triggered == True:
                            amount_ok, swap_coin = check_amount(step['amount'], wallet.balances, True)
                            
                            if amount_ok == True:

                                if 'swap to' in step:
                                    swap_to_denom:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(step['swap to'])]

                                    transaction_result:TransactionResult = swap_coins(wallet, swap_coin, swap_to_denom, '', False)
                                    transaction_result.showResults()
                                else:
                                    print ("'swap to' not specified in this workflow.")
                            else:
                                print ('No valid amount was available in this wallet!')
                        else:
                            print ("'when' trigger not fired!")
                            print (f"- when: {step['when']}")
                        

    # print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()