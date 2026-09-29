from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from nique.shared.http.response import HttpResponse


@dataclass(frozen=True, slots=True)
class RecordedRequest:
    method: str
    url: str
    params: Mapping[str, object] | None
    data: Mapping[str, object] | None
    headers: Mapping[str, str] | None
    timeout: float | None


class FakeTransport:
    """Deterministic in-memory transport for tests and local integrations."""

    def __init__(self, responses: Iterable[HttpResponse] = ()) -> None:
        self._responses = deque(responses)
        self.requests: list[RecordedRequest] = []
        self.closed = False

    def enqueue(self, response: HttpResponse) -> None:
        self._responses.append(response)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        data: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        self.requests.append(RecordedRequest(method, url, params, data, headers, timeout))
        if not self._responses:
            raise AssertionError("FakeTransport has no queued response")
        return self._responses.popleft()

    async def aclose(self) -> None:
        self.closed = True
