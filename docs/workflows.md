# Workflows

This is probably the most useful part of the utility scripts project. Workflows allow you to chain actions together, across multiple wallets, and on an automated basis.
All you need to do is to describe your actions in YML file, and follow a simple structure.

There are no limitations to what you can do (within the constraints of YML though).

Full examples can be found at the end of this document, and in the ```user_workflows.example.yml``` file.

> [!WARNING]
> **terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu** is the burn address for Terra Classic. Do not send anything to this address!

## Introduction

A workflow has 3 components: the header, the wallets, and the steps.

## Header

The header contains the name of the workflow and an optional extended decription.
Technically, the name is optional but I highly recommend that you include a name just so it's obvious what workflow is being run.

> [!NOTE]
> **This is a required section.**

**Example** - *standard header.*

```yml
workflows:
  - name: Weekly withdrawal 1
    description: Redelegate 100% of staking rewards in most wallets
```

## Wallets
This is a list of wallets that this workflow will be applied to. This can be a single wallet, or a long list.

> [!NOTE]
> **This is a required section.**

**Definition:**

```yml
- wallets:
    - wallet name 1 (required, must have at least 1)
    - wallet name 2 (optional)
    - address (optional)
```

The wallet value can be either the name or the address, but for clarity I recommend that you use the wallet name. These need to be set up in the ```configure_user_wallets.py``` script.

