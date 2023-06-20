from time import sleep
import requests
import logging
from datetime import datetime, timedelta
from eth_withdrawals.constants import DATA_DIR

from eth_withdrawals.utils import get_output_format, write_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupplyParser")


def call(url: str):
    resp = requests.get(url)
    return resp.json()


def call_etherscan(url: str) -> dict | int:
    """Free APIs provided by etherscan, rate limited to 1 request/5seconds.
    MAINNET ONLY

    :raises requests.HTTPError: if the response is invalid
    :raises requests.exceptions.Timeout: if the request times out
    """
    resp = call(url)
    if resp["status"] != "1":
        raise requests.HTTPError("Etherscan response was invalid.")
    result = resp["result"]

    return result


def get_ethsupply2() -> dict:
    """Free API provided by etherscan, rate limited to 1 request/5seconds.
    MAINNET ONLY
    """
    result = call_etherscan(
        "https://api.etherscan.io/api?module=stats&action=ethsupply2"
    )

    return {
        "el_supply": int(
            result["EthSupply"]
        ),  # total Eth ever issued on the execution layer
        "burnt_fees": int(result["BurntFees"]),  # total burnt fees
        "staking_rewards": int(result["Eth2Staking"]),  # total staking rewards
        "staking_withdrawals": int(result["WithdrawnTotal"]),  # total ETH withdrawn
    }


def get_beacon_chain_deposits() -> dict:
    """Free API provided by etherscan, rate limited to 1 request/5seconds.
    MAINNET ONLY
    """
    result = call_etherscan(
        "https://api.etherscan.io/api?module=account&action=balance&address=0x00000000219ab540356cBB839Cbe05303d7705Fa&tag=latest"
    )
    return {"beacon_chain_deposits": int(result)}


def transform_etherscan_data(data: dict) -> dict:
    # ultrasound.money fields
    data["evm_balances"] = (
        data["el_supply"] - data["burnt_fees"] + data["staking_withdrawals"]
    )
    data["current_supply"] = (
        data["el_supply"] - data["burnt_fees"] + data["staking_rewards"]
    )
    data["beacon_chain_balances"] = (
        data["beacon_chain_deposits"]
        + data["staking_rewards"]
        - data["staking_withdrawals"]
    )

    # supply of ETH on the execution layer
    data["circulating_supply"] = data["evm_balances"] - data["beacon_chain_deposits"]
    return data


def main():
    """Main function to orchestrate the processing of finalized slots."""
    output_format = get_output_format()

    eth_supply_output_file = DATA_DIR / f"circulating_supply.{output_format}"

    next_whole_minute = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(
        minutes=1
    )
    logger.info("Waiting until the next whole minute.")
    sleep((next_whole_minute - datetime.utcnow()).total_seconds())
    while True:
        data = {"timestamp": next_whole_minute.isoformat() + "Z"}
        next_whole_minute = next_whole_minute + timedelta(minutes=1)

        logger.info("Fetching ethsupply2 data from Etherscan.")
        ethsupply2_data = get_ethsupply2()

        sleep(6)  # rate limit is 1 request/5seconds

        logger.info("Fetching the beacon chain deposits data from Etherscan.")
        beacon_chain_deposits_data = get_beacon_chain_deposits()

        data |= ethsupply2_data | beacon_chain_deposits_data
        logger.info("Transforming circulating supply data.")
        eth_supply = transform_etherscan_data(data)

        write_data(eth_supply, eth_supply_output_file, output_format)

        sleep((next_whole_minute - datetime.utcnow()).total_seconds())


if __name__ == "__main__":
    main()
