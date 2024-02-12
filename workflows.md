# Workflows

This is probably the most useful part of the utility scripts project. Workflows allow you to chain actions together, across multiple wallets, and on an automated basis.
All you need to do is to describe your actions in YML file, and follow a simple structure.

There are no limitations to what you can do (within the constraints of YML though).

Full examples can be found at the end of this document, and in the ```user_workflows.example.yml``` file

**terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu** is the burn address for Terra Classic. Do not send anything to this address!

## Introduction

A workflow has 3 components: the header, the wallets, and the steps.

## Header

This is contains the name of the workflow and an optional extended decription.
Technically, the name is optional but I highly recommend that you include one just so it's obvious what workflow is being run.

**This is a required section.**

**Example** - *standard header*

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

**Example 1** - *A very basic configuration*

```yml
workflows:
    - name: Weekly withdrawal 1
      description: Withdraw 100% of staking rewards in one wallet
      wallets:
        - Workflow wallet 1
```

**Example 2** - *This shows multiple wallets, with one being a terra address*

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

 ### Withdraw

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

 **Example 1** - *always withdraw all rewards*

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

 **Example 2** - *only withdraw rewards on Sunday at 5pm, when the rewards exceed 1000 LUNC*

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

### Redelegate

Redelegation is a special action because it only works if you have completed a 'withdraw' step beforehand. The redelegation action keeps track of what has been withdrawn and will redelegate some or all of this amount back. This allows you to hold an amount in the wallet balance which will not be touched in the redelegation step.

```yml
- action: redelegate
  amount: 100% LUNC/500 LUNC (required, takes either a percentage or a specific amount)
  when: 
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```
Example 1: Withdraw the rewards if they exceed 1000 LUNC and redelegate all of it back to the same validator.

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

Example 2: Withdraw the rewards if they exceed 1000 LUNC, and redelegate 50% but only if it's Sunday.

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

Example 3: Withdraw the rewards from multiple validators if they exceed 1000 LUNC, and redelegate 600 LUNC but only if it's 5pm on Sunday.

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
        when: 
          - Day = Sunday
          - Time = 5pm
```

General notes:
Delegations will retain a minimum amount of LUNC, so you have enough to pay for transfers with other actions.





### Delegate

### Send

You can send any supported coin to another wallet. This is especially useful for cleaning up airdrops, or chaining rewards into an Osmosis swap or liquidity pool.

#### Parameters

**amount**: Required. The amount you want to send. This can be either a fixed amount or a percentage.
Examples:
```yml
- amount: 1500 LUNC
- amount: 100% LUNC
```

You can transfer the entire amount out of a wallet, no minimum amount will be retained. If you don't specify a denomination, it will be assumed to be LUNC but for clarity, I highly recomment specifying a denomination.

**recipient**: Required. Who are you sending this to? It can be either a wallet name, or the actual address.

Example:
```yml
- recipient: Workflow wallet 1
- recipient: terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
```
**when**: Required. Please see the 'Trigger' section for the available options.

**wallet**: Optional. You can run this action on a different wallet if required. You would normally only need to do this if you have chained several actions together. This value can be either a wallet name, or the actual address.

Example:
```yml
- wallet: Osmosis Wallet
- wallet: terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
```
**memo**: Optional. A message you want to include in this transaction.

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