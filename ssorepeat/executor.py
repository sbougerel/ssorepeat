import subprocess
import json
import sys
import os

from typing import Optional

from botocore.exceptions import ClientError

from ssorepeat.ssosession import SsoSession


class Executor:
    """Provide functions to run the command"""

    def __init__(self, session: SsoSession) -> None:
        self.session = session

    def _get_credentials(
        self,
        assoc: dict[str, str],
    ) -> Optional[dict[str, str]]:
        try:
            credentials = self.session.get_credentials(
                assoc["accountId"], assoc["role"]
            )
        except ClientError as exc:
            # Ignore this exception: this account/role association is invalid
            if exc.response["Error"]["Code"] == "ForbiddenException":
                return None
            raise
        return credentials

    def list_associations(self, associations: list[dict[str, str]]) -> None:
        """list all valid association by checking if roles exist in account.

        Results are writen to stdout as a JSON string.

        """
        sys.stdout.write("[")
        first = True
        for assoc in associations:
            # This is cached already
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
            credentials = self._get_credentials(assoc)
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
            credentials = self._get_credentials(assoc)
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
