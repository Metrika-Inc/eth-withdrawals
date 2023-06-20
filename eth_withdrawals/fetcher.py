import time

from pydantic import BaseModel, ValidationError
from eth_withdrawals.constants import (
    GENESIS_TIMESTAMP,
    SECONDS_PER_SLOT,
    SLOTS_PER_EPOCH,
)
from typing import Type
import logging
import requests

from eth_withdrawals.utils import EthereumAPIError, MissingHeightError, RequestError


class Fetcher:
    def __init__(self, endpoint: str, logger: logging.Logger):
        self.endpoint = endpoint
        self.logger = logger

    def fetch(self, method: str, **kwargs) -> dict:
        """Fetch data from ethereum's consensus API.

        :param method:
        :type method: str
        :param kwargs:
        :rtype: dict
        """
        try:
            start = time.time()
            self.logger.debug("Making request")
            api_response = requests.get(
                url=self.endpoint + method,
                headers=kwargs.get("headers"),
                params=kwargs.get("params"),
            )
            self.logger.debug("Request took %s", time.time() - start)
        except requests.RequestException as exc:
            self.logger.warning(exc)
            raise RequestError(exc)

        try:
            response_json = api_response.json()
        except requests.JSONDecodeError as exc:
            self.logger.warning(
                "API did not return a valid JSON:\napi_endpoint=%s, api_response=%s",
                self.endpoint + method,
                api_response,
            )
            raise RequestError(exc)

        return response_json

    def parse_response(
        self,
        api_response: dict,
        parser: Type[BaseModel],
        err_msg: str = "block can't be nil",
    ):
        """parse_response.

        :param api_response:
        :type api_response: dict
        :param parser:
        :type parser: BaseModel
        :param err_msg:
        :type err_msg: str, defaults to 'block can't be nil'
        """
        if (response_code := api_response.get("code")) and (
            response_msg := api_response.get("message")
        ):
            if err_msg in response_msg:
                self.logger.warning(
                    "Fetch returned empty result: message='%s'", response_msg
                )
                raise MissingHeightError
            if response_code in [400, 404, 500]:
                raise EthereumAPIError(msg=response_msg, code=response_code)
            else:
                self.logger.warning(
                    "Unexpected error getting Attestations: api_response='%s'",
                    api_response,
                )

        try:
            return parser.parse_obj(api_response)
        except ValidationError as exc:
            self.logger.error(
                "Pydantic failed to parse api response: api_response='%s', exception='%s'",
                api_response,
                exc,
            )
            raise

    def fetch_and_parse(
        self, *, method: str, parser: Type[BaseModel], err_msg: str
    ) -> BaseModel:
        api_response = self.fetch(method)
        return self.parse_response(
            api_response=api_response, parser=parser, err_msg=err_msg
        )

    def get_finalized_slot(self):
        """Get the latest finalized slot from the beacon chain.

        :param endpoint:
        :type endpoint: str
        :param logger:
        :type logger: logging.Logger
        """
        api_response = self.fetch("/eth/v1/beacon/headers/finalized")
        return int(api_response["data"]["header"]["message"]["slot"])
