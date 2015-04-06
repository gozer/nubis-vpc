
Q2.template is the "parent" template.
It calls each of the other templates found in this directory:

	CreateVpc.template
	CoreSecurityGroups.template
	VpcResources.template

Those templates must be located in the following AWS S3 bucket loations:

	https://s3.amazonaws.com/netops-cf-templates/CreateVpc.template
	https://s3.amazonaws.com/netops-cf-templates/CoreSecurityGroups.template
	https://s3.amazonaws.com/netops-cf-templates/VpcResources.template

The Q2.template is the parent template that calls each of the three nested templates,
which do the actual work of creating the various resources.

CreateVpc.template creates just the VPC in the specified region, and returns the
"VpcId" as output.

CoreSecurityGroups.template takes the VpcId as an input parameter, and creates three
security groups:
1. The shared services security group, which all instances should belong to.
2. The Internet Access security group, which instances requiring access to the Internet
   should belong to.
3. The NAT security group, which is the security group assigned the shared NATs.
   That security group allows only members of the Internet Access security group
   to talk to the NATs.



