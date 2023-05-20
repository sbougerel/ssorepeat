# Copyright 2023 Sylvain Bougerel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
