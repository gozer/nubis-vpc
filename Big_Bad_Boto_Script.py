#!/usr/bin/python

import argparse, sys, re, time
from boto.vpc import connect_to_region
import boto

#----------------------------------------------------------------------------------
#  This is a python boto script to create a VPC for Mozilla's IT AWS deployment.
#  It is being used as a "first try" to create the required VPCs with the 
#  subnets, gateways, NATs and bastion host.
#  The VPC design is documented here:
#  https://mana.mozilla.org/wiki/display/EA/VPC+app-per-subnet+design
#
#  This script may be replaced by CloudFormation templates or something that
#  creates them.  
#  That said, there are a definite set of steps that must be done to 
#  instantiate a VPC which meets the current design:
#  1. create the VPC
#  2. create an Internet gateway
#  3. create the public "ELB" subnets, one in each of three avail.zones
#  4. create the public "nonELB" subnets, one in each of three avail.zones
#  5. create a NAT in each of the public ELB subnets
#  6. create a Bastion Host on one of the public ELB subnets
#  7. create 3 shared services private subnets, 1 in each of 3 avail.zones
#  8. create 5 sets of private subnets, each with a subnet in 3 avail.zones
#  9. create a customer VPN connection back to Mozilla's network
#
#  Each of the above steps have been put into its own function.
#  The "main()" portion of this script, just calls the functions, one after
#  another.  Pretty basic.
#  Note that after almost every API call to AWS, lots of checking
#  has to be done to ensure that the resource you just created is actually
#  ready to be used.  AWS is quite unreliable and laggy!
# 
#  IMPORTANT: This script requires that you set an env variable of $BOTO_CONFIG
#   that points to your boto.config file.  Here's what the boto.config file needs 
#   to look like:
#
#   [Credentials]
# 
#   [profile us-east-1-sandbox]
#   aws_access_key_id = xxxxxxxxxx
#   aws_secret_access_key = xxxxxxxx
# 
#   [profile us-west-2-sandbox]
#   aws_access_key_id = xxxxxxx
#   aws_secret_access_key = xxxxxxxxx
# 
#   [profile us-east-1-dev]
#   aws_access_key_id = xxxxxxxxxx
#   aws_secret_access_key = xxxxxxxx
# 
#   [profile us-west-2-dev]
#   aws_access_key_id = xxxxxxx
#   aws_secret_access_key = xxxxxxxxx
# 
#   [profile us-east-1-prod]
#   aws_access_key_id = xxxxxxxxxx
#   aws_secret_access_key = xxxxxxxx
# 
#   [profile us-west-2-prod]
#   aws_access_key_id = xxxxxxx
#   aws_secret_access_key = xxxxxxxxx
#----------------------------------------------------------------------------------

#----------------------------------------------------------------------------------
# user editable mappings...
# if you need to add regions and/or availability zones, do it here
#----------------------------------------------------------------------------------

# these are the regions where we plan on deploying VPCs
regions = ['us-east-1', 'us-west-2']

# this is the list of VPC types we plan on deploying
environments = ['sandbox', 'dev', 'prod']

# this is the list of bastion host AMIs for each region
bastion_host_AMIs = { 'us-east-1' : 'ami-50842d38',  'us-west-2' : 'ami-af86c69f' }

# this is the list of NAT AMIs for each region
NAT_AMIs = { 'us-east-1' : 'ami-c6699baf',  'us-west-2' : 'ami-52ff7262' }

# the following is the data structure to hold the VPC CIDR blocks
cidr_dict = {}
#
cidr_dict['us-east-1', 'sandbox'] = '10.160.0.0/16'
cidr_dict['us-east-1', 'dev']     = '10.162.0.0/16'
cidr_dict['us-east-1', 'prod']    = '10.164.0.0/16'
#
cidr_dict['us-west-2', 'sandbox'] = '10.166.0.0/16'
cidr_dict['us-west-2', 'dev']     = '10.168.0.0/16'
cidr_dict['us-west-2', 'prod']    = '10.170.0.0/16'

