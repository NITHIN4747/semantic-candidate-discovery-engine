#!/bin/bash
# INDIA RUNS Hackathon - TrioLogic Network Topology Provisioning
# Run this script to establish the Zero-Trust VPC, Subnets, and Security Groups.

echo "🚀 Initiating Zero-Trust AWS Infrastructure Deployment..."

# 1. Create the Isolated VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=TrioLogic-Semantic-VPC
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
echo "✅ VPC Created: $VPC_ID"

# 2. Provision Private Subnets
# Compute Subnet (For EC2/Docker)
SUBNET_COMPUTE=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $SUBNET_COMPUTE --tags Key=Name,Value=TrioLogic-Compute-Subnet

# Database Subnet (For RDS PostgreSQL pgvector)
SUBNET_DB=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $SUBNET_DB --tags Key=Name,Value=TrioLogic-DB-Subnet
echo "✅ Private Subnets Created."

# 3. Create Strict Security Groups
SG_NLB=$(aws ec2 create-security-group --group-name SG-NLB --description "Network Load Balancer Ingress" --vpc-id $VPC_ID --query 'GroupId' --output text)
SG_EC2=$(aws ec2 create-security-group --group-name SG-EC2-Compute --description "EC2 Docker App Host" --vpc-id $VPC_ID --query 'GroupId' --output text)
SG_RDS=$(aws ec2 create-security-group --group-name SG-RDS-Database --description "PostgreSQL Vector DB" --vpc-id $VPC_ID --query 'GroupId' --output text)
echo "✅ Security Groups Initialized."

# 4. Enforce the Zero-Trust Matrix Rules
# SG-NLB: Accept public HTTPS (443) -> Forward to EC2 (8443)
aws ec2 authorize-security-group-ingress --group-id $SG_NLB --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-egress --group-id $SG_NLB --protocol tcp --port 8443 --source-group $SG_EC2

# SG-EC2: Accept ONLY from NLB on 8443. Allow Outbound to DB (5432) and Internet (443 for API/Docker pulls)
aws ec2 authorize-security-group-ingress --group-id $SG_EC2 --protocol tcp --port 8443 --source-group $SG_NLB
aws ec2 authorize-security-group-egress --group-id $SG_EC2 --protocol tcp --port 5432 --source-group $SG_RDS
aws ec2 authorize-security-group-egress --group-id $SG_EC2 --protocol tcp --port 443 --cidr 0.0.0.0/0

# SG-RDS: Accept ONLY from EC2 on 5432. Absolute isolation.
aws ec2 authorize-security-group-ingress --group-id $SG_RDS --protocol tcp --port 5432 --source-group $SG_EC2
echo "✅ Security Group Matrix Locked."

echo "🎉 Base Network Topology Successfully Provisioned!"
