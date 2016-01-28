provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}

resource "aws_cloudformation_stack" "vpc" {
  name = "${var.aws_region}-vpc"
  capabilities = [ "CAPABILITY_IAM" ]
  template_body = "${file("${path.module}/../../vpc-account.template")}"
  
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
