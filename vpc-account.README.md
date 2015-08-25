# Working with Cloudformation

## Set Up
Before you deploy with Cloudformation you need to set up your parameters.json file. There is an example copy called parameters.json-dist that you can copy and edit. It should look something like this:

```json
[
  {
    "ParameterKey": "ServiceName",
    "ParameterValue": "nubis-sandbox"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "sandbox"
  },
  {
    "ParameterKey": "SSHKeyName",
    "ParameterValue": "my_key"
  },
  {
    "ParameterKey": "TechnicalOwner",
    "ParameterValue": "my-email@domain.dom"
  }
]
```

### ServiceName
The ServiceName is the name of this service. For Mozilla deployments this should be the name of a real service as noted in [inventory](https://inventory.mozilla.org/en-US/core/service/)

### Environment
The environment is one of *admin*, *stage* or *prod*. For this (and all manual deployments) you will set this to *sandbox*.

### SSHKeyName
This is the name of an existing ssh key that you have either created or uploaded to AWS.

### TechnicalOwner
The technical owner should be a valid email or distribution list which is monitored by the team responsible for maintaining this service.

## Commands to work with CloudFormation
NOTE: All examples run from the top level project directory.

In these examples the stack is called *us-west-2-sandbox-vpc*. You will need to choose a unique name for your stack as their can only be one *us-west-2-sandbox-vpc* stack at a time.

### Create
To create a new stack:
```bash
aws cloudformation create-stack --template-body file://vpc-account.template --parameters file://parameters/parameters-us-west-2-sandbox.json --capabilities CAPABILITY_IAM --stack-name us-west-2-sandbox-vpc
```

### Update
To update an existing stack:
```bash
aws cloudformation update-stack --template-body file://vpc-account.template --parameters file://parameters/parameters-us-west-2-sandbox.json --capabilities CAPABILITY_IAM --region us-east-1 --profile prod --stack-name us-west-2-sandbox-vpc
```

### Delete
To delete the stack:
```bash
aws cloudformation delete-stack --capabilities CAPABILITY_IAM --stack-name us-west-2-sandbox-vpc
```

#### Nested Stacks

We are using nested stacks to deploy the necessary resources. You can find the nested stack templates at [nubis-stacks](https://github.com/Nubisproject/nubis-stacks/vpc).