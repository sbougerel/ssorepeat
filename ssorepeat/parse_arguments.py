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
"""Parses arguments from the command line.

Arguments come in 3 optional groups that follow the sequence:

    ssorepeat [<profile>] [<filters>] [<commands>]

The only odd one out is the "--help" argument, which has a special rule: it is
interpreted as the program's help so long as it is placed before the second
token in the `<command>` group (since the first token is the command itself).
Example:

    ssorepeat exec --help aws s3 ls

        This command will show `ssorepeat` help.

    ssorepeat exec aws s3 ls --help

        This command will execute `aws s3 ls --help` across all account.

The 2 groups `<filters>` and `<commands>` accept multiple tokens. The parser
validates each sequence of token.

"""

# Considered using the public `argparse` package but it wouldn't really help
# reduce the code in this case, given all the positional arguments.
from typing import Optional, Tuple


class InvalidArgument(Exception):
    """When --profile is given without any other parameters."""

    def __init__(self, arg: str, pos: int):
        self.arg = arg
        self.pos = pos
        super().__init__(f"Unexpected argument '{arg}' encountered in position {pos}")


class MissingArgumentParameter(Exception):
    """When an argument is missing a parameter."""

    def __init__(self, arg: str):
        self.arg = arg
        super().__init__(
            f"The argument '{arg}' expects a parameter but none was specified"
        )


def _has_parameter_or_throw(argv: list[str], arg: str) -> bool:
    """Returns True if the arg is at the start of argv but throw if argv is
    empty after that."""
    if argv[0] != arg:
        return False
    if len(argv) == 1:
        raise MissingArgumentParameter(arg)
    return True


def _parse_help(argv) -> bool:
    """Handle --help if it appears before "exec" or immediately after it."""
    show_help = False
    try:
        help_pos = argv.index("--help")
        show_help = True
        exec_pos = argv.index("exec", 0, help_pos)
        show_help = exec_pos == help_pos - 1
    except ValueError:
        pass
    return show_help


def _parse_profile(argv) -> tuple[int, Optional[str]]:
    """--profile PROFILE is either first or it isn't."""
    profile = None
    consume = 0
    if len(argv) > 0 and _has_parameter_or_throw(argv, "--profile"):
        profile = argv[1]
        consume = 2
    return consume, profile


def _parse_filters(argv) -> tuple[int, list[str]]:
    """Parse the filters from argv."""
    filters = []
    consume = 0
    while len(argv) > 0:
        if _has_parameter_or_throw(argv, "--include-only"):
            consume += 2
            filters += argv[0:2]
            argv = argv[2:]
        elif _has_parameter_or_throw(argv, "--exclude"):
            consume += 2
            filters += argv[0:2]
            argv = argv[2:]
        elif _has_parameter_or_throw(argv, "--assoc"):
            consume += 2
            filters += argv[0:2]
            argv = argv[2:]
        elif argv[0] == "--assoc-default":
            consume += 1
            filters += argv[0:1]
            argv = argv[1:]
        elif argv[0] == "--reset":
            consume += 1
            filters += argv[0:1]
            argv = argv[1:]
        else:
            break
    return consume, filters


def _parse_commands(argv) -> tuple[int, list[str]]:
    """Parse the commands from argv."""
    commands = []
    consume = 0
    if len(argv) > 0:
        if argv[0] == "exec":
            consume += len(argv)
            commands = argv
            argv = []
        elif argv[0] == "list":
            consume += 1
            commands += argv[0:1]
            argv = argv[1:]
        elif argv[0] == "creds":
            consume += 1
            commands += argv[0:1]
            argv = argv[1:]
    return consume, commands


def parse_arguments(argv) -> Tuple[bool, Optional[str], list[str], list[str]]:
    """Parse argv into show_help, profile, filters, and commands."""
    profile = None
    filters: list[str] = []
    commands: list[str] = []

    # Skip the first argument, it's the program name
    argv = argv[1:]
    consumed = 0

    if _parse_help(argv):
        return True, profile, filters, commands

    consume, profile = _parse_profile(argv)
    consumed += consume
    argv = argv[consume:]

    consume, filters = _parse_filters(argv)
    consumed += consume
    argv = argv[consume:]

    consume, commands = _parse_commands(argv)
    consumed += consume
    argv = argv[consume:]

    # Leftovers are mistakes
    if len(argv) > 0:
        raise InvalidArgument(argv[0], consumed + 1)

    return False, profile, filters, commands
