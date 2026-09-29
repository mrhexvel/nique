from __future__ import annotations

import json

from nique.features.auth.captcha import VKNotRobotChallengeProvider
from nique.features.auth.verification import AuthChallenge
from nique.shared.http.fake import FakeTransport
from nique.shared.http.response import HttpResponse


def json_response(payload: object) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps(payload).encode())


async def test_not_robot_solver_completes_pow_and_sensor_flow() -> None:
    transport = FakeTransport(
        [
            HttpResponse(
                200,
                {},
                b'<script>(function(a,b,c){window["captchaPowResult"]="";}'
                b'("proof",0,"pow_timeout"))</script>',
            ),
            json_response({"response": 1}),
            json_response({"response": {"bridge_sensors_list": ["mouse", "screen"]}}),
            json_response({"response": {"success_token": "solved"}}),
            json_response({"response": 1}),
        ]
    )
    provider = VKNotRobotChallengeProvider(transport)

    result = await provider.resolve(
        AuthChallenge(
            type="captcha",
            sid="sid",
            url=(
                "https://id.vk.ru/not_robot_captcha"
                "?domain=vk.com&session_token=session&variant=popup"
            ),
        )
    )

    assert result.success_token == "solved"
    assert transport.requests[3].data is not None
    assert transport.requests[3].data["mouse"] == "[]"
    assert transport.requests[3].data["screen"] == "[]"
    assert transport.requests[3].data["answer"] == "e30="
    assert str(transport.requests[3].data["hash"]).startswith("v2.")
