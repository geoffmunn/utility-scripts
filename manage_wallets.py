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
USER_ACTION_WITHDRAW      = 'w'
USER_ACTION_SWAP          = 's'
USER_ACTION_DELEGATE      = 'd'
USER_ACTION_SWAP_DELEGATE = 'sd'
USER_ACTION_ALL           = 'a'

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
UUSD_TO_ULUNA_SWAP_ADDRESS      = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
ASTROPORT_UUSD_TO_MINA_ADDRESS = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'

def strtobool (val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        #raise ValueError("invalid truth value %r" % (val,))
        return -1
    
def get_user_choice(question:str, yes_choices:list, no_choices:list):
    """Get the user selection for a prompt and convert it to a standard value
    """
    while True:    
        answer = input(question).lower()
        if answer in yes_choices or answer in no_choices:
            break
    
    booly = strtobool(answer)
    if  booly== -1:
        result = answer
    else:
        result = booly

    return result

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

class TerraInstance:
    def __init__(self, gas_price_url:str, gas_adjustment:float):
        self.chain_id       = 'columbus-5'
        self.gas_adjustment = gas_adjustment
        self.gas_price_url  = gas_price_url
        self.terra          = None
        #self.url            = 'https://lcd.terrarebels.net'
        self.url            = 'https://lcd.terra.dev'
        
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
        self.delegateTx       = DelegationTransaction()
        self.details:dict     = {}
        self.name:str         = ''
        self.seed:str         = ''
        self.swapTx           = SwapTransaction()
        self.terra:LCDClient  = None
        self.validated: bool  = False
        self.withdrawalTx     = WithdrawalTransaction()
        
    def create(self, name, address, seed, password) -> Wallet:
        self.name    = name
        self.address = address
        self.seed    = cryptocode.decrypt(seed, password)
        self.terra   = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        return self
    
    def updateDelegation(self, amount:str, threshold:int) -> bool:
       self.delegations = {'delegate': amount, 'threshold': threshold}

       return True
    
    def getBalances(self) -> dict:
        
        # Default pagination options
        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)

        # Get the current balance in this wallet
        result:Coins
        result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)

        # Convert the result into a friendly list
        balances:dict = {}
        for coin in result:
            balances[coin.denom] = coin.amount

        # Go through the pagination (if any)
        while pagination['next_key'] is not None:
            pagOpt.key          = pagination["next_key"]
            result, pagination  = self.terra.bank.balance(address = self.address, params = pagOpt)
            for coin in result:
                balances[coin.denom] = coin.amount

        self.balances = balances

        return balances

    def validateAddress(self) -> bool:

        # Check that the password does actually resolve against any wallets
        
        # Go through each wallet and create it based on the password that was provided
        # then check it against the saved address
        # if it's not the same, then the password is wrong or the file has been edited

        try:
            generated_wallet_key     = MnemonicKey(self.seed)
            generated_wallet         = self.terra.wallet(generated_wallet_key)
            generated_wallet_address = generated_wallet.key.acc_address
        
            if generated_wallet_address == self.address:
                return True
            else:
                return False
        except:
            return False

    def getDelegations(self):
        self.details = Delegations().create(self.address)

        return self.details
    
    def formatUluna(self, uluna:float, add_suffix:bool = False) -> float|str:

        lunc:float = uluna / 1000000

        if add_suffix:
            lunc = str(lunc) + 'LUNC'

        return lunc
    
    def withdrawal(self):
        # Update the withdrawal class with the data it needs
        # It will be created via the create() command

        self.withdrawalTx.seed = self.seed
        self.withdrawalTx.balances = self.balances

        return self.withdrawalTx
    
    def swap(self):
        # Update the swap class with the data it needs
        # It will be created via the create() command

        self.swapTx.seed     = self.seed
        self.swapTx.balances = self.balances

        return self.swapTx
    
    def delegate(self):
        # Update the delegate class with the data it needs
        # It will be created via the create() command

        self.delegateTx.seed     = self.seed
        self.delegateTx.balances = self.balances

        return self.delegateTx
    
