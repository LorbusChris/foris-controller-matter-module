# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests over the message bus.

The one behaviour worth pinning down is the pairing code: it authenticates only
while a commissioning window is open, so it must not be handed out at any other
time. A frontend developed against a backend that always returned it would show
a code that does not work.
"""

from foris_controller_backends.matter import MatterQr


def test_get_onboarding(infrastructure):
    res = infrastructure.process_message(
        {"module": "matter", "action": "get_onboarding", "kind": "request"}
    )
    assert "present" in res["data"]


def test_pairing_code_only_while_a_window_is_open(infrastructure):
    infrastructure.process_message(
        {"module": "matter", "action": "close_window", "kind": "request"}
    )
    data = infrastructure.process_message(
        {"module": "matter", "action": "get_onboarding", "kind": "request"}
    )["data"]
    if not data.get("live"):
        return
    assert data["window"] == "closed"
    assert "manual_code" not in data
    assert "qr" not in data

    infrastructure.process_message(
        {"module": "matter", "action": "open_window", "kind": "request"}
    )
    data = infrastructure.process_message(
        {"module": "matter", "action": "get_onboarding", "kind": "request"}
    )["data"]
    assert data["window"] in ("basic", "enhanced")
    assert data.get("manual_code")

    infrastructure.process_message(
        {"module": "matter", "action": "close_window", "kind": "request"}
    )


def test_window_notifications(infrastructure):
    filters = [("matter", "window")]
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {"module": "matter", "action": "open_window", "kind": "request"}
    )
    if res["data"]["error"]:
        return
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1]["action"] == "window"

    infrastructure.process_message(
        {"module": "matter", "action": "close_window", "kind": "request"}
    )


def test_remove_unknown_fabric_changes_nothing(infrastructure):
    before = infrastructure.process_message(
        {"module": "matter", "action": "get_onboarding", "kind": "request"}
    )["data"].get("fabrics")
    infrastructure.process_message(
        {"module": "matter", "action": "remove_fabric", "kind": "request", "data": {"index": 254}}
    )
    after = infrastructure.process_message(
        {"module": "matter", "action": "get_onboarding", "kind": "request"}
    )["data"].get("fabrics")
    assert before == after


#
# QR payload handling -- no daemon involved.
#


def test_qr_rejects_anything_that_is_not_an_onboarding_payload():
    """The payload reaches a shell command, so its alphabet is checked first."""
    assert MatterQr.svg(None) is None
    assert MatterQr.svg("") is None
    assert MatterQr.svg("http://example.invalid") is None
    assert MatterQr.svg("MT:lowercase") is None
    assert MatterQr.svg("MT:ABC; rm -rf /") is None
