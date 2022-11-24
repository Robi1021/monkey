# Retries improve reliability and slightly mitigates performance issues
import functools
import logging
from enum import Enum, auto

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from common.common_consts.timeouts import MEDIUM_REQUEST_TIMEOUT
from infection_monkey.island_api_client import (
    IslandAPIConnectionError,
    IslandAPIError,
    IslandAPIRequestError,
    IslandAPIRequestFailedError,
    IslandAPITimeoutError,
)

logger = logging.getLogger(__name__)


RETRIES = 5


class RequestMethod(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()


class HTTPRequestsFacade:
    def __init__(self, api_url: str, retries=RETRIES):
        self._session = requests.Session()
        retry_config = Retry(retries)
        self._session.mount("https://", HTTPAdapter(max_retries=retry_config))
        self._api_url = api_url

    def get(self, *args, **kwargs) -> requests.Response:
        return self._send_request(RequestMethod.GET, *args, **kwargs)

    def post(self, *args, **kwargs) -> requests.Response:
        return self._send_request(RequestMethod.POST, *args, **kwargs)

    def put(self, *args, **kwargs) -> requests.Response:
        return self._send_request(RequestMethod.PUT, *args, **kwargs)

    def _send_request(
        self,
        request_type: RequestMethod,
        endpoint: str,
        timeout=MEDIUM_REQUEST_TIMEOUT,
        data=None,
        *args,
        **kwargs,
    ) -> requests.Response:
        url = f"{self._api_url}/{endpoint}".strip("/")
        logger.debug(f"{request_type.name} {url}, timeout={timeout}")

        method = getattr(self._session, str.lower(request_type.name))
        response = method(url, *args, timeout=timeout, verify=False, json=data, **kwargs)
        response.raise_for_status()

        return response


def handle_island_errors(fn):
    @functools.wraps(fn)
    def decorated(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IslandAPIError as err:
            raise err
        except (requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects) as err:
            raise IslandAPIConnectionError(err)
        except requests.exceptions.HTTPError as err:
            if 400 <= err.response.status_code < 500:
                raise IslandAPIRequestError(err)
            elif 500 <= err.response.status_code < 600:
                raise IslandAPIRequestFailedError(err)
            else:
                raise IslandAPIError(err)
        except TimeoutError as err:
            raise IslandAPITimeoutError(err)
        except Exception as err:
            raise IslandAPIError(err)

    return decorated
