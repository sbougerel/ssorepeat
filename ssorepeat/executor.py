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
import subprocess
import json
import sys
import os

from typing import Protocol, Optional


class SsoManager(Protocol):
    """A protocol for SsoManager"""

    def get_credentials(
        self, account_id: str, role_name: str
    ) -> Optional[dict[str, str]]:
        ...

    def get_account_roles(self, account_id: str) -> list[dict[str, str]]:
        ...


class Executor:
    """Provide functions to run the command"""

    def __init__(self, session: SsoManager) -> None:
        self.session = session

    def list_associations(self, associations: list[dict[str, str]]) -> None:
        """list all valid association by checking if roles exist in account.

        Results are writen to stdout as a JSON string.

        """
        sys.stdout.write("[")
        first = True
        for assoc in associations:
            roles = self.session.get_account_roles(assoc["accountId"])
            if assoc["role"] not in [role["roleName"] for role in roles]:
                continue
            if first:
                first = False
            else:
                sys.stdout.write(",")
            json.dump(assoc, sys.stdout)
            sys.stdout.flush()
        sys.stdout.write("]\n")

    def fetch_credentials(self, associations: list[dict[str, str]]) -> None:
        """Return credentials for each valid association.

        Results are writen to stdout as a JSON string.

        """
        sys.stdout.write("[")
        first = True
        for assoc in associations:
            credentials = self.session.get_credentials(
                assoc["accountId"], assoc["role"]
            )
            if credentials is None:
                continue
            if first:
                first = False
            else:
                sys.stdout.write(",")
            json.dump(
                {
                    "accountName": assoc["accountName"],
                    "accountId": assoc["accountId"],
                    "role": assoc["role"],
                    "accessKeyId": credentials["accessKeyId"],
                    "secretAccessKey": credentials["secretAccessKey"],
                    "sessionToken": credentials["sessionToken"],
                },
                sys.stdout,
            )
            sys.stdout.flush()
        sys.stdout.write("]\n")

    def run_sequence(
        self, command_args: list[str], associations: list[dict[str, str]]
    ) -> None:
        """Run `command_args` for each valid `associations`

        Results are writen to stdout as a JSON string.

        """
        # Why not just print the JSON directly? Because I wanted to print
        # command outputs as it happens to make the program feel more
        # "responsive". This is a bit of a hack, but it works.
        sys.stdout.write("[")
        first = True
        for assoc in associations:
            credentials = self.session.get_credentials(
                assoc["accountId"], assoc["role"]
            )
            if credentials is None:
                continue
            if first:
                first = False
            else:
                sys.stdout.write(",")
            self.run_subprocess(command_args, assoc, credentials)
            sys.stdout.flush()
        sys.stdout.write("]\n")

    def run_subprocess(
        self,
        command_args: list[str],
        assoc: dict[str, str],
        credentials: dict[str, str],
    ) -> None:
        """Run `command_args` with `credentials`

        Results are writen to stdout as a JSON string.

        """
        environ = os.environ.copy()
        environ["AWS_ACCESS_KEY_ID"] = credentials["accessKeyId"]
        environ["AWS_SECRET_ACCESS_KEY"] = credentials["secretAccessKey"]
        environ["AWS_SESSION_TOKEN"] = credentials["sessionToken"]

        result = subprocess.run(
            command_args,
            env=environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        json.dump(
            {
                "accountName": assoc["accountName"],
                "accountId": assoc["accountId"],
                "role": assoc["role"],
                "exitCode": result.returncode,
                "stdout": result.stdout.decode("utf-8"),
                "stderr": result.stderr.decode("utf-8"),
            },
            sys.stdout,
        )