# the following is the data structure to hold the availability zones per region
availability_zone_dict = {}
#
availability_zone_dict['us-east-1', '1'] = 'us-east-1a'
availability_zone_dict['us-east-1', '2'] = 'us-east-1c'
availability_zone_dict['us-east-1', '3'] = 'us-east-1d'
#
availability_zone_dict['us-west-2', '1'] = 'us-west-2a'
availability_zone_dict['us-west-2', '2'] = 'us-west-2b'
availability_zone_dict['us-west-2', '3'] = 'us-west-2c'

max_retries = 20

#----------------------------------------------------------------------------------
# end of user editable mappings...
# everything below this point is my fault - dcurado Mon Mar  2 21:37:45 EST 2015
#----------------------------------------------------------------------------------

#----------------------------------------------------------
def create_connection_to_aws(region, environment):
#----------------------------------------------------------
    """this subroutine creates a connection to the appropriate region and 
       returns a handle to the connection"""

    print "attempting to connect to AWS...",
 
    profile = region + '-' + environment
    try:
        connection = connect_to_region(region, profile_name=profile)
    except Exception, e:
        print "connection failed."
        print e
        sys.exit(1)
    print "connected."
    return connection

#----------------------------------------------------------
def check_for_existing_vpc(region,environment,connection):
#----------------------------------------------------------
    """this subroutine checks if there is already a VPC with the
    same name, where name is aws_region_name + environment_type.
    Code stolen from Gene Wood -- Thanks Gene!"""

    print "checking if a VPC of the same type already exists in this region...",

    vpc_name_tag = region + '_' + environment
    existing_vpcs = connection.get_all_vpcs()
    if vpc_name_tag in [x.tags['Name'] for x in existing_vpcs if 'Name' in x.tags]:
        print ''
        print '*************************************************************************************************'
        print "*********** It appears that a VPC with the Name tag of %s already exists in this region." % vpc_name_tag
        print "*********** Stopping here."
        print '*************************************************************************************************'
        sys.exit(1)

    print "done"

#----------------------------------------------------------
def create_the_vpc(region,environment,connection):
#----------------------------------------------------------
    """this subroutine creates the VPC, and waits for the
    VPC 'state' to be marked 'available'"""

    print "attempting to create a %s VPC in %s..." % (environment, region),

    try:
        vpc_cidr_block = cidr_dict[region, environment]

        vpc = connection.create_vpc(vpc_cidr_block)

        count = 0
        while vpc.state != 'available': 
            if (count > max_retries):
                print 'timed out waiting for vpc to be created. =-('
                sys.exit(1)
            time.sleep(3)
            count += 1
            vpc.update()

        time.sleep(3)
        tag = region + '_' + environment
        vpc.add_tag('Name',tag)
        vpc.add_tag('TechnicalOwner', 'netops')
        vpc.add_tag('Environment', environment)

	# enable dns support
        connection.modify_vpc_attribute(vpc.id, enable_dns_support=True)
        connection.modify_vpc_attribute(vpc.id, enable_dns_hostnames=True)

    except Exception, e:
        print "vpc creation failed."
        print e
        sys.exit(1)

    print "done."
    return vpc

#----------------------------------------------------------
def verify_route_table(connection, vpc_id, route_table_id):
#----------------------------------------------------------
   """ The logic here is that I'm trying to work around the
       race condition that can occur with AWS, where you create
       a resource, but then try to manipulate that object before
       AWS *really* knows about it.  So this bit of code queries
       AWS for the list of route_tables in the VPC, and if the 
       route table we just created shows up in the list of all
       route tables, then I guess AWS knows it actually exists"""

   route_tables = connection.get_all_route_tables(filters={'vpc-id': vpc_id})
   for x in route_tables:
      if x.id == route_table_id:
         break
      else:
         time.sleep(3)
   return

