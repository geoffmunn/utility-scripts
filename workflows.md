# Workflows

This is probably the most useful part of the utility scripts project. Workflows allow you to chain actions together, across multiple wallets, and on an automated basis.
All you need to do is to describe your actions in YML file, and follow a simple structure.

There are no limitations to what you can do (within the constraints of YML though).

Full examples can be found at the end of this document, and in the ```user_workflows.example.yml``` file

**terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu** is the burn address for Terra Classic. Do not send anything to this address!

## Introduction

A workflow has 3 components: the header, the wallets, and the steps.

## Header

The header contains the name of the workflow and an optional extended decription.
Technically, the name is optional but I highly recommend that you include one just so it's obvious what workflow is being run.

**This is a required section.**

**Example** - *standard header.*

```yml
workflows:
  - name: Weekly withdrawal 1
    description: Redelegate 100% of staking rewards in most wallets
```

## Wallets
This is a list of wallets that this workflow will be applied to. This can be a single wallet, or a long list.

**This is a required section.**

```yml
- wallets:
    - wallet name 1 (required, must have at least 1)
    - wallet name 2 (optional)
    - address (optional)
```

The wallet value can be either the name or the address, but for clarity I recommend that you use the wallet name. These need to be set up in the ```configure_user_wallets.py``` script.

**Workflows do not support non-managed addresses for security and safety reasons.**

**Example 1** - *A very basic configuration.*

```yml
workflows:
  - name: Weekly withdrawal 1
    description: Withdraw 100% of staking rewards in one wallet
    wallets:
      - Workflow wallet 1
```

**Example 2** - *This shows multiple wallets, with one being a terra address.*

```yml
workflows:
  - name: Weekly withdrawal 1
    description: Withdraw 100% of staking rewards in most wallets
    wallets:
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
```

## Steps

This is where the magic happens.

Steps can consist of one or more of the following:

 - **Withdraw rewards** - *withdraw*
 - **Redelegate rewards** - *redelegate*
 - **Delegate LUNC to a validator** - *delegate*
 - **Send LUNC or any other coin** - *send*
 - **Swap LUNC or any other coin** - *swap*
 - **Join a liquidity pool on Osmosis** - *join pool*
 - **Exit a liquidity pool on Osmosis** - *exit pool*
 - **Switch delegations between validators** - *switch validator*
 - **Unstake delegations from a validator** - *unstake delegation*

 Each step has its own set of required and optional parameters.

 Steps are run in the order they appear, and if a step fails then all successive steps will be skipped.
 If this is part of a multi-wallet workflow, then next wallet will have the entire set of steps applied to it, regardless of if it failed on a previous wallet.

 If you find that a step fails on a regular basis (problems with Osmosis for example, or unstable infrastructure), then it would be a good idea to have a tidy-up workflow that takes care of any transactions that left coins in limbo.

 ### Withdraw rewards - *withdraw*

 This lets you withdraw rewards from a validator. You can only withdraw 100% of the available rewards.

 ```yml
 - action: withdraw
   when:
     - always (optional, always run this step)
     - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
     - Day = Sun (optional, only run this on Sunday)
     - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
     - Time = 5:30pm (optional, only run this at exactly 5:30pm)
 ```

 Pick a combination of the 'when' values to match your requirements.

 Putting a reward condition in the 'when' section is a good idea so you don't withdraw tiny amounts of rewards and incur fees each time.

 **Example 1** - *always withdraw all rewards.*

 ```yml
 workflows:
    - name: Weekly withdrawal 1
      description: Withdraw 100% of staking rewards in one wallet
      wallets:
        - Workflow wallet 1
      steps:
        - action: withdraw
          when:
            - always
 ```

 **Example 2** - *only withdraw rewards on Sunday at 5pm, when the rewards exceed 1000 LUNC.*

```yml
workflows:
  - name: Weekly withdrawal 2
    description: Withdraw 100% of staking rewards in multiple wallets
    wallets:
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
    steps:
      - action: withdraw
        when:
          - LUNC > 1000
          - Day = Sunday
          - Time = 5pm
 ```

You can try different combinations of the LUNC amount, day and time to get the result you want.

