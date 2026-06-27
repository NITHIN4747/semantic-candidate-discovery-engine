#!/bin/bash
# INDIA RUNS Hackathon - TrioLogic Database Provisioning
# Provisions the isolated RDS PostgreSQL instance with IAM Auth and pgvector support.

echo "🚀 Initiating Zero-Trust Database Deployment..."

# 1. Satisfy RDS Multi-AZ Subnet Requirements
# RDS requires subnets in at least 2 Availability Zones. We create a second DB subnet here.
# NOTE: Replace $VPC_ID with your actual VPC ID.
VPC_ID="vpc-03a243947f34ba4b2"
SUBNET_DB_2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $SUBNET_DB_2 --tags Key=Name,Value=TrioLogic-DB-Subnet-2

# Create the DB Subnet Group
DB_SUBNET_GROUP="triologic-db-subnet-group"
aws rds create-db-subnet-group \
    --db-subnet-group-name $DB_SUBNET_GROUP \
    --db-subnet-group-description "Private subnets for Semantic Vector DB" \
    --subnet-ids "subnet-0c216aa2b76347ab3" $SUBNET_DB_2

echo "✅ DB Subnet Group Created: $DB_SUBNET_GROUP"

# 2. Launch the PostgreSQL RDS Instance
# We use Postgres 15+ as it natively supports the pgvector extension in AWS RDS.
DB_IDENTIFIER="semantic-vector-db"
echo "🚀 Launching RDS PostgreSQL Instance (This may take 5-10 minutes)..."

# Generate dynamic secure password
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)

aws rds create-db-instance \
    --db-instance-identifier $DB_IDENTIFIER \
    --engine postgres \
    --db-instance-class db.t3.medium \
    --allocated-storage 20 \
    --db-subnet-group-name $DB_SUBNET_GROUP \
    --vpc-security-group-ids "sg-06d637c8e6029259e" \
    --master-username "postgres_admin" \
    --master-user-password "$DB_PASSWORD" \
    --no-publicly-accessible \
    --enable-iam-database-authentication \
    --backup-retention-period 0 \
    --tags Key=Name,Value=TrioLogic-Semantic-VectorDB

echo "🎉 RDS PostgreSQL Instance Provisioning Started!"
echo "🔒 IAM Database Authentication is ENABLED. Static passwords will not be used by the application."
echo "✅ Dynamic Master Password Generated. Please store it in AWS Secrets Manager: aws secretsmanager create-secret --name rds-master-pass --secret-string \"$DB_PASSWORD\""
echo "⚠️ ACTION REQUIRED: Once 'Available', connect via SSM to the EC2 node and run 'CREATE EXTENSION vector;' in the database."
