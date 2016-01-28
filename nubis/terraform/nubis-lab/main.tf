variable aws_access_key {}
variable aws_secret_key {}
variable service_name {}
variable stacks_version {}

module "us-east-1" {
  source  = ".."
  aws_region = "us-east-1"
  aws_access_key = "${var.aws_access_key}"
  aws_secret_key = "${var.aws_secret_key}"

  service_name = "${var.service_name}"
  stacks_version = "${var.stacks_version}"

  admin_network = "10.162.0.0/24"
  prod_network = "10.162.1.0/24"
  stage_network = "10.162.2.0/24"

  prod_ipsec_target = "63.245.214.114"
  stage_ipsec_target = "63.245.214.112"
}

module "us-west-2" {
  source  = ".."
  aws_region = "us-west-2"
  aws_access_key = "${var.aws_access_key}"
  aws_secret_key = "${var.aws_secret_key}"

  service_name = "${var.service_name}"
  stacks_version = "${var.stacks_version}"

  admin_network = "10.164.0.0/24"
  prod_network = "10.164.1.0/24"
  stage_network = "10.164.2.0/24"

  prod_ipsec_target = "63.245.214.114"
  stage_ipsec_target = "63.245.214.112"
}
