"""
The MIT License (MIT)
Copyright (c) 2016 Coin Graham IV

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import boto3
import time
import json
from pprint import pprint

class lena:

    def __init__(self):
        self.nat_instance_id = None
        self.nat_instance = None
        self.vpc_id = None
        self.routetables = {}
        self.routetable = []
        self.routes = []
        self.associations = None
        self.routes_to_update = []
        self.dest_cidr_block = None
        self.subnet_id = None
        self.nat_sourcedest = None
        self.nat_addresses = None
        self.nat_eip_alloc_id = None
        self.nat_eip_assoc_id = None
        self.new_eip = None
        self.nat_gateway_eip = None
        self.nat_gateway = None
        self.nat_gateway_id = None
        self.result = {}
        self.result['log'] = []


    def prep_work(self, _vpc_id, _nat_instance_id, _new_eip):
        self.vpc_id = _vpc_id
        self.info("vpc id is {}".format(self.vpc_id))
        self.nat_instance_id = _nat_instance_id
        self.info("nat id is {}".format(self.nat_instance_id))
        self.new_eip = _new_eip
        self.info("new eip is {}".format(self.new_eip))
        self.ec2_client = boto3.client('ec2')
        self.ec2_resource = boto3.resource('ec2')

        try:
            self.nat_instance = self.ec2_client.describe_instances(
                InstanceIds=[self.nat_instance_id]
            )['Reservations'][0]['Instances'][0]

            self.subnet_id = self.nat_instance['SubnetId']

            if self.vpc_id == self.nat_instance['VpcId']:
                self.info("Verified instance id {} exists in VPC {}".format(
                    self.nat_instance_id,
                    self.vpc_id)
                )

            else:
                self.fail("Nat instance not in VPC designated")

        except:
            return self.fail("Nat Instance does not exist with this ID")

        self.nat_sourcedest = self.ec2_client.describe_instance_attribute(
            InstanceId=self.nat_instance_id,
            Attribute='sourceDestCheck'
        )

        self.info("Source Destination Check is {} on instance id {}".format(
            self.nat_sourcedest['SourceDestCheck']['Value'],
            self.nat_instance_id)
        )

        if self.nat_sourcedest['SourceDestCheck']['Value'] == True:
            return self.fail("Instance ID does not appear to be a NAT")

        self.routetables = self.ec2_client.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [self.vpc_id]}]
        )

        for self.routetable in self.routetables['RouteTables']:
            for self.routes in self.routetable['Routes']:
                if 'InstanceId' in self.routes and self.nat_instance_id == self.routes['InstanceId']:
                    self.routes_to_update.append(
                        {'RouteTableId': self.routetable['RouteTableId'],
                         'InstanceId':self.routes['InstanceId'],
                         'DestinationCidrBlock':self.routes['DestinationCidrBlock']}
                    )

        self.migrate_nat(self.new_eip)

    def migrate_nat(self, _new_eip):
        """do the nat migration activity"""
        self.new_eip = _new_eip
        self.info("Create new EIP is {}".format(self.new_eip))
        if self.new_eip == "True":
            self.info("Allocating NEW EIP Address")
            nat_new_eip = self.ec2_client.allocate_address(Domain='vpc')
            self.nat_eip_alloc_id = nat_new_eip['AllocationId']
            self.nat_gateway_eip = nat_new_eip['PublicIp']
            self.info("Public EIP {} allocated".format(self.nat_gateway_eip))
        else:
            try:
                self.info("Migrating the EIP of the existing NAT")
                self.nat_addresses = self.ec2_client.describe_addresses(
                    Filters=[{'Name': 'instance-id',
                              'Values': [self.nat_instance_id]}]
                )['Addresses'][0]
            except:
                self.fail("Unable to discover NAT EIP")

            self.nat_eip_alloc_id = self.nat_addresses['AllocationId']
            self.nat_eip_assoc_id = self.nat_addresses['AssociationId']
            self.info("Captured the allocation id of the Nat EIP: {}".format(
                self.nat_eip_alloc_id)
            )

            try:
                self.info("Removing EIP from NAT instance")
                self.ec2_client.disassociate_address(
                    AssociationId=self.nat_eip_assoc_id
                )
                time.sleep(10)
                self.info("EIP removed from NAT instance")
            except:
                self.fail("Failed to disassociate EIP from NAT instance")

        self.info("Creating NAT Gateway")
        self.nat_gateway = self.ec2_client.create_nat_gateway(
            SubnetId=self.subnet_id,
            AllocationId=self.nat_eip_alloc_id
        )

        self.nat_gateway_id = self.nat_gateway['NatGateway']['NatGatewayId']

        self.info("Created NAT Gateway: {}".format(self.nat_gateway_id))
        while not self.ec2_client.describe_nat_gateways(
                NatGatewayIds=[self.nat_gateway_id]
        )['NatGateways'][0]['State'] == 'available':
            time.sleep(15)
            self.info("Waiting for NAT Gateway to become available...")
            if self.ec2_client.describe_nat_gateways(
                    NatGatewayIds=[self.nat_gateway_id]
            )['NatGateways'][0]['State'] == 'failed':
                self.fail("Failed to provision NAT Gateway")

        for updateroute in self.routes_to_update:
            self.ec2_client.delete_route(
                RouteTableId=updateroute['RouteTableId'],
                DestinationCidrBlock=updateroute['DestinationCidrBlock']
            )

            self.info("Route {} --> {} deleted".format(
                updateroute['InstanceId'],
                updateroute['DestinationCidrBlock'],
                self.nat_gateway_id)
            )

            print self.ec2_client.create_route(
                RouteTableId=updateroute['RouteTableId'],
                DestinationCidrBlock=updateroute['DestinationCidrBlock'],
                NatGatewayId=self.nat_gateway_id
            )

            self.info("Route {} --> {} updated to {} --> {} for {}".format(
                updateroute['InstanceId'],
                updateroute['DestinationCidrBlock'],
                self.nat_gateway_id, updateroute['DestinationCidrBlock'],
                updateroute['RouteTableId'])
            )

            try:
                self.ec2_resource.RouteTable(
                    updateroute['RouteTableId']
                ).create_tags(
                    Tags=[
                        {
                            'Key': 'Lena',
                            'Value': 'RouteTable Migrated from nat instance: {} to nat gateway: {}, terminate as necessary'.format(
                                self.nat_eip_alloc_id, self.nat_gateway_id
                            )
                        }
                    ]
                )

            except:
                self.info("Failed to tag RouteTable")

        try:
            self.ec2_resource.Instance(
                self.nat_instance_id
            ).create_tags(
                Tags=[
                    {
                        'Key': 'Lena',
                        'Value': 'RouteTables Migrated from nat instance: {} to nat gateway: {}, terminate as necessary'.format(
                            self.nat_eip_alloc_id, self.nat_gateway_id
                        )
                    }
                ]
            )

        except:
            self.info("Failed to tag Nat instance")

        self.complete("NAT Migration completed successfully")

    def complete(self, message):
        self.result['status'] = 'COMPLETE'
        self.result['message'] = message
        self.result['log'].append("{}: {}".format(
            self.result['status'],
            self.result['message'])
        )
        return self.result

    def info(self, message):
        print message

    def fail(self, message):
        self.result['status'] = 'FAIL'
        self.result['message'] = message
        self.result['log'].append("{}: {}".format(
            self.result['status'],
            self.result['message'])
        )
        return self.result

    def output_logs(self):
        for log in self.result['log']:
            print(log)

def lambda_handler(event, context):
    pprint(event)
    lenamigration = lena()
    lenamigration.prep_work(
        event['ResourceProperties']['VpcId'],
        event['ResourceProperties']['NatInstanceId'],
        event['ResourceProperties']['NewEIP']
    )
    lenamigration.output_logs()

    status = 'SUCCESS'
    reason = 'See the details in CloudWatch Log Stream: %s' \
             % context.log_stream_name
    data = {'MigrationStatus': 'Success'}

    send_response(event, context, status, reason, data)

def send_response(event, context, status, reason, data):
    import requests

    body = json.dumps(
        {
            'Status': status,
            'RequestId': event['RequestId'],
            'StackId': event['StackId'],
            'PhysicalResourceId': context.log_stream_name,
            'Reason': reason,
            'LogicalResourceId': event['LogicalResourceId'],
            'Data': data
        }
    )

    headers = {
        'content-type': '',
        'content-length': len(body)
    }

    r = requests.put(event['ResponseURL'], data=body, headers=headers)