#----------------------------------------------------------
def verify_subnet(connection, subnet):
#----------------------------------------------------------
   """ The logic here is that I'm trying to work around the
       race condition that can occur with AWS, where you create
       a resource, but then try to manipulate that object before
       AWS *really* knows about it.  So this bit of code queries
       AWS for the list of subnets in the VPC, grabs our subnet
       out of the list, and checks its state, until the state
       shows the subnet is ready """

   while subnet.state == 'pending':
       subnets = connection.get_all_subnets()
       # this part updates the state of the object
       for x in subnets:
           if x.id == subnet.id:
               subnet.state = x.state
       time.sleep(5)
   return

#----------------------------------------------------------
def create_internet_gateway(connection, vpc_id, environment):
#----------------------------------------------------------
   """ This subroutine creates an Internet gateway, creates
       a routing table, associates that route table and gateway,
       and adds a default route in the routing table."""

   print "creating Internet gateway...",

   # the sleep statements here are bogus.  I could not find
   # a way to verify that the gateway was actually ready
   gateway = connection.create_internet_gateway()
   time.sleep(10)
   connection.attach_internet_gateway(gateway.id, vpc_id)
   time.sleep(30)
   gateway.add_tag('Name','InternetGateway')
   gateway.add_tag('TechnicalOwner', 'netops')
   gateway.add_tag('Environment', environment)
   # create the route table
   route_table = connection.create_route_table(vpc_id)
   verify_route_table(connection, vpc_id, route_table.id)
   route_table.add_tag('Name','InternetRouteTable')
   connection.create_route(route_table.id, '0.0.0.0/0', gateway.id)

   print "done"
   return route_table

#----------------------------------------------------------
def create_ELB_subnet(region, environment, connection, vpc_id, iteration): 
#----------------------------------------------------------
   """ This subroutine creates a public ELB subnet.
       The ip addressing scheme used for the VPCs is documented here:
       https://mana.mozilla.org/wiki/display/EA/Project+Nubis+IP+allocation+plan 
   """

   print "creating ELB public subnet %s..." % str(iteration),

   vpc_cidr_block = cidr_dict[region, environment]
   cidr_block = re.sub(r'0.0/16$', "", vpc_cidr_block)
   third_octet = 238 + (iteration * 2)
   cidr_block += str(third_octet) + '.0/23'
   az = availability_zone_dict[region, str(iteration)]
   ELB_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
   verify_subnet(connection, ELB_subnet)
   tag = 'AZ' + str(iteration) + '_ELB_subnet'
   ELB_subnet.add_tag('Name',tag)
   ELB_subnet.add_tag('TechnicalOwner', 'netops')
   ELB_subnet.add_tag('Environment', environment)
   print "done"
   return(ELB_subnet.id)

#----------------------------------------------------------
def create_nonELB_subnet(region, environment, connection, vpc_id, iteration): 
#----------------------------------------------------------
   """ This subroutine creates a public nonELB subnet.
       The ip addressing scheme used for the VPCs is documented here:
       https://mana.mozilla.org/wiki/display/EA/Project+Nubis+IP+allocation+plan 
       nonELB subnets are for services like IRC which can live behind an ELB
   """

   print "creating nonELB public subnet %s..." % str(iteration),

   vpc_cidr_block = cidr_dict[region, environment]
   cidr_block = re.sub(r'0.0/16$', "", vpc_cidr_block)
   third_octet = 246 + (iteration * 2)
   cidr_block += str(third_octet) + '.0/23'
   az = availability_zone_dict[region, str(iteration)]
   nonELB_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
   verify_subnet(connection, nonELB_subnet)
   tag = 'AZ' + str(iteration) + '_nonELB_subnet'
   nonELB_subnet.add_tag('Name',tag)
   nonELB_subnet.add_tag('TechnicalOwner', 'netops')
   nonELB_subnet.add_tag('Environment', environment)
   print "done"
   return(nonELB_subnet.id)

