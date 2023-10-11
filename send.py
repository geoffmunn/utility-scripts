#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.send_transaction import SendTransaction

from classes.common import (
    check_version,
    get_user_choice
)

from constants.constants import (
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    ULUNA,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD,
)

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
        if item not in [ULUNA, UUSD]:
            label_widths.append(len(FULL_COIN_LOOKUP[item]))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        if ULUNA in user_wallets[wallet_name].balances:
            uluna_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[ULUNA], ULUNA)
        else:
            uluna_val = ''
            
        if UUSD in user_wallets[wallet_name].balances:
            ustc_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[UUSD], ULUNA)
        else:
            ustc_val = ''

        if len(str(uluna_val)) > label_widths[2]:
            label_widths[2] = len(str(uluna_val))

        if len(str(ustc_val)) > label_widths[3]:
            label_widths[3] = len(str(ustc_val))

        count = 1
        for item in FULL_COIN_LOOKUP:
            if item not in [ULUNA, UUSD]:
                if item in user_wallets[wallet_name].balances:
                    item_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[item], item)

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
            wallet:UserWallet  = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]

            if ULUNA in wallet.balances:
                lunc_str =wallet.formatUluna(wallet.balances[ULUNA], ULUNA, False)
            else: 
                lunc_str = ''

            lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
            
            if UUSD in wallet.balances:
                ustc_str = wallet.formatUluna(wallet.balances[UUSD], UUSD, False)
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

