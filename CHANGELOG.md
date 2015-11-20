# Change Log

## [v1.0.1](https://github.com/nubisproject/nubis-vpc/tree/v1.0.1) (2015-11-20)
[Full Changelog](https://github.com/nubisproject/nubis-vpc/compare/v1.0.0...v1.0.1)

**Implemented enhancements:**

- Need custom template for deploying Sandbox VPC [\#51](https://github.com/nubisproject/nubis-vpc/issues/51)

**Fixed bugs:**

- Redeploy sandbox to conform to new VPC design [\#34](https://github.com/nubisproject/nubis-vpc/issues/34)
- \[VPC\] Ensure VPN connections function correctly [\#18](https://github.com/nubisproject/nubis-vpc/issues/18)

**Closed issues:**

- Tag  release [\#52](https://github.com/nubisproject/nubis-vpc/issues/52)
- Deploy new VPC to sandbox in us-west-2 [\#41](https://github.com/nubisproject/nubis-vpc/issues/41)
- Create VPN Connections from applications to the datacenter [\#40](https://github.com/nubisproject/nubis-vpc/issues/40)
- Deploy jumphost to each of the apps accounts [\#38](https://github.com/nubisproject/nubis-vpc/issues/38)
- Deploy CI to each of the apps accounts [\#37](https://github.com/nubisproject/nubis-vpc/issues/37)
- Deploy fluentd to each of the apps accounts [\#36](https://github.com/nubisproject/nubis-vpc/issues/36)
- Deploy nubis meta/vpc to each of the apps accounts [\#35](https://github.com/nubisproject/nubis-vpc/issues/35)
- \#banhammerintegration - Applications moving to AWS will lose automated BGP blackhole protection [\#28](https://github.com/nubisproject/nubis-vpc/issues/28)
- Shared security group rules are egress instead of ingress rules [\#20](https://github.com/nubisproject/nubis-vpc/issues/20)

**Merged pull requests:**

- Fix VPC dependencies on VPCMeta stack [\#50](https://github.com/nubisproject/nubis-vpc/pull/50) ([gozer](https://github.com/gozer))
- Add forgotten change to sandbox VPC definitiaon [\#49](https://github.com/nubisproject/nubis-vpc/pull/49) ([gozer](https://github.com/gozer))
- Add StacksVersion input to vpc-meta [\#47](https://github.com/nubisproject/nubis-vpc/pull/47) ([gozer](https://github.com/gozer))
- Adding VPN IPs to all required parameters files [\#45](https://github.com/nubisproject/nubis-vpc/pull/45) ([tinnightcap](https://github.com/tinnightcap))
- Add parameter files for all deployments [\#44](https://github.com/nubisproject/nubis-vpc/pull/44) ([tinnightcap](https://github.com/tinnightcap))
- VPC Fix up [\#43](https://github.com/nubisproject/nubis-vpc/pull/43) ([tinnightcap](https://github.com/tinnightcap))
- Add vpc-sandbox.template [\#42](https://github.com/nubisproject/nubis-vpc/pull/42) ([tinnightcap](https://github.com/tinnightcap))
- Add meta stack deployment and move hosted zone [\#39](https://github.com/nubisproject/nubis-vpc/pull/39) ([tinnightcap](https://github.com/tinnightcap))

## [v1.0.0](https://github.com/nubisproject/nubis-vpc/tree/v1.0.0) (2015-08-31)
[Full Changelog](https://github.com/nubisproject/nubis-vpc/compare/v0.9.0...v1.0.0)

**Implemented enhancements:**

- \[VPC\] Create account container template [\#30](https://github.com/nubisproject/nubis-vpc/issues/30)
- \[VPC\] Deconstruct cloudformation template [\#27](https://github.com/nubisproject/nubis-vpc/issues/27)
- \[VPC\] Break out Private Subnet [\#25](https://github.com/nubisproject/nubis-vpc/issues/25)
- \[VPC\] Break out Public Subnet [\#24](https://github.com/nubisproject/nubis-vpc/issues/24)
- \[VPC\] Simplify mappings [\#23](https://github.com/nubisproject/nubis-vpc/issues/23)
- \[VPC\] Break out VPN logic [\#22](https://github.com/nubisproject/nubis-vpc/issues/22)

**Closed issues:**

- Fixing some typo's in nubis-vpc templates [\#15](https://github.com/nubisproject/nubis-vpc/issues/15)
- Tag v1.0.0 release [\#21](https://github.com/nubisproject/nubis-vpc/issues/21)

**Merged pull requests:**

- Update CHANGELOG for v1.0.0 [\#33](https://github.com/nubisproject/nubis-vpc/pull/33) ([gozer](https://github.com/gozer))
- Add project hosted zone and outputs [\#32](https://github.com/nubisproject/nubis-vpc/pull/32) ([tinnightcap](https://github.com/tinnightcap))
- Add template for multiple VPC creation [\#31](https://github.com/nubisproject/nubis-vpc/pull/31) ([tinnightcap](https://github.com/tinnightcap))

## [v0.9.0](https://github.com/nubisproject/nubis-vpc/tree/v0.9.0) (2015-07-23)
**Implemented enhancements:**

- Removing bastion host instance in nubis-vpc [\#12](https://github.com/nubisproject/nubis-vpc/issues/12)
- jumphosts: Should be built from nubis-base [\#6](https://github.com/nubisproject/nubis-vpc/issues/6)
- Create DNS entries for BastionHosts \(and NAT instances ?\) [\#5](https://github.com/nubisproject/nubis-vpc/issues/5)

**Merged pull requests:**

- Updating changelog for v0.9.0 release [\#17](https://github.com/nubisproject/nubis-vpc/pull/17) ([gozer](https://github.com/gozer))
- Merge [\#16](https://github.com/nubisproject/nubis-vpc/pull/16) ([gozer](https://github.com/gozer))
- Removal of bastion hosts [\#14](https://github.com/nubisproject/nubis-vpc/pull/14) ([limed](https://github.com/limed))
- Fixes various json syntax errors [\#13](https://github.com/nubisproject/nubis-vpc/pull/13) ([limed](https://github.com/limed))
- Fix the DHCP Options bits, as they were jamming the dns servers into the [\#2](https://github.com/nubisproject/nubis-vpc/pull/2) ([gozer](https://github.com/gozer))
- Splitting subnet outputs into individual outputs [\#1](https://github.com/nubisproject/nubis-vpc/pull/1) ([tinnightcap](https://github.com/tinnightcap))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*