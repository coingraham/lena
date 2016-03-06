# (LENA) Lambda Executed NAt Migration Tool
Automated legacy NAT to NAT gateway migration tool

### IANAD - Fair warning.  This is a project for fun and educational purposes.  Please review before using as there are no warranties.

## Description
LENA migration tool is a simple cloudformation template that creates a custom resource lambda function that will take your inputs and use them to create a new NAT gateway (in the same subnet as your NAT instance) and update all your route tables that have the NAT instance id to the new NAT gateway id.  Additionally, if you choose, it can migrate the current NAT instance EIP to the new NAT gateway.

