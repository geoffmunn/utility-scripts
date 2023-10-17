#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from constants.constants import (
    MAX_VALIDATOR_COUNT,
    ULUNA,
    USER_ACTION_QUIT
)

from classes.wallet import UserWallet
from classes.terra_instance import TerraInstance

from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.core.staking.data.validator import Validator
class Validators():

    def __init__(self):        
        self.validators:dict            = {}
        self.sorted_validators:dict     = {}
        self.validators_by_address:dict = {}

    def __iter_result__(self, validator:Validator) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about validator
        commission       = validator.commission
        details          = validator.description.details
        identity         = validator.description.identity
        is_jailed        = validator.jailed
        moniker          = validator.description.moniker
        operator_address = validator.operator_address
        status           = validator.status
        token_count      = validator.tokens
        unbonding_time   = validator.unbonding_time
        
        commision_rate   = int(commission.commission_rates.rate * 100)

        self.validators[moniker] = {'commission': commision_rate, 'details': details, 'identity': identity, 'is_jailed': is_jailed, 'moniker': moniker, 'operator_address': operator_address, 'status': status, 'token_count': token_count, 'unbonding_time': unbonding_time, 'voting_power': 0}
        
    def create(self) -> dict:
        """
        Create a dictionary of information about the validators that are available.
        """

        # Defaults to uluna/terra
        terra = TerraInstance().create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        result, pagination       = terra.staking.validators(params = pagOpt)

        validator:Validator
        for validator in result:
            self.__iter_result__(validator)

        while pagination['next_key'] is not None:

            pagOpt.key         = pagination['next_key']
            result, pagination = terra.staking.validators(params = pagOpt)
            
            validator:Validator
            for validator in result:
                self.__iter_result__(validator)

        # Go through each validator and create an ordered list
        sorted_validators:dict = {}

        # Calculate the voting power for each validator:
        coin_total = 0
        for validator in self.validators:
            coin_total += int(self.validators[validator]['token_count'])

        for validator in self.validators:

            moniker = self.validators[validator]['moniker']

            self.validators[validator]['voting_power'] = (int(self.validators[validator]['token_count']) / coin_total) * 100

            key = self.validators[validator]['token_count']
            if key not in sorted_validators:
                sorted_validators[moniker] = {}
            
            current:dict               = sorted_validators[moniker]
            current[moniker]           = self.validators[validator]['voting_power']
            sorted_validators[moniker] = key

        sorted_list:list = sorted(sorted_validators.items(), key=lambda x:x[1], reverse=True)[0:len(sorted_validators)]
        sorted_validators = dict(sorted_list)

        # Populate the sorted list with the actual validators
        for validator in sorted_validators:
            sorted_validators[validator] = self.validators[validator]
            self.validators_by_address[self.validators[validator]['operator_address']] = self.validators[validator]

        self.sorted_validators = sorted_validators

        return self.validators

    def getValidatorSingleChoice(self, question:str, validators:dict, filter_list:list, delegations:dict):
        """
        Get a single user selection from a list.
        This is a custom function because the options are specific to this list.
        """

        # We need a wallet object so we can format LUNC values
        wallet = UserWallet()

        # Get the longest validator name:
        label_widths:list = []

        label_widths.append(len('Number'))
        label_widths.append(len('Commission'))
        label_widths.append(len('Voting power'))
        label_widths.append(len('Delegated'))
        label_widths.append(len('Validator name'))

        for delegation in delegations:
            if len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False))) > label_widths[3]:
                label_widths[3] = len(str(wallet.formatUluna(delegations[delegation]['balance_amount'], ULUNA, False)))

        for validator_name in validators:
            if len(validator_name) > label_widths[4]:
                label_widths[4] = len(validator_name)

        padding_str:str   = ' ' * 100
        header_string:str = ' Number |'

        if label_widths[3] > len('Delegated'):
            header_string +=  ' Commission | Voting power | Delegated' + padding_str[0:label_widths[3]-len('Delegated')]
        else:
            header_string +=  ' Commission | Voting power | Delegated'

        if label_widths[4] > len('Validator name'):
            header_string +=  ' | Validator name' + padding_str[0:label_widths[4]-len('Validator name')]
        else:
            header_string +=  ' | Validator name'

        horizontal_spacer:str = '-' * len(header_string)

        validators_to_use:dict = {}
        user_validator:dict    = {}

        while True:

            count:int              = 0
            validator_numbers:dict = {}

            print (horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)
            
            for validator_name in validators:

                if len(filter_list) == 0 or (len(filter_list) > 0 and validator_name in filter_list):
                    count += 1
                    validator_numbers[count] = validators[validator_name]
                        
                    if validator_name in validators_to_use:
                        glyph = '✅'
                    else:
                        glyph = '  '

                    voting_power:str = str(round(validators[validator_name]['voting_power'],2)) + '%'
                    commission:str   = str(validators[validator_name]['commission']) + '%'

                    count_str:str        =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                    commission_str:str   = commission + padding_str[0:label_widths[1] - len(commission)]
                    voting_power_str:str = ' ' + voting_power + padding_str[0:label_widths[2] - len(voting_power)]

                    if validator_name in delegations:
                        delegated_lunc = wallet.formatUluna(delegations[validator_name]['balance_amount'], ULUNA, False)
                        delegated = ' ' + str(delegated_lunc) + padding_str[0:label_widths[3] - len(str(delegated_lunc))]
                    else:
                        delegated = ' ' + padding_str[0:label_widths[3]]

                    validator_name_str = ' ' + validator_name + padding_str[0:label_widths[4] - len(validator_name)]

                    print (f"{count_str}{glyph} | {commission_str} |{voting_power_str} |{delegated} |{validator_name_str}")

                    if count == MAX_VALIDATOR_COUNT:
                        break
                
            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            if answer.isdigit() and int(answer) in validator_numbers:

                validators_to_use:dict = {}

                key = validator_numbers[int(answer)]['moniker']
                if key not in validators_to_use:
                    validators_to_use[key] = validator_numbers[int(answer)]
                else:
                    validators_to_use.pop(key)
                
            if answer == 'x':
                if len(validators_to_use) > 0:
                    break
                else:
                    print ('\nPlease select a validator first.\n')

            if answer == USER_ACTION_QUIT:
                break

        # Get the first (and only) validator from the list
        for item in validators_to_use:
            user_validator = validators_to_use[item]
            break

        return user_validator, answer