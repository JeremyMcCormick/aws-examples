#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: Amazon VPC
Scenario 1: VPC with a Single Public Subnet
https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Scenario1.html

@author Jeremy McCormick
"""

import boto3
from botocore.exceptions import ClientError

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#client
client = boto3.client('ec2', region_name = 'ap-southeast-1')

ec2 = boto3.resource('ec2', region_name = 'ap-southeast-1')

# examples
# https://gist.github.com/nguyendv/8cfd92fc8ed32ebb78e366f44c2daea6

try:

    # Create the VPC.
    resp = client.create_vpc(CidrBlock='10.0.0.0/16')
    #print(resp)
    vpc_id = resp['Vpc']['VpcId']
    vpc = ec2.Vpc(vpc_id)
    vpc.wait_until_available()

    # Set name tag on VPC.
    # https://stackoverflow.com/questions/50108783/aws-sdk-how-to-set-the-vpc-name-tag-using-boto3
    resp = client.create_tags(Resources=[vpc_id], Tags=[
        {'Key': 'Name', 'Value': 'vpc-scenario-1'}])

    # Create the public subnet.
    resp = client.create_subnet(
        CidrBlock='10.0.0.0/24',
        VpcId=vpc_id)
    #print(resp)
    subnet_id = resp['Subnet']['SubnetId']

    # Create a SG.
    resp = client.create_security_group(
        Description='web server SG', GroupName='WebServerSG', VpcId=vpc_id)
    #print(resp)
    group_id = resp['GroupId']

    # Add ingress rules to the SG.  The default outbound rules will allow all traffic.
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-security-group.html
    resp = client.authorize_security_group_ingress(
        GroupId=group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 443,
             'ToPort': 443,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    #print(resp)
    
    # Create an Internet Gateway.    
    resp = client.create_internet_gateway()
    gateway_id = resp['InternetGateway']['InternetGatewayId']
    
    # Attach the Internet Gatway to the VPC.
    resp = client.attach_internet_gateway(InternetGatewayId=gateway_id, VpcId=vpc_id)
        
    # Create a route table.
    resp = client.create_route_table(VpcId=vpc_id)
    route_table_id = resp['RouteTable']['RouteTableId']
    
    # Get the route table.
    route_table = ec2.RouteTable(route_table_id)

    # Create a route to the IGW.
    route = route_table.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=gateway_id)

    # Associate route table with subnet.
    route_table.associate_with_subnet(SubnetId=subnet_id)
          
    # Create a key pair to use for SSHing into the instance.
    # https://sdbrett.com/BrettsITBlog/2016/05/creating-aws-instances-with-boto3/
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-key-pairs.html    
    outfile = open('MyKeyPair.pem', 'w')
    key_pair = client.create_key_pair(KeyName='MyKeyPair')
    key_pair_out = str(key_pair['KeyMaterial'])
    outfile.write(key_pair_out)
    outfile.close()
#    os.chmod(outfile.name, 400)
    
    # Create an EC2 instance associated to the subnet.
    # https://stackoverflow.com/questions/32863768/how-to-create-an-ec2-instance-using-boto3
    resp = client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                }
            }
        ],
        ImageId='ami-00158b185c8cc09dc',        
        InstanceType='t2.micro',
        KeyName='MyKeyPair',
        MaxCount=1,
        MinCount=1,        
        NetworkInterfaces=[
            {
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': True,
                'Groups': [group_id]
            }
        ]
    )
    #         ImageId='ami-02da3a138888ced85',
    
except ClientError as e:
    print(e)