> [!IMPORTANT] 
> **Workflows do not support non-managed addresses for security and safety reasons.**

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

 - [**Withdraw rewards**](#withdraw-rewards---withdraw) - *withdraw*
 - [**Redelegate rewards**](#redelegate-rewards---redelegate) - *redelegate*
 - [**Delegate LUNC to a validator**](#delegate-lunc-to-a-validator---delegate) - *delegate*
 - [**Send LUNC or any other coin**](#send-lunc-or-any-other-coin---send) - *send*
 - [**Swap LUNC or any other coin**](#swap-lunc-or-any-other-coin---swap) - *swap*
 - [**Join a liquidity pool on Osmosis**](#join-a-liquidity-pool-on-osmosis---join-pool) - *join pool*
 - [**Exit a liquidity pool on Osmosis**](#exit-a-liquidity-pool-on-osmosis---exit-pool) - *exit pool*
 - [**Switch delegations between validators**](#switch-delegations-between-validators---switch-validator) - *switch validator*
 - [**Unstake delegations from a validator**](#unstake-delegations-from-a-validator---unstake-delegation) - *unstake delegation*

 Each step has its own set of required and optional parameters.

 Steps are run in the order that they appear, and if a step fails then all successive steps will be skipped.
 If this is part of a multi-wallet workflow, then next wallet will start with the entire set of steps available, regardless of if it failed on a previous wallet.

 If you find that a step fails on a regular basis (problems with Osmosis for example, or unstable infrastructure), then it would be a good idea to have a tidy-up workflow that takes care of any transactions that left coins in limbo.

 ### Withdraw rewards - *withdraw*

 This lets you withdraw rewards from a validator. You can only withdraw 100% of the available rewards.

**Definition:**

 ```yml
 - action: withdraw
   description: (optional) Withdraw rewards from a validator
   when:
     - always (optional, always run this step)
     - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
     - Day = Sun (optional, only run this on Sunday)
     - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
     - Time = 5:30pm (optional, only run this at exactly 5:30pm)
 ```

 Pick a combination of the 'when' values to match your requirements.

 Putting a reward condition in the 'when' section is a good idea so you don't withdraw tiny amounts of rewards and incur fees each time.

 Specifing an exact time is risky if you have lots of workflows. These may take a while to complete and the time might change while the workflows are completing. I recommend specifying just an hour, or if you definitley want something run at a precise time, then make a workflow YML file with just this particular workflow.

 **Example 1** - *always withdraw all rewards.*

 ```yml
 workflows:
    - name: Weekly withdrawal 1
      description: Withdraw 100% of staking rewards in one wallet
      wallets:
        - Workflow wallet 1
      steps:
        - action: withdraw
          description: Withdraw rewards from the validator
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
        description: Withdraw rewards from the validator if there are more than 1000 LUNC on a Sunday at 5pm
        when:
          - LUNC > 1000
          - Day = Sunday
          - Time = 5pm
 ```

You can try different combinations of the LUNC amount, day and time to get the result you want.

### Redelegate rewards - *redelegate*

Redelegation is a special action because it only works if you have completed a 'withdraw' step beforehand. The redelegation action keeps track of what has been withdrawn from each validator and will redelegate some or all of this amount back. This allows you to hold an amount in the wallet balance which will not be touched in the redelegation step.

**Definition:**

```yml
- action: redelegate
  description: (optional) Redelegate rewards back to the same validator
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
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC > 1000
      - action: redelegate
        description: Redelegate rewards back to the same validator
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
        description: Withdraw rewards from the validator if there are more than 1000 LUNC and it is a Sunday
        when: 
          - LUNC > 1000
          - Day = Sunday
      - action: redelegate
        description: Redelegate 50% of the rewards back to the same validator
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
        description: Withdraw rewards from the validator if there are more than 1000 LUNC and it is 5pm on Sunday
        when: 
          - LUNC > 1000
          - Day = Sunday
          - Time = 5pm
      - action: redelegate
        description: Redelegate 600 LUNC to the same validator
        amount: 600 LUNC
        when:
          - always
```

### Delegate LUNC to a validator - *delegate*

Delegation will take an amount in the wallet balance and delegate it to the supplied validator.
If you specify '100% LUNC', a small amount will be retained so you can still do other actions.

**Definition:**

```yml
- action: delegate
  description: (optional) Delegate a specific amount to a validator
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
        description: Delegate all available LUNC to the validator
        amount: 100% LUNC
        validator: 🦅 Garuda Universe - 🎮 Airdrop Gaming Token💰
        when: 
          - always
```

**Example 2** - *Delegate 500 LUNC in the wallet to the supplied validator, if there is more than 500 LUNC available.*

```yml
workflows:
  - name: Specific delegation to a validator
    description: Delegate 500 LUNC to the wallets in the list
    wallets: 
      - Workflow wallet 1
      - Workflow wallet 2
      - terra1sk06e3dyexuq4shw77y3dsv480xv42mq73anxu
    steps:
      - action: delegate
        description: Delegate 500 LUNC to the validator
        amount: 500 LUNC
        validator: 🦅 Garuda Universe - 🎮 Airdrop Gaming Token💰
        when: 
          - LUNC >= 500
```
Technnically the 'when' clause could be replaced with 'always' but you'll get an error if the wallet balance isn't enough and all successive steps will be skipped.

> [!IMPORTANT]
> **Reminder**: Delegations will retain a minimum amount of LUNC, so you have enough to pay for transfers with other actions.

### Send LUNC or any other coin - *send*

You can send any supported coin to another wallet. This is especially useful for cleaning up airdrops, or chaining rewards into an Osmosis swap or liquidity pool.

**Definition:**

```yml
- action: send
  description: (optional) Delegate a specific amount to a validator
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
        description: Send all available GRDX to the Workflow 3 wallet if there is more than 10 GRDX
        amount: 100% GRDX
        memo: Tidying up GRDX amounts
        recipient: Workflow Wallet 3
        when: 
          - GRDX > 10
```

**Example 2**: *Withdraw all the rewards, and send an exact amount to another address. Then delegate everything that's left over back to a particular validator.*

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
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC >= 1000
      - action: send
        description: Send 200 LUNC to the Workflow 3 wallet
        amount: 200 LUNC
        memo: Here is 200 LUNC
        recipient: Workflow Wallet 3
        when: 
          - LUNC >= 1000
      - action: delegate
        description: Delegate all remaining LUNC to the validator
        amount: 100% LUNC
        validator: FireFi Capital
        when: 
          - always
```

### Swap LUNC or any other coin - *swap*
Swapping is really useful and quite complicated. There is a lot that can go wrong, but the process tries to accommodate most issues.
Chaining across different wallets introduces a new parameter concept:

```yml
wallet:  [wallet name or address]
```

**Definition:**

```yml
- action: swap
  description: (optional) Swap some LUNC to another coin
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  swap to: Denomination name (required, ie LUNC, OSMO)
  wallet: Wallet name (optional - required if the network has changed during this workflow)
  when:
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

This will apply the current step to the named wallet. You can actually use this on any of the prior examples but it's not really necessary most of the time.

**Example 1** - *Swap all the rewards into USTC.*

```yml
workflows:
  - name: Withdraw and on-chain swap full amount
    description: Withdraw all the rewards and swap all of the LUNC into USTC
    wallets:
      - Workflow Wallet 1
    steps:
      - action: withdraw
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC > 1000
      - action: swap
        description: Swap all available LUNC to USTC if there are more than 1000 LUNC
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
      - Workflow Wallet 1
    steps:
      - action: withdraw
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC > 1000
      - action: swap
        description: Swap 50% of all available LUNC to BASE
        amount: 50% LUNC
        swap to: BASE
        when: 
          - always
      - action: swap
        description: Swap all remaining LUNC to GRDX
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
      - Workflow Wallet 1
    steps:
      - action: withdraw
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC > 1000
      - action: send
        description: Send all available LUNC to the Osmosis wallet if there is more than 1000 LUNC
        amount: 100% LUNC
        recipient:  Osmosis Workflow 1
        when:
          - LUNC > 1000
      - action: swap
        description: Swap 50% of all LUNC in the Osmosis wallet to KUJI
        wallet:  Osmosis Workflow 1
        amount: 50% LUNC
        swap to: KUJI
        when:
          - always
      - action: swap
        description: Swap all remaining LUNC in the Osmosis wallet to CRO
        wallet:  Osmosis Workflow 1
        amount: 100% LUNC
        swap to: CRO
        when:
          - always
```

If you move coins to a new chain (Osmosis in this case), then all actions from that point on will need a 'wallet' parameter to be specified. Otherwise it will try to use the current wallet which is probably a Terra address.

### Join a liquidity pool on Osmosis - *join pool*

You can join and exit liquidity pools on Osmosis. Currently we only support pools with LUNC as a pool asset.
To see what pool IDs are available, run the ```liquidity.py``` script.

> [!NOTE]
> To contribute LUNC into a pool, you need to have sent it to an Osmosis address first. You can't use a Terra address (currently)

**Definition:**

```yml
- action: join pool
  description: (optional) Join a liquidity pool in Osmosis
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  pool id: pool ID (required - a pool with LUNC assets)
  wallet: Wallet name (optional - required if the network has changed during this workflow)
  when:
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

The wallet needs to be an Osmosis wallet at this step. If you started off with a Terra address, then use the 'wallet' parameter to specify an Osmosis address.

**Example 1** - *Put 100% of LUNC on an Osmosis address into Pool 562.*

```yml
workflows:
  - name: Add to pool 562
    description: Add the available LUNC to an Osmosis pool
    wallets:
      - Osmosis Workflow 1
    steps:
      - action: join pool
        description: Add all available LUNC to pool 562
        amount: 100% LUNC
        pool id: 562
        when:
          - always
```

**Example 2** - *Send rewards to an Osmosis address and join a pool.*

```yml
workflows:
  - name: Withdraw, send to Osmosis, add to pool
    description: Add the delegation rewards to an Osmosis pool
    wallets:
      - Workflow Wallet 1
    steps:
      - action: withdraw
        description: Withdraw rewards from the validator if there are more than 1000 LUNC
        when: 
          - LUNC > 1000
      - action: send
        description: Send all available LUNC to the Osmosis Workflow 1 wallet
        amount: 100% LUNC
        memo: Send to Osmosis for Pool 562
        recipient: Osmosis Workflow 1
        when:
          - always
      - action: join pool
        description: Add all available LUNC in the Osmosis wallet to pool 562
        wallet: Osmosis Workflow 1
        amount: 100% LUNC
        pool id: 562
        when:
          - always
```

> [!IMPORTANT]
> Because this workflow started with a terra address (Workflow Wallet 1), the 'wallet' parameter in the 'join pool' step is essential, to provide the Osmosis wallet that this step uses.

### Exit a liquidity pool on Osmosis - *exit pool*

You can exit a pool on Osmosis if it contains a LUNC asset - basically the same list of pools as from the 'join pool' action.

**Definition:**

```yml
- action: exit pool
  description: (optional) Exit an Osmosis liquidity pool
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  pool id: pool ID (required - a pool with LUNC assets)
  wallet: Wallet name (optional - required if the network has changed during this workflow)
  when:
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

As with the 'join pool' action, the wallet needs to be an Osmosis wallet at this step. If you started off with a Terra address, then use the 'wallet' parameter to specify an Osmosis address.

**Example 1** - *Remove 50% of LUNC from Osmosis pool 562, when there's more than 500 LUNC in there.*

```yml
workflows:
  - name: Exit 50% from pool 562
    description: Remove 50% of the available LUNC from an Osmosis pool
    wallets:
      - Osmosis Workflow 1
    steps:
      - action: exit pool
        description: Remove 50% of LUNC from pool 562 if there is more than 500 LUNC there
        amount: 50% LUNC
        pool id: 562
        when:
          - LUNC > 500
```
**Example 2** - *Remove 500 LUNC from Osmosis pool 562, when there's more than 500 LUNC in there.*

```yml
workflows:
  - name: Exit 500 LUNC from pool 562
    description: Remove 500 of the available LUNC from an Osmosis pool
    wallets:
      - Osmosis Workflow 1
    steps:
      - action: exit pool
        description: Remove 500 LUNC from pool 562 if there is more than 500 LUNC there
        amount: 500 LUNC
        pool id: 562
        when:
          - LUNC > 500
```

> [!TIP]
> When exiting a pool, you will always receive a mixture of LUNC and whatever the other assets are. This is because your exit amount is turned into a percentage of the total number of shares, and this is across the entire asset range. Consider it a gift :)

###  Switch delegations between validators - *switch validator*

You can also switch validators by moving your delegations from one validator to another.

**Definition:**

```yml
- action: switch validator
  description: (optional) Switch to another validator
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  old validator: Old validator name (required)
  new validator: New validator name (required)
  when:
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

> [!NOTE]
> If you move 100% of funds from a validator, then make sure you don't have any workflows trying to withdraw rewards from the old validator. The workflow will probably fail if there are no rewards to use.

**Example 1** - Move 20% of delegations to another validator

```yml
workflows:
  - name: Switch validator
    description: Move from one validator to another
    wallets:
      - Workflow Wallet 1
    steps:
      - action: switch validator
        description: Move 20% of delegated LUNC to a new validator if it's 11pm on Sunday
        amount: 20% LUNC
        old validator: FireFi Capital
        new validator: 🦅 Garuda Universe - 🎮 Airdrop Gaming Token💰
        when:
          - Day = Sunday
          - Time = 11pm
```

### Unstake delegations from a validator - *unstake delegation*

To be honest, I'm not sure why you'd want to unstake from a validator via a workflow, but the functionality is there and it *is* possible to do it.

**Definition:**

```yml
- action: unstake delegation
  description: (optional) Unstake a delegation from a validator
  amount: 100% LUNC / 500 LUNC (required, takes either a percentage or a specific amount)
  validator: Validator name (required)
  when:
    - always (optional, always run this step)
    - LUNC > 1000 (optional, only run when the LUNC amount is greater than 1000)
    - Day = Sun (optional, only run this on Sunday)
    - Time = 5pm (optional, only run this at any point between 5pm and 6pm)
    - Time = 5:30pm (optional, only run this at exactly 5:30pm)
```

**Example 1** - Unstake 10% of delegations from a validator

```yml
workflows:
  - name: Unstake test
    description: Unstake a small amount to make sure this still works
    wallets:
      - Workflow Wallet 1unexpected error occurred in the governance vote functi
    steps:
      - action: unstake delegation
        description: Undelegate 10% of delegated LUNC if it's 3pm on Sunday
        amount: 10% LUNC
        validator: FireFi Capital
        when:
          - Day = Sunday
          - Time = 3pm
```

## FINAL NOTES

Sometimes IBC transfers might fail. The transaction search tries 50 times before quitting - 99% of the time this is enough for the transfer to succeed, but sometimes it doesn't. In these cases you'll have to either complete the transaction manually, or adjust your workflow and do it again later.

When you make a delegation to a validator, any existing rewards will be automatically withdrawn, so your balance may actually go up depending on how much you delegated and received. This can be a bit surprising if you haven't made a reward withdrawal for a while.


