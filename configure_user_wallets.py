import cryptocode
from getpass import getpass
from os.path import exists

from utility_classes import (
    get_user_choice,
    get_user_number,
    get_user_recipient,
    get_user_text,
    isPercentage,
    USER_ACTION_QUIT,
    Wallet
)

from utility_constants import (
    COIN_DIVISOR,
    CONFIG_FILE_NAME
)

# @TODO
#   - confirm password?
#   - check if supplied password is the same as already in use

def main():

    print ('\n*********************************************************************************************************')
    print ('You can add either just an address (for sending funds to), or an entire wallet.')
    print ('Adding an entire wallet will allow you to send, delegate, and swap coins.')
    print ('If you send funds to an address on a frequent basis, you can add just the address for extra convienience.')
    print ('*********************************************************************************************************\n')

    entire_wallet = get_user_choice('Are you just adding an entire wallet? (y/n) ', [])

    if entire_wallet == False:
        wallet:Wallet   = Wallet().create()
        wallet_name:str = get_user_text('Wallet name: ', 255, False)
        wallet_address  = get_user_recipient("What is the wallet address address? (or type 'Q' to quit) ", wallet, {})

        if wallet_address == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        wallet_seed_encrypted:str = None
        delegations               = False
        allow_swaps               = None
    else:
        user_password = getpass('Secret password (do not forget what this is):')
        wallet_name   = get_user_text('Wallet name: ', 255, False)
        is_new_wallet = get_user_choice('You want to generate a new wallet address? (y/n) ', [])
        
        if is_new_wallet == True:
            new_wallet:Wallet = Wallet().create(wallet_name, '', '', '')
            wallet_seed, wallet_address = new_wallet.newWallet()

            print (f'Your seed and address for the new wallet "{wallet_name}" are about to be displayed on the screen')
            wallet_continue = get_user_choice('Do you want to continue? (y/n) ', [])
            
            if wallet_continue == False:
                print (' 🛑 Exiting...\n')
                exit()

            print ('\nYour wallet seed is displayed below. Please write this down and keep it somewhere secure.\n')
            print (wallet_seed)
            print (f'\nYour wallet address is: {wallet_address}\n')
            
        else:
            wallet_address = get_user_text('Lunc address: ', 44, False)
            wallet_seed    = get_user_text('Seed phrase (this will be encrypted with your secret password):\n', 1024, False)

        delegations = get_user_choice('Do you want to delegate funds to validators? (y/n) ', [])

        redelegate_amount:str = ''
        threshold:int         = 0

        if delegations == True:
            redelegate_amount = get_user_number('From the available amount in the wallet, how much do you want to redelegate (eg 100%, 5000 LUNC): ', {'percentages_allowed': True, 'min_number': 0})
            threshold         = get_user_number('What is the minimum amount in LUNC before we withdraw rewards? ', {'min_number': 0, 'min_equal_to': True})

            # Convert the amount and threshold into uluna:
            threshold         = threshold * COIN_DIVISOR
            if isPercentage(redelegate_amount) == False:
                redelegate_amount = redelegate_amount * COIN_DIVISOR

        allow_swaps = get_user_choice('Do you want to allow swaps? (y/n) ', [])

        # Create an encrypted version of the provided seed, using the provided password
        wallet_seed_encrypted:str = cryptocode.encrypt(wallet_seed, user_password)

    # Get the user configuration details from the default location
    file_exists = exists(CONFIG_FILE_NAME)
    data:list = {}

    if file_exists:
        with open(CONFIG_FILE_NAME, 'r') as file:
            output = file.read()

        # Turn the existing user file into a list
        lines:list = output.split("\n")

        # Existing items will be put here:
        item:dict = {}

        # Key values we're looking for
        tokens = ['seed', 'address', 'delegations', 'threshold', 'redelegate', 'allow_swaps']

        for line in lines:
            if line != '---' and line != '...':
                line = line.strip(' ')
                if len(line) > 0:
                    if line[0] != '#':
                        if line[0:len('- wallet')] == '- wallet':
                            if len(item) > 0:
                                data[existing_name] = item

                            item          = {}
                            item['name']  = line[len('- wallet')+1:].strip(' ')
                            existing_name = item['name']

                        for token in tokens:
                            if line[0:len(token)] == token:
                                item[token] = line[len(token) + 1:].strip()


        # Add any remaining items into the list        
        if len(item) > 0:
            data[existing_name] = item

        if wallet_name in data:
            update_wallet = get_user_choice('\nThis wallet already exists, do you want to update it? (y/n) ', [])

            if update_wallet == False:
                print ('Exiting...')
                exit()
    
    # Now add the new wallet:
    item         = {}
    item['name'] = wallet_name
    if wallet_seed_encrypted is not None:
        item['seed'] = wallet_seed_encrypted

    item['address'] = wallet_address

    if delegations == True:
        item['delegations'] = ''
        if threshold > 0:
            if isPercentage(threshold):
                item['threshold'] = threshold
            else:
                item['threshold'] = int(threshold)

        if isPercentage(redelegate_amount):
            item['redelegate'] = redelegate_amount
        else:
            item['redelegate'] = int(redelegate_amount)

    if allow_swaps is not None:
        item['allow_swaps'] = allow_swaps

    data[wallet_name] = item
    
    # Now generate the string
    output = '---\n\nwallets:'

    for item in data:
        output += '\n  - wallet: ' + str(data[item]['name']) + '\n'
        if 'seed' in data[item]:
            output += '    seed: ' + str(data[item]['seed']) + '\n'
        output += '    address: ' + str(data[item]['address']) + '\n'
        if 'delegations' in data[item]:
            output += '    delegations:\n'
            if 'threshold' in data[item]:
                output += '      threshold: ' + str(data[item]['threshold']) + '\n'
            output += '      redelegate: ' + str(data[item]['redelegate']) + '\n'

        if 'allow_swaps' in data[item]:
            output += '    allow_swaps: ' + str(data[item]['allow_swaps']) + "\n"

    output += '\n...'
    
    # Write the entire contents to a new version of the file
    file = open(CONFIG_FILE_NAME, 'w')
    file.write(output )
    file.close()

    print ('\nDone. The user_config.yml file has been updated.\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()