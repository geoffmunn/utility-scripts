#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    get_user_choice,
    get_user_number,
    get_user_text,
    UserConfig,
    Wallets,
    Wallet
)

import utility_constants

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

        print (horizontal_spacer)
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
                lunc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uluna'], False))).rstrip('0').rstrip('.')
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if 'uusd' in wallet.balances:
                ustc_str = ("%.6f" % (wallet.formatUluna(wallet.balances['uusd'], False))).rstrip('0').rstrip('.')
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
            
        if answer == utility_constants.USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == utility_constants.USER_ACTION_QUIT:
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
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
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
        print (f'You can send LUNC on the following wallets:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue', or 'Q' to quit: ", user_wallets)

        if answer == utility_constants.USER_ACTION_QUIT:
            print (' 🛑 Exiting...')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.")
        exit()

    if 'uluna' not in wallet.balances:
        print (" 🛑 This wallet doesn't have any LUNC available to transfer.")
        exit()
                       
    # If we're sending LUNC then we need a few more details:
    recipient_address:str = input('What is the address you are sending to? ')

    print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances['uluna'], True)}")
    print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")
    user_number:str = get_user_number('How much are you sending? ', {'max_number': float(wallet.formatUluna(wallet.balances['uluna'], False)), 'min_number': 0, 'percentages_allowed': True})
    memo:str        = get_user_text('Provide a memo (optional): ', 255, True)

    # Convert the provided value into actual numbers:
    lunc_amount, uluna_amount = wallet.convertPercentage(user_number, False, wallet.balances['uluna'])

    complete_transaction = get_user_choice(f"You are about to send {wallet.formatUluna(uluna_amount, True)} to {recipient_address} - do you want to continue? (y/n) ", [])

    if complete_transaction == False:
        print (" 🛑 Exiting...")
        exit()

    # NOTE: I'm pretty sure the memo size is int64, but I've capped it at 255 so python doens't panic

    # Now start doing stuff
    print (f'\nAccessing the {wallet.name} wallet...')
    
    if 'uluna' in wallet.balances:
        # Adjust this so we have the desired amount still remaining

        if uluna_amount > 0 and uluna_amount <= (wallet.balances['uluna'] - (utility_constants.WITHDRAWAL_REMAINDER * utility_constants.COIN_DIVISOR)):
            print (f'Sending {wallet.formatUluna(uluna_amount, True)}')

            # Create the send tx object
            send_tx = wallet.send().create()

            # Assign the details:
            send_tx.recipient_address = recipient_address
            send_tx.memo              = memo
            send_tx.uluna_amount      = uluna_amount
            
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
                            send_tx.terra.gas_adjustment += utility_constants.GAS_ADJUSTMENT_INCREMENT
                            print (f' 🛎️  Gas adjustment value is now {send_tx.terra.gas_adjustment}')
                            send_tx.simulate()
                            print (send_tx.readableFee())
                            send_tx.send()
                            send_tx.broadcast()

                            if send_tx.broadcast_result.code != 11:
                                break

                            if send_tx.terra.gas_adjustment >= utility_constants.MAX_GAS_ADJUSTMENT:
                                break

                    if send_tx.broadcast_result.is_tx_error():
                        print (' 🛎️  The send transaction failed, an error occurred:')
                        print (f' 🛎️  {send_tx.broadcast_result.raw_log}')
                    else:
                        print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, True)}')
                        print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
                else:
                    print (' 🛎️  The send transaction could not be completed')
            else:
                print (' 🛎️  The send transaction could not be completed')
                
        else:
            print (' 🛎️  Sending error: Not enough LUNC will be left in the account to cover fees')
            
    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()