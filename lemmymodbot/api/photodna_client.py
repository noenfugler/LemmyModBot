from dataclasses import dataclass

import requests
from pykson import JsonObject, StringField, BooleanField, Pykson


@dataclass
class PhotoDNARequest(JsonObject):
    data_representation = StringField(serialized_name="DataRepresentation")
    value = StringField(serialized_name="Value")


@dataclass
class PhotoDNAResponse:
    is_match = BooleanField(serialized_name="IsMatch")


class PhotoDNAClient:
    base_url: str = "https://api.microsoftmoderator.com/photodna"
    api_key: str
    pykson: Pykson

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.pykson = Pykson()

    def _do_match(self, request: PhotoDNARequest) -> PhotoDNAResponse:
        return self.pykson.from_json(requests.post(
            f"{self.base_url}/Match",
            data=self.pykson.to_json(request),
            headers={
                "Ocp-Apim-Subscription-Key": self.api_key
            }
        ).content.decode("utf-8"), PhotoDNAResponse)

    def check_url(self, url: str) -> PhotoDNAResponse:
        request = PhotoDNARequest()
        request.data_representation = "URL"
        request.value = url
        return self._do_match(
            request
        )
