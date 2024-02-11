# Workflows

This is probably the most useful part of the utility scripts project. Workflows allow you to chain actions together, across multiple wallets, on an automated basis.
All you need to do is to describe your actions in YML file, and follow a simple structure.

There are no limitations to what you can do (within the constraints of YML though).

Full examples can be found at the end of this document, and in the ```user_workflows.example.yml``` file

**terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu** is the burn address for Terra Classic. Do not send anything to this address!

## Introduction

A workflow has 3 components: the header, the wallets, and the steps.

## Header

This is contains the name of the workflow and an optional extended decription.
Technically, the name is optional but I highly recommend that you include one just so it's obvious what workflow is being run.

Example:
```yml
workflows:
  - name: Weekly withdrawal 1
    description: Redelegate 100% of staking rewards in most wallets
```

## Wallets
You can provide a list of wallets that this workflow will be applied to. This can be a single wallet, or a long list.
The wallet value can be either the name or the address, but for clarity I recommend that you use the wallet name. These need to be set up in the ```configure_user_wallets.py``` script.

**Workflows do not support non-managed addresses for security and safety reasons.**

Examples:

```yml
# Single wallet example
workflows:
    - name: Weekly withdrawal 1
      description: Redelegate 100% of staking rewards in most wallets
      wallets:
        - Workflow wallet 1
```

```yml
# Multiple wallets with an address
workflows:
    - name: Weekly withdrawal 1
    description: Redelegate 100% of staking rewards in most wallets
    wallets:
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
```

## Steps

This is where the magic happens.

Steps can consist of one or more of the following:
 - withdraw
 - redelegate
 - delegate
 - send
 - swap
 - join pool
 - exit pool
 


General notes:
Delegations will retain a minimum amount of LUNC, so you have enough to pay for transfers with other actions.

## Actions

### Withdraw

### Redelegate

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