#!/usr/bin/env python3

import yaml
import requests
import json
import cryptocode

from getpass import getpass

from terra_sdk.client.lcd import LCDClient
from terra_sdk.client.lcd.api.distribution import Rewards
from terra_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_sdk.client.lcd.params import PaginationOptions
from terra_sdk.client.lcd.wallet import Wallet
from terra_sdk.core.broadcast import BlockTxBroadcastResult
from terra_sdk.core.coin import Coin
from terra_sdk.core.coins import Coins
from terra_sdk.core.distribution.msgs import MsgWithdrawDelegatorReward
from terra_sdk.core.fee import Fee
from terra_sdk.core.staking import MsgDelegate
from terra_sdk.core.staking.data.delegation import Delegation
from terra_sdk.core.staking.data.validator import Validator
from terra_sdk.core.wasm.msgs import MsgExecuteContract
from terra_sdk.exceptions import LCDResponseError
from terra_sdk.key.mnemonic import MnemonicKey

# User settings - can be changed if required
WITHDRAWAL_REMAINDER = 100   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.

# System settings - these can be changed, but shouldn't be necessary
GAS_PRICE_URI       = 'https://fcd.terra.dev/v1/txs/gas_prices'
TAX_RATE_URI        = 'https://lcd.terra.dev/terra/treasury/v1beta1/tax_rate'
CONFIG_FILE_NAME    = 'user_config.yml'
GAS_ADJUSTMENT      = 3

# Do not change these
USER_ACTION_WITHDRAW   = 'w'
USER_ACTION_SWAP       = 's'
USER_ACTION_REDELEGATE = 'r'
USER_ACTION_ALL        = 'a'

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
UUSD_TO_ULUNA_SWAP_ADDRESS      = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'

def get_user_choice(question:str, yes_choices:list, no_choices:list):

    while True:    
        answer = input(question).lower()
        if answer in yes_choices or answer in no_choices:
            break
    
    if answer in yes_choices:
        result = True
    elif answer in no_choices:
        result = False

    return result, answer

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

class TerraInstance:
    def __init__(self, gas_price_url:str, gas_adjustment:float):
        self.chain_id       = 'columbus-5'
        self.gas_adjustment = gas_adjustment
        self.gas_price_url  = gas_price_url
        self.terra          = None
        self.url            = 'https://lcd.terrarebels.net'
        
    def create(self) -> LCDClient:

        terra:LCDClient = LCDClient(
            chain_id        = self.chain_id,
            gas_adjustment  = self.gas_adjustment,
            url             = self.url
        )

        self.terra = terra

        return self.terra

    def gasList(self) -> json:
        if self.gas_price_url is not None:
            gas_list:json = requests.get(self.gas_price_url).json()
        else:
            print ('No gas price URL set at self.gas_price_url')
            exit()

        return gas_list
    
    def taxRate(self) -> json:
        tax_rate:json = requests.get(TAX_RATE_URI).json()
        
        return tax_rate

    def instance(self) -> LCDClient:
        return self.terra

class Wallet:
    def __init__(self):
        self.address:str      = ''
        self.balances:dict    = {}
        self.delegations:dict = {}
        self.name:str         = ''
        self.seed:str         = ''
        self.terra:LCDClient  = None
        self.validated: bool  = False

    def create(self, name, address, seed) -> Wallet:
        self.name    = name
        self.address = address
        self.seed    = seed

        self.terra   = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        return self
    
    def getBalances(self) -> dict:
        
        # Default pagination options
        terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)

        # Get the current balance in this wallet
        result, pagination = terra.bank.balance(address = self.address, params = pagOpt)

        # Convert the result into a friendly list
        balances:dict = coin_list(result, {})

        # Go through the pagination (if any)
        while pagination['next_key'] is not None:
            pagOpt.key          = pagination["next_key"]
            result, pagination  = terra.bank.balance(address = self.address, params = pagOpt)
            balances            = coin_list(result, balances)

        self.balances = balances

        return balances

    def validateAddress(self, user_password) -> bool:

        # Check that the password does actually resolve against any wallets
        
        # Go through each wallet and create it based on the password that was provided
        # then check it against the saved address
        # if it's not the same, then the password is wrong or the file has been edited

        try:
            generated_wallet_seed:str = cryptocode.decrypt(self.seed, user_password)
            generated_wallet_key     = MnemonicKey(generated_wallet_seed)
            generated_wallet         = self.terra.wallet(generated_wallet_key)
            generated_wallet_address = generated_wallet.key.acc_address
        
            if generated_wallet_address == self.address:
                self.validated = True
            else:
                self.validated = False
        except:
            self.validated = False

        return self.validated
    
    def updateDelegation(self, amount:str, threshold:int) -> bool:
        self.delegations = {'delegate': amount, 'threshold': threshold}

        return True
    
    def formatUluna(uluna:float, add_suffix:bool = False) -> float|str:

        lunc:float = uluna / 1000000

        if add_suffix:
            lunc = str(lunc) + 'LUNC'

        return lunc
    
