#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    check_version,
    get_coin_selection,
    get_user_choice,
    get_user_number,
    UATOM,
    UKAVA,
    UKUJI,
    ULUNA,
    UOSMO,
    UserConfig,
    UUSD,
    Wallets,
    Wallet,
    WETH,
)

from utility_constants import (
    GAS_ADJUSTMENT_INCREMENT,
    GAS_ADJUSTMENT_SWAPS,
    FULL_COIN_LOOKUP,
    MAX_GAS_ADJUSTMENT,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT
)

def get_user_singlechoice(question:str, user_wallets:dict):
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

        if ULUNA in user_wallets[wallet_name].balances:
            uluna_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[ULUNA], ULUNA)
        else:
            uluna_val = ''
            
        if UUSD in user_wallets[wallet_name].balances:
            ustc_val = user_wallets[wallet_name].formatUluna(user_wallets[wallet_name].balances[UUSD], UUSD)
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

            if ULUNA in wallet.balances:
                lunc_str = wallet.formatUluna(wallet.balances[ULUNA], ULUNA, False)
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

#from hashlib import sha256

def main():

    # for i in range(2000):
    #     test = f'transfer/channel-{i}/weth-wei'.encode('utf-8')
    #     hashed =  sha256(test).hexdigest()
    #     if hashed.upper() == 'EA1D43981D5C9A1C4AAEA9C23BB1D4FA126BA9BC7020A25E0AE4AA841EA25DC5':
    #         print ('found on channel', i)
    #         print (hashed)
    #         exit

    # # ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2
    # # ibc/c4cff46fd6de35ca4cf4ce031e643c8fdc9ba4b99ae598e9b0ed98fe3a2319f9
    # exit()
    
    # Check if there is a new version we should be using
    check_version()
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    if decrypt_password == '':
        print (' 🛑 Exiting...\n')
        exit()

    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
        exit()

    print ('Decrypting and validating wallets - please wait...\n')

    # Create the wallet object based on the user config file
    wallet_obj       = Wallets().create(user_config, decrypt_password)
    decrypt_password = None

    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)
    
    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

    if len(user_wallets) > 0:
        print (f'You can make swaps on the following wallets:')

        wallet, answer = get_user_singlechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue, or 'Q' to quit: ", user_wallets)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # List all the coins in this wallet, with the amounts available:
    print ('\nWhat coin do you want to swap FROM?')
    coin_from, answer, null_value = get_coin_selection("Select a coin number 1 - " + str(len(wallet.balances)) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    available_balance:float = wallet.formatUluna(wallet.balances[coin_from], coin_from)
    print (f'This coin has a maximum of {available_balance} {FULL_COIN_LOOKUP[coin_from]} available.')
    swap_uluna = get_user_number("How much do you want to swap? (Or type 'Q' to quit) ", {'max_number': float(available_balance), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': coin_from})

    if swap_uluna == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()


    print ('\nWhat coin do you want to swap TO?')
    coin_to, answer, estimated_amount = get_coin_selection("Select a coin number 1 - " + str(len(wallet.balances)) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances, False, {'denom':coin_from, 'amount':swap_uluna}, wallet)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    estimated_amount = str(("%.6f" % (estimated_amount)).rstrip('0').rstrip('.'))

    print (f'You will be swapping {wallet.formatUluna(swap_uluna, coin_from, False)} {FULL_COIN_LOOKUP[coin_from]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[coin_to]}')
    complete_transaction = get_user_choice('Do you want to continue? (y/n) ', [])

    if complete_transaction == False:
        print (' 🛑 Exiting...\n')
        exit()

    # Create the swap object
    swaps_tx = wallet.swap().create(wallet.getPrefix(wallet.address))

    # Assign the details:
    swaps_tx.swap_amount        = int(swap_uluna)
    swaps_tx.swap_denom         = coin_from
    swaps_tx.swap_request_denom = coin_to
    swaps_tx.sender_address     = wallet.address
    swaps_tx.sender_prefix      = wallet.getPrefix(wallet.address)
    
    # Bump up the gas adjustment - it needs to be higher for swaps it turns out
    swaps_tx.terra.gas_adjustment = float(GAS_ADJUSTMENT_SWAPS)

    # Set the contract based on what we've picked
    # As long as the swap_denom and swap_request_denom values are set, the correct contract should be picked
    use_market_swap = swaps_tx.setContract()
    
    #if swaps_tx.swap_request_denom == UOSMO and swaps_tx.sender_prefix != 'terra':
    if swaps_tx.swap_request_denom in [UOSMO, UATOM, UKAVA, UKUJI, WETH] or swaps_tx.swap_denom in [UOSMO, UATOM, UKAVA, UKUJI, WETH]:
        # This is an off-chain swap. Something like LUNC->OSMO
        result = swaps_tx.offChainSimulate()

        if result == True:
            print (swaps_tx.readableFee())
                
            user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

            if user_choice == False:
                exit()

            result = swaps_tx.offChainSwap()
    else:
        if use_market_swap == True:
            result = swaps_tx.marketSimulate()
            if result == True:
                print (swaps_tx.readableFee())
                
                user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

                if user_choice == False:
                    exit()

                result = swaps_tx.marketSwap()
        else:
            result = swaps_tx.simulate()

            if result == True:
                print (swaps_tx.readableFee())

                user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

                if user_choice == False:
                    exit()

                result = swaps_tx.swap()
    
    #print ('about to broadcast... exiting')
    #exit()
    if result == True:
        swaps_tx.broadcast()
    
        # if swaps_tx.broadcast_result.code == 11:
        #     while True:
        #         print (' 🛎️  Increasing the gas adjustment fee and trying again')
        #         swaps_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
        #         print (f' 🛎️  Gas adjustment value is now {swaps_tx.terra.gas_adjustment}')

        #         if use_market_swap == True:
        #             swaps_tx.marketSimulate()
        #             print (swaps_tx.readableFee())
        #             swaps_tx.marketSwap()
        #         else:
        #             swaps_tx.simulate()
        #             print (swaps_tx.readableFee())
        #             swaps_tx.swap()

        #         swaps_tx.broadcast()

        #         if swaps_tx.broadcast_result.code != 11:
        #             break

        #         if swaps_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
        #             break

        if swaps_tx.broadcast_result is not None and swaps_tx.broadcast_result.code == 32:
            while True:
                print (' 🛎️  Boosting sequence number and trying again...')

                swaps_tx.sequence = swaps_tx.sequence + 1
                swaps_tx.simulate()
                print (swaps_tx.readableFee())
                swaps_tx.swap()
                swaps_tx.broadcast()

                if swaps_tx is None:
                    break

                # Code 32 = account sequence mismatch
                if swaps_tx.broadcast_result.code != 32:
                    break

        if swaps_tx.broadcast_result is None or swaps_tx.broadcast_result.is_tx_error():
            if swaps_tx.broadcast_result is None:
                print (' 🛎️  The swap transaction failed, no broadcast object was returned.')
            else:
                print (' 🛎️  The swap transaction failed, an error occurred:')
                if swaps_tx.broadcast_result.raw_log is not None:
                    print (f' 🛎️  {swaps_tx.broadcast_result.raw_log}')
                else:
                    print ('No broadcast log was available.')
        else:
            print (f' ✅ Swapped amount: {wallet.formatUluna(swaps_tx.swap_amount, swaps_tx.swap_denom)} {FULL_COIN_LOOKUP[swaps_tx.swap_denom]}')
            print (f' ✅ Tx Hash: {swaps_tx.broadcast_result.txhash}')
    else:
        print (' 🛎️  The swap transaction could not be completed')
            
    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()