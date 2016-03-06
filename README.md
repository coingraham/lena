# (LENA) Lambda Executed NAt Migration Tool
Automated legacy NAT to NAT gateway migration tool

### IANAD - Fair warning.  This is a project for fun and educational purposes.  Please review before using as there are no warranties.

## Description
LENA migration tool is a simple cloudformation template that creates a custom resource lambda function that will take your inputs and use them to create a new NAT gateway (in the same subnet as your NAT instance) and update all your route tables that have the NAT instance id to the new NAT gateway id.  Additionally, if you choose, it can migrate the current NAT instance EIP to the new NAT gateway.

## How To Use
Simply clone this repo to acquire both the lambda and CFT.  Then deploy the CFT in a region where you want to migrate the NAT instance to a NAT gateway.  You'll need to make a note of your NAT instance id before you start and decide whether you want to migrate the EIP off of the NAT or not.

### Here's what the options in the template look like
![lena template image](https://github.com/coingraham/lena/blob/master/cloudformationtemplate/templateimage.PNG "LENA template image")