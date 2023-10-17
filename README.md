# Luna Classic utility scripts

These are Python scripts for use on the Luna Classic chain. These scripts demonstrate full independance from the TFL infrastructure.

## What are these?

These scripts will help you manage wallets and make transactions on the Luna Classic chain.

They are intended to be useful for anyone making repeated interactions across multiple wallets. These are especially useful for people who are comfortable with the python environment.

Current functionality includes:

 * Address book functionality for commonly used addresses
   * Includes LUNC and any supported IBC address
 * Viewing the balances across all your wallets
 * Withdrawing rewards from validator delegations
 * Managing validators
   * Delegating to new validators
   * Switching between validators
   * Undelegating from validators
   * Viewing undelegations in progress
 * Swapping USTC for LUNC
 * Staking LUNC with validators
 * Sending LUNC to other addresses
 * Swapping Terra coins (KRT, MNT, IDT etc) to USTC or LUNC where possible
 * IBC integration
   * Send LUNC to Osmosis addresses
 * Support for LUNC chain projects
   * BASE token swapping and sending
 * Support for swapping of non-Terra coins via Osmosis
   * Atom
   * Kava
   * Kujira
   * Osmosis
   * Secret
   * USTC
   * Whale
   * Wrapped Bitcoin
   * Wrapped Ethereum

 ## Why should you use these scripts?

 By running these on your own computer, you get direct access to the Luna Classic chain. You don't need to rely on 3rd party software like the Terra Station app, browser extension wallets, or centralised exchanges.


 You can also be sure you're getting the correct prices and fees. You can edit the script to behave differently if you want to.

 ## Requirements
 
  * python 3.10.9+
  * terra_classic_sdk
  * terra_proto (Terra Classic version)
  * cryptocode
  * yaml

  These can be installed via pip:

  ```
  python - m pip pip install terra-classic-sdk
  python - m pip pip install terra-classic-proto
  python - m pip install cryptocode
  python - m pip install pyyaml
  ```

NOTE: installing terra-classic-sdk first should automatically install the terra-classic-proto dependency.

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

 - **Are you adding an entire wallet?** If you are just adding an address that you want to send funds to, then say 'No'.
 
 - **If you said no - just add an address:**
   - **What is the wallet address address?** Provide the address of the wallet here - it starts with 'terra'.
   - Finished!

 - **If you said yes - add an entire wallet:**
   - **Secret password (do not forget what this is)** A password to decrypt the seed value. For improved security, please make this a complex password.
    - **Do you want to generate a new wallet address?** Yes or no - if you say 'yes' then a new address and seed phrase will be displayed and used for this wallet.
    - **Terra address**: Provide the address of the wallet here - it starts with 'terra'.
    - **Wallet seed**: Provide the secret seed phrase to generate the wallet here. This is the ONLY time you'll need to provide this - see the security section below.
    - Finished!

This script will create a file called ```user_config.yml```.
You can edit this file if you need to, but do not modify the encrypted seed string.

If this file is corrupted or you forget the password then you can delete it and start again.

### balances.py

This will return the balances for each coin type on all of your wallets. You provide the same password as you used in the configuration step, and say 'yes' or 'no' to just getting the LUNC and USTC summaries.

### manage_wallets.py

To automatically update your wallets, you need to run ```manage_wallets.py```. Provide the same password you used in the configuration step, and then select the operation you want to do.

 - **Withdrawals**: All the staking rewards are withdrawn. The fee is paid by either a random minor coin (KRT for example), or LUNC, or USDT (in that order).
 - **Swap**: All the available USTC is swapped for LUNC. Currently the fee must be paid in USTC.
 - **Delegate**: LUNC is redelegated back to the same validator. A set amount is always kept in reserve to cover fees for later transactions (250 LUNC). Depending on how the wallet was configured (via ```configure_user_wallets.py```), either a percentage of the available funds is delegated, or a set amount.

 **Special note about delegations**: delegating will also withdraw all existing rewards (which are not part of the delegation), so your balance afterwards might also reflect the withdrawals.

### send.py