class Wallets:
    def __init__(self, yml_file:dict):
        self.file         = yml_file
        self.wallets:dict = {}
        
        # Create a list of wallets
        for wallet in self.file['wallets']:

            delegation_amount:str = ''
            threshold:int         = 0

            if 'delegations' in wallet:
                if 'redelegate' in wallet['delegations']:
                    delegation_amount = wallet['delegations']['redelegate']
                    if 'threshold' in wallet['delegations']:
                        threshold = wallet['delegations']['threshold']

            wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'])
            wallet_item.updateDelegation(delegation_amount, threshold)
            self.wallets[wallet['wallet']] = wallet_item


    def validateAddresses(self, user_password:str) -> bool:

        for wallet in self.wallets:
            self.wallets[wallet].validateAddress(user_password)

        return True
        
    def getWallets(self):
       return self.wallets

class Delegations:

    def __init__(self, wallet_address:str):
        
        self.details:dict = {}

        terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        result, pagination       = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

        delegator:Delegation 
        for delegator in result:
            self.__iter_result__(terra, delegator)

        while pagination['next_key'] is not None:

            pagOpt.key          = pagination['next_key']
            result, pagination  = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

            delegator:Delegation 
            for delegator in result:
                self.__iter_result__(terra, delegator)

    def __iter_result__(self, terra:LCDClient, delegator):
        
        # Get the basic details about the delegator and validator etc
        delegator_address:str       = delegator.delegation.delegator_address
        validator_address:str       = delegator.delegation.validator_address
        validator_details           = terra.staking.validator(validator_address)
        validator_details:Validator = terra.staking.validator(validator_address)
        validator_name:str          = validator_details.description.moniker
        validator_commission:float  = float(validator_details.commission.commission_rates.rate)

        # Get any rewards
        rewards:Rewards             = terra.distribution.rewards(delegator_address)
        reward_coins:dict           = coin_list(rewards.rewards[validator_address], {})
        
        print ('reward coins:', reward_coins['uluna'])

        print (f'Withdrawing rewards from {validator_name}')
        print (f'This validator has a {validator_commission}% commission')
        print (f"This delegation has {Wallet.formatUluna(reward_coins['uluna'], True)} rewards")

        self.details[validator_name] = {'delegator': delegator_address, 'validator': validator_address, 'rewards': reward_coins}
        

