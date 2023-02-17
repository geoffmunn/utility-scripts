import cryptocode
from getpass import getpass

CONFIG_FILE_NAME    = 'user_config.yml'

# @TODO
#   - check if the wallet name already exists
#       - update existing record
#   - confirm password?
#   - check if supplied password is the same as already in use

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
        answer = input(question)

        if is_percentage == True:
            last_char = answer[-1]
            if last_char == '%':
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
    yes_choices:list    = ['yes', 'y', 'true']
    no_choices:list     = ['no', 'n', 'false']

    user_password   = getpass('Secret password (do not forget what this is):')
    wallet_name     = input('Wallet name: ')
    wallet_address  = input('Lunc address: ')
    wallet_seed     = input('Seed phrase (this will be encrypted with your secret password):\n')
    delegations     = get_user_choice('Do you want to delegate funds? (y/n) ', yes_choices, no_choices)

    redelegate_amount:str   = ''
    threshold:int           = 0

    if delegations == True:
        redelegate_amount   = get_user_number('Redelegate amount (eg 100%): ', True)
        threshold           = get_user_number('What is the minimum amount before we withdraw rewards? ', False)

    wallet_seed_encrypted = cryptocode.encrypt(wallet_seed, user_password)

    # Get the user configuration details from the default location
    with open(CONFIG_FILE_NAME, 'r') as file:
        output      = file.read()
        new_output  = ''

    if output is None or output == '':
        output      = ''
        new_output  = '---\n\nwallets:\n'

    # Construct the string we need to write to the file.
    # For some reason, yaml.safe_dump doesn't preserve the correct structure

    new_output += '  - wallet: ' + str(wallet_name) + '\n'
    new_output += '    seed: ' + str(wallet_seed_encrypted) + '\n'
    new_output += '    address: ' + str(wallet_address) + '\n'

    if delegations == True:
        new_output += '    delegations:\n'
        if threshold > 0:
            new_output += '      threshold: ' + str(threshold) + '\n'
        new_output += '      redelegate: ' + str(redelegate_amount) + '\n'
        
    new_output += '\n'

    file = open(CONFIG_FILE_NAME, 'w')
    file.write(output + new_output)
    file.close()

    print ('Done. The user_config.yml file has been updated with this entry:\n')
    print (new_output)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()