"""This module parses the consenus layer Execution Payload."""
from enum import Enum
from typing import Optional, Union
from eth_withdrawals.constants import (
    MAX_BLS_TO_EXECUTION_CHANGES,
    MAX_WITHDRAWALS_PER_PAYLOAD,
)

from pydantic import constr, conint, conlist, BaseModel

Hex40 = constr(regex="^0x[a-fA-F0-9]{40}$")
Hex64 = constr(regex="^0x[a-fA-F0-9]{64}$")
HexExtraData = constr(regex="^0x[a-fA-F0-9]{0,64}$")
HexTransaction = constr(regex="^0x[a-fA-F0-9]{0,2147483648}$")
Hex96 = constr(regex="^0x[a-fA-F0-9]{96}$")
Hex192 = constr(regex="^0x[a-fA-F0-9]{192}$")
Hex512 = constr(regex="^0x[a-fA-F0-9]{512}$")
ValIndex = conint(ge=0)
WithdrawalIndex = conint(ge=0)
PosInt = conint(ge=0)


class EthereumVersion(Enum):
    """Available Ethereum Versions."""

    phase0 = "phase0"
    altair = "altair"
    bellatrix = "bellatrix"
    capella = "capella"


class Withdrawal(BaseModel):
    """The Withdrawal object from the CL Capella spec."""

    index: WithdrawalIndex
    validator_index: ValIndex
    address: Hex40
    amount: PosInt


class BLSToExecutionChange(BaseModel):
    """The BLSToExecutionChange object from the CL Capella spec."""

    validator_index: ValIndex
    from_bls_pubkey: Hex96
    to_execution_address: Hex40


class SignedBLSToExecutionChange(BaseModel):
    """The SignedBLSToExecutionChange object from the CL Capella spec."""

    message: BLSToExecutionChange
    signature: Hex192


class ExecutionPayload(BaseModel):
    """The ExecutionPayload object from the CL Capella spec."""

    parent_hash: Hex64
    fee_recipient: Hex40
    state_root: Hex64
    receipts_root: Hex64
    logs_bloom: Hex512
    prev_randao: Hex64
    block_number: PosInt
    gas_limit: PosInt
    gas_used: PosInt
    timestamp: PosInt
    extra_data: HexExtraData
    base_fee_per_gas: PosInt
    block_hash: Hex64
    transactions: conlist(HexTransaction, max_items=1048576)
    withdrawals: conlist(
        Withdrawal, max_items=MAX_WITHDRAWALS_PER_PAYLOAD
    )  # [New in Capella]


class BeaconBlockBody(BaseModel):
    """The BeaconBlockBody object from the CL Bellatrix spec."""

    execution_payload: Optional[ExecutionPayload]
    bls_to_execution_changes: conlist(
        SignedBLSToExecutionChange, max_items=MAX_BLS_TO_EXECUTION_CHANGES
    )  # [New in Capella]


class BeaconBlock(BaseModel):
    """The BeaconBlock object from the CL Bellatrix spec."""

    slot: PosInt
    proposer_index: ValIndex
    parent_root: Hex64
    state_root: Hex64
    body: BeaconBlockBody


class SignedBeaconBlock(BaseModel):
    """The SignedBeaconBlock object envelope from the CL Bellatrix spec."""

    message: BeaconBlock
    signature: Hex192


class EthereumApiBlockResponse(BaseModel):
    """The API response from /eth/v2/beacon/blocks/{block_id} method."""

    version: EthereumVersion
    execution_optimistic: bool
    data: SignedBeaconBlock


class EthereumApiValidatorStatus(Enum):
    """Possible Validator status as per <https://hackmd.io/ofFJ5gOmQpu1jjHilHbdQQ>."""

    pending_initialized = "pending_initialized"
    pending_queued = "pending_queued"
    active_ongoing = "active_ongoing"
    active_exiting = "active_exiting"
    active_slashed = "active_slashed"
    exited_unslashed = "exited_unslashed"
    exited_slashed = "exited_slashed"
    withdrawal_possible = "withdrawal_possible"
    withdrawal_done = "withdrawal_done"
    active = "active"
    pending = "pending"
    exited = "exited"
    withdrawal = "withdrawal"


class EthereumApiValidatorData(BaseModel):
    """The Validator container from the CL phase0 spec."""

    pubkey: Hex96
    withdrawal_credentials: Hex64
    effective_balance: PosInt
    slashed: bool
    activation_eligibility_epoch: PosInt
    activation_epoch: PosInt
    exit_epoch: PosInt
    withdrawable_epoch: PosInt


class EthereumApiValidator(BaseModel):
    """The Validators Balance information."""

    index: ValIndex
    balance: PosInt
    status: EthereumApiValidatorStatus
    validator: EthereumApiValidatorData


class EthereumApiValidators(BaseModel):
    """The API response from /eth/v1/beacon/states/{state_id}/validators method."""

    execution_optimistic: bool
    data: Union[EthereumApiValidator, list[EthereumApiValidator]]
