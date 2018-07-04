# Really Quickstart

```console
$ bash <(curl https://raw.githubusercontent.com/makethunder/awsudo/master/install)
```

For a somewhat more broad introduction to what can be accomplished, read on...

# Quick Tutorial

Install it:

```console
$ pip install --user git+https://github.com/makethunder/awsudo.git
```

The `--user` option asks `pip` to install to your home directory, so you might
need to add that to `$PATH`:

```console
$ echo 'export PATH="$(python -m site --user-base)/bin:${PATH}"' >> ~/.bashrc
$ source ~/.bashrc
```

Configure `aws` if you haven't already, substituting your own credentials and
preferences:

```console
$ aws configure
AWS Access Key ID [None]: AKIAIXAKX3ABKZACKEDN
AWS Secret Access Key [None]: rkCLOMJMx2DbGoGySIETU8aRFfjGxgJAzDJ6Zt+3
Default region name [None]: us-east-1
Default output format [None]: table
```

Now you have a basic configuration in `~/.aws/`. [Some tools will read this
configuration][credentials], but for less enlightened tools that only read from
environment variables, you can invoke them with `awsudo`:

```console
$ awsudo env | grep AWS
AWS_ACCESS_KEY_ID=AKIAIXAKX3ABKZACKEDN
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=rkCLOMJMx2DbGoGySIETU8aRFfjGxgJAzDJ6Zt+3
```

It's been a while, and you want to rotate your API keys according to [best
practices]. Or maybe you were doing a presentation and accidentally flashed your
credentials to the audience. Oops! Just one command rotates your keys and
updates your configuration:

```console
$ awsrotate
```

If you want to rotate your key every day at 5:26 AM automatically, you might
ask [cron](https://en.wikipedia.org/wiki/Cron) to run `awsrotate` for you, like
so:

```console
$ (crontab -l; echo "26 05 * * * $(which awsrotate)") | crontab -
```

Maybe you have separate development and production accounts, and you need to
[assume a role] to use them? You might a section like this to `~/.aws/config`
for each account, substituting your own [account number] and role name:

```
[profile development]
role_arn = arn:aws:iam::123456789012:role/development
source_profile = default
region = us-east-1
```

Now you can use the `-u PROFILE_NAME` option to have `awsudo` assume that role,
and put those [temporary credentials] in the environment:

```console
$ awsudo -u development env | grep AWS
AWS_ACCESS_KEY_ID=AKIAIXAKX3ABKZACKEDN
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=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
AWS_SESSION_TOKEN=AQoDYXdzEBcaoAKIYnZ67+8/BzPkkpbpR3yfv9bAQoDYXdzEBcaoAKIYnZ67+8/BzPkkpbpR3yfv9b
AWS_DEFAULT_REGION=us-east-1
```

Maybe assuming that role [requires MFA]? Just add that to the configuration and
`awsudo` will prompt you for your MFA code when necessary. Example:

```
[profile development]
role_arn = arn:aws:iam::123456789012:role/development
source_profile = default
region = us-east-1
mfa_serial = arn:aws:iam::98765432100:mfa/phil.frost
```

The `mfa_serial` option should correspond to an MFA device in the account
referenced by `source_profile`.

Many more configurations are possible. See the [AWS CLI guide] for more detail.
`awsudo` uses the same code as `aws` to find and resolve credentials and so
works identically.

## Testing

We recommend using pyenv as our tests run on 2.7 and 3.4.

```bash
pyenv install 2.7 && pyenv install 3.4.8
pyenv local 2.7 3.4.8
eval "$(pyenv init -)"
pyenv rehash
tox
```

  [credentials]: http://blogs.aws.amazon.com/security/post/Tx3D6U6WSFGOK2H/A-New-and-Standardized-Way-to-Manage-Credentials-in-the-AWS-SDKs
  [best practices]: http://docs.aws.amazon.com/general/latest/gr/aws-access-keys-best-practices.html
  [assume a role]: http://docs.aws.amazon.com/cli/latest/userguide/cli-roles.html
  [temporary credentials]: http://docs.aws.amazon.com/STS/latest/UsingSTS/Welcome.html
  [account number]: http://docs.aws.amazon.com/general/latest/gr/acct-identifiers.html
  [requires MFA]: http://docs.aws.amazon.com/cli/latest/userguide/cli-roles.html#cli-roles-mfa
  [AWS CLI guide]: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
