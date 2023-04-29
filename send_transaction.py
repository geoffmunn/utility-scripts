#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    get_coin_selection,
    get_user_choice,
    get_user_number,
    get_user_text,
    UserConfig,
    Wallets,
    Wallet
)

from utility_constants import (
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT_INCREMENT,
    GAS_ADJUSTMENT_SEND,
    MAX_GAS_ADJUSTMENT,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT
)

def get_user_recipient(question:str, wallet:Wallet):
    """
    Get the recipient address that we are sending to.
    """

    while True:
        recipient_address = input(question)
    
        if recipient_address == USER_ACTION_QUIT:
            break

        is_valid, is_empty = wallet.validateAddress(recipient_address)

        if is_valid == False and is_empty == True:
            continue_action = get_user_choice('This wallet seems to be emptyr - do you want to continue? (y/n) ', [])
            if continue_action == True:
                break

        if is_valid == True:
            break

        print (' 🛎️  This is an invalid address - please check and try again.')

    return recipient_address


def get_user_singlechoice(question:str, user_wallets:dict) -> dict|str:
    """
    Get a single user selection from a list.
    This is a custom function because the options are specific to this list.
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))
    label_widths.append(len('LUNC'))
    label_widths.append(len('USTC'))

    for item in FULL_COIN_LOOKUP:
        if item not in ['uluna', 'uusd']:
            label_widths.append(len(FULL_COIN_LOOKUP[item]))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        if 'uluna' in user_wallets[wallet_name].balances:
            uluna_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances['uluna'])
        else:
            uluna_val = ''
            
        if 'uusd' in user_wallets[wallet_name].balances:
            ustc_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances['uusd'])
        else:
            ustc_val = ''

        if len(str(uluna_val)) > label_widths[2]:
            label_widths[2] = len(str(uluna_val))

        if len(str(ustc_val)) > label_widths[3]:
            label_widths[3] = len(str(ustc_val))

        count = 1
        for item in FULL_COIN_LOOKUP:
            if item not in ['uluna', 'uusd']:
                if item in user_wallets[wallet_name].balances:
                    item_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[item])

                    if len(str(item_val)) > label_widths[3 + count]:
                        label_widths[3 + count] = len(str(item_val))

                    count += 1
                
    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
    else:
        header_string +=  ' Wallet name '

    if label_widths[2] > len('LUNC'):
        header_string += '| LUNC' + padding_str[0:label_widths[2] - len('LUNC')] + ' '
    else:
        header_string += '| LUNC '

    if label_widths[3] > len('USTC'):
        header_string += '| USTC'  + padding_str[0:label_widths[3] - len('USTC')] + ' '
    else:
        header_string += '| USTC '

    horizontal_spacer = '-' * len(header_string)

    wallets_to_use = {}
    user_wallet    = {}
    
    while True:

        count = 0
        wallet_numbers = {}

        print ('\n' + horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:Wallet  = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]

            if 'uluna' in wallet.balances:
                lunc_str =wallet.formatUluna(wallet.balances['uluna'], False)
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if 'uusd' in wallet.balances:
                ustc_str = wallet.formatUluna(wallet.balances['uusd'], False)
            else:
                ustc_str = ' '
            
            print (f"{count_str}{glyph} | {wallet_name_str} | {lunc_str} | {ustc_str}")
            
        print (horizontal_spacer + '\n')

        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use = {}

            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) validator from the list
    for item in wallets_to_use:
        user_wallet = wallets_to_use[item]
        break
    
    return user_wallet, answer

def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
        exit()

    print ('Decrypting and validating wallets - please wait...')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You can send LUNC, USTC, and minor coins on the following wallets:')

        wallet, answer = get_user_singlechoice(f"Select a wallet number 1 - {str(len(user_wallets))}, 'X' to continue, or 'Q' to quit: ", user_wallets)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.")
        exit()

    denom, answer, null_value = get_coin_selection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...')
        exit()

    print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom])} {FULL_COIN_LOOKUP[denom]}")
    print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")
    uluna_amount:int  = get_user_number('How much are you sending? ', {'max_number': float(wallet.formatUluna(wallet.balances[denom], False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False})
    recipient_address = get_user_recipient("What is the address you are sending to? (or type 'Q' to quit) ", wallet)
    
    if recipient_address == USER_ACTION_QUIT:
        print (' 🛑 Exiting...')
        exit()

    # NOTE: I'm pretty sure the memo size is int64, but I've capped it at 255 so python doens't panic
    memo:str = get_user_text('Provide a memo (optional): ', 255, True)

    # Convert the provided value into actual numbers:
    complete_transaction = get_user_choice(f"You are about to send {wallet.formatUluna(uluna_amount)} {FULL_COIN_LOOKUP[denom]} to {recipient_address} - do you want to continue? (y/n) ", [])

    if complete_transaction == False:
        print (" 🛑 Exiting...")
        exit()

    # Now start doing stuff
    print (f'\nAccessing the {wallet.name} wallet...')

    if 'uluna' in wallet.balances:
        print (f'Sending {wallet.formatUluna(uluna_amount)} {FULL_COIN_LOOKUP[denom]}')

        # Create the send tx object
        send_tx = wallet.send().create()

        send_tx.terra.gas_adjustment = GAS_ADJUSTMENT_SEND

        # Assign the details:
        send_tx.recipient_address = recipient_address
        send_tx.memo              = memo
        send_tx.amount            = int(uluna_amount)
        send_tx.denom             = denom
        
        # Simulate it            
        result = send_tx.simulate()

        if result == True:
            
            print (send_tx.readableFee())

            # Now we know what the fee is, we can do it again and finalise it
            result = send_tx.send()
            
            if result == True:
                send_tx.broadcast()
            
                if send_tx.broadcast_result.code == 11:
                    while True:
                        print (' 🛎️  Increasing the gas adjustment fee and trying again')
                        send_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                        print (f' 🛎️  Gas adjustment value is now {send_tx.terra.gas_adjustment}')
                        send_tx.simulate()
                        print (send_tx.readableFee())
                        send_tx.send()
                        send_tx.broadcast()

                        if send_tx.broadcast_result.code != 11:
                            break

                        if send_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                            break

                if send_tx.broadcast_result.is_tx_error():
                    print (' 🛎️  The send transaction failed, an error occurred:')
                    print (f' 🛎️  {send_tx.broadcast_result.raw_log}')
                else:
                    print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount)} {FULL_COIN_LOOKUP[denom]}')
                    print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The send transaction could not be completed')
        else:
            print (' 🛎️  The send transaction could not be completed')
        
    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()