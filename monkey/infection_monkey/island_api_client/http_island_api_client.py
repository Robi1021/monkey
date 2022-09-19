import functools
import logging

import requests

from common.common_consts.timeouts import LONG_REQUEST_TIMEOUT, MEDIUM_REQUEST_TIMEOUT

from . import IIslandAPIClient, IslandAPIConnectionError, IslandAPIError, IslandAPITimeoutError

logger = logging.getLogger(__name__)


def handle_island_errors(fn):
    @functools.wraps(fn)
    def decorated(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.ConnectionError as err:
            raise IslandAPIConnectionError(err)
        except TimeoutError as err:
            raise IslandAPITimeoutError(err)
        except Exception as err:
            raise IslandAPIError(err)

    return decorated

        # TODO: set server address as object property when init is called in find_server and pass
        #       object around? won't need to pass island server and create object in every function
        def send_log(self, data: str):
            requests.post(  # noqa: DUO123
                "https://%s/api/log" % (self._island_server,),
                json=data,
                verify=False,
                timeout=MEDIUM_REQUEST_TIMEOUT,
            )

        def get_pba_file(self, filename: str):
            return requests.get(  # noqa: DUO123
                "https://%s/api/pba/download/%s" % (self.server_address, filename),
                verify=False,
                timeout=LONG_REQUEST_TIMEOUT,
            )
