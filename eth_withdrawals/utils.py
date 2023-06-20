import csv
import datetime
import sys
import jsonlines

from eth_withdrawals.constants import (
    GENESIS_TIMESTAMP,
    SECONDS_PER_SLOT,
    SLOTS_PER_EPOCH,
)
import pendulum
from typing import Union


class EthereumAPIError(Exception):
    """Custom error for API messages."""

    def __init__(self, msg: str, code=None) -> None:
        """Add error code to exception."""
        super().__init__(msg)
        self.code = code


class RequestError(Exception):
    """Custom error to capture requests exceptions."""

    pass


class MissingHeightError(Exception):
    """Custom error to capture missing slots."""

    pass


def SlotToEpoch(slot: int) -> int:
    """Convert slot to epochs."""
    return slot // SLOTS_PER_EPOCH


def SlotToUnixEpoch(slot: int) -> int:
    """Convert slot into unix epoch."""
    return GENESIS_TIMESTAMP + slot * SECONDS_PER_SLOT


def SlotToTime(slot: int) -> datetime:
    """Convert slot into UTC localized datetime."""
    return datetime.datetime.fromtimestamp(
        SlotToUnixEpoch(slot), tz=datetime.timezone.utc
    )


def DateTimeConverter(dt_input: Union[datetime.datetime, datetime.date]) -> str:
    """Convert a datetime to a custom format."""
    if isinstance(dt_input, datetime.datetime):
        pendulum_ts = pendulum.instance(dt_input)
        return pendulum_ts.format(r"YYYY-MM-DDTHH:mm:ss.SSS\Z")
    if isinstance(dt_input, datetime.date):
        return dt_input.strftime("%Y-%m-%d")


def get_output_format(default: str = "jsonl") -> str:
    """Get the output format from the command line input.

    :param default: the default output format
    :type default: str, defaults to 'jsonl'
    """
    if len(sys.argv) <= 1:
        return default
    output_format = sys.argv[1]
    if output_format not in ["jsonl", "csv", "json"]:
        raise ValueError(
            f"Output format '{output_format}' is invalid, must be one of jsonl, csv, json"
        )
    return output_format


def write_data(data: dict, path: str, output_format: str = "jsonl") -> None:
    """Write data to a file.

    :param data:
    :type data: dict
    :param path:
    :type path: str
    :param output_format:
    :type output_format: str, defaults to 'jsonl'
    :raises ValueError: if output_format is not supported
    """
    if output_format in ["json", "jsonl"]:
        with jsonlines.open(path, mode="a") as f:
            f.write(data)
    elif output_format == "csv":
        write_dictionary_to_csv(data, path)
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def write_dictionary_to_csv(data: dict, path: str) -> None:
    """Write the contents of a dict to a csv, handling the header.

    :param data: the data to write
    :type data: dict
    :param path: the file path
    :type path: str
    """
    file_exists = path.is_file()
    mode = "a" if file_exists else "w"

    with open(path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())

        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