def get_send_to_address(user_wallets:UserWallet):
    """
    Show a simple list address from what is found in the user_config file
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)
                
    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
    else:
        header_string +=  ' Wallet name '

    horizontal_spacer = '-' * len(header_string)

    # Create default variables and values
    wallets_to_use         = {}
    user_wallet            = {}
    recipient_address: str = ''

    while True:

        count          = 0
        wallet_numbers = {}
        wallets_by_name = {}

        print ('\n' + horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:UserWallet = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
            wallets_by_name[wallet.name.lower()] = count

            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]
            
            print (f"{count_str}{glyph} | {wallet_name_str}")
            
        print (horizontal_spacer + '\n')

        print ('You can send to an address in your config file by typing the wallet name or number.')
        print ('You can also send to a completely new address by entering the wallet address.\n')

        answer = input("What is the address you are sending to? (or type 'X' to continue, or 'Q' to quit) ").lower()
        
        # Check if someone typed the name of a wallet
        if answer in wallets_by_name.keys():
            answer = str(wallets_by_name[answer])
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use = {}

            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
        else:
            # check if this is an address we support:
            prefix = wallet.getPrefix(answer)
            if prefix in ['terra', 'osmo']:
                recipient_address = answer
                break
            
        if answer == USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) wallet from the list
    if len(wallets_to_use) > 0:
        for item in wallets_to_use:
            user_wallet:UserWallet = wallets_to_use[item]
            recipient_address  = user_wallet.address
            break
    
    return recipient_address, answer

def main():
    
    # Check if there is a new version we should be using
    check_version()

    wallet_obj:UserWallets = UserWallets()
    wallet_obj.loadUserWallets()
    user_wallets:dict = wallet_obj.wallets
    user_addresses:dict = wallet_obj.addresses

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You can send LUNC, USTC, and minor coins on the following wallets:')

        wallet, answer = get_user_singlechoice(f"Select a wallet number 1 - {str(len(user_wallets))}, 'X' to continue, or 'Q' to quit: ", user_wallets)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    #denom, answer, null_value = get_coin_selection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)
    denom, answer, null_value = wallet.getCoinSelection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom], denom)} {FULL_COIN_LOOKUP[denom]}")
    print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")
    uluna_amount:int  = wallet.getUserNumber('How much are you sending? ', {'max_number': float(wallet.formatUluna(wallet.balances[denom], denom, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': denom})

    # Print a list of the addresses in the user_config.yml file:
    recipient_address, answer = get_send_to_address(user_addresses)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    if recipient_address == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # NOTE: I'm pretty sure the memo size is int64, but I've capped it at 255 so python doens't panic
    memo:str = wallet.getUserText('Provide a memo (optional): ', 255, True)

    # Convert the provided value into actual numbers:
    complete_transaction = get_user_choice(f"You are about to send {wallet.formatUluna(uluna_amount, denom)} {FULL_COIN_LOOKUP[denom]} to {recipient_address} - do you want to continue? (y/n) ", [])

    if complete_transaction == False:
        print (' 🛑 Exiting...\n')
        exit()

    # Now start doing stuff
    print (f'\nAccessing the {wallet.name} wallet...')

    if ULUNA in wallet.balances:
        print (f'Sending {wallet.formatUluna(uluna_amount, denom)} {FULL_COIN_LOOKUP[denom]}')

        # Create the send tx object
        #send_tx = wallet.send().create(wallet.denom)
        send_tx = SendTransaction().create(wallet.seed, wallet.denom)
        
        # Populate it with required details:
        send_tx.balances          = wallet.balances
        send_tx.recipient_address = recipient_address
        send_tx.recipient_prefix  = wallet.getPrefix(recipient_address)
        send_tx.sender_address    = wallet.address
        send_tx.sender_prefix     = wallet.getPrefix(wallet.address)
        send_tx.wallet_denom      = wallet.denom

        send_tx.receiving_denom = wallet.getDenomByPrefix(send_tx.recipient_prefix)
        
        if wallet.terra.chain_id == 'columbus-5' and send_tx.recipient_prefix == 'terra':
            send_tx.is_on_chain = True
            send_tx.revision_number = 1
        else:
            send_tx.is_on_chain = False
            send_tx.source_channel = CHAIN_DATA[wallet.denom]['ibc_channels'][send_tx.receiving_denom]
            if wallet.terra.chain_id == 'osmosis-1':
                send_tx.revision_number = 6
            else:
                send_tx.revision_number = 1
        
        # Assign the user provided details:
        send_tx.memo              = memo
        send_tx.amount            = int(uluna_amount)
        send_tx.denom             = denom
        send_tx.block_height      = send_tx.terra.tendermint.block_info()['block']['header']['height']
            
        # Simulate it            
        if send_tx.is_on_chain == True:
            result = send_tx.simulate()
        else:
            result = send_tx.simulateOffchain()
        
        # Now complete it
        if result == True:
            print (send_tx.readableFee())

            user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

            if user_choice == False:
                exit()

            # Now we know what the fee is, we can do it again and finalise it
            if send_tx.is_on_chain == True:
                result = send_tx.send()
            else:
                result = send_tx.sendOffchain()
            
            if result == True:
                send_tx.broadcast()

                if send_tx.broadcast_result is not None and send_tx.broadcast_result.code == 32:
                    while True:
                        print (' 🛎️  Boosting sequence number and trying again...')

                        send_tx.sequence = send_tx.sequence + 1
                        if send_tx.is_on_chain == True:
                            send_tx.simulate()
                            send_tx.send()
                        else:
                            send_tx.simulateOffchain()
                            send_tx.sendOffchain()
                            
                        send_tx.broadcast()

                        if send_tx is None:
                            break

                        # Code 32 = account sequence mismatch
                        if send_tx.broadcast_result.code != 32:
                            break

                if send_tx.broadcast_result is None or send_tx.broadcast_result.is_tx_error():
                    if send_tx.broadcast_result is None:
                        print (' 🛎️  The send transaction failed, no broadcast object was returned.')
                    else:
                        print (' 🛎️  The send transaction failed, an error occurred:')
                        if send_tx.broadcast_result.raw_log is not None:
                            print (f' 🛎️  Error code {send_tx.broadcast_result.code}')
                            print (f' 🛎️  {send_tx.broadcast_result.raw_log}')
                        else:
                            print ('No broadcast log was available.')
                else:
                    print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, denom)} {FULL_COIN_LOOKUP[denom]}')
                    print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
            else:
                print (' 🛎️  The send transaction could not be completed')
        else:
            print (' 🛎️  The send transaction could not be completed')
    else:
        print (" 🛑 This wallet has no LUNC - you need a small amount to be present to pay for fees.")

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()