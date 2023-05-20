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
"""Filter module: create a list of account/role associations from a list of
accounts and a list of filters (given in arguments).
"""
from typing import Optional

import re


class UnexpectedFilterArgument(Exception):
    """When Filter is given an unexpected argument."""

    def __init__(self, arg: str):
        self.arg = arg
        super().__init__(f"Unexpected argument '{arg}'")


class MissingFilterParameter(Exception):
    """When a filter is missing an parameter."""

    def __init__(self, arg: str):
        self.arg = arg
        super().__init__(
            f"The filter '{arg}' expects a parameter but none was specified"
        )


def _has_parameter_or_throw(argv: list[str], arg: str) -> bool:
    """Returns True if the arg is at the start of argv but throw if argv is empty after that."""
    if argv[0] != arg:
        return False
    if len(argv) == 1:
        raise MissingFilterParameter(arg)
    return True


def _buf_include_only(
    buf: list[dict[str, str]], regex_str: str
) -> list[dict[str, str]]:
    """Remove accounts from `buf` that do not match `regex_str`."""
    new_buf = []
    regex = re.compile(regex_str)
    for account in buf:
        if regex.search(account["accountName"]):
            new_buf.append(account)
    return new_buf


def _buf_exclude(buf: list[dict[str, str]], regex_str: str) -> list[dict[str, str]]:
    """Remove accounts from `buf` that match `regex_str`."""
    new_buf = []
    regex = re.compile(regex_str)
    for account in buf:
        if not regex.search(account["accountName"]):
            new_buf.append(account)
    return new_buf


def _result_associate(
    buf: list[dict[str, str]], role_names: str
) -> list[dict[str, str]]:
    """Return an array with the given role associated with each account in the buffer."""
    result = []
    for account in buf:
        for role_name in role_names.split(","):
            result.append(
                {
                    "accountName": account["accountName"],
                    "accountId": account["accountId"],
                    "role": role_name,
                }
            )
    return result


def filter_accounts(
    filters: list[str], accounts: list[dict[str, str]], default_role: str
) -> list[dict[str, str]]:
    """Returns a list of account/role association, together with the account
    name.

    The object returned has the form:

    [
        {
            "accountName": "Account Name"",
            "accountId": "123456789012",
            "role": "Role Name",
        },
        ...
    ]

    This list is not guaranteed to hold valid account/role associations.
    Commands will validate associations depending on their tasks.

    """
    acc_buf = accounts
    result = []

    argv = filters
    while len(argv) > 0:
        if _has_parameter_or_throw(argv, "--include-only"):
            acc_buf = _buf_include_only(acc_buf, argv[1])
            argv = argv[2:]
        elif _has_parameter_or_throw(argv, "--exclude"):
            acc_buf = _buf_exclude(acc_buf, argv[1])
            argv = argv[2:]
        elif _has_parameter_or_throw(argv, "--assoc"):
            result += _result_associate(acc_buf, argv[1])
            acc_buf = []
            argv = argv[2:]
        elif argv[0] == "--assoc-default":
            result += _result_associate(acc_buf, default_role)
            acc_buf = []
            argv = argv[1:]
        elif argv[0] == "--reset":
            acc_buf = accounts
            argv = argv[1:]
        else:
            # Not supposed to happen, since we already parsed the arguments
            raise UnexpectedFilterArgument(argv[0])

    result += _result_associate(acc_buf, default_role)
    return result