#----------------------------------------------------------
def create_nat_security_group(vpc_id, connection, region, environment):
#----------------------------------------------------------
   """ This subroutine creates the security group to be used by the NATs."""

   print "creating NAT security group...",

   security_group = connection.create_security_group('nat_security_group', 'NAT Security Group', vpc_id)
   count = 0
   # stolen from Gene Wood
   while True:
       try:
           count += 1
           security_group = connection.get_all_security_groups(group_ids=[security_group.id])[0]
           break
       except boto.exception.EC2ResponseError:
           time.sleep(1)
           if (count > max_retries):
               print "timed out waiting for NAT security group to be ready"
               raise
   time.sleep(3)
   vpc_cidr_block = cidr_dict[region, environment]
   security_group.authorize(ip_protocol='tcp', from_port='0', to_port='65535', cidr_ip='0.0.0.0/0') 
   security_group.authorize(ip_protocol='udp', from_port='0', to_port='65535', cidr_ip='0.0.0.0/0') 
   security_group.authorize(ip_protocol='icmp', from_port='8', to_port='-1', cidr_ip='0.0.0.0/0') 
   security_group.add_tag('Name','SSH_SecurityGroup') 
   print "done"
   return(security_group)

#----------------------------------------------------------
def create_nat(vpc_id, connection, security_group, subnet, region, key, iteration, environment):
#----------------------------------------------------------
   """ This subroutine creates a NAT."""

   print "creating NAT %s..." % str(iteration),

   interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
       subnet_id=subnet,
       groups=[security_group.id],
       associate_public_ip_address=True,
   )
   interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)

   reservation = connection.run_instances(
       image_id=NAT_AMIs[region], 
       key_name=key, 
       network_interfaces=interfaces,
   )

   nat = reservation.instances[0]

   # wait for the instance to be running
   count = 0
   while nat.state != 'running': 
       time.sleep(3)
       nat.update()
       count += 1
       if (count > max_retries):
           print 'NAT for %s never went to running state' % subnet
           sys.exit(1)

   time.sleep(3)
   if not connection.modify_instance_attribute(nat.id, 'sourceDestCheck', False):
       print 'Failed to set sourceDestCheck to false for NAT%d' % iternation
       sys.exit(1)

   tag = 'AZ' + str(iteration) + '_NAT'
   nat.add_tag('Name',tag) 
   nat.add_tag('TechnicalOwner', 'netops')
   nat.add_tag('Environment', environment)
   print "done"
   return(nat.id)

#----------------------------------------------------------
def create_bastion_security_group(vpc_id, connection, region, environment):
#----------------------------------------------------------
   """ This subroutine creates a security group to be used by the bastion host"""

   print "creating Bastion Host security group...",

   security_group = connection.create_security_group('ssh_security_group', 'SSH Security Group', vpc_id)
   count = 0
   # stolen from Gene Wood
   while True:
       try:
           count += 1
           security_group = connection.get_all_security_groups(group_ids=[security_group.id])[0]
           break
       except boto.exception.EC2ResponseError:
           time.sleep(1)
           if (count > max_retries):
               print "timed out waiting for bastion host security group to be ready"
               raise
   time.sleep(3)
   vpc_cidr_block = cidr_dict[region, environment]
   security_group.authorize(ip_protocol='tcp', from_port='22', to_port='22', cidr_ip='0.0.0.0/0') 
   security_group.authorize(ip_protocol='icmp', from_port='8', to_port='-1', cidr_ip='0.0.0.0/0') 
   security_group.add_tag('Name','SSH_SecurityGroup') 
   print "done"
   return(security_group)

