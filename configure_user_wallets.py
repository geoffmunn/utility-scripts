import cryptocode
from getpass import getpass
from os.path import exists

from constants.constants import (
    CHAIN_OSMO,
    CHAIN_TERRA,
    CONFIG_FILE_NAME,
    ULUNA,
    USER_ACTION_QUIT
)

from classes.common import (
    check_version,
    get_user_choice
)

from classes.wallet import UserWallet

# @TODO
#   - confirm password?
#   - check if supplied password is the same as already in use

def main():

    # Check if there is a new version we should be using
    check_version()

    print ('\n*************************************************************************************************************')
    print ('You can add either just an address (for sending funds to), or an entire wallet.')
    print ('Adding an entire wallet will allow you to send, delegate, and swap coins.\n')
    print ('If you send funds to an address on a frequent basis, adding just an address is useful for extra convienience.')
    print ('*************************************************************************************************************\n')

    # Create the basic wallet object
    wallet:UserWallet  = UserWallet().create(denom = ULUNA)

    wallet_name:str    = wallet.getUserText('Wallet name: ', 255, False)
    entire_wallet:bool = get_user_choice('Are you adding an entire wallet? (y/n) ', [])

    if entire_wallet == False:
        wallet_address:str = wallet.getUserRecipient("What is the wallet address address? (or type 'Q' to quit) ", {})

        if wallet_address == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()

        wallet_seed_encrypted:str = ''
    else:
        user_password:str  = getpass('Secret password (do not forget what this is):')
        is_new_wallet:bool = get_user_choice('You want to generate a new wallet address? (y/n) ', [])
        
        chain:str = get_user_choice('Is this a Terra Classic address (T) or an Osmosis address (O)? (T/O) ', [CHAIN_TERRA, CHAIN_OSMO])

        if chain == CHAIN_TERRA:
            prefix:str = 'terra'
        else:
            prefix:str = 'osmo'

        if is_new_wallet == True:
            wallet_seed, wallet_address = wallet.newWallet(prefix)

            print (f'Your seed and address for the new wallet "{wallet_name}" are about to be displayed on the screen')
            wallet_continue:bool = get_user_choice('Do you want to continue? (y/n) ', [])
            
            if wallet_continue == False:
                print (' 🛑 Exiting...\n')
                exit()

            print ('\nYour wallet seed is displayed below. Please write this down and keep it somewhere secure.\n')
            print (wallet_seed)
            print (f'\nYour wallet address is: {wallet_address}\n')
            
        else:
            wallet_address:str = wallet.getUserText('Wallet address: ', 100, False)
            wallet_seed:str    = wallet.getUserText('Seed phrase (this will be encrypted with your secret password):\n', 1024, False)


        # Create an encrypted version of the provided seed, using the provided password
        wallet_seed_encrypted:str = cryptocode.encrypt(wallet_seed, user_password)

    # Get the user configuration details from the default location
    file_exists = exists(CONFIG_FILE_NAME)
    data:list   = {}

    if file_exists:
        with open(CONFIG_FILE_NAME, 'r') as file:
            output = file.read()

        # Turn the existing user file into a list
        lines:list = output.split("\n")

        # Existing items will be put here:
        item:dict = {}

        # Key values we're looking for
        tokens:list = ['seed', 'address']

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
            update_wallet:bool = get_user_choice('\nThis wallet already exists, do you want to update it? (y/n) ', [])

            if update_wallet == False:
                print ('Exiting...')
                exit()
    
    # Now add the new wallet:
    item         = {}
    item['name'] = wallet_name
    if wallet_seed_encrypted != '':
        item['seed'] = wallet_seed_encrypted

    item['address'] = wallet_address

    data[wallet_name] = item
    
    # Now generate the string
    output = '---\n\nwallets:'

    for item in data:
        output += '\n  - wallet: ' + str(data[item]['name']) + '\n'
        if 'seed' in data[item]:
            output += '    seed: ' + str(data[item]['seed']) + '\n'
        output += '    address: ' + str(data[item]['address']) + '\n'

    output += '\n...'
    
    # Write the entire contents to a new version of the file
    file = open(CONFIG_FILE_NAME, 'w')
    file.write(output )
    file.close()

    print ('\nDone. The user_config.yml file has been updated.\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()