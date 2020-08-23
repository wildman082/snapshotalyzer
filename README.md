# snapshotalyzer

acloud.guru project to manage snapshot instances

## About

This project uses boto3 to manage AWS ec2 instance shapshots.

## Configuring

shotty uses the configuration files created the the AWS cli

`aws configure --profile acloudguru`

## Running

`pipenv run shotty.py <command> <subcommand> <--project=PROJECT>`

*command* is instances, volumes, or snapshots  
*subcommand for intsances* is list, start, stop, or snapshot  
*subcommand for volumes* is list  
*subcommand for snapshots* is list  
*project* is optional  
