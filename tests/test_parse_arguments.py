#!/usr/bin/env python3

import pytest

from ssorepeat.parse_arguments import (
    parse_arguments,
    InvalidArgument,
    MissingArgumentParameter,
)


def test_empty_args():
    argv = ["command"]
    assert parse_arguments(argv) == (False, None, [], [])


def test_help():
    argv = ["command", "--help"]
    assert parse_arguments(argv) == (True, None, [], [])


def test_help_before_exec():
    argv = ["command", "--help", "exec", "command"]
    assert parse_arguments(argv) == (True, None, [], [])


def test_help_after_exec():
    argv = ["command", "exec", "--help", "command"]
    assert parse_arguments(argv) == (True, None, [], [])


def test_help_way_after_exec():
    argv = ["command", "exec", "command", "--help"]
    assert parse_arguments(argv) == (False, None, [], ["exec", "command", "--help"])


def test_missing_profile_parameter():
    with pytest.raises(MissingArgumentParameter) as exc:
        argv = ["command", "--profile"]
        parse_arguments(argv)
    assert exc.value.arg == "--profile"


def test_uknown_command():
    with pytest.raises(InvalidArgument) as exc:
        argv = ["command", "unknown"]
        parse_arguments(argv)
    assert exc.value.arg == "unknown"
    assert exc.value.pos == 1