### Redelegate rewards - *redelegate*

Redelegation is a special action because it only works if you have completed a 'withdraw' step beforehand. The redelegation action keeps track of what has been withdrawn and will redelegate some or all of this amount back. This allows you to hold an amount in the wallet balance which will not be touched in the redelegation step.

```yml
- action: redelegate
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  when: 
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```
**Example 1** - *Withdraw the rewards if they exceed 1000 LUNC and redelegate all of it back to the same validator.*

```yml
workflows:
  - name: Withdraw and full redelegation
    description: Redelegate 100% of staking rewards in one wallet
    wallets: 
      - Workflow wallet 1
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
      - action: redelegate
        amount: 100% LUNC
        when: 
          - always
```

**Example 2** - *Withdraw the rewards if they exceed 1000 LUNC, and redelegate 50% but only if it's Sunday.*

```yml
workflows:
  - name: Withdraw and full redelegation
    description: Redelegate 50% of staking rewards in one wallet, but only on Sundays
    wallets: 
      - Workflow wallet 1
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
          - Day = Sunday
      - action: redelegate
        amount: 50% LUNC
        when: 
          - always
```

**Example 3** - *Withdraw the rewards from multiple validators if they exceed 1000 LUNC, and redelegate 600 LUNC but only if it's 5pm on Sunday.*

```yml
workflows:
  - name: Withdraw and full redelegation
    description: Redelegate 600 LUNC from multiple wallets, but only on Sundays at 5pm
    wallets: 
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
          - Day = Sunday
          - Time = 5pm
      - action: redelegate
        amount: 600 LUNC
        when:
          - always
```

### Delegate LUNC to a validator - *delegate*

Delegation will take an amount in the wallet balance and delegate it to the supplied validator.
If you specify '100% LUNC', a small amount will be retained so you can still do other actions.

```yml
- action: delegate
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  validator: validator name (required)
  when: 
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

**Example 1** - *Delegate everything in the wallet to the listed validator.*

```yml
workflows:
  - name: Full delegation to a specific validator
    description: Delegate all the available balance in the wallet list
    wallets: 
      - Workflow wallet 1
    steps:
      - action: delegate
        amount: 100% LUNC
        validator: 🦅 Garuda Universe - 🎮 Airdrop Gaming Token💰
        when: 
          - always
```

**Example 2** - *Delegate 500 LUNC in the wallet to the supplied validator, if there is more than 500 LUNC available.*

```yml
workflows:
  - name: Full delegation to a specific validator
    description: Delegate 500 LUNC to the wallets in the list
    wallets: 
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
    steps:
      - action: delegate
        amount: 500 LUNC
        validator: 🦅 Garuda Universe - 🎮 Airdrop Gaming Token💰
        when: 
          - LUNC >= 500
```
Technnically the 'when' clause could be replaced with 'always' but you'll get an error if the wallet balance isn't enough and all successive steps will be skipped.

**Reminder**: Delegations will retain a minimum amount of LUNC, so you have enough to pay for transfers with other actions.

### Send LUNC or any other coin - *send*

You can send any supported coin to another wallet. This is especially useful for cleaning up airdrops, or chaining rewards into an Osmosis swap or liquidity pool.

```yml
- action: send
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  memo: A specific message (optional)
  recipient: The recipient address (required)
  wallet: Workflow Wallet 1 (optional, see notes in the swap section)
  when: 
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

**Example 1** - *Move all GRDX tokens to Workflow Wallet 3, but only if the GRDX amount is greater than 10.*

```yml
workflows:
  - name: Clean up wallets
    description: Move all GRDX coins into the one wallet
    wallets:
      - Workflow wallet 1
    steps:
      - action: send
        amount: 100% GRDX
        memo: Tidying up GRDX amounts
        recipient: Workflow Wallet 3
        when: 
          - GRDX > 10
```

Example 2: Withdraw all the rewards, and send an exact amount to another address. Then delegate everything that's left over back to a particular validator.

