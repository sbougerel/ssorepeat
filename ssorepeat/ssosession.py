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
from typing import Optional
from functools import lru_cache

import botocore.session
import boto3


class InvalidSsoProfile(Exception):
    """The AWS profile used is not a Single Sign-On profile.

    Attributes:
        profile -- name of the profile used
        message -- explanation of the error
    """

    def __init__(self, profile: Optional[str], field: str) -> None:
        self.profile = profile
        super().__init__(
            f"Excepted single sign-on '{profile}' but the field '{field}' is missing"
        )


class SsoSession:
    """Represent a Single Sign-On session. This is a thin wrapper around
    botocore.session.Session.

    Most calls are cached, except calls for credentials, as they should each be
    needed only once.

    """

    def __init__(self, profile: Optional[str]) -> None:
        self._session = None
        self._config = None
        self._auth_token = None

        session = botocore.session.Session(profile=profile)
        config = session.get_scoped_config()

        if "sso_session" not in config:
            raise InvalidSsoProfile(profile, "sso_session")

        if "sso_role_name" not in config:
            raise InvalidSsoProfile(profile, "sso_role_name")

        self._auth_token = session.get_auth_token().get_frozen_token()
        self._session = session
        self._config = config

    def _get_token(self) -> Optional[str]:
        if self._auth_token is None:
            return None
        return self._auth_token.token

    def get_default_role_name(self) -> Optional[str]:
        """Return the default role name for this profile.

        None if config is not set.

        """
        if self._config is None:
            return None
        return self._config["sso_role_name"]

    @lru_cache
    def get_accounts(self) -> list[dict[str, str]]:
        """Return a list of accounts, of the form:

        [
            {
                "accountId": "123456789012",
                "accountName": "Account Name",
                "emailAddress": "accounts@email.address",
            },
            ...
        ]

        """
        accounts = []
        sso_client = boto3.Session(botocore_session=self._session).client("sso")
        list_accounts_paginator = sso_client.get_paginator("list_accounts")
        for response in list_accounts_paginator.paginate(accessToken=self._get_token()):
            if "accountList" in response:
                accounts += response["accountList"]

        return accounts

    @lru_cache
    def get_account_roles(self, account_id: str) -> list[dict[str, str]]:
        """Return a list of roles, of the form:

        [
            {
                "roleName": "string",
                "accountId": "string"
            },
            ...
        ]

        """
        roles = []
        sso_client = boto3.Session(botocore_session=self._session).client("sso")
        list_account_roles_paginator = sso_client.get_paginator("list_account_roles")
        for response in list_account_roles_paginator.paginate(
            accountId=account_id, accessToken=self._get_token()
        ):
            if "roleList" in response:
                roles += response["roleList"]
        return roles

    def get_credentials(self, account_id: str, role_name: str) -> dict[str, str]:
        """Return a dict of credentials, of the form:

        {
            "accessKeyId": "string",
            "secretAccessKey": "string",
            "sessionToken": "string",
            "expiration": 123
        }

        """
        sso_client = boto3.Session(botocore_session=self._session).client("sso")
        response = sso_client.get_role_credentials(
            roleName=role_name, accountId=account_id, accessToken=self._get_token()
        )
        return response["roleCredentials"]
