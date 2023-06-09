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
"""Help text for the CLI"""
USAGE = "Usage: ssorepeat [--help] [--profile PROFILE] [FILTERS] [COMMAND [ARGS]]"
DOCUMENTATION = """ssorepeat

    `ssorepeat` repeats execution of `COMMAND` across AWS accounts selected via
    `FILTERS` when logged in a Single Sign-On (SSO) session. Use `--profile
    PROFILE` to select session credentials for `botocore.session`. `ssorepeat`
    writes the results of `COMMAND` as a JSON on the standard output.

    Usage:
        ssorepeat [--help] [--profile PROFILE] [FILTERS] [COMMAND [ARGS]]

    Example:
        ssorepeat --profile PROFILE exec aws s3 ls

    The above example will spawn subprocesses running "aws s3 ls" in all
    accounts available via the SSO session and role found in PROFILE.

    When "exec ARGS..." is not specified, the script will instead list all
    accounts available.

    DANGER: USING ssorepeat WITH A WRITE OPERATION IS NOT RECOMMENDED AND CAN
    HAVE DIRE CONSEQUENCES ACROSS THE ENTIRE INFRASTRUCTRE, YOU HAVE BEEN
    WARNED.

Arguments:

    [--help]

        Prints this help. This argument is only taken into account if it appears
        before "exec" or immediately after it. Otherwise it is passed to the
        subcommand instead.

    [--profile PROFILE]

        Always the first option. The profile to use for the botocore SSO
        session. If profile is not specified, botocore session is created with a
        profile parameter being None. See botocore session documentation.

    [FILTERS]

        A set of sequential conditions to select accounts and roles for
        commands. See "Filters:" for details.

    [COMMANDS]

        Either "list" (default), "exec ARGS..." or "creds". With "list", the
        program returns a list of accounts and roles according to the conditions
        defined in FILTERS. See "Commands:" for details.

Configuration:

    The script assume that `~/.aws/config` is configured with a valid SSO
    section, and that you have already logged in. A typical AWS SSO
    configuration looks like this (ACCOUNTID, ROLE, SSO_SESSION, SUBDOMAIN are
    placeholders):

        [profile ROLE-ACCOUNTID]
        sso_session = SSO_SESSION
        sso_account_id = ACCOUNTID
        sso_role_name = ROLE
        region = ap-southeast-1
        [sso-session SSO_SESSION]
        sso_start_url = https://SUBDOMAIN.awsapps.com/start#
        sso_region = ap-southeast-1
        sso_registration_scopes = sso:account:access

    When configured as such, you can use `ssorepeat` in the following sequence
    of commands:

        aws sso login --profile ROLE-ACCOUNTID
        ssorepeat --profile ROLE-ACCOUNTID s3 ls

How it works:

    `ssorepeat` uses `botocore.session` package to find the `sso_session` and
    `sso_role_name` configured for the profile, as well as the corresponding
    session token. Using the session token, it fetches temporary AWS
    credientials for each execution of command, across all accounts and
    roles selected by `FILTERS`.

    `ssorepeat` provides the temporary AWS credentials to each subprocess via
    the environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and
    AWS_SESSION_TOKEN. Thus it is possible to use `ssorepeat` to run any command
    or scripts that uses the AWS SDK, `botocore`, `boto3`, etc.

    If the profile does not correspond to an SSO session, however, it returns an
    error.

Filters:

    The filters are sequential in nature, so the order in which arguments
    appears matter (e.g. similar to GNU `find`). Filters are designed to narrow
    the pairs of account/role selected for the command. Filters work on an array
    of accounts called the "buffer". Accounts in the buffer can be associated
    with roles, which causes all valid account/role pairs to be copied to the
    resulting array, exhausting the buffer. Commands are executed on the
    resulting array of account/roles pairs.

    [--reset]

        Resets the buffer array to its original state.

    [--include-only REGEX]

        Remove from buffer any account ID for which account name does not match
        with REGEX specified as argument. Opposite of [--exclude REGEX].

    [--exclude REGEX]

        Remove from buffer any account ID for which account name matches with
        REGEX. Opposite of [--include-only REGEX].

    [--assoc ROLES,...]

        Appends the content of the buffer array to the final array for all
        account/role pairs where any of the roles in ROLES,... exists. Multiple
        roles can be selected in this way. This filter will empty the buffer,
        use [--reset] to refill the buffer.

    [--assoc-default]

        Appends the content of the buffer array to the final array for all
        account/role pairs where the default role (the one from PROFILE) exists.
        This filter will empty the buffer, use [--reset] to refill the buffer.
        This filter is always added at the queue of any sequence of filters
        (even an empty sequence).

Commands:

    "list" (default command) helps you ensure that you've selected the correct
    account/role pairs.

    "creds" generates credentials for each of the account/role pair selected, if
    you want to do the work yourself.

    "exec", finally, executes the command in subprocesses and return its
    standard and error output for each account/role pair in a JSON object. It's
    recommanded to always use "list" first.

Examples:

        ssorepeat --profile PROFILE \\
            --exclude "\\b[pP]layground\\b" \\
            --exclude "\b[Ss][Tt][Gg]\\b" \\
            --exclude "\\b[S]taging\\b" \\
            exec aws s3 ls

    Will execute "aws s3 ls" in all accounts/role pairs where the account name
    does not contain words such as "playground", "STG" or "Staging".

        ssorepeat --profile PROFILE \\
            --include-only "\\b[pP]layground\\b" \\
            --assoc ROLE1 \\
            --reset \\
            --include-only "\\b[Ss][Tt][Gg]\\b" \\
            --assoc ROLE2 \\
            exec aws s3 ls

    Will execute "aws s3 ls" first in accounts/role pairs where the account name
    has words such as "playground" and where ROLE1 exists, then in account/role
    pairs where the account name has words such as STG and where ROLE2 exists."""