#----------------------------------------------------------
def create_bastion_host(vpc_id, connection, security_group, subnet, region, key, environment):
#----------------------------------------------------------
   """ This subroutine creates a bastion host"""

   print "creating bastion host...", 

   interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
       subnet_id=subnet,
       groups=[security_group.id],
       associate_public_ip_address=True
   )
   interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)

   reservation = connection.run_instances(
       image_id=bastion_host_AMIs[region], 
       instance_type='t1.micro', 
       key_name=key, 
       network_interfaces=interfaces,
   )

   bastion_host = reservation.instances[0]

   # If we ever decide we want the bastion host to have an EIP...
   # eip = aws_connection.allocate_address(domain='vpc')
   # And associate the EIP with our instance
   # aws_connection.associate_address(instance_id=instance.id, allocation_id=eip.allocation_id)

   # wait for the instance to be running and have an public dns name
   count = 0
   while bastion_host.state != 'running': 
       time.sleep(3)
       bastion_host.update()
       count += 1
       if (count > max_retries):
           print 'bastion host never went to running state'
           sys.exit(1)

   time.sleep(3)
   bastion_host.add_tag('Name','BastionHost') 
   bastion_host.add_tag('TechnicalOwner', 'netops')
   bastion_host.add_tag('Environment', environment)
   print "done"

#----------------------------------------------------------
def create_shared_services_subnets(region, environment, connection, vpc_id, nat1, nat2, nat3):
#----------------------------------------------------------
   """ This subroutine creates a set of shared services subnets.
       These subnets are designed to hold various management functions, like Consul.
       Each private subnet is allowed to communicate with the shared services subnets. 
   """

   print 'creating shared service subnets...',

   vpc_cidr_block = cidr_dict[region, environment]

   new_block = '0.0/26'
   cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
   az = availability_zone_dict[region, '1']
   shared_svcs_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
   verify_subnet(connection, shared_svcs_subnet)
   name_tag = 'shared_svcs_subnet_' + az
   shared_svcs_subnet.add_tag('Name',name_tag)
   route_table = connection.create_route_table(vpc_id)
   verify_route_table(connection, vpc_id, route_table.id)
   name_tag = 'shared_svcs_route_table_' + az
   route_table.add_tag('Name',name_tag)
   connection.create_route(route_table_id=route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat1) 
   connection.associate_route_table(route_table.id, shared_svcs_subnet.id)

   new_block = '0.64/26'
   cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
   az = availability_zone_dict[region, '2']
   shared_svcs_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
   verify_subnet(connection, shared_svcs_subnet)
   name_tag = 'shared_svcs_subnet_' + az
   shared_svcs_subnet.add_tag('Name',name_tag)
   route_table = connection.create_route_table(vpc_id)
   verify_route_table(connection, vpc_id, route_table.id)
   name_tag = 'shared_svcs_route_table_' + az
   route_table.add_tag('Name',name_tag)
   connection.create_route(route_table_id=route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat2) 
   connection.associate_route_table(route_table.id, shared_svcs_subnet.id)

   new_block = '0.128/26'
   cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
   az = availability_zone_dict[region, '3']
   shared_svcs_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
   verify_subnet(connection, shared_svcs_subnet)
   name_tag = 'shared_svcs_subnet_' + az
   shared_svcs_subnet.add_tag('Name',name_tag)
   route_table = connection.create_route_table(vpc_id)
   verify_route_table(connection, vpc_id, route_table.id)
   name_tag = 'shared_svcs_route_table_' + az
   route_table.add_tag('Name',name_tag)
   connection.create_route(route_table_id=route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat3) 
   connection.associate_route_table(route_table.id, shared_svcs_subnet.id)
   
   print "done."

