# nubis-vpc

There are several files here:

1. The Big_Bad_Boto_Script, which is a python/boto script.  
   It has built in help, and a lot of comments explaining how
   to use it.  Creates the Q1 2015 based VPC topology.

2. Q1.template, a CloudFormation template that does the same thing
   as the Big_Bad_Boto_Script, just via CloudFormation. 
   Creates the Q1 2015 based VPC topology.

3. vpc_dump, a python/boto script that dumps out all the network
   related stuff in a VPC.  It spells out the NACLs applied to each
   subnet.  Could be useful for debugging... or not.

4. Q2.template, monolithic CloudFormation template that creates
   the flattened Q2 2015 VPC topology and related resources

5. NestedTemplate is a directory containing a set of CloudFormation 
   nested templates which do the same thing as the monolithic Q2.template




