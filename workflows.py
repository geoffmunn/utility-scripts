#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import yaml

from datetime import datetime
from enum import Enum
from os.path import exists

from classes.common import (
    check_database,
    check_version,
    get_precision,
    is_percentage
)

from constants.constants import (
    FULL_COIN_LOOKUP,
    OUTPUT_ERROR,
    OUTPUT_USER,
    ULUNA,
    WITHDRAWAL_REMAINDER,
    WORKFLOWS_FILE_NAME,
)

from classes.delegation_transaction import delegate_to_validator, switch_validator, undelegate_from_validator
from classes.liquidity_transaction import LiquidityTransaction, join_liquidity_pool, exit_liquidity_pool
from classes.send_transaction import send_transaction
from classes.swap_transaction import swap_coins
from classes.transaction_core import TransactionResult
from classes.validators import Validators
from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.withdrawal_transaction import claim_delegation_rewards

from terra_classic_sdk.core.coin import Coin    

def check_amount(amount:str, balances:dict, preserve_minimum:bool = False) -> list[bool, Coin]:
    """
    The amount will be either a percentage or a specific amount.
    If it's a percentage, then ee need to convert this to an actual amount.
    If it's a specific amount, we need to check that we have this amount in the provided balance

    @params:
        - amount: the amount we want to perform an action with. It can be either specific or a percentage, ie: 50% LUNC or 2000 LUNC
        - balances: a dictionary of coins. This can be from the wallet.balances list, or the validator withdrawals
        - preserve_minimum: if True, then deduct the WITHDRAWAL_REMAINDER value off the available amount

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
            available_balance:int = int(int(balances[coin_denom]) - (WITHDRAWAL_REMAINDER * (10 ** get_precision(coin_denom))))
        else:
            available_balance:int = int(balances[coin_denom])

        if available_balance > 0:

            if amount_bits[0].replace('.', '').isnumeric():
                coin_amount:int = int(float(amount_bits[0]) * (10 ** get_precision(coin_denom)))
            
            elif is_percentage(amount_bits[0]):
                amount:float      = float(amount_bits[0][0:-1]) / 100
                coin_amount:int   = int(float(available_balance * amount))

            if coin_amount > available_balance:
                amount_ok = False
            else:
                # Create a coin with the final denom and amount
                amount_ok = True
                coin_result = wallet.createCoin(coin_amount, coin_denom)
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
            # Should be something like LUNC >= 1000 or DAY = SUNDAY or TIME = 13:30
            condition:str      = str(trigger_bits[0])
            comparison:str      = str(trigger_bits[1])
            requirement:str = str(trigger_bits[2])

            # Get this coin's technical name (ie, uluna)
            if condition in FULL_COIN_LOOKUP.values():
                coin_denom:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(condition)]
                if coin_denom.lower() in balances:
                    coin_balance:float = int(balances[coin_denom]) / (10 ** get_precision(coin_denom))
                    eval_string:str    = f'{coin_balance}{comparison}{requirement}'
                    
                    # Evaluate this string and return the value
                    value:bool = eval(eval_string)
                    if value == False:
                        is_triggered = False
            elif condition.lower() == 'day':
                # Check for days
                dt = datetime.now()
                
                current_day:str = dt.strftime('%A')
                if requirement.lower() != current_day.lower():
                    is_triggered = False
            elif condition.lower() == 'time':
                # Check the time requirement
                time_bits:list = requirement.split(':')
                if len(time_bits) == 1:
                    # Hour only
                    hour:str = datetime.today().strftime("%I%p").lower().lstrip('0')
                    if hour != requirement.lower():
                        is_triggered = False
                    
                elif len(time_bits) == 2:
                    hourMinute:str = datetime.today().strftime("%I:%M%p").lower()
                    if hourMinute != requirement.lower():
                        is_triggered = False
                else:
                    # Not a time format we recognise
                    is_triggered = False
            else:
                # denom not in balances
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

    result:str = ''
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

def get_wallet(user_wallets:UserWallets, user_wallet:str) -> UserWallet:
    """
    Basically a clone of find_address_in_wallet
    """

    result:UserWallet = None

    wallet:UserWallet
    for wallet_name in user_wallets:
        wallet = user_wallets[wallet_name]
        
        if wallet.name.lower() == user_wallet.lower():
            result = wallet
            break
        if wallet.address.lower() == user_wallet.lower():
            result = wallet
    
    for wallet_name in user_wallets:
        wallet = user_wallets[wallet_name]
        
        if wallet.name.lower() == user_wallet.lower():
            result = wallet
            break
        if wallet.address.lower() == user_wallet.lower():
            result = wallet

    return result

class MessageType(Enum):
    MESSAGE = 1
    ERROR = 2
class Log():

    def __init__(self, *args, **kwargs):
        self.silentMode:bool = False
        self.items:list = []

    def header(self, title:str, description:str) -> bool:
        """
        A special method to show a multi-line header for the workflow that has just started.

        @params:
           - title: the workflow title
           - description: the longer optional description

        @return: True
        """

        if len(title) > len(description):
            header:str = '#' * (len(title) + 4)
        else:
            header:str = '#' * (len(description) + 4)

        self.items.append(header)
        print ('\n' + header)

        self.items.append(f"# {title}")
        print (f"# {title}")
        
        if description != '':
            self.items.append(f'# {description}')
            print (f'# {description}')

        self.items.append(header)
        print (header)

        return True

    def message(self, msg:str) -> bool:
        """
        Store a simple message - not an error

        @params:
            - msg: the message

        @return: True
        """

        if msg.strip(' ') != '':
            self.items.append({'messsage': msg, 'type': MessageType.MESSAGE})

            if self.silentMode == False:
                print (msg)

        return True
    
    def error(self, msg:str) -> bool:
        """
        Store an error message. Will be displayed in the silent mode summary.

        @params:
            - msg: the error message

        @return: True
        """

        self.items.append({'messsage': msg, 'type': MessageType.ERROR})

        if self.silentMode == False:
            print (msg)

        return True
    
    def print(self) -> bool:
        
        for item in self.items:
            if self.silentMode == True:
                if item.type == MessageType.ERROR:
                    print (item['message'])
            else:
                print (item['message'])

        return True

def output(msg:str, silent:bool, type:int = OUTPUT_USER) -> bool:
    """
    Print a message depending on what type it is and what mode we're in
    """

    if type==OUTPUT_ERROR:
        print (msg)
        return True
    else:
        if type == OUTPUT_USER and silent == False:
            print (msg)
            return True

    return False

def main():
    
    # Check if there is a new version we should be using
    check_version()
    check_database()

    parser = argparse.ArgumentParser()
    #parser.add_argument("workflow", nargs='?',default=WORKFLOWS_FILE_NAME)
    parser.add_argument('--workflow', default=WORKFLOWS_FILE_NAME)
    parser.add_argument('--silent', default=False)

    args = parser.parse_args()

    silent_mode:bool = False
    if args.silent.lower() == 'true':
        print ('These workflows will be run in silent mode - only errors will be shown.')
        silent_mode = True

    file_exists = exists(args.workflow)
    if file_exists:
        # Now open this file and get the contents
        user_workflows:dict = {}
        try:
            with open(args.workflow, 'r') as file:
                user_workflows = yaml.safe_load(file)

        except:
               print (f'\n 🛑 The {args.workflow} file could not be opened - please check the workflow documentation and review it for syntax errors.\n')
               exit()
    else:
        print (f'\n 🛑 The {args.workflow} file does not exist - you can use the default user_workflow.yml file if necessary.\n')
        exit()
    
    # Get the user wallets. We'll be getting the balances futher on down.
    user_wallets = UserWallets().loadUserWallets(get_balances = False)
    
    if len(user_wallets) == 0:
        print ("\n 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # Set up the log object
    logs:Log = Log()
    logs.silentMode = silent_mode
    
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
            wallets:list = workflow['user_wallets']
            steps:list   = workflow['steps']

            name:str = ''
            if 'name' in workflow:
                if workflow['name'] is None:
                    name = ''
                else:
                    name =  workflow['name']

            description:str = ''
            if 'description' in workflow:
                if workflow['description'] is None:
                   description = ''
                else:
                    description = workflow['description']

            logs.header(name, description)

            # Go through each wallet
            wallet:UserWallet
            for wallet in wallets:
                logs.message(f'\n 📓 {wallet.name}')

                validator_withdrawals:dict = {}  # This keeps track of what we've removed from each validator in this wallet
                # Go through each step

                # Each step must complete successfully before the next one starts
                can_continue:bool = True

                step_count:int = 0
                for step in steps:
                    step_count += 1

                    action = step['action'].lower()

                    if can_continue == True:
                        logs.message(f' 🪜 Performing {action} step... {step_count}/{len(steps)}')
                        
                        if 'description' in step:
                            logs.message(f"    {step['description']}")

                        if action == 'withdraw':
                            # Get an updated list of delegations on this wallet
                            wallet.getDelegations()
                            delegations:dict = wallet.delegations

                            # Withdrawals are a bit different - we'll set 'can_continue' to be true if ANY of the validator withdrawals work
                            withdrawal_succeeded:bool = False

                            for validator in delegations:
                                # One last check to make sure LUNC is in the reward list
                                if ULUNA in delegations[validator]['rewards']:
                                    uluna_reward:int = delegations[validator]['rewards'][ULUNA]

                                    # Check that the 'when' clause is triggered
                                    # We will pass a dictionary of the validator LUNC rewards that we are expecting
                                    is_triggered:bool = check_trigger(step['when'], {ULUNA: uluna_reward})

                                    if is_triggered == True:
                                        logs.message(f"  ➜ Withdrawing {wallet.formatUluna(uluna_reward, ULUNA, False)} rewards from {delegations[validator]['validator_name']}.")

                                        transaction_result:TransactionResult = claim_delegation_rewards(wallet, validator_address = delegations[validator]['validator'])
                                        transaction_result.showResults()
                                        
                                        if transaction_result.is_error == True:
                                            can_continue = False

                                        received_coin:Coin
                                        for received_coin in transaction_result.result_received:
                                            if delegations[validator]['validator'] not in validator_withdrawals:
                                                validator_withdrawals[delegations[validator]['validator']] = {}
                                                validator_withdrawals[delegations[validator]['validator']]['balances']       = {}
                                                validator_withdrawals[delegations[validator]['validator']]['validator_name'] = delegations[validator]['validator_name']

                                            validator_withdrawals[delegations[validator]['validator']]['balances'][received_coin.denom] = received_coin.amount

                                        withdrawal_succeeded = True
                                    else:
                                        logs.error(" ❗ 'when' trigger not fired!")
                                        logs.error(f"    - when: {step['when']}")
                                        can_continue = False
                                else:
                                    logs.error(' ❗ No LUNC in the validator to withdraw!')
                                    can_continue = False
                            
                            # If any of the with validator withdrawals worked, then keep going
                            if withdrawal_succeeded == True:
                                can_continue = True

                        if action == 'redelegate':
                            # We don't support specific wallet selection on the 'redelegate' step
                            delegations:dict = wallet.delegations

                            for validator in validator_withdrawals:
                                is_triggered = check_trigger(step['when'], validator_withdrawals[validator]['balances'])
                                    
                                if is_triggered == True:
                                    # We will redelegate an amount based on the 'amount' value, calculated from the returned rewards
                                    amount_ok, delegation_coin = check_amount(step['amount'], validator_withdrawals[validator]['balances'], True)

                                    if amount_ok == True:
                                        
                                        logs.message(f"  ➜ Redelegating {wallet.formatUluna(delegation_coin.amount, delegation_coin.denom, True)} back to {validator_withdrawals[validator]['validator_name']}.")

                                        transaction_result:TransactionResult = delegate_to_validator(wallet, validator, delegation_coin, True)
                                        transaction_result.showResults()
                                        
                                        if transaction_result.is_error == True:
                                            can_continue = False

                                    else:
                                        logs.error(' ❗ Not enough LUNC in the rewards to make this delegation.')
                                else:
                                    logs.error(" ❗ 'when' trigger not fired!")
                                    logs.error(f"    - when: {step['when']}")
                                    can_continue = False
                    
                        if action == 'delegate':
                            # This is going to a specific validator, and is from the wallet balance
                            # Check if there's a specific wallet to use:
                            if 'wallet' in step:
                                step_wallet:UserWallet = get_wallet(user_wallets, step['wallet'])
                            else:
                                step_wallet:UserWallet = wallet

                            if step_wallet is not None:
                                step_wallet.getBalances()

                                is_triggered = check_trigger(step['when'], step_wallet.balances)
                                        
                                if is_triggered == True:
                                    # We will delegate a specific amount of LUNC from the wallet balance
                                    # We only support LUNC for this action                            
                                    amount_ok, delegation_coin = check_amount(step['amount'], step_wallet.balances, True)

                                    if amount_ok == True:
                                        # Find the validator
                                        if 'validator' in step:
                                            # Find the validator details
                                            validators = Validators()
                                            validators.create()
                                            validator_address:str = validators.findValidatorByName(step['validator'])

                                            if validator_address != '':

                                                logs.message(f"  ➜ Delegating {wallet.formatUluna(delegation_coin.amount, delegation_coin.denom, True)} to {step['validator']}.")
                                                
                                                transaction_result:TransactionResult = delegate_to_validator(step_wallet, validator_address, delegation_coin)
                                                transaction_result.wallet_denom      = step_wallet.denom
                                                transaction_result.showResults()

                                                if transaction_result.is_error == True:
                                                    can_continue = False       
                                            else:
                                                logs.error(' ❗ The validator could not be found, please check the name')
                                                can_continue = False
                                        else:
                                            logs.error(' ❗ No validator specified to delegated to!')
                                            can_continue = False
                                    else:
                                        logs.error(' ❗ Not enough LUNC in the rewards to make this delegation.')
                                        can_continue = False
                                else:
                                    logs.error(" ❗ 'when' trigger not fired!")
                                    logs.error(f"    - when: {step['when']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ No valid wallet could be found for this step.')
                                can_continue = False

                        if action == 'send':

                            # We are sending an amount to a specific address (could be terra or osmo)
                            # Check if there's a specific wallet to use:
                            if 'wallet' in step:
                                step_wallet:UserWallet = get_wallet(user_wallets, step['wallet'])
                            else:
                                step_wallet:UserWallet = wallet

                            if step_wallet is not None:
                                step_wallet.getBalances()

                                if 'when' in step:
                                    is_triggered = check_trigger(step['when'], step_wallet.balances)
                                else:
                                    logs.error(" ❗ No when clause included, defaulting to 'always'.")
                                    is_triggered = True
                                        
                                if is_triggered == True:
                                    amount_ok, send_coin = check_amount(step['amount'], step_wallet.balances, True)

                                    if amount_ok == True:
                                        # Get the address based on the recipient value
                                        # We will restrict recipients to just whats in the address book for safety reasons
                                        recipient_address:str = find_address_in_wallet(user_wallets, step['recipient'])

                                        if recipient_address != '':
                                            # We should be ok to send at this point
                                            logs.message(f"  ➜ Sending {wallet.formatUluna(send_coin.amount, send_coin.denom, True)} to {step['recipient']}")

                                            # Memos are optional
                                            memo:str = ''
                                            if 'memo' in step:
                                                memo = step['memo']

                                            transaction_result:TransactionResult = send_transaction(step_wallet, recipient_address, send_coin, memo, False)
                                            transaction_result.wallet_denom      = step_wallet.denom
                                            transaction_result.showResults()

                                            if transaction_result.is_error == True:
                                                can_continue = False
                                        else:
                                            logs.error(' ❗ No valid recipient was included!')
                                            can_continue = False
                                    else:
                                        logs.error(' ❗ No valid amount was available in this wallet!')
                                        can_continue = False
                                else:
                                    logs.error(" ❗ 'when' trigger not fired!")
                                    logs.error(f"    - when: {step['when']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ No valid wallet could be found for this step.')
                                can_continue = False

                        if action == 'swap':
                            # We are sending an amount to a specific address (could be terra or osmo)
                            # Check if there's a specific wallet to use:
                            if 'wallet' in step:
                                step_wallet:UserWallet = get_wallet(user_wallets, step['wallet'])
                            else:
                                step_wallet:UserWallet = wallet

                            if step_wallet is not None:
                                step_wallet.getBalances()

                                is_triggered = check_trigger(step['when'], step_wallet.balances)
                                        
                                if is_triggered == True:
                                    amount_ok, swap_coin = check_amount(step['amount'], step_wallet.balances, True)
                                    
                                    if amount_ok == True:

                                        if 'swap to' in step:
                                            swap_to_denom:str = list(FULL_COIN_LOOKUP.keys())[list(FULL_COIN_LOOKUP.values()).index(step['swap to'])]
                                            logs.message(f'  ➜ You are swapping {wallet.formatUluna(swap_coin.amount, swap_coin.denom, True)} for {FULL_COIN_LOOKUP[swap_to_denom]}.')

                                            transaction_result:TransactionResult = swap_coins(step_wallet, swap_coin, swap_to_denom, '', False, True)
                                            transaction_result.showResults()

                                            if transaction_result.is_error == True:
                                                can_continue = False
                                        else:
                                            logs.error(" ❗ 'swap to' not specified in this workflow.")
                                            can_continue = False
                                    else:
                                        logs.error(' ❗ No valid amount was available in this wallet!')
                                        can_continue = False
                                else:
                                    logs.error(" ❗ 'when' trigger not fired!")
                                    logs.error(f"    - when: {step['when']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ No valid wallet could be found for this step.')
                                can_continue = False

                        if action == 'join pool':
                            # Check if there's a specific wallet to use:
                            if 'wallet' in step:
                                step_wallet:UserWallet = get_wallet(user_wallets, step['wallet'])
                            else:
                                step_wallet:UserWallet = wallet

                            if step_wallet is not None:
                                step_wallet.getBalances()

                                is_triggered = check_trigger(step['when'], step_wallet.balances)

                                if is_triggered == True:
                                    amount_ok, swap_coin = check_amount(step['amount'], step_wallet.balances, True)
                                    
                                    if amount_ok == True:

                                        if 'pool id' in step:
                                            pool_id:int = step['pool id']

                                            logs.message(f'   ➜  You are joining pool {pool_id} by adding {wallet.formatUluna(swap_coin.amount, swap_coin.denom, True)}.')
                                            
                                            transaction_result:TransactionResult = join_liquidity_pool(step_wallet, pool_id, swap_coin.amount, False)
                                            transaction_result.wallet_denom      = step_wallet.denom
                                            transaction_result.showResults()

                                            if transaction_result.is_error == True:
                                                can_continue = False
                                        else:
                                            logs.error(' ❗ No pool ID provided in this step!')
                                    else:
                                        logs.error(' ❗ No valid amount was available in this wallet!')
                                        can_continue = False
                                else:
                                    logs.error(" ❗ 'when' trigger not fired!")
                                    logs.error(f"    - when: {step['when']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ No valid wallet could be found for this step.')
                                can_continue = False

                        if action == 'exit pool':
                            # Check if there's a specific wallet to use:
                            if 'wallet' in step:
                                step_wallet:UserWallet = get_wallet(user_wallets, step['wallet'])
                            else:
                                step_wallet:UserWallet = wallet

                            if step_wallet is not None:
                                step_wallet.getBalances()

                                if 'pool id' in step:
                                    pool_id:int = step['pool id']

                                # Create the send tx object
                                liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)

                                # Update the liquidity object with the details so we can get the pool assets
                                liquidity_tx.pools        = wallet.pools
                                liquidity_tx.wallet       = wallet
                                liquidity_tx.wallet_denom = wallet.denom
                                liquidity_tx.pool_id      = pool_id
                                
                                # Get the assets for the summary list
                                pool_assets:dict = liquidity_tx.getPoolAssets()

                                # This is the amount we want to exit out:
                                amount_out = step['amount']
                                if is_percentage(amount_out):
                                    amount_out:float  = float(amount_out[:-1]) / 100
                                else:
                                    # If this is a precise amount, we need to convert this into a percentage of the total amount of LUNC   
                                    amount_ok, amount_coin = check_amount(amount_out, {ULUNA:(pool_assets[ULUNA] * (10 ** get_precision(ULUNA)))})
                                    if amount_ok == True:
                                        amount_out:float = round(int(amount_coin.amount) / int(pool_assets[ULUNA]), 2)
                                    else:
                                        amount_out:float = 0

                                if amount_out > 0 and amount_out <= 1:

                                    is_triggered = check_trigger(step['when'], pool_assets)

                                    if is_triggered == True:
                                        logs.message(f' ➜  You are exiting pool {pool_id} by withdrawing {amount_out * 100}%.')
                                        
                                        transaction_result:TransactionResult = exit_liquidity_pool(step_wallet, pool_id, amount_out, False)
                                        transaction_result.wallet_denom      = wallet.denom
                                        transaction_result.showResults()

                                        if transaction_result.is_error == True:
                                            can_continue = False
                                    else:
                                        logs.error(" ❗ 'when' trigger not fired!")
                                        logs.error(f"    - when: {step['when']}")
                                        can_continue = False
                                else:
                                    logs.error(' ❗ No valid amount to exit with was specified.')
                                    logs.error(f"    - amount: {step['amount']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ No valid wallet could be found for this step.')
                                can_continue = False

                        if action == 'switch validator':
                            # Move from one validator to another

                            validators = Validators()
                            validators.create()
                            old_validator_address:str = validators.findValidatorByName(step['old validator'])
                            new_validator_address:str = validators.findValidatorByName(step['new validator'])

                            if old_validator_address != '':
                                if new_validator_address != '':

                                    wallet.getBalances()
                                    wallet.getDelegations()
                                    delegations:dict = {ULUNA: wallet.delegations[step['old validator']]['balance_amount']}

                                    amount_ok, amount_coin = check_amount(step['amount'], delegations)

                                    if amount_ok == True:
                                                
                                        is_triggered = check_trigger(step['when'], delegations)

                                        if is_triggered == True:
                                            logs.message(f" ➜  Switching {wallet.formatUluna(amount_coin.amount, amount_coin.denom, True)} from {step['old validator']} to {step['new validator']}")
                                            
                                            transaction_result:TransactionResult = switch_validator(wallet, new_validator_address, old_validator_address, amount_coin)
                                            transaction_result.showResults()

                                            if transaction_result.is_error == True:
                                                can_continue = False
                                        else:
                                            logs.error(" ❗ 'when' trigger not fired!")
                                            logs.error(f"    - when: {step['when']}")
                                            can_continue = False
                                    else:
                                        logs.error(' ❗ No valid amount to exit with was specified.')
                                        logs.error(f"    - amount: {step['amount']}")
                                        can_continue = False
                                else:
                                    logs.error(' ❗ The new validator name is invalid, please check the workflow.')
                                    can_continue = False
                            else:
                                logs.error(' ❗ The old validator name is invalid, please check the workflow.')
                                can_continue = False

                        if action == 'unstake delegation':
                            # Withdraw a delegation entirely

                            validators = Validators()
                            validators.create()
                            validator_address:str = validators.findValidatorByName(step['validator'])
                            
                            if old_validator_address != '':

                                wallet.getBalances()
                                wallet.getDelegations()
                                
                                delegations:dict = {ULUNA: wallet.delegations[step['validator']]['balance_amount']}

                                amount_ok, amount_coin = check_amount(step['amount'], delegations)

                                if amount_ok == True:
                                            
                                    is_triggered = check_trigger(step['when'], delegations)

                                    if is_triggered == True:
                                        logs.message(f" ➜   This validator has a total amount of {wallet.formatUluna(wallet.delegations[step['validator']]['balance_amount'], ULUNA, True)}.")
                                        logs.message(f" ➜   You are unstaking {wallet.formatUluna(amount_coin.amount, amount_coin.denom, True)} from {step['validator']}.")
                                        logs.message(' ➜   IMPORTANT NOTE: this will be unavailable for 21 days. Please check the status by using the validator.py script.')
                                        
                                        transaction_result:TransactionResult = undelegate_from_validator(wallet, validator_address, amount_coin)
                                        transaction_result.showResults()

                                        if transaction_result.is_error == True:
                                            can_continue = False
                                    else:
                                        logs.error(" ❗ 'when' trigger not fired!")
                                        logs.error(f"    - when: {step['when']}")
                                        can_continue = False
                                else:
                                    logs.error(' ❗ No valid amount to exit with was specified.')
                                    logs.error(f"    - amount: {step['amount']}")
                                    can_continue = False
                            else:
                                logs.error(' ❗ The old validator name is invalid, please check the workflow.')
                                can_continue = False

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()