class WithdrawalTransaction():

    def __init__(self, wallet_seed:str, delegator_address:str, validator_address:str):

        self.balances:dict                              = {}
        self.broadcast_result:BlockTxBroadcastResult    = None
        self.current_wallet:Wallet                      = None
        self.delegator_address:str                      = delegator_address
        self.fee:Fee                                    = None
        self.gas_list:json                              = None
        self.terra:LCDClient                            = None
        self.transaction:Tx                             = None
        self.validator_address:str                      = validator_address
        self.wallet_seed:str                            = wallet_seed
        
        terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)

        self.terra    = terra.create()
        self.gas_list = terra.gasList()

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(wallet_seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)
        
    def updateBalances(self):

        # Default pagination options
        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        wallet_address           = self.current_wallet.key.acc_address

        # Get the current balance in this wallet
        result, pagination       = self.terra.bank.balance(address = wallet_address, params = pagOpt)

        # Convert the result into a friendly list
        balances:dict            = coin_list(result, {})

        # Go through the pagination (if any)
        while pagination['next_key'] is not None:
            pagOpt.key          = pagination["next_key"]
            result, pagination  = self.terra.bank.balance(address = wallet_address, params = pagOpt)
            balances            = coin_list(result, balances)

        self.balances = balances
        
        
    def simulate(self) -> Tx:
        
        # Set the fee to be None so it is simulated
        self.fee = None
        # Run the withdrawal transaction as a simulation
        tx:Tx    = self.withdraw()

        # Store the fee so we can actually make the transaction via self.withdraw()
        # We need to go through fee list to find a currency that also exists in the correct amount in this wallet's balances
        # Fee(gas_limit=1471956, amount=Coins('1398359uaud,1398359ucad,1030370uchf,7212585ucny,6623802udkk,919973ueur,809576ugbp,8610943uhkd,16044320400uidr,80074407uinr,120479599ujpy,1251162600ukrw,41693154uluna,3154188275umnt,4415868umyr,9199725unok,55934328uphp,772321usdr,9199725usek,1471956usgd,34002184uthb,29439120utwd,1103967uusd'), payer='', granter='')

        self.updateBalances()

        requested_fees:dict  = coin_list(tx.auth_info.fee.amount, {})
        available_funds:dict = {}
        ratio:float          = 9999999 # Very large number that won't be exceeded

        for currency in requested_fees:
            if currency in self.balances:
                if self.balances[currency] >= requested_fees[currency]:
                    if requested_fees[currency] / self.balances[currency] < ratio:
                        ratio                     = requested_fees[currency] / self.balances[currency]
                        available_funds[currency] = requested_fees[currency]
            
        if len(available_funds) > 0:
            requested_fee:Fee    = tx.auth_info.fee
            # Replace the fee amount with the currency we will pay with
            coins:Coins          = Coins(available_funds)
            requested_fee.amount = coins
            self.fee             = requested_fee

        # TODO: how do we handle unavailable funds?
        return tx

    def withdraw(self) -> Tx:

        msg = MsgWithdrawDelegatorReward(
            delegator_address = self.delegator_address,
            validator_address = self.validator_address
        )
        
        tx:Tx = self.current_wallet.create_and_sign_tx(
            CreateTxOptions(
                fee         = self.fee,
                gas_prices  = self.gas_list,
                msgs        = [msg]
            )
        )

        self.transaction = tx

        return tx

    def broadcast(self) -> BlockTxBroadcastResult:

        result:BlockTxBroadcastResult = self.terra.tx.broadcast(self.transaction)
        self.broadcast_result         = result

        # Wait for this transaction to appear in the blockchain
        if not self.broadcast_result.is_tx_error():
            while True:
                result:dict = self.terra.tx.search([("tx.hash", self.broadcast_result.txhash)])
                
                if len(result['txs']) > 0:
                    print ('Transaction received')
                    break
                    
                else:
                    print ('No such tx yet...')

        return result

class DelegationTransaction():

    def __init__(self, wallet_seed:str, delegator_address:str, validator_address:str):

        self.broadcast_result:BlockTxBroadcastResult    = None
        self.current_wallet:Wallet                      = None
        self.delegator_address:str                      = delegator_address
        self.fee:Fee                                    = None
        self.gas_list:json                              = None
        self.sequence:int                               = None
        self.terra:LCDClient                            = None
        self.transaction:Tx                             = None
        self.validator_address:str                      = validator_address
        self.wallet_seed:str                            = wallet_seed
        
        terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)
        self.terra = terra.create()
        self.gas_list = terra.gasList()

        # Create the wallet based on the calculated key
        current_wallet_key         = MnemonicKey(wallet_seed)
        self.current_wallet:Wallet = self.terra.wallet(current_wallet_key)

    def simulate(self, redelegated_uluna:int) -> Tx:
        
        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        tx:Tx         = self.delegate(redelegated_uluna)

        # Store the fee so we can actually make the transaction via self.withdraw()
        # Always use uluna since there should be heaps after doing the withdrawal
        self.fee = tx.auth_info.fee

        return tx

    def delegate(self, redelegated_uluna:int) -> Tx:
        
        msg = MsgDelegate(
            delegator_address   = self.delegator_address,
            validator_address   = self.validator_address,
            amount              = Coin('uluna', redelegated_uluna)
        )

        options = CreateTxOptions(
            fee         = self.fee,
            fee_denoms  = ['uluna'],
            gas_prices  = {'uluna': self.gas_list['uluna']},
            msgs        = [msg],
            sequence    = self.sequence
        )

        # This process often generates sequence errors. If we get a response error, then
        # bump up the sequence number by one and try again.
        while True:
            try:
                tx:Tx = self.current_wallet.create_and_sign_tx(options)
                break
            except LCDResponseError as err:
                self.sequence    = self.sequence + 1
                options.sequence = self.sequence
            except Exception as err:
                print ('Random error has occurred')
                print (err)
                break

        self.transaction = tx

        return tx

    def broadcast(self, confirm_tx = False) -> BlockTxBroadcastResult:

        result:BlockTxBroadcastResult   = self.terra.tx.broadcast(self.transaction)
        self.broadcast_result           = result

        # Wait for this transaction to appear in the blockchain
        if confirm_tx == True:
            if not self.broadcast_result.is_tx_error():
                while True:
                    result:dict = self.terra.tx.search([("tx.hash", self.broadcast_result.txhash)])
                    
                    if len(result['txs']) > 0:
                        print ('Transaction received')
                        break
                        
                    else:
                        print ('No such tx yet...')

        return result