You use ```transaction.py``` to send LUNC to another address, from wallets in the ```user_config.yml``` file. Provide the same password you used in the configuration step.

Two points to remember:
 - Memos are optional
 - You should keep a minimum amount of LUNC in reserve for payment of fees for future operations

 ### validators.py

You can delegate, undelegate, and switch between validators by running the ```validators.py``` script.
If you undelegate funds, then they will be unavailable for 21 days.

### swap.py

You can swap the minor Terra coins for any other coin, including USTC and LUNC, as well as supported coins on Osmosis.

First, provide the same password you used in the configuration step, and then select the coin you want to swap from.

After pressing 'X' to continue, you will can then choose what you want to swap your selection to. You can also see the estimated conversion result.

## Osmosis usage

You can swap to other non-Terra coins by using the Osmosis exchange functionality. Support for other coins needs to be specifically added to the list in the ```constants.py``` file.

Fees are kept as low as possible, and slippage defaults to 1%. The swap paths are calculated automatically to use the lowest swap fee pool, and also required a pool with a significantly larger liquidity amount than what is being swapped.

To use this, you need to send an amount of LUNC to your Osmosis address (starting with 'terra'). Once you have some funds there, you can swap them to other coins as well as using them for paying fees.

For the sake of simplicity, LUNC is used as the fee payment option.

Transfers are usually instantaneous - by the time you have run the ```balances.py``` script, you should see them in your balance list. However, it can sometimes take longer - even hours for a transfer to appear. If transaction reported success and the hash showes up in the explorer, then it will eventually appear.

## BASE usage

You can swap LUNC to BASE by using ```swap.py```. Select the amount and BASE and the swap will complete.

Due to the how BASE works, you need to wait 21 days for a swap from BASE back to LUNC. This will show up in the list generated by ```validators.py```.

### Troubleshooting

Examples of errors and what they might mean:

**The script is stuck on 'Starting delegations' and isn't doing anything**

Sometimes it seems to timeout and nothing will happen for many minutes. In these cases you can press 'control+C' (on the Mac) to quit the script. You can run ```python3 balances.py``` to check where your coins currently sit, and re-run the ```manage_wallets.py``` script to start again.

**LCD Response Error Status 400 - failed to execute message; message index: 0: Operation exceeds max spread limit: execute wasm contract failed: invalid request**

Seems to be a problem with the LCD - try again later and it should work.

**terra_classic_sdk.exceptions.LCDResponseError: Status 502 - Bad Gateway**

Network connectivity issues with the LCD endpoint. Try again later.

**out of gas in location: ReadFlat; gasWanted: 150762, gasUsed: 151283: out of gas**

The gas adjustment value needs to be increased.

**terra_classic_sdk.exceptions.LCDResponseError: Status 400 - failed to execute message; message index: 0: token amount calculated (xxx) is lesser than min amount (yyy): invalid request

If this was an Osmosis swap (probably to or from Ethereum) then increase the max_slippage value and try again.

## Gas adjustment

Currently it seems that a successful gas adjustment value is 3.6. If you don't want to try the initial value, then you can change the default to to something else.

You can change the values in the ```constants/constants.py``` file:

```
GAS_ADJUSTMENT           = 3.6
GAS_ADJUSTMENT_INCREMENT = 0.1
MAX_GAS_ADJUSTMENT       = 4
```

## Security notes

Your wallet seed phrase is extremely important and must be kept safe at all times. You need to provide the seed phrase so the wallet can be recreated to allow withdrawals and delegations.

Each wallet seed phrase is encrypted with the cryptocode library (https://pypi.org/project/cryptocode/) which uses AES encryption. You provide a password which makes the encrypted string impossible to guess or brute-force as long as it's a sufficiently complex password.

The encrypted string is saved in the ```user_config.yml``` file, and your seed phrase will never be visible in plain text.

When you run any of the other scripts, you provide the same password you used when you ran ```configure_user_wallets.py```. If this password doesn't decrypt any valid wallets then the script will stop.

If you have any questions or concerns about the security aspect of your seed, then please raise an issue on this project.
