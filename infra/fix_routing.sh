#!/bin/bash
echo "🚀 Fixing Zero-Trust Network Routing for SSM and Docker Pulls..."

VPC_ID="vpc-03a243947f34ba4b2"
INSTANCE_ID="i-05ceb7faa5d6383d4"

# 1. Create and attach an Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=TrioLogic-IGW
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
echo "✅ Internet Gateway Created & Attached: $IGW_ID"

# 2. Add the internet route to the main route table
RT_ID=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[0].RouteTableId' --output text)
aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
echo "✅ Route Table Updated for Internet Access"

# 3. Assign an Elastic IP to the EC2 Node
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $EIP_ALLOC
echo "✅ Elastic IP Assigned to EC2 Node"

echo "🎉 Network routing fixed! Wait ~30 seconds for the SSM Agent to come online, then try connecting again."