#----------------------------------------------------------
def create_private_subnets(region, environment, connection, vpc_id, nat1, nat2, nat3):
#----------------------------------------------------------
   """ This subroutine creates all the app-per-subnet private subnets.
       There is a NACL in place on each private subnet which allows instances
       in the private subnet to talk with instances belong to the same app,
       or the shared services subnets, but no other application subnets.
       Note that in the NACL code below, the CIDR block 10.0.0.0/10 is
       the IP address space used by Mozilla's data centers
   """

   print 'creating private subnets'

   vpc_cidr_block = cidr_dict[region, environment]

   for n in range(1,6):

      nacl = connection.create_network_acl(vpc_id)
      new_block = str(n) + '.0/24'
      private_cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
      elb_cidr_block = re.sub(r'0.0/16$', '240.0/21', vpc_cidr_block)
      shared_svcs_cidr_block = re.sub(r'0.0/16$', '0.0/24', vpc_cidr_block)
      connection.create_network_acl_entry(nacl.id, '10', '-1', 'allow', private_cidr_block, egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '20', '-1', 'allow', elb_cidr_block, egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '30', '-1', 'allow', shared_svcs_cidr_block, egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '40', '-1', 'allow', '10.0.0.0/10', egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '50', '-1', 'deny', '10.0.0.0/8', egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '60', '-1', 'allow', '0.0.0.0/0', egress='True', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)
      connection.create_network_acl_entry(nacl.id, '70', '-1', 'allow', '0.0.0.0/0', egress='False', \
          icmp_code=None, icmp_type=None, port_range_from=None, port_range_to=None)

      print "app %d: subnet id for AZ1..." % n,
      new_block = str(n) + '.0/26'
      cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
      az = availability_zone_dict[region, '1']
      private_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
      verify_subnet(connection, private_subnet)
      name_tag = 'private_subnet_' + str(n) + '_' + az
      private_subnet.add_tag('Name',name_tag)
      private_subnet.add_tag('TechnicalOwner', 'netops')
      private_subnet.add_tag('Environment', environment)
      private_route_table = connection.create_route_table(vpc_id)
      verify_route_table(connection, vpc_id, private_route_table.id)
      name_tag = 'private_route_table' + str(n) + '_' + az
      private_route_table.add_tag('Name',name_tag)
      connection.create_route(route_table_id=private_route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat1) 
      connection.associate_route_table(private_route_table.id, private_subnet.id)
      connection.associate_network_acl(nacl.id, private_subnet.id)
      print "done"

      print "app %d: subnet id for AZ1..." % n,
      new_block = str(n) + '.64/26'
      cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
      az = availability_zone_dict[region, '2']
      private_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
      verify_subnet(connection, private_subnet)
      name_tag = 'private_subnet_' + str(n) + '_' + az
      private_subnet.add_tag('Name',name_tag)
      private_subnet.add_tag('TechnicalOwner', 'netops')
      private_subnet.add_tag('Environment', environment)
      private_route_table = connection.create_route_table(vpc_id)
      verify_route_table(connection, vpc_id, private_route_table.id)
      name_tag = 'private_route_table' + str(n) + '_' + az
      private_route_table.add_tag('Name',name_tag)
      connection.create_route(route_table_id=private_route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat2) 
      connection.associate_route_table(private_route_table.id, private_subnet.id)
      connection.associate_network_acl(nacl.id, private_subnet.id)
      print "done"

      print "app %d: subnet id for AZ1..." % n,
      new_block = str(n) + '.128/26'
      cidr_block = re.sub(r'0.0/16$', new_block, vpc_cidr_block)
      az = availability_zone_dict[region, '3']
      private_subnet = connection.create_subnet(vpc_id, cidr_block, availability_zone=az)
      verify_subnet(connection, private_subnet)
      name_tag = 'private_subnet_' + str(n) + '_' + az
      private_subnet.add_tag('Name',name_tag)
      private_subnet.add_tag('TechnicalOwner', 'netops')
      private_subnet.add_tag('Environment', environment)
      private_route_table = connection.create_route_table(vpc_id)
      verify_route_table(connection, vpc_id, private_route_table.id)
      name_tag = 'private_route_table' + str(n) + '_' + az
      private_route_table.add_tag('Name',name_tag)
      connection.create_route(route_table_id=private_route_table.id, destination_cidr_block='0.0.0.0/0', instance_id=nat3) 
      connection.associate_route_table(private_route_table.id, private_subnet.id)
      connection.associate_network_acl(nacl.id, private_subnet.id)
      print "done"

