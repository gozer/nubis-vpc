variable aws_access_key {}
variable aws_secret_key {}
variable aws_region {}

variable admin_network {}
variable stage_network {}
variable prod_network {}

variable prod_ipsec_target {}
variable stage_ipsec_target {}

variable service_name {}

variable technical_owner {
  default = "infra-aws@mozilla.com"
}

variable stacks_version {
  default = "master"
}

variable ssh_key_name {
  default = "nubis"
}

