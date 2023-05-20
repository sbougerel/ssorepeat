# ssorepeat
---

Execute commands across multiple AWS accounts available via single sign-on
(SSO).

## Quick start

``` sh
aws --profile some-profile sso login
ssorepeat --profile some-profile \
  --include-only "\b[Dd]emo\b" \
  exec aws s3 ls
```

After SSO login, `ssorepeat` will run `aws s3 ls` in all accounts whose name
contains the word "Demo" or "demo", using the default SSO role setup for this
profile.

## Installation

[Get poetry](https://python-poetry.org/docs/#installation):

``` sh
curl -sSL https://install.python-poetry.org | python3 -
```

Add it to your `$PATH` then proceed into the repository:

``` sh
poetry build
pip install .
cp bin/ssorepeat ~/.local/bin
```

If you don't like to pollute your own local python environment and only need it
temporarily, a quick and dirty way is to move `bin/ssorepeat` to the
repository's root and renaming it:

``` sh
cp bin/ssorepeat ssorepeat.sh
chmod a+x ssorepeat.sh
./assorepeat.sh --help
```

## Documentation

``` sh
ssorepeat --help
```

---
`ssorepeat` is free software provided as-is under the terms of the Apache
License, version 2.0. This software and its authors are not affiliated to AWS.
