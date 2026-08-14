# SPDX-License-Identifier: GPL-3.0-or-later

import os

import pytest


@pytest.fixture(scope="session")
def uci_config_default_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "uci_configs")


@pytest.fixture(scope="session")
def cmdline_script_root():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_root")


@pytest.fixture(scope="session")
def file_root():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files")


@pytest.fixture(scope="module")
def controller_modules():
    return ["matter"]


def pytest_addoption(parser):
    parser.addoption(
        "--backend",
        action="append",
        default=[],
        help="Set test backend here. available values = (mock, openwrt)",
    )
    parser.addoption(
        "--message-bus",
        action="append",
        default=[],
        help="Set test bus here. available values = (unix-socket, ubus, mqtt)",
    )
    parser.addoption("--debug-output", action="store_true", help="Print debug output.")
