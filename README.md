# Luna Classic utility scripts

These are some Python scripts for use on the Luna Classic chain.

## What are these?

These scripts will help you manage wallets and make transactions on the Luna Classic chain.
They are intended to be useful for anyone making repeated interactions across multiple wallets.

Current functionality includes:

 * Withdrawing rewards from validator delegations
 * Swapping USTC for LUNC
 * Staking LUNC with validators

 ## Why should you use these scripts?

 By running these on your own computer, you get direct access to the Luna Classic chain. You don't need to rely on 3rd party software like the Terra Station, browser extension wallets, or centralised exchanges.
 This way you can be sure you're getting the correct prices and fees. You can also edit the script to behave differently if you want to.

 ## Requirements
 
  * python 3.10.9+
  * terra.proto 1.1.0
  * terra_skd 2.0.6
  * cryptocode

  These can be installed via pip:
  ```
  pip install -Iv terra.proto==1.1.0
  pip install -Iv terra_sdk==2.0.6
  pip install cryptocode
  ```

NOTE: terra.proto 1.0.1 will work but you'll need to use the terra.proto_v1.0.1 branch (not recommended)

 ## Installation guide

### Step 1
 Download the modified terra.py library from here:
 https://github.com/geoffmunn/terra.py

 There have been some minor changes from the original library (https://github.com/terra-money/terra.py) to make this Luna Classic compatible.

### Step 2
 Download the utility scripts and put them inside this folder. There won't be any name collisions so a simple copy and paste will be fine.

https://github.com/geoffmunn/utility-scripts

## Configuration and usage

### configure_user_wallets.py

Before you can manage your wallets, you need to run the ```configure_user_wallets.py``` script first. This will require you to name the wallets you want to use and provide some basic details as well as the seed. Please take a look at the security section below for details on how your seed is kept safe.

You will be prompted for the following details:

 - **Wallet name**: A unique identifier for your reference. If you use the same name as an existing entry, it will overwrite the existing values
 - **Terra address**: The address of the wallet - starts with 'terra'
 - **Wallet seed**: Your secret seed to generate the wallet. This is the ONLY time you'll need to provide this - see the security section below.
 - **Do you want to withdraw or delegate anything?**: Optional - if you're staking coins then say 'yes'
 - **Delegation amount**: You can provide a percentage (usually 100%), or a fixed number. This percentage or number comes from the balance in the wallet at the time, unrelated to the withdrawn amount.
 - **Withdrawal threshold**: The amount that must be in the wallet before it is withdrawn.


This script will create a file called ```user_config.yml``` which you can edit if necessary, but do not modify the encrypted seed string.

If this file is corrupted or you forget the password then you can delete it and start again.

Once this is done, you can run the ```manage_wallets.py``` script and select the operation you want from the list.

### manage_wallets.py

To make transactions on your wallets, you need to run ```manage_wallets.py```. Provide the same password you used in the configuration step, and then select the operation you want to do.

 - **Withdrawals**: All the staking rewards are withdrawn. The fee is paid by either a random minor coin (KRT for example), or LUNC, or USDT (in that order).
 - **Swap**: All the available USDT is swapped for LUNC. Currently the fee must be paid in USDT.
 - **Delegate**: LUNC is redelegated back to the same validator. A set amount is always kept in reserve to cover fees for later transactions (100 LUNC). Depending on how the wallet was configured, either a percentage of the available funds is delegated, or a set amount.

### Troubleshooting

**LCD Response Error Status 400 - failed to execute message; message index: 0: Operation exceeds max spread limit: execute wasm contract failed: invalid request**

Seems to be a problem with thbe LCD - try again later and it should work

## Security notes

Your wallet seed is extremely important and must be kept safe at all times. You need to provide the seed so the wallet can be recreated to allow withdrawals and delegations.

Each wallet seed is encrypted with the cryptocode library (https://pypi.org/project/cryptocode/) which uses AES encryption. You provide a password which makes the encrypted string impossible to guess or brute-force as long as it's a sufficiently complex password.

The encrypted string is saved in the user_config.yml file, and your seed will never be visible in plain text.

When you run the ```manage_wallets.py``` script, you provide the same password you used to encrypt the seed. If this password doesn't decrypt any valid wallets then the script will stop.
