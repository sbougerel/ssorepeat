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
"""CLI entry point for ssorepeat"""
import sys
import json

from botocore.exceptions import TokenRetrievalError, ProfileNotFound


from ssorepeat.help import USAGE, DOCUMENTATION
from ssorepeat.parse_arguments import (
    parse_arguments,
    InvalidArgument,
    MissingArgumentParameter,
)
from ssorepeat.ssosession import SsoSession, InvalidSsoProfile
from ssorepeat.filter import filter_accounts
from ssorepeat.executor import Executor


def perror(*args, **kwargs) -> None:
    """Print to stderr"""
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def run() -> int:
    """Main entry point for the CLI"""
    try:
        show_help, profile_arg, filter_args, command_args = parse_arguments(sys.argv)
    except InvalidArgument as exc:
        perror(exc)
        perror(USAGE)
        return 1
    except MissingArgumentParameter as exc:
        perror(exc)
        perror(USAGE)
        return 1

    if show_help:
        print(DOCUMENTATION)
        return 0

    try:
        session = SsoSession(profile=profile_arg)
    except InvalidSsoProfile as exc:
        perror(exc)
        perror("Hint: did you forget to specify the '--profile' argument?")
        return 2
    except ProfileNotFound as exc:
        perror(exc)
        perror("Hint: typo in the parameter to '--profile'?")
        return 2
    except TokenRetrievalError as exc:
        perror(exc)
        perror(
            "Hint: try logging in again with 'aws --profile PROFILE sso login'",
        )
        return 2

    associations = filter_accounts(
        filter_args, session.get_accounts(), str(session.get_default_role_name())
    )

    executor = Executor(session)
    if len(command_args) == 0 or command_args[0] == "list":
        executor.list_associations(associations)
    elif command_args[0] == "creds":
        executor.fetch_credentials(associations)
    elif command_args[0] == "exec":
        executor.run_sequence(command_args[1:], associations)

    return 0
