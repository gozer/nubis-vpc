provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}

resource "aws_key_pair" "nubis" {
  key_name = "nubis"
  public_key = "${file("~/.ssh/nubis.pub")}"
}

resource "tls_private_key" "default" {
    algorithm = "RSA"
}

resource "tls_self_signed_cert" "default" {
    key_algorithm = "${tls_private_key.default.algorithm}"
    private_key_pem = "${tls_private_key.default.private_key_pem}"

    # Certificate expires after 12 hours.
    validity_period_hours = 43800

    # Generate a new certificate if Terraform is run within three
    # hours of the certificate's expiration time.
    early_renewal_hours = 168

    # Reasonable set of uses for a server SSL certificate.
    allowed_uses = [
        "key_encipherment",
        "digital_signature",
        "server_auth",
    ]

    subject {
        common_name = "*.${var.aws_region}.${var.service_name}.nubis.allizom.org"
        organization = "Mozilla Nubis"
    }
}

resource "aws_iam_server_certificate" "default" {
    name = "${var.aws_region}.${var.service_name}.nubis.allizom.org"
    certificate_body = "${tls_self_signed_cert.default.cert_pem}"
    private_key = "${tls_private_key.default.private_key_pem}"
}

resource "aws_lambda_function" "UUID" {
	function_name = "UUID"
	filename = "${path.module}/../../UUID.zip"
	handler = "index.handler"
	description = "Generate UUIDs for use in Cloudformation stacks"
	memory_size = 128
	runtime = "nodejs"
	timeout = "10"
	role = "${aws_cloudformation_stack.vpc.outputs.LambdaRoleArn}"
}

resource "aws_lambda_function" "LookupStackOutputs" {
	function_name = "LookupStackOutputs"
	filename = "${path.module}/../../LookupStackOutputs.zip"
	handler = "index.handler"
	description = "Gather outputs from Cloudformation stacks to be used in other Cloudformation stacks"
	memory_size = 128
	runtime = "nodejs"
	timeout = "10"
	role = "${aws_cloudformation_stack.vpc.outputs.LambdaRoleArn}"
}

resource "aws_lambda_function" "LookupNestedStackOutputs" {
	function_name = "LookupNestedStackOutputs"
	filename = "${path.module}/../../LookupNestedStackOutputs.zip"
	handler = "index.handler"
	description = "Gather outputs from Cloudformation enviroment specific nested stacks to be used in other Cloudformation stacks"
	memory_size = 128
	runtime = "nodejs"
	timeout = "10"
	role = "${aws_cloudformation_stack.vpc.outputs.LambdaRoleArn}"
}

resource "aws_cloudformation_stack" "vpc" {

  depends_on = ["aws_key_pair.nubis"]

  name = "${var.aws_region}-vpc"
  capabilities = [ "CAPABILITY_IAM" ]
  template_body = "${file("${path.module}/../../vpc-account.template")}"
  on_failure = "DELETE"
  
  parameters = {
    ServiceName = "${var.service_name}"
    TechnicalOwner = "${var.technical_owner}"
    StacksVersion = "${var.stacks_version}"
    SSHKeyName = "${var.ssh_key_name}"
    
    AdminVpcCidr = "${var.admin_network}"
    StageVpcCidr = "${var.stage_network}"
    ProdVpcCidr = "${var.prod_network}"
  
    ProdIPSecTunnelTarget = "${var.prod_ipsec_target}"
    StageIPSecTunnelTarget = "${var.stage_ipsec_target}"
  
    AdminPublicSubnetAZ1Cidr = "${cidrsubnet(var.admin_network, 3, 0)}"
    AdminPublicSubnetAZ2Cidr = "${cidrsubnet(var.admin_network, 3, 1)}"
    AdminPublicSubnetAZ3Cidr = "${cidrsubnet(var.admin_network, 3, 2)}"
  
    AdminPrivateSubnetAZ1Cidr = "${cidrsubnet(var.admin_network, 3, 3)}"
    AdminPrivateSubnetAZ2Cidr = "${cidrsubnet(var.admin_network, 3, 4)}"
    AdminPrivateSubnetAZ3Cidr = "${cidrsubnet(var.admin_network, 3, 5)}"
  
    ProdPublicSubnetAZ1Cidr = "${cidrsubnet(var.prod_network, 3, 0)}"
    ProdPublicSubnetAZ2Cidr = "${cidrsubnet(var.prod_network, 3, 1)}"
    ProdPublicSubnetAZ3Cidr = "${cidrsubnet(var.prod_network, 3, 2)}"
  
    ProdPrivateSubnetAZ1Cidr = "${cidrsubnet(var.prod_network, 3, 3)}"
    ProdPrivateSubnetAZ2Cidr = "${cidrsubnet(var.prod_network, 3, 4)}"
    ProdPrivateSubnetAZ3Cidr = "${cidrsubnet(var.prod_network, 3, 5)}"
  
    StagePublicSubnetAZ1Cidr = "${cidrsubnet(var.stage_network, 3, 0)}"
    StagePublicSubnetAZ2Cidr = "${cidrsubnet(var.stage_network, 3, 1)}"
    StagePublicSubnetAZ3Cidr = "${cidrsubnet(var.stage_network, 3, 2)}"
  
    StagePrivateSubnetAZ1Cidr = "${cidrsubnet(var.stage_network, 3, 3)}"
    StagePrivateSubnetAZ2Cidr = "${cidrsubnet(var.stage_network, 3, 4)}"
    StagePrivateSubnetAZ3Cidr = "${cidrsubnet(var.stage_network, 3, 5)}"
  
  }
}
