# (LENA) Lambda Executed NAt Migration Tool
Automated legacy NAT to NAT gateway migration tool

##### IANAD - Fair warning.  This is a project for fun and educational purposes.  Please review before using as there are no warranties.

## Description
LENA migration tool is a simple cloudformation template that creates a custom resource lambda function that will take your inputs and use them to create a new NAT gateway (in the same subnet as your NAT instance) and update all your route tables that have the NAT instance id to the new NAT gateway id.  Additionally, if you choose, it can migrate the current NAT instance EIP to the new NAT gateway.

## How To Use
Simply clone this repo to acquire both the lambda and CFT.  Then deploy the CFT in a region where you want to migrate the NAT instance to a NAT gateway.  You'll need to make a note of your NAT instance id before you start and decide whether you want to migrate the EIP off of the NAT or not.

Here's what the options in the template look like
![lena template image](https://github.com/coingraham/lena/blob/master/cloudformationtemplate/templatescreenshot.png "LENA template image")

Note:  If you choose "False" for "Generate new EIP?" the lambda function will disassociate your NAT EIP before building your NAT Gateway.  This may need to be considered if you want to migrate with zero downtime.

## What it creates
The CFT will create a python based lambda with a lambda assumer role and the following policies attached:
```json
    "Policies": [
        {
            "PolicyName": "root",
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:*:*:*"
                    },
                    {
                        "Sid": "LenaMigrationPolicy",
                        "Effect": "Allow",
                        "Action": [
                            "ec2:AllocateAddress",
                            "ec2:CreateNatGateway",
                            "ec2:CreateRoute",
                            "ec2:CreateTags",
                            "ec2:DeleteRoute",
                            "ec2:DescribeAddresses",
                            "ec2:DescribeInstanceAttribute",
                            "ec2:DescribeInstances",
                            "ec2:DescribeNatGateways",
                            "ec2:DescribeRouteTables",
                            "ec2:DisassociateAddress"
                        ],
                        "Resource": [
                            "*"
                        ]
                    }
                ]
            }
        }
    ]
```

Take a look inside the lambda folder for more details on the python there.

## Once Complete
Once the tool has completed the CFT will be marked as complete and if you look in the Outputs section you should see a Migration Status of Success.  You can also look at the output of the lambda function in CloudWatch logs.  Once it is completely finished, you can decide to terminate your NAT instance and also delete the Cloudformation Stack to eliminate the lambda.

## Authors
In addition to myself, I worked with @ianwilloughby on various permutations of the python pieces of the tool.  If you'd like to run a CLI version of the script, you can take a look at his implementation at https://github.com/ianwilloughby/aws_nat_gateway_converter