# LUNC-Utility-Scripts

Python scripts to use on the LUNC chain.

## What are these?

These scripts will help you manage wallets and make transactions on the Luna Classic chain.

Currently, functionality includes:

 * Withdrawing rewards from validator delegations
 * Swapping USTC for LUNC
 * Staking LUNC with validators

 ## Requirements

  * terra.proto 1.0.1 or terra.proto 1.1.0
  * terra_skd 2.0.6
  * cryptocode

  These can be installed via pip:
  ```
  pip install -Iv terra.proto==1.1.0
  pip install -Iv terra_sdk==2.0.6
  pip install cryptocode
  ```

 ## Installation guide

### Step 1
 Download the modified terra.py library from here:
 https://github.com/geoffmunn/terra.py

 There have been some minor changes to make this Luna Classic compatible.

### Step 2
 Download the utility scripts and put them inside this folder. There won't be any name collisions so a simple copy and paste will be fine.

https://github.com/geoffmunn/utility-scripts

## Configuration and usage

To run operations on any wallet, you need to run the ```configure_user_wallets.py``` script first. This will require you to name the wallets you want to use and provide some basic details plus the seed. Please take a look at the security section below for details on how your seed is kept safe.

This script will create a file called ```user_config.yml``` which you can edit if required, but do not modify the encrypted seed string.

If this file is corrupted or you forget the password then you can delete it and start again.

One this is done, you can run the ```manage_wallets.py``` script and select the operation you want from the list.

## Security notes

Your wallet seed is extremely important and must be kept safe at all times. You need to provide the seed so the wallet can be recreated to allow withdrawals and delegations.

Each wallet seed is encrypted with the cryptocode library (https://pypi.org/project/cryptocode/) which uses AES encryption. You provide a password which makes this impossible to guess or brute-force as long as it's a sufficiently complex password.

The encrypted string is saved in the user_config.yml file, and your seed will never be visible in plain text.

When you run the ```manage_wallets.py``` script, you provide the same password you used to encrypt the seed. If this password doesn't decrypt any valid wallets then the script will stop.
