"""Support for APIs that use livewire.js/Laravel."""
from copy import deepcopy
import json
import random

from apptk.http import HttpClient
from bs4 import Tag
from requests import Response

from webnovel.utils import int2base, merge_dicts


class LiveWireAPI:
    """A wrapper around a livewire.js / Laravel API component."""

    wire_id: str
    initial_data: dict
    initial_data_raw: str
    server_memos: list[dict]
    fingerprint: dict
    csrf_token: str
    app_url: str
    _client: HttpClient
    _referer_url: str
    last_response: Response
    path_history: list[str]

    def __init__(
        self,
        app_url: str,
        wire_id: str,
        element: Tag,
        csrf_token: str,
        referer_url: str = None,
        client: HttpClient = None,
    ) -> None:
        self.app_url = app_url
        self.path_history = []
        self._element = element
        self._client = client
        self._referer_url = referer_url
        self.wire_id = wire_id
        self.csrf_token = csrf_token
        self.server_memos = []

        #
        # wire:id is defined on the top-level HTML element passed in.
        #
        if "wire:id" in element.attrs:
            self._load_data(element)
        #
        # If the top-level element doesn't have wire:id, then search through all descendants
        # for a matching wire:id
        #
        else:
            for _element in element.select(r"[wire\:id]"):
                if _element["wire:id"] == self.wire_id:
                    self._load_data(_element)

        if not self.initial_data_raw:
            raise ValueError(f"Failed to load initial data for wire:id={self.wire_id}")

        self.server_memos.append(self.initial_data["serverMemo"])
        self.fingerprint = dict(self.initial_data["fingerprint"])

    @property
    def client(self):
        """Return the HTTPClient instance to use when hitting the API."""
        if self._client is None:
            self._client = HttpClient(use_cloudscraper=True)
        return self._client

    @property
    def component_name(self) -> str:
        """Return the 'name' of the component."""
        return self.fingerprint["name"]

    @property
    def api_url(self) -> str:
        """Return the API url for this component."""
        join_by_str = "" if self.app_url.endswith("/") else "/"
        return self.app_url + join_by_str + "livewire/message/" + self.component_name

    @property
    def referer_url(self) -> str:
        """Return the URL to use as for the Referer HTTP header in the requests."""
        if not self.path_history:
            join_by_str = "" if self.app_url.endswith("/") else "/"
            self.path_history.append(self.app_url + join_by_str + self.fingerprint["path"])
        return self.path_history[-1]

    def most_recent_server_memo(self) -> dict:
        """Return the most recent serverMemo."""
        return deepcopy(self.server_memos[-1])

    def make_call(self, method: str, *args, suppress_status_error: bool = False) -> Response:
        """
        Make a 'method' call against the API.

        :param method: The name of the 'method' to call on the component.
        :param args: The list of arguments passed to the method.
        :param suppress_status_error: By default raise_for_status() is called on the response. Set this to true to
            suppress that behaviour.
        """
        response = self.client.post(
            url=self.api_url,
            headers={
                "X-CSRF-TOKEN": self.csrf_token,
                "X-Livewire": "true",
                "Referer": self.referer_url,
            },
            json={
                "fingerprint": dict(self.fingerprint),
                "serverMemo": self.most_recent_server_memo(),
                "updates": [
                    {
                        "type": "callMethod",
                        "payload": {
                            "id": self.generate_call_id(),
                            "method": method,
                            "params": list(args),
                        },
                    }
                ],
            },
        )

        self.last_response = response

        if not suppress_status_error:
            response.raise_for_status()

        if response.ok:
            response_json = response.json()

            #
            # We need to update the path history, so that we can use the most recent path as the
            # referer url.
            #
            new_path = response_json.get("effects", {}).get("path")
            self.path_history.append(new_path)

            #
            # If the response is ok, then we need to record the returned serverMemo, so that
            # we can use it in the next response.
            #
            dirty_attributes = response_json.get("effects", {}).get("dirty", [])
            response_memo = response_json.get("serverMemo", {})
            self.update_server_memo(response_memo, dirty_attributes)

        return response

    def update_server_memo(self, response_server_memo: dict, dirty_attrs: list[str]) -> None:
        """
        Create a new entry in server_memos.

        Create a copy of the most recent item in server_memos and update values from response_server_memo based on the
        attribute paths specified in dirty_attrs.

        :param response_server_memo: The "serverMemo" value from the most recent response.
        :param dirty_attrs: A list of attribute paths that need to be updated due to the change in state from the last
            api call.
        """
        new_server_memo = deepcopy(self.most_recent_server_memo())
        new_server_memo["htmlHash"] = response_server_memo.get("htmlHash") or new_server_memo["htmlHash"]
        new_server_memo["checksum"] = response_server_memo.get("checksum") or new_server_memo["checksum"]

        # The "dirty" list tells the attributes on serverMemo.data that need to be updated
        for dirty_path in dirty_attrs:
            source = response_server_memo["data"]
            target = new_server_memo["data"]
            path_parts = dirty_path.split(".")
            for part in path_parts[:-1]:
                source = source[part]
                target = target[part]
            part = path_parts[-1]
            target[part] = source[part]

        # There's no real _need_ to keep all the past server memos, but it's useful for debugging purposes, and I'm
        # not using this heavily at the moment where I'm worried about the memory usage of this.
        self.server_memos.append(new_server_memo)

    @staticmethod
    def generate_call_id() -> str:
        """
        Generate the "id" for the update.

        The following JavaScript is used to generate these on ReaperScans page
        (comes from Laravel or livewire.js):

            (Math.random() + 1).toString(36).substring(8)

        This is my approximation of that in Python... for shits and giggles as it just seems to
        need to be a 3-4 character unique string.
        """
        return int2base(random.randint(100000, 999999), 36)

    def _load_data(self, element: Tag) -> None:
        """
        Load the wire:id and wire:initial-data from the pass-in element.

        :param element: An HTML element that should have wire:id and wire:initial-data attributes set.
        """
        if element["wire:id"] != self.wire_id:
            raise ValueError(f"LiveWire ID passed in does not match wire:id value on element.")

        if "wire:initial-data" not in element.attrs:
            raise ValueError(f"wire:initial-data not defined on element for wire:id={self.wire_id}")

        self.initial_data_raw = element["wire:initial-data"]
        self.initial_data = json.loads(self.initial_data_raw)

    def __repr__(self):
        """Implement repr() output that's useful to the user."""
        return (
            f"{self.__class__.__name__}("
            f"app_url={self.app_url!r}, "
            f"wire_id={self.wire_id!r}, "
            # f"element={self._element!r}, "
            f"csrf_token={self.csrf_token!r}, "
            f"referer_url{self._referer_url!r}, "
            f"client={self._client!r}"
            f")"
        )

    def __str__(self):
        """Stringify in an even simpler way that __repr__."""
        return f"{self.__class__.__name__}({self.wire_id} // {self.component_name})"