class SwapTransaction():

    def __init__(self, wallet_seed:str):

        self.belief_price          = None
        self.current_wallet:Wallet = None
        self.exchange_rates:json   = None
        self.fee:Fee               = None
        self.fee_deductables:float = None
        self.gas_list:json         = None
        self.max_spread:float      = 0.01
        self.tax:float             = None
        self.tax_rate:json         = None
        self.terra:LCDClient       = None
        self.transaction:Tx        = None
        self.wallet_seed:str       = wallet_seed
        
        terra         = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)
        self.terra    = terra.create()
        self.gas_list = terra.gasList()
        self.tax_rate = terra.taxRate()

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(wallet_seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)
        
    def beliefPrice(self):
        result = self.terra.wasm.contract_query(UUSD_TO_ULUNA_SWAP_ADDRESS, {"pool": {}})

        belief_price:float = int(result['assets'][0]['amount']) / int(result['assets'][1]['amount']) 

        return round(belief_price, 18)

    def simulate(self, uusd):

        self.belief_price    = None
        self.fee             = None
        self.tax             = None
        self.belief_price    = self.beliefPrice()
        self.fee_deductables = None

        # Perform the swap as a simulation, with no fee details
        print ('Simulating a swap!')
        tx:Tx = self.swap(uusd)

        # Get the fee details
        requested_fee:Fee = tx.auth_info.fee
        print ('requested fee:', requested_fee)

        # Get the fee details:
        fee_coin:Coin = requested_fee.amount.to_list()
        
        # Take the first fee payment option
        self.tax = uusd * float(self.tax_rate['tax_rate'])
        
        # Build a fee object with 
        new_coin:Coin = Coin('uusd', int(fee_coin[0].amount + self.tax))
        requested_fee.amount = new_coin

        # This will be used by the swap function next time we call it
        self.fee = requested_fee
        
        # Store this so we can deduct it off the total amount to swap
        self.fee_deductables = int(fee_coin[0].amount + self.tax)

        return tx
    
    def swap(self, uusd):

        if self.belief_price is not None:

            if self.tax is not None:
                uusd = uusd - self.fee_deductables

            print (f'Requesting to swap {uusd}')

            tx_msg = MsgExecuteContract(
                sender   = self.current_wallet.key.acc_address,
                contract = ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
                execute_msg = {
                    'swap': {
                        'belief_price': str(self.belief_price),
                        'max_spread': str(self.max_spread),
                        'offer_asset': {
                            'amount': str(uusd),
                            'info': {
                                'native_token': {
                                    'denom': 'uusd'
                                }
                            }
                        },
                    }
                },
                coins = Coins(str(uusd) + 'uusd')            
            )

            options = CreateTxOptions(
                fee         = self.fee,
                # fee_denoms  = ['uluna'],
                # gas_prices  = {'uluna': self.gas_list['uluna']},
                fee_denoms  = ['uusd'],
                gas_prices  = {'uusd': self.gas_list['uusd']},
                msgs        = [tx_msg]
            )
            
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    print ('LCD Response Error', err)
                    exit()
                    
                except Exception as err:
                    print ('Random error has occurred')
                    print (err)
                    break

            self.transaction = tx

            return tx
        else:
            print ('No belief price calculated - did you run the simulation first?')
            exit()

    def broadcast(self) -> BlockTxBroadcastResult:

        result:BlockTxBroadcastResult = self.terra.tx.broadcast(self.transaction)
        self.broadcast_result         = result

        # Wait for this transaction to appear in the blockchain
        if not self.broadcast_result.is_tx_error():
            while True:
                result:dict = self.terra.tx.search([("tx.hash", self.broadcast_result.txhash)])
                
                if len(result['txs']) > 0:
                    print ('Transaction received')
                    break
                    
                else:
                    print ('no such tx yet')

        return result
    