class Wallets:
    def __init__(self):
        self.file         = None
        self.wallets:dict = {}

    def create(self, yml_file:dict, user_password:str):
        # Create a list of wallets
        for wallet in yml_file['wallets']:

            delegation_amount:str = ''
            threshold:int         = 0

            if 'delegations' in wallet:
                if 'redelegate' in wallet['delegations']:
                    delegation_amount = wallet['delegations']['redelegate']
                    if 'threshold' in wallet['delegations']:
                        threshold = wallet['delegations']['threshold']

            wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'], user_password)
            wallet_item.updateDelegation(delegation_amount, threshold)
            wallet_item.validated = wallet_item.validateAddress()

            self.wallets[wallet['wallet']] = wallet_item

        return self
        
    def getWallets(self, validate):
       
        if validate == True:
            validated_wallets = {}
            for wallet_name in self.wallets:
                wallet:Wallet = self.wallets[wallet_name]
                
                if wallet.validated == True:
                    validated_wallets[wallet_name] = wallet
        else:
            validated_wallets = self.wallets
       
        return validated_wallets
    
class Delegations(Wallet):

    def __init__(self):        
        self.delegations:dict = {}

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
        
        print (f'Withdrawing rewards from {validator_name}')
        print (f'This validator has a {validator_commission}% commission')
        
        self.delegations[validator_name] = {'delegator': delegator_address, 'validator': validator_address, 'rewards': reward_coins}
        
    def create(self, wallet_address:str):
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

        return self.delegations
    
class TransactionCore():

    def __init__(self):
        
        self.balances:dict = {}
        self.broadcast_result:BlockTxBroadcastResult = None
        self.current_wallet:Wallet                   = None
        self.gas_list:json                           = None
        self.tax_rate:json                           = None
        self.terra                                   = None
        
        terra         = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)
        self.terra    = terra.create()
        self.gas_list = terra.gasList()
        self.tax_rate = terra.taxRate()
        
    def calculateFee(self, requested_fee:Fee, fee_coins:Coins) -> Fee:

        other_coin_list:list = []
        has_uluna:int        = 0
        has_uusd:int         = 0
        
        coin:Coin
        for coin in fee_coins:
            if coin.denom in self.balances and self.balances[coin.denom] >= coin.amount:
                
                if coin.denom == 'uluna':
                    has_uluna = coin.amount
                elif coin.denom == 'uusd':
                    has_uusd = coin.amount
                else:
                    other_coin_list.append(coin)

        if has_uluna > 0 or has_uusd > 0 or len(other_coin_list) > 0:
            
            # @TODO: check that this works for random alts
            if len(other_coin_list) > 0:
                requested_fee.amount = Coin(other_coin_list[0].denom, other_coin_list[0].amount)
            elif has_uusd > 0:
                requested_fee.amount = Coin('uusd', has_uusd)
            else:
                requested_fee.amount = Coin('uluna', has_uluna)

        else:
            print ('Not enough funds to pay for delegation!')

        return requested_fee
    
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
    
    def updateBalances(self) -> bool:

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
        
        return True
    
class WithdrawalTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(WithdrawalTransaction, self).__init__(*args, **kwargs)

        self.current_wallet:Wallet                      = None
        self.delegator_address:str                      = ''
        self.fee:Fee                                    = None
        self.gas_list:json                              = None
        self.seed:str                                   = ''
        self.transaction:Tx                             = None
        self.validator_address:str                      = ''

    def create(self, delegator_address:str, validator_address:str):

        self.delegator_address:str = delegator_address
        self.validator_address:str = validator_address
        
        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        return self
    
    def simulate(self) -> bool:
        
        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        self.withdraw()

        tx:Tx = self.transaction

        requested_fee = tx.auth_info.fee
        simulation_result:BlockTxBroadcastResult = self.broadcast()
        
        bits = simulation_result.raw_log.split('required:')
        if len(bits) > 1:
            fee_bit         = bits[1].split('=')
            fee_coins:Coins = Coins.from_str(fee_bit[0].strip(' "'))
            self.fee        = self.calculateFee(requested_fee, fee_coins)

            return True
        else:
            print ('Error parsing logs - no fee suggestions found')
            return False

    def withdraw(self) -> bool:

        try:
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
            return True
        except:
            return False
        

class DelegationTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(DelegationTransaction, self).__init__(*args, **kwargs)

        #self.broadcast_result:BlockTxBroadcastResult    = None
        self.current_wallet:Wallet                      = None
        #self.delegator_address:str                      = delegator_address
        self.fee:Fee                                    = None
        self.gas_list:json                              = None
        self.sequence:int                               = None
        #self.terra:LCDClient                            = None
        self.transaction:Tx                             = None
        #self.validator_address:str                      = validator_address
        #self.wallet_seed:str                            = wallet_seed
        
        # terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)
        # self.terra = terra.create()
        # self.gas_list = terra.gasList()

        # # Create the wallet based on the calculated key
        # current_wallet_key         = MnemonicKey(wallet_seed)
        # self.current_wallet:Wallet = self.terra.wallet(current_wallet_key)

    def create(self, delegator_address:str, validator_address:str):

        self.delegator_address = delegator_address
        self.validator_address = validator_address

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        return self
    
    def simulate(self, redelegated_uluna:int) -> bool:
        
        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        self.delegate(redelegated_uluna)

        tx:Tx = self.transaction

        # Store the fee so we can actually make the transaction via self.delegate()
        requested_fee = tx.auth_info.fee

        simulation_result:BlockTxBroadcastResult = self.broadcast()

        bits = simulation_result.raw_log.split('required:')
        if len(bits) > 1:
            fee_bit         = bits[1].split('=')
            fee_coins:Coins = Coins.from_str(fee_bit[0].strip(' "'))
            self.fee        = self.calculateFee(requested_fee, fee_coins)

            return True
        else:
            print ('Error parsing logs - no fee suggestions found')
            return False

    def delegate(self, redelegated_uluna:int) -> bool:
        
        try:
            msg = MsgDelegate(
                delegator_address   = self.delegator_address,
                validator_address   = self.validator_address,
                amount              = Coin('uluna', redelegated_uluna)
            )

            options = CreateTxOptions(
                fee         = self.fee,
                #fee_denoms  = ['uluna', 'uusd', 'uaud' ,'ukrw'], # Seems to be ignored
                #gas_prices  = {'uluna': self.gas_list['uluna']},
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

            return True
        except:
            return False

class SwapTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(SwapTransaction, self).__init__(*args, **kwargs)

        #self.current_wallet:Wallet = None
        self.belief_price          = None
        self.fee:Fee               = None
        self.fee_deductables:float = None
        #self.gas_list:json         = None
        self.max_spread:float      = 0.01
        self.tax:float             = None
        #self.tax_rate:json         = None
        self.transaction:Tx        = None
        
    def create(self):

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        return self

    def beliefPrice(self):
        result = self.terra.wasm.contract_query(UUSD_TO_ULUNA_SWAP_ADDRESS, {"pool": {}})

        belief_price:float = int(result['assets'][0]['amount']) / int(result['assets'][1]['amount']) 

        return round(belief_price, 18)

    def simulate(self) -> bool:

        self.belief_price    = self.beliefPrice()
        self.fee             = None
        self.tax             = None
        self.fee_deductables = None

        if 'uusd' in self.balances:
            uusd = self.balances['uusd']
            
            # Perform the swap as a simulation, with no fee details
            print ('Simulating a swap!')
            self.swap(uusd)
            
            tx:Tx = self.transaction

            # Get the fee details
            requested_fee:Fee = tx.auth_info.fee
            #print ('requested fee:', requested_fee)

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

            return True
        else:
            print ('No USTC available to swap!')

            return False

    
    def swap(self) -> bool:

        if self.belief_price is not None:

            if 'uusd' in self.balances:
                uusd = self.balances['uusd']

                if self.tax is not None:
                    uusd = uusd - self.fee_deductables

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

                return True
            else:
                return False
        else:
            print ('No belief price calculated - did you run the simulation first?')
            return False
    
def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the desired actions
    print ('What action do you want to take?')
    print ('  (W)  Withdraw rewards')
    print ('  (S)  Swap coins')
    print ('  (D)  Delegate')
    print ('  (SD) Swap & Delegate')
    print ('  (A)  All of the above')

    user_action = get_user_choice('', ['w', 's', 'd', 'sd', 'a'], [])

    try:
        with open(CONFIG_FILE_NAME, 'r') as file:
            user_config = yaml.safe_load(file)
    except :
        print ('The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    # Validate them - this is how we know if the password is correct
    #wallet_obj.validateAddresses(decrypt_password)

    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    if user_action == USER_ACTION_WITHDRAW:
        action_string = 'withdrawing rewards'
    if user_action == USER_ACTION_SWAP:
        action_string = 'swapping USTC etc for LUNC'
    if user_action == USER_ACTION_DELEGATE:
        action_string = 'delegating all available funds'
    if user_action == USER_ACTION_SWAP_DELEGATE:
        action_string = 'swapping USTC etc for LUNC and delegating everything'
    if user_action == USER_ACTION_ALL:
        action_string = 'withdrawing rewards, swapping USTC etc for LUNC, and then delegating everything'

    if len(user_wallets) > 0:
        print (f'You will be {action_string} on the following wallets:')

        for wallet_name in user_wallets:
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
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        print ('####################################')
        print (f'Working on {wallet.name}...')
        delegations = wallet.getDelegations()
 
        for validator in delegations:
            if user_action in [USER_ACTION_WITHDRAW, USER_ACTION_ALL]:
                uluna_reward:int = delegations[validator]['rewards']['uluna']

                # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                if wallet.formatUluna(uluna_reward, False) > wallet.delegations['threshold']:

                    print (f'Withdrawing {wallet.formatUluna(uluna_reward, False)} rewards')

                    # Update the balances so we know what we have to pay the fee with
                    wallet.getBalances()

                    # Set up the withdrawal object
                    withdrawal_tx = wallet.withdrawal().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                    # Simulate it
                    result = withdrawal_tx.simulate()

                    if result == True:
                        fee_coin:Coin = withdrawal_tx.fee.amount
                        
                        if fee_coin.denom == 'uluna':
                            print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                        else:
                            print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                            
                        # Now we know what the fee is, we can do it again and finalise it
                        result = withdrawal_tx.withdraw()

                        if result == True:
                            withdrawal_tx.broadcast()
                        
                            if withdrawal_tx.broadcast_result.is_tx_error():
                                print ('Withdrawal failed, an error occurred')
                                print (withdrawal_tx.broadcast_result.raw_log)
                        
                            else:
                                print (f'Withdrawn amount: {wallet.formatUluna(uluna_reward, True)}')
                                print (f'Tx Hash: {withdrawal_tx.broadcast_result.txhash}')
                    else:
                        print ('The withdrawal could not be completed')

            # Swap any udst coins for uluna
            if user_action in [USER_ACTION_SWAP, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
                # Update the balances so we know we have the correct amount
                wallet.getBalances()
                
                if 'uusd' in wallet.balances:
                    swap_amount = wallet.balances['uusd']

                    if swap_amount > 0:
                        print (f'Swapping {swap_amount} USTC for LUNC')

                        # Set up the basic swap object
                        swaps_tx = wallet.swap().create()

                        # Simulate it so we can get the fee
                        result = swaps_tx.simulate()
                        if result == True:
                            fee_coin:Coin = swaps_tx.fee.amount
                                
                            if fee_coin.denom == 'uluna':
                                print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                            else:
                                print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                            
                            result = swaps_tx.swap()
                            if result == True:
                                swaps_tx.broadcast()
                            
                                if swaps_tx.broadcast_result.is_tx_error():
                                    print ('Withdrawal failed, an error occurred')
                                    print (swaps_tx.broadcast_result.raw_log)
                            
                                else:
                                    print (f'Tx Hash: {swaps_tx.broadcast_result.txhash}')
                            else:
                                print ('Swap transaction could not be completed')
                    else:
                        print ('No USTC in this wallet at the moment')
                else:
                    print ('No USTC in this wallet at the moment')

            # Redelegate anything we might have
            if user_action in [USER_ACTION_DELEGATE, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
                # Update the balances after having done withdrawals and swaps
                wallet.getBalances()
                if 'uluna' in wallet.balances:            
                    uluna_balance = wallet.balances['uluna']
                    delegated_uluna = int(uluna_balance - (WITHDRAWAL_REMAINDER * 1000000))

                    if delegated_uluna > 0:
                        print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}')

                        delegation_tx = wallet.delegate().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                        # Simulate it
                        result = delegation_tx.simulate(delegated_uluna)

                        if result == True:
                            fee_coin:Coin = delegation_tx.fee.amount
                            
                            if fee_coin.denom == 'uluna':
                                print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                            else:
                                print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                                
                            # Now we know what the fee is, we can do it again and finalise it
                            result = delegation_tx.delegate(delegated_uluna)
                            
                            if result == True:
                                delegation_tx.broadcast()
                            
                                if delegation_tx.broadcast_result.is_tx_error():
                                    print ('Delegation failed, an error occurred')
                                    print (delegation_tx.broadcast_result.raw_log)
                            
                                else:
                                    print (f'Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                                    print (f'Tx Hash: {delegation_tx.broadcast_result.txhash}')
                            else:
                                print ('The deleggation could not be completed')

                        else:
                            print ('The delegation could not be completed')

                    else:
                        print ('Delegation error: amount is not greater than zero')
                else:
                    print ('No LUNC to delegate!')
            print ('------------------------------------')
            
    print ('Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()