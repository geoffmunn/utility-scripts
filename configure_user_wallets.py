import cryptocode
from getpass import getpass
from os.path import exists

import utility_constants

# @TODO
#   - confirm password?
#   - check if supplied password is the same as already in use
#   - support currency preferences

def get_user_choice(question:str, yes_choices:list, no_choices:list):

    while True:    
        answer = input(question).lower()
        if answer in yes_choices or answer in no_choices:
            break
    
    if answer in yes_choices:
        answer = True
    elif answer in no_choices:
        answer = False

    return answer

def get_user_number(question:str, is_percentage:bool) -> int|str:

    while True:
        answer = input(question).strip(' ')

        last_char = answer[-1]
        if is_percentage == True:
            answer = answer[0:-1]

        if answer.isdigit():
            if is_percentage:
                if int(answer) > 0 and int(answer) <= 100:
                    break
            else:
                if int(answer) >= 0:
                    break

    if is_percentage == True and last_char == '%':
        answer = answer + '%'
    else:
        answer = int(answer)

    return answer

def main():
    yes_choices:list = ['yes', 'y', 'true']
    no_choices:list  = ['no', 'n', 'false']

    user_password  = getpass('Secret password (do not forget what this is):')
    wallet_name    = input('Wallet name: ')
    wallet_address = input('Lunc address: ')
    wallet_seed    = input('Seed phrase (this will be encrypted with your secret password):\n')
    delegations    = get_user_choice('Do you want to delegate funds? (y/n) ', yes_choices, no_choices)

    redelegate_amount:str = ''
    threshold:int         = 0

    if delegations == True:
        redelegate_amount = get_user_number('Redelegate amount (eg 100%): ', True)
        threshold         = get_user_number('What is the minimum amount before we withdraw rewards? ', False)

    allow_swaps    = get_user_choice('Do you want to allow swaps? (y/n) ', yes_choices, no_choices)

    wallet_seed_encrypted = cryptocode.encrypt(wallet_seed, user_password)

    # Get the user configuration details from the default location
    file_exists = exists(utility_constants.CONFIG_FILE_NAME)
    data:list = {}

    if file_exists:
        with open(utility_constants.CONFIG_FILE_NAME, 'r') as file:
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
                if len(line)>0:
                    if line[0] != '#':
                        if line[0:len('- wallet')] == '- wallet':
                            if len(item)>0:

                                # defaults in case they're not present:
                                if 'allow_swaps' not in item:
                                    item['allow_swaps'] = 'True'

                                data[existing_name] = item

                            item = {}
                            item['name'] = line[len('- wallet')+1:].strip(' ')
                            existing_name = item['name']

                        for token in tokens:
                            if line[0:len(token)] == token:
                                item[token] = line[len(token) + 1:].strip()


        # Add any remaining items into the list        
        if len(item)>0:
            # defaults in case they're not present:
            if 'allow_swaps' not in item:
                item['allow_swaps'] = 'True'
                
            data[existing_name] = item

        if wallet_name in data:
            update_wallet = get_user_choice('This wallet already exists, do you want to update it? (y/n) ', yes_choices, no_choices)

            if update_wallet == False:
                print ('Exiting...')
                exit()
    
    # Now add the new wallet:
    item = {}
    item['name']    = wallet_name
    item['seed']    = wallet_seed_encrypted
    item['address'] = wallet_address

    if delegations == True:
        item['delegations'] = ''
        if threshold > 0:
            item['threshold'] = threshold
        item['redelegate'] = redelegate_amount

    item['allow_swaps'] = allow_swaps

    data[wallet_name] = item
    
    print (data)
    print ('.......')
    # Now generate the string
    output = '---\n\nwallets:'

    for item in data:

        print (data[item])
        output += '\n  - wallet: ' + str(data[item]['name']) + '\n'
        output += '    seed: ' + str(data[item]['seed']) + '\n'
        output += '    address: ' + str(data[item]['address']) + '\n'
        if 'delegations' in data[item]:
            output += '    delegations:\n'
            if 'threshold' in data[item]:
                output += '      threshold: ' + str(data[item]['threshold']) + '\n'
            output += '      redelegate: ' + str(data[item]['redelegate']) + '\n'
        output += '    allow_swaps: ' + str(data[item]['allow_swaps']) + "\n"

    output += '\n...'
    
    # Write the entire contents to a new version of the file
    file = open(utility_constants.CONFIG_FILE_NAME, 'w')
    file.write(output )
    file.close()

    print ('\nDone. The user_config.yml file has been updated.\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()