# awsudo
sudo-like utility to manage AWS credentials

Ever wish you could easily provide your AWS credentials to applications when
necessary, but not have them sitting around in environment variables when they
aren't needed? Want to avoid putting your credentials in disparate
configuration files for each tool you use?

`awsudo` works just like sudo: stick it before a command to run that command in
a context that has access to your AWS credentials. Say you wrote a great script
to deploy your project, but it needs an AWS API key to work:

    awsudo ./aws_deployment_script

Most tools will attempt to get credentials from [environment variables].
`awsudo` reads the same configuration files as the [AWS CLI], and then runs the
command you specify with those environment variables set.

Do you have multiple accounts? `awsudo` also understands [named profiles]. If a
profile is configured to [assume a role], `awsudo` can do that also, meaning
you can easily use [temporary credentials] with most AWS tools. To use the
profile `deployment`:

    awsudo -u deployment ./aws_deployment_script

  [environment variables]: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-environment
  [AWS CLI]: http://aws.amazon.com/cli/
  [named profiles]: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-multiple-profiles
  [assume a role]: http://docs.aws.amazon.com/cli/latest/userguide/cli-roles.html
  [temporary credentials]: http://docs.aws.amazon.com/STS/latest/UsingSTS/Welcome.html
