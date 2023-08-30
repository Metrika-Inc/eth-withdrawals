# Ethereum Withdrawals Overview Dashboard Data Parsers
Data parsers for Ethereum withdrawals data.

These parsers can be used to retrieve the data required to produce the Metrika [Withdrawals Overview](https://eth.metrika.co) dashboards. The Ethereum Foundation sponsored dashboard is a leading resource for tracking the Ethereum validator withdrawal process and was tracked closely during the Shapella upgrade.

# Usage
To install the required dependencies, from the root directory, run:
```
poetry install
```

To run a parser, from the root directory, run:
```
poetry run <parser-name> <output-format>
```

The supported parser names are:
- `block-parser`
- `status-parser`
- `supply-parser`

The supported output formats are:
- `jsonl` (default)
- `csv`
- `json` (supported but will result in `jsonl` output)

# Output
The parsers will save the output data files in the repo's `data/` directory. The `block-parser` produces `execution_payload.jsonl` and `withdrawals_data.jsonl` files, the `status-parser` produces `validator_status.jsonl` and the `supply-parser` produces `circulating_supply.jsonl`.

## `block-parser`: `exeuction_payload.jsonl`
Each record/row relates to a beacon chain block's execution payload.

| Field | Description |
| --- | --- |
| slot | Slot |
| epoch | Epoch |
| proposer_index | Proposer index |
| timestamp | Timestamp in ISO format |
| data_type | Type of data |
| transaction_count | Number of transactions |
| withdrawals_count | Number of withdrawals |
| withdrawals_amount | Total value of withdrawals |
| withdrawals_latest_sweep_index | Latest sweep index |
| withdrawals_latest_validator_index | Latest validator to receive a withdrawal |
| withdrawals_unique_validator_count | Number of unique validators to receive withdrawals in the block |
| withdrawals_unique_withdrawal_count | Number of unique withdrawal addresses to receive withdrawals in the block |
| parent_hash | Hash of the parent block |
| fee_recipient | Address of the fee recipient |
| state_root | State root hash |
| receipts_root | Receipts root hash |
| logs_bloom | Logs bloom |
| prev_randao | Previous RANDAO value |
| block_number | Block number |
| gas_limit | Gas limit |
| gas_used | Gas used |
| extra_data | Extra data |
| base_fee_per_gas | Base fee per gas |
| block_hash | Hash of the block |

## `block-parser`: `withdrawals_data.jsonl`
Each record/row relates to an individual withdrawal.

| Field | Description |
| --- | --- |
| slot | Slot |
| epoch | Epoch |
| timestamp | Timestamp in ISO format |
| data_type | Type of data |
| withdrawal_index | Withdrawal index |
| validator_index | Validator index |
| withdrawal_address | Withdrawal address |
| withdrawal_amount | Withdrawal amount |


## `status-parser`: `validator_status.jsonl`
Each record/row relates to the distribution of validator statuses at a specific time.

| Field | Description |
| --- | --- |
| slot | Slot |
| epoch | Epoch |
| timestamp | Timestamp in ISO format |
| data_type | Type of data |
| total_count | Total number of validators |
| total_balance | Total balance of all validators |
| exited_count | Number of validators that have exited |
| slashed_count | Number of validators that have been slashed |
| pending_initialized_count | Number of validators with the status pending_initialized |
| pending_initialized_balance | Total balance of validators with the status pending_initialized |
| pending_queued_count | Number of validators with the status pending_queued |
| pending_queued_balance | Total balance of validators with the status pending_queued |
| active_ongoing_count | Number of validators with the status active_ongoing |
| active_ongoing_balance | Total balance of validators with the status active_ongoing |
| active_exiting_count | Number of validators with the status active_exiting |
| active_exiting_balance | Total balance of validators with the status active_exiting |
| exited_unslashed_count | Number of validators that have exited and not been slashed |
| exited_unslashed_balance | Total balance of validators that have exited and not been slashed |
| exited_slashed_count | Number of validators that have exited and been slashed |
| exited_slashed_balance | Total balance of validators that have exited and been slashed |
| withdrawal_possible_count | Number of validators with the status withdrawal_possible |
| withdrawal_possible_balance | Total balance of validators with the status withdrawal_possible |
| withdrawal_done_count | Number of validators with the status withdrawal_done |
| withdrawal_done_balance | Total balance of validators with the status withdrawal_done |
| type_1_addr_count | Number of validators with a type 1 (0x01) withdrawal address |

## `supply-parser`: `circulating_supply.jsonl`
Each record/row relates to the Ethereum supply at a specific time. All values are in wei.

| Field | Description |
| --- | --- |
| timestamp | Timestamp in ISO format |
| el_supply | Total supply of ETH on the Execution Layer |
| burnt_fees | Total fees burnt to date |
| staking_rewards | Total staking rewards to date |
| staking_withdrawals | Total staking withdrawals to date |
| beacon_chain_deposits | Total ETH deposited to the Beacon Chain |
| evm_balances | Total ETH held in EVM accounts (el_supply - burnt_fees + staking_withdrawals) |
| current_supply | Total ETH supply (el_supply - burnt_fees + staking_rewards) |
| beacon_chain_balances | Total ETH held on the Beacon Chain |
| circulating_supply | Total ETH in circulation (evm_balances - beacon_chain_deposits) |
