"""This module parses the consenus layer Execution Payload."""
import logging
from pathlib import Path
from time import sleep
from typing import Any
from eth_withdrawals.constants import DATA_DIR, ENDPOINT, SLOTS_PER_EPOCH
from eth_withdrawals.models import (
    EthereumApiBlockResponse,
    Withdrawal,
)
from eth_withdrawals.fetcher import Fetcher
from eth_withdrawals.utils import (
    DateTimeConverter,
    EthereumAPIError,
    MissingHeightError,
    RequestError,
    SlotToEpoch,
    SlotToTime,
    get_output_format,
    write_data,
)
from pydantic import ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionPayload")


def transform_execution_payload(
    api_response: EthereumApiBlockResponse, **kwarg
) -> dict[str, dict[str, Any]]:
    """parse the execution payload data.

    :param api_response: parsed Block api responsed
    :return: dictionary with all the information of the execution payload

    Return example:
    {
        "slot": 123,
        "epoch": 10,
        "proposer_index": 543,
        "timestamp": "2022-01-30T13:49:32.304Z",
        "data_type": "execution_payload",
        "bls_changes_count": 16,
        "transaction_count": 300,
        "withdrawals_count": 16,
        "withdrawals_amount": 123456789,
        "withdrawals_latest_sweep_index": 2000,
        "withdrawals_latest_validator_index": 123456,
        "withdrawals_unique_validator_count": 16,
        "withdrawals_unique_withdrawal_count": 16,
    }
    """
    message = api_response.data.message
    if not message:
        return {}
    exec_payload = message.body.execution_payload
    if not exec_payload:
        return {}
    output: dict[str, Any] = exec_payload.dict(exclude={"transactions", "withdrawals"})
    output |= {
        "slot": message.slot,
        "epoch": SlotToEpoch(message.slot),
        "proposer_index": message.proposer_index,
        "timestamp": DateTimeConverter(SlotToTime(message.slot)),
        "data_type": "execution_payload",
        "transaction_count": len(exec_payload.transactions),
    } | get_withdrawal_stats(exec_payload.withdrawals)
    return output


def get_withdrawal_stats(withdrawals: list[Withdrawal]) -> dict:
    """get statistics relating to the withdrawals of the block.

    :param withdrawals: list of withdrawals
    :type withdrawals: list[Withdrawal]
    :return: dictionary with withdrawal statistics
    """
    withdrawals = withdrawals or []
    return {
        "withdrawals_count": len(withdrawals),
        "withdrawals_amount": sum(withdrawal.amount for withdrawal in withdrawals),
        "withdrawals_latest_sweep_index": max(
            (withdrawal.index for withdrawal in withdrawals), default=-1
        ),
        "withdrawals_latest_validator_index": max(
            (withdrawal.validator_index for withdrawal in withdrawals), default=-1
        ),
        "withdrawals_unique_validator_count": len(
            {withdrawal.validator_index for withdrawal in withdrawals}
        ),
        "withdrawals_unique_withdrawal_count": len(
            {withdrawal.address for withdrawal in withdrawals}
        ),
    }


def transform_withdrawals_data(
    api_response: EthereumApiBlockResponse, **kwarg
) -> dict[str, dict[str, Any]]:
    """parse the withdrawals data.

    :param api_response: parsed Block api response
    :return: list of all withdrawals information from the execution payload

    Return example:
    [
        {
            "slot": 123,
            "epoch": 10,
            "timestamp": "2022-01-30T13:49:32.304Z",
            "data_type": "withdrawals_data",
            "withdrawal_index": 123,
            "validator_index": 123,
            "withdrawal_address": 0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b,
            "withdrawal_amount": 123456789,
        },
        ...
    ]
    """
    message = api_response.data.message
    if not message:
        return []
    exec_payload = message.body.execution_payload
    if not exec_payload:
        return []

    slot_data = {
        "slot": message.slot,
        "epoch": SlotToEpoch(message.slot),
        "timestamp": DateTimeConverter(SlotToTime(message.slot)),
        "data_type": "withdrawals_data",
    }
    return [
        slot_data
        | {
            "withdrawal_index": withdrawal.index,
            "validator_index": withdrawal.validator_index,
            "withdrawal_address": withdrawal.address,
            "withdrawal_amount": withdrawal.amount,
        }
        for withdrawal in exec_payload.withdrawals
    ]


def process_slot(
    slot: int,
    fetcher: Fetcher,
    output_format: str,
    withdrawals_output_file: Path,
    exc_payload_output_file: Path,
) -> None:
    """Fetch, parse, transform and write the data for a given slot.

    :param slot: the slot to process
    :type slot: int
    :param fetcher: a fetcher instance
    :type fetcher: Fetcher
    :param output_format: the output file's format
    :type output_format: str
    :param withdrawals_output_file: the output file for the withdrawals data
    :type withdrawals_output_file: Path
    :param exc_payload_output_file: the output file for the execution payload data
    :type exc_payload_output_file: Path
    """
    slot_data = fetcher.fetch_and_parse(
        method=f"/eth/v2/beacon/blocks/{slot}",
        parser=EthereumApiBlockResponse,
        err_msg="Could not find requested block",
    )

    execution_payload = transform_execution_payload(slot_data)
    write_data(execution_payload, exc_payload_output_file, output_format)

    withdrawals = transform_withdrawals_data(slot_data)
    for withdrawal in withdrawals:
        write_data(withdrawal, withdrawals_output_file, output_format)


def main():
    """Main function to orchestrate the processing of finalized slots."""
    output_format = get_output_format()

    withdrawals_output_file = DATA_DIR / f"withdrawals_data.{output_format}"
    exc_payload_output_file = DATA_DIR / f"execution_payload.{output_format}"

    fetcher = Fetcher(ENDPOINT, logger)
    last_finalized_slot = 0
    while True:
        try:
            finalized_slot = fetcher.get_finalized_slot()
        except RequestError:
            logger.warning("Could not get finalized slot, trying again in 60s.")
            sleep(60)  # wait a minute and try again
            continue

        last_finalized_slot = last_finalized_slot or finalized_slot - SLOTS_PER_EPOCH

        if finalized_slot == last_finalized_slot:
            sleep(60)  # wait a minute and try again
            continue

        logger.info("Parsing slots %s to %s", last_finalized_slot, finalized_slot)
        for slot in range(last_finalized_slot, finalized_slot):
            try:
                process_slot(
                    slot,
                    fetcher,
                    output_format,
                    withdrawals_output_file,
                    exc_payload_output_file,
                )
            except (
                RequestError,
                MissingHeightError,
                EthereumAPIError,
                ValidationError,
            ):
                logger.warning("Could not get block %s, skipping.", slot)
        logger.info("Parsing complete.")
        last_finalized_slot = finalized_slot


if __name__ == "__main__":
    main()