#----------------------------------------------------------
def create_vpn_connection(vpc_id, connection, environment, region, route_table):
#----------------------------------------------------------

    """ This subroutines takes care of creating the customer VPN connection back to SCL3.
        steps: 
        - create customer gateway
        - create virtual private gw
        - attach virtual private gw to vpc
        - create VPN connection
        - add route to Internet Route Table for 10.0.0.0/10 next-hop vgw-xxxxxxx
    """

    nametag = region + '-' + environment

    print "creating customer vpn gateway"
    customer_gateway = connection.create_customer_gateway('ipsec.1', '63.245.214.54', '65022')
    count = 0
    while customer_gateway.state != 'available': 
        if (count > max_retries):
            print 'timed out waiting for customer VPN gateway to be marked as available.'
            sys.exit(1)
        time.sleep(3)
        count += 1
    time.sleep(10)
    customer_gateway.add_tag('Name', nametag)
    print "customer gateway state is %s" % customer_gateway.state

    # create the VPN gateway
    print "creating vpn gateway"
    vpn_gateway = connection.create_vpn_gateway('ipsec.1')
    count = 0
    while vpn_gateway.state != 'available': 
        if (count > max_retries):
            print 'timed out waiting for vpn gateway to be marked as available.'
            sys.exit(1)
        time.sleep(3)
        count += 1
    vpn_gateway.add_tag('Name', nametag)
    print "vpn gateway state is %s" % vpn_gateway.state

    # attach the VPN gateway
    print "attaching vpn gateway to vpc"
    vpn_gateway.attach(vpc_id)
    count = 0
    while vpn_gateway.state != 'available':
        print "state is %s" % vpn_gateway.state
        vpn_gateways = connection.get_all_vpn_connections()
        for item in vpn_gateways:
           if item.id == vpn_gateway.id:
              vpn_gateway.state = item.state
        time.sleep(3)
        count += 1
        if count > max_retries:
           print "timed out waiting for vpn gateway to attach."
           sys.exit(1)

    print "creating VPN connection..."
    vpn_connection = connection.create_vpn_connection("ipsec.1", customer_gateway.id, vpn_gateway.id)
    count = 0
    # stolen from Gene Wood
    while True:
        try:
            count += 1
            vpn_connection = connection.get_all_vpn_connections(vpn_connection_ids=[vpn_connection.id])[0]
            break
        except boto.exception.EC2ResponseError:
            time.sleep(1)
            if (count > 50):
                print "timed out waiting for vpn connection to be ready"
                raise
    vpn_connection.add_tag('Name', nametag)

    print "installing route back to Mozilla data centers..."
    # this is lame
    time.sleep(120)
    connection.create_route(route_table.id, '10.0.0.0/10', gateway_id=vpn_gateway.id)
    print "done"

