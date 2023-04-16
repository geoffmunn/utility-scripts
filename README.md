# Luna Classic utility scripts

These are Python scripts for use on the Luna Classic chain. These scripts demonstrate full independance from the TFL infrastructure.

## What are these?

These scripts will help you manage wallets and make transactions on the Luna Classic chain.

They are intended to be useful for anyone making repeated interactions across multiple wallets. These are especially useful for people who are comfortable with the python environment.

Current functionality includes:

 * Viewing the balances across all your wallets
 * Withdrawing rewards from validator delegations
 * Swapping USTC for LUNC
 * Staking LUNC with validators
 * Sending LUNC to other addresses
 * Swapping Terra coins to USTC etc
 * Managing validators
   * Delegating to new validators
   * Switching between validators
   * Undelegating from validators

 ## Why should you use these scripts?

 By running these on your own computer, you get direct access to the Luna Classic chain. You don't need to rely on 3rd party software like the Terra Station, browser extension wallets, or centralised exchanges.


 You can also be sure you're getting the correct prices and fees. You can edit the script to behave differently if you want to.

 ## Requirements
 
  * python 3.10.9+
  * terra.proto 1.0.0
  * terra_classic_skd 2.0.7
  * cryptocode
  * yaml

  These can be installed via pip:
  ```
  python - m pip pip install terra.proto==1.0.0
  python - m pip pip install terra_classic_sdk
  python - m pip install cryptocode
  python - m pip install pyyaml
  ```

 ## Installation guide

### Step 1
 Make sure you have completed the installation steps in the Requirements section.

### Step 2
 Download the utility scripts:
 ```git clone https://github.com/geoffmunn/utility-scripts.git```

## Configuration and usage

### configure_user_wallets.py

Before you can manage your wallets, you need to run the ```configure_user_wallets.py``` script first. This will require you to name the wallets you want to use and provide some basic details as well as the seed phrase. 

Please take a look at the security section below for details on how your seed phrase is kept safe.

You will be prompted for the following details:

 - **Wallet name**: A unique identifier for your reference. If you use the same name as an existing entry, it will overwrite the existing values
 - **Do you want to generate a new wallet address?** Yes or no - if you say 'yes' then a new address and seed phrase will be displayed and used for this wallet.
 - **Terra address**: If you said 'no' to the previous prompt, then you provide the address of the wallet here - it starts with 'terra'.
 - **Wallet seed**: If you said 'no' to creating a new wallet, then you provide the secret seed phrase to generate the wallet here. This is the ONLY time you'll need to provide this - see the security section below.
 - **Do you want to withdraw or delegate anything?**: Optional - if you're staking coins then say 'yes'.
 - **Delegation amount**: You can provide a percentage (usually 100%), or a fixed number (in LUNC). This percentage or number comes from the balance in the wallet at the time, unrelated to the withdrawn amount.
 - **Withdrawal threshold**: The amount of LUNC that must be available as a staking reward before it is withdrawn. If you want to always withdraw everything, enter '0'.
 - **Allow swaps?**: Yes or no - if you say 'no' then the swaps function will not apply to this wallet.

This script will create a file called ```user_config.yml```.
You can edit this file if you need to, but do not modify the encrypted seed string.

If this file is corrupted or you forget the password then you can delete it and start again.

### get_balances.py

This will return the balances for each coin type on all of your wallets. You provide the same password as you used in the configuration step, and say 'yes' or 'no' to just getting the LUNC and USTC summaries.

### manage_wallets.py

To make automatically update your wallets, you need to run ```manage_wallets.py```. Provide the same password you used in the configuration step, and then select the operation you want to do.

 - **Withdrawals**: All the staking rewards are withdrawn. The fee is paid by either a random minor coin (KRT for example), or LUNC, or USDT (in that order).
 - **Swap**: All the available USTC is swapped for LUNC. Currently the fee must be paid in USTC.
 - **Delegate**: LUNC is redelegated back to the same validator. A set amount is always kept in reserve to cover fees for later transactions (250 LUNC). Depending on how the wallet was configured (via ```configure_user_wallets.py```), either a percentage of the available funds is delegated, or a set amount.

 **Special note about delegations**: delegating will also withdraw all existing rewards (which are not part of the delegation), so your balance afterwards might also reflect the withdrawals.

### send_transaction.py

You use ```send_transaction.py``` to send LUNC to another address, from wallets in the ```user_config.yml``` file. Provide the same password you used in the configuration step.

Two points to remember:
 - Memos are optional
 - A minimum amount of LUNC is kept in reserve for payment of fees for future operations

 ### validators.py

You can delegate, undelegate, and switch between validators by running the ```validators.py``` script.
If you undelegate funds, then they will be unavailable for 21 days.

### swaps.py

You can swap the minor Terra coins for any other coin, including USTC and LUNC.

First, provide the same password you used in the configuration step, and then select the coin you want to swap from.

After pressing 'X' to continue, you will can then choose what you want to swap your selection to. You can also see the estimated conversion result.

### Troubleshooting

Examples of errors and what they might mean:

**The script is stuck on 'Starting delegations' and isn't doing anything**

Sometimes it seems to timeout and nothing will happen for many minutes. In these cases you can press 'control+C' (on the Mac) to quit the script. You can run ```python3 get_balances.py``` to check where your coins currently sit, and re-run the ```manage_wallets.py``` script to start again.

**LCD Response Error Status 400 - failed to execute message; message index: 0: Operation exceeds max spread limit: execute wasm contract failed: invalid request**

Seems to be a problem with the LCD - try again later and it should work.

**terra_classic_sdk.exceptions.LCDResponseError: Status 502 - Bad Gateway**

Network connectivity issues with the LCD endpoint. Try again later.

**out of gas in location: ReadFlat; gasWanted: 150762, gasUsed: 151283: out of gas**

The gas adjustment value needs to be increased.

## Gas adjustment

By default, the gas adjustment value starts at 1. This is a very low amount, and will usually fail. When it fails, the script will increase the value by 0.1 and try again. This will keep repeating until the gas adjustment value reaches 4, and then fail if it hasn't successfully finished at this point.

Currently it seems that a successful gas adjustment value is 1.1. If you don't want to try the initial value, then you can change the default to 1.1.

You can change the values in the ```utility_constants.py``` file:

```
GAS_ADJUSTMENT           = 1
GAS_ADJUSTMENT_INCREMENT = 0.1
MAX_GAS_ADJUSTMENT       = 4
```

## Security notes

Your wallet seed phrase is extremely important and must be kept safe at all times. You need to provide the seed phrase so the wallet can be recreated to allow withdrawals and delegations.

Each wallet seed phrase is encrypted with the cryptocode library (https://pypi.org/project/cryptocode/) which uses AES encryption. You provide a password which makes the encrypted string impossible to guess or brute-force as long as it's a sufficiently complex password.

The encrypted string is saved in the ```user_config.yml``` file, and your seed phrase will never be visible in plain text.

When you run any of the other scripts, you provide the same password you used when you ran ```configure_user_wallets.py```. If this password doesn't decrypt any valid wallets then the script will stop.

If you have any questions or concerns about the security aspect of your seed, then please raise an issue on this project.
