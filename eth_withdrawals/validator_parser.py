"""This module parses the consenus layer's validator state."""
from collections import defaultdict
import logging
from pathlib import Path
from time import sleep
from typing import Any
from eth_withdrawals.constants import DATA_DIR, ENDPOINT
from eth_withdrawals.models import (
    EthereumApiValidators,
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
logger = logging.getLogger("ValidatorStatus")


def parse_validator_status(
    api_response: EthereumApiValidators, slot: int, **kwarg
) -> dict[str, dict[str, Any]]:
    """parse the validator status data.

    :param api_response: parsed Validator api response
    :return: dictionary with validator status information

    Return example:
    {
        "slot": 123,
        "epoch": 10,
        "timestamp": "2022-01-30T13:49:32.304Z",
        "data_type": "validator_status",
        "total_count": 123,
        "total_balance": 123456789,
        "type_1_addr_count": 123,
        "slashed_count": 123,
        "exited_count": 123,
        "pending_initialized_count": 123,
        "pending_initialized_balance": 123456789,
        "pending_queued_count": 123,
        "pending_queued_balance": 123456789,
        "active_ongoing_count": 123,
        "active_ongoing_balance": 123456789,
        "active_exiting_count": 123,
        "active_exiting_balance": 123456789,
        "active_slashed_count": 123,
        "active_slashed_balance": 123456789,
        "exited_unslashed_count": 123,
        "exited_unslashed_balance": 123456789,
        "exited_slashed_count": 123,
        "exited_slashed_balance": 123456789,
        "withdrawal_possible_count": 123,
        "withdrawal_possible_balance": 123456789,
        "withdrawal_done_count": 123,
        "withdrawal_done_balance": 123456789,
    }
    """
    validators = api_response.data
    if not validators:
        return {}

    result = defaultdict(int)
    for validator in validators:
        result[validator.status.value + "_count"] += 1
        result["total_count"] += 1

        result[validator.status.value + "_balance"] += validator.balance
        result["total_balance"] += validator.balance

        result["type_1_addr_count"] += (
            validator.validator.withdrawal_credentials[:4] == "0x01"
        )
        result[
            "slashed_count"
        ] += validator.validator.slashed and validator.status.value in [
            "exited_slashed",
            "withdrawal_possible",
            "withdrawal_done",
        ]
        # Don't count the active_exiting because they still need to perform their duties
        result[
            "exited_count"
        ] += not validator.validator.slashed and validator.status.value in [
            "exited_unslashed",
            "withdrawal_possible",
            "withdrawal_done",
        ]

    return {
        "slot": slot,
        "epoch": SlotToEpoch(slot),
        "timestamp": DateTimeConverter(SlotToTime(slot)),
        "data_type": "validator_status",
    } | dict(result)


def process_status(
    slot: int, fetcher: Fetcher, output_format: str, status_output_file: Path
):
    """Process the validator status.

    :param slot: the slot to process
    :type slot: int
    :param fetcher: a fetcher object
    :type fetcher: Fetcher
    :param output_format: the output file format
    :type output_format: str
    :param status_output_file: the output file name
    :type status_output_file: Path
    """
    status_data = fetcher.fetch_and_parse(
        method=f"/eth/v1/beacon/states/{slot}/validators",
        parser=EthereumApiValidators,
        err_msg="Could not get validator container",
    )
    validator_status = parse_validator_status(status_data, slot)
    write_data(validator_status, status_output_file, output_format)


def main():
    """Main function to orchestrate the hourly processing of validator statuses."""
    output_format = get_output_format()

    status_output_file = DATA_DIR / f"validator_status.{output_format}"

    fetcher = Fetcher(ENDPOINT, logger)
    while True:
        try:
            slot = fetcher.get_finalized_slot()
        except RequestError:
            logger.warning("Could not get finalized slot, trying again in 60 seconds")
            sleep(60)  # wait a minute and try again
            continue

        try:
            process_status(slot, fetcher, output_format, status_output_file)
        except (
            RequestError,
            MissingHeightError,
            EthereumAPIError,
            ValidationError,
        ):
            sleep(60)  # wait a minute and try again
            continue

        logger.info("Parsed validator statuses at slot %s, sleeping for an hour", slot)
        sleep(3_600)  # wait an hour and go again


if __name__ == "__main__":
    main()
