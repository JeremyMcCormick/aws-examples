#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: Amazon VPC
Scenario 1: VPC with a Single Public Subnet
"""

import boto3
from botocore.exceptions import ClientError

client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

try:

    # Create the VPC.
    resp = client.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = resp['Vpc']['VpcId']

    # Set name tag on VPC.
    # https://stackoverflow.com/questions/50108783/aws-sdk-how-to-set-the-vpc-name-tag-using-boto3
    resp = client.create_tags(Resources=[vpc_id], Tags=[
        {'Key': 'Name', 'Value': 'vpc-scenario-1'}])

    # Create the public subnet.
    resp = client.create_subnet(
        CidrBlock='10.0.0.0/24',
        VpcId=vpc_id)
    subnet_id = resp['Subnet']['SubnetId']

    # Create a SG.
    data = client.create_security_group(
        Description='web server SG', GroupName='WebServerSG', VpcId=vpc_id)
    group_id = data['GroupId']

    # Add ingress rules to the SG.  The default outbound rules will allow all.
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
        ImageId='ami-02da3a138888ced85',
        InstanceType='t2.micro',
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
    
except ClientError as e:
    print(e)