def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the desired actions
    print ('What action do you want to take?')
    print ('  (W)ithdraw rewards')
    print ('  (S)wap coins')
    print ('  (R)edelegate')
    print ('  (A)ll of the above')

    void, user_action = get_user_choice('', ['w', 's', 'r', 'a'], [])

    with open(CONFIG_FILE_NAME, 'r') as file:
        user_config = yaml.safe_load(file)

    wallet_obj = Wallets(user_config)
    wallet_obj.validateAddresses(decrypt_password)

    user_wallets = wallet_obj.getWallets()

    # Check that we have some valid wallets to operate against
    validated_wallets = {}
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        
        if wallet.validated == True:
            validated_wallets[wallet_name] = wallet

    if len(validated_wallets) > 0:
        print ('You will be doing withdrawals on the following wallets:')
        for wallet_name in validated_wallets:
            print (f'  * {wallet_name}')
        
        yes_choices:list    = ['yes', 'y', 'true']
        no_choices:list     = ['no', 'n', 'false']
        continue_withdrawal = get_user_choice('Do you want to continue? (y/n) ', yes_choices, no_choices)

        if continue_withdrawal == False:
            print ('Exiting...')
            exit()
    else:
        print ('This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()


    # Now start doing stuff
    for wallet_name in validated_wallets:
        wallet:Wallet = validated_wallets[wallet_name]

        wallet_seed:str = cryptocode.decrypt(wallet.seed, decrypt_password)

        print ('####################################')
        print (f'Working on {wallet.name}...')

        delegations = Delegations(wallet.address)

        for validator in delegations.details:

            if user_action == USER_ACTION_WITHDRAW or user_action == USER_ACTION_ALL:
                uluna_reward:int = delegations.details[validator]['rewards']['uluna']

                # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                if wallet.formatUluna(uluna_reward, False) > wallet.delegations['threshold']:
                    # Set up the withdrawal object
                    withdrawal_tx = WithdrawalTransaction(wallet_seed, delegations.details[validator]['delegator'], delegations.details[validator]['validator'])
                    # Simulate it
                    withdrawal_tx.simulate()
                    
                    if withdrawal_tx.fee.to_data()['amount'][0]['denom'] == 'uluna':
                        print (f"Fee is {wallet.formatUluna(int(withdrawal_tx.fee.to_data()['amount'][0]['amount']), True)}")
                    else:
                        print (f"Fee is {withdrawal_tx.fee.to_data()['amount'][0]['amount']} {withdrawal_tx.fee.to_data()['amount'][0]['denom']}")
                        
                    # Now we know what the fee is, we can do it again and finalise it
                    withdrawal_tx.withdraw()
                    withdrawal_tx.broadcast()
                
                    if withdrawal_tx.broadcast_result.is_tx_error():
                        print ('Withdrawal failed, an error occurred')
                        print (withdrawal_tx.broadcast_result.raw_log)
                
                    else:
                        print (f'Withdrawn amount: {wallet.formatUluna(uluna_reward, True)}')
                        print (f'Tx Hash: {withdrawal_tx.broadcast_result.txhash}')

            # Swap any udst coins for uluna
            if user_action == USER_ACTION_SWAP or user_action == USER_ACTION_ALL:
                print ('Updating balances...')
                balances = wallet.getBalances()
                
                swaps_tx = SwapTransaction(wallet_seed)
                swaps_tx.simulate(balances['uusd'])
                swaps_tx.swap(balances['uusd'])
                swaps_tx.broadcast()

                print (swaps_tx.broadcast_result)
                    
            # Redelegate anything we might have
            if user_action == USER_ACTION_REDELEGATE or user_action == USER_ACTION_ALL:

                if user_action == 'a':
                    # Update the balances after having done withdrawals and swaps
                    print ('Updating balances...')
                    balances = wallet.getBalances()
                    uluna_reward:int = balances['uluna']

                delegated_uluna = int(uluna_reward - (WITHDRAWAL_REMAINDER * 1000000))
                if delegated_uluna > 0:
                    delegation_tx = DelegationTransaction(wallet_seed, delegations.details[validator]['delegator'], delegations.details[validator]['validator'])
                    delegation_tx.simulate(delegated_uluna)
                    print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}')
                    print (f"Delegation fee is {wallet.formatUluna(int(delegation_tx.fee.to_data()['amount'][0]['amount']), True)}")
                    delegation_tx.delegate(delegated_uluna)
                    delegation_tx.broadcast(True)
                    print (f'Tx Hash: {delegation_tx.broadcast_result.txhash}')
                    
                    # Lack of funds:
                    # BlockTxBroadcastResult(height=0, txhash='A25CC552AE2DB8CACDA6F960E141D6A6DBEC78AD5A43B84D3E7DD0942DF1DF4B', raw_log='33254144uluna is smaller than 44985001uluna: insufficient funds: insufficient funds', gas_wanted=1588173, gas_used=18893, logs=None, code=5, codespace='sdk', info=None, data=None, timestamp=None)
                    if delegation_tx.broadcast_result.is_tx_error():
                        print ('Delegation failed, an error occurred')
                        print (delegation_tx.broadcast_result.raw_log)
                    else:
                        print ('Completed!')
                else:
                    print ('Delegation error: amount is not greater than zero')
            
            print ('------------------------------------')
            
    print ('Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()