#----------------------------------------------------------
def main():
#----------------------------------------------------------

    #----------------------------------------------------------------------------------
    # handle command line arguments, this script requires "region" and "environment" and "key"
    #----------------------------------------------------------------------------------

    parser = argparse.ArgumentParser(description='script to create AWS VPCs')
    parser.add_argument('-r','--region', help='The AWS Region', required=True)
    parser.add_argument('-e','--environment', help='The VPC environment type', required=True)
    parser.add_argument('-k','--key', help='The name of the .pem key file for creating instances', required=True)
    args = parser.parse_args()

    if args.region not in regions:
        print '\tinvalid region name.'
        print '\tvalid region names are:'
        for region in regions:
          print "\t\t%s" % region
        sys.exit(1)

    if args.environment not in environments:
        print '\tinvalid environment name.'
        print '\tvalid environment names are:'
        for environment in environments:
          print "\t\t%s" % environment
        sys.exit(1)
 
    aws_region = args.region
    aws_environment = args.environment
    aws_key = args.key

    #----------------------------------------------------------------------------------
    # create the connection and make sure we're not overwriting an existing VPC
    #----------------------------------------------------------------------------------

    aws_connection = create_connection_to_aws(aws_region, aws_environment)
    check_for_existing_vpc(aws_region, aws_environment, aws_connection)

    #----------------------------------------------------------------------------------
    # create the vpc and internet gateway
    #----------------------------------------------------------------------------------

    vpc = create_the_vpc(aws_region, aws_environment, aws_connection)
    internet_route_table = create_internet_gateway(aws_connection, vpc.id, aws_environment)

    #----------------------------------------------------------------------------------
    # create the public subnets
    #----------------------------------------------------------------------------------

    ELB_subnet_AZ1_id = create_ELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 1)
    if not aws_connection.associate_route_table(internet_route_table.id, ELB_subnet_AZ1_id):
        print 'failed to associate ELB_subnet_AZ1 with the VPC routing table.'
        sys.exit(1)
    ELB_subnet_AZ2_id = create_ELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 2)
    if not aws_connection.associate_route_table(internet_route_table.id, ELB_subnet_AZ2_id):
        print 'failed to associate ELB_subnet_AZ2 with the VPC routing table.'
        sys.exit(1)
    ELB_subnet_AZ3_id = create_ELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 3)
    if not aws_connection.associate_route_table(internet_route_table.id, ELB_subnet_AZ3_id):
        print 'failed to associate ELB_subnet_AZ3 with the VPC routing table.'
        sys.exit(1)
    nonELB_subnet_AZ1_id = create_nonELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 1)
    if not aws_connection.associate_route_table(internet_route_table.id, nonELB_subnet_AZ1_id):
        print 'failed to associate nonELB_subnet_AZ1 with the VPC routing table.'
        sys.exit(1)
    nonELB_subnet_AZ2_id = create_nonELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 2)
    if not aws_connection.associate_route_table(internet_route_table.id, nonELB_subnet_AZ2_id):
        print 'failed to associate nonELB_subnet_AZ1 with the VPC routing table.'
        sys.exit(1)
    nonELB_subnet_AZ3_id = create_nonELB_subnet(aws_region,aws_environment,aws_connection, vpc.id, 3)
    if not aws_connection.associate_route_table(internet_route_table.id, nonELB_subnet_AZ3_id):
        print 'failed to associate nonELB_subnet_AZ1 with the VPC routing table.'
        sys.exit(1)

    #----------------------------------------------------------------------------------
    # create the NATs and bastion host
    #----------------------------------------------------------------------------------

    nat_security_group = create_nat_security_group(vpc.id, aws_connection, aws_region, aws_environment)
    nat1_id=create_nat(vpc.id, aws_connection, nat_security_group, ELB_subnet_AZ1_id, aws_region, aws_key, 1, aws_environment)
    nat2_id=create_nat(vpc.id, aws_connection, nat_security_group, ELB_subnet_AZ2_id, aws_region, aws_key, 2, aws_environment)
    nat3_id=create_nat(vpc.id, aws_connection, nat_security_group, ELB_subnet_AZ3_id, aws_region, aws_key, 3, aws_environment)
    bastion_security_group = create_bastion_security_group(vpc.id, aws_connection, aws_region, aws_environment)
    create_bastion_host(vpc.id, aws_connection, bastion_security_group, ELB_subnet_AZ1_id, aws_region, aws_key, aws_environment)

    #----------------------------------------------------------------------------------
    # create the shared services subnets
    #----------------------------------------------------------------------------------

    create_shared_services_subnets(aws_region, aws_environment, aws_connection, vpc.id, nat1_id, nat2_id, nat3_id)

    #----------------------------------------------------------------------------------
    # create the private subnets
    #----------------------------------------------------------------------------------

    create_private_subnets(aws_region, aws_environment, aws_connection, vpc.id, nat1_id, nat2_id, nat3_id)

    #----------------------------------------------------------------------------------
    # create the VPN connection back to Mozilla's network
    #----------------------------------------------------------------------------------

    create_vpn_connection(vpc.id, aws_connection, aws_environment, aws_region, internet_route_table)
    print 'script complete!'
    sys.exit(0)

#-------------------------------------------------------------
if __name__ == '__main__':
    main ()
#-------------------------------------------------------------