```yml
workflows:
  - name: Withdraw and send exact amount
    description: Withdraw all the rewards and send an exact amount to another address. Then delegate back.
    wallets:
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
    steps:
      - action: withdraw
        when: 
          - LUNC >= 1000
      - action: send
        amount: 200 LUNC
        memo: Here is 200 LUNC
        recipient: Workflow Wallet 3
        when: 
          - LUNC >= 1000
      - action: delegate
        amount: 100% LUNC
        validator: FireFi Capital
        when: 
          - always
```

### Swap
Swapping is really useful and quite complicated. There is a lot that can go wrong, but the process tries to accommodate most issues.
Chaining across different wallets introduces a new parameter concept:

```yml
wallet:  [wallet name or address]
```

This will apply the current step to the named wallet. You can actually use this on any of the prior examples but it's not really necessary most of the time.

**Example 1** - Swap all the rewards into USTC.

```yml
workflows:
  - name: Withdraw and on-chain swap full amount
    description: Withdraw all the rewards and swap all of the LUNC into USTC
    wallets:
      - Workflow Wallet 1
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
      - action: swap
        amount: 100% LUNC
        swap to: USTC
        when: 
          - LUNC > 1000
```

**Example 2** - *Swap all the rewards into LUNC and GRDX (50/50 split).*

```yml
workflows:
  - name: Withdraw and on-chain swap full amount in 2 parts
    description: Withdraw all the rewards and to a multipart swap into different coins.
    wallets:
      - Workflow Wallet 8
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
      - action: swap
        amount: 50% LUNC
        swap to: BASE
        when: 
          - always
      - action: swap
        amount: 100%
        swap to: GRDX
        when: 
          - always
```

**Example 3** - *Send the rewards to Osmosis and swap them into KUJI and CRO (50/50 split).*

```yml
workflows:
  - name: Withdraw, send to Osmosis, swap to 2 coins
    description: Send coins to Osmosis and swap all of them to 2 separate coins
    wallets:
      - Workflow Wallet 11
    steps:
      - action: withdraw
        when: 
          - LUNC > 1000
      - action: send
        amount: 100% LUNC
        recipient:  Osmosis Workflow 2
        when:
          - LUNC > 1000
      - action: swap
        wallet:  Osmosis Workflow 2
        amount: 50% LUNC
        swap to: KUJI
        when:
          - always
      - action: swap
        wallet:  Osmosis Workflow 2
        amount: 100% LUNC
        swap to: CRO
        when:
          - always
```

If you move coins to a new chain (Osmosis in this case), then all actions from that point on will need a 'wallet' parameter to be specified. Otherwise it will try to use the current wallet which is probably a Terra address.

#### Parameters

**amount**: Required. The amount you want to send. This can be either a fixed amount or a percentage.
Examples:
```yml
- amount: 1500 LUNC
- amount: 100% LUNC
```

You can transfer the entire amount out of a wallet, no minimum amount will be retained. If you don't specify a denomination, it will be assumed to be LUNC but for clarity, I highly recomment specifying a denomination.



**Complete examples**

```yml
  - name: Clean up wallets
    description: Move all GRDX coins into the one wallet
    wallets:
      - Workflow Wallet 1
      - Workflow Wallet 2
      - Workflow Wallet 3
    steps:
      - action: send
        amount: 100% GRDX
        memo: Tidying up GRDX amounts
        recipient: GRDX Wallet
        when: 
          - always

  - name: Withdraw and send full amount
    description: Withdraw all the rewards and send them to another address. Then delegate them.
    wallets: 
      - Workflow wallet 1
    steps:
      - action: withdraw
        when: 
          - LUNC >= 1000
      - action: send
        amount: 100% LUNC
        memo: This is a workflow test
        recipient: Workflow Wallet 2
        when: 
          - always
      - action: delegate
        wallet: Workflow Wallet 2
        amount: 100% LUNC
        validator: FireFi Capital
        when: 
          - always
```

### Swap

## When Triggers



- name: Withdraw and send exact amount (WORKING)
    description: Withdraw all the rewards and send an exact amount to the same address. Then delegate back.
    wallets:
      - Workflow Wallet 5
    steps:
      - action: withdraw
        when: LUNC >= 1000


# NOTES:

Sometimes IBC transfers might fail. Try again.