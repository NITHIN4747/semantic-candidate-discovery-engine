#!/bin/bash
# TrioLogic — Database Provisioning
# Provisions the isolated RDS PostgreSQL instance with IAM Auth and pgvector support.
#
# Prerequisites — run provision_network.sh first, then export its outputs:
#   export VPC_ID=<value from provision_network.sh output>
#   export SUBNET_DB=<value from provision_network.sh output>
#   export SG_RDS=<value from provision_network.sh output>
# All three must be set or this script exits immediately.

echo "🚀 Initiating Zero-Trust Database Deployment..."

# Validate required env vars before touching AWS
: "${VPC_ID:?VPC_ID is not set. Export it from provision_network.sh before running this script.}"
: "${SUBNET_DB:?SUBNET_DB is not set. Export it from provision_network.sh before running this script.}"
: "${SG_RDS:?SG_RDS is not set. Export it from provision_network.sh before running this script.}"

# RDS requires subnets in at least 2 AZs. We create a second DB subnet here.
SUBNET_DB_2=$(aws ec2 create-subnet --vpc-id "$VPC_ID" --cidr-block 10.0.3.0/24 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources "$SUBNET_DB_2" --tags Key=Name,Value=TrioLogic-DB-Subnet-2

DB_SUBNET_GROUP="triologic-db-subnet-group"
aws rds create-db-subnet-group \
    --db-subnet-group-name "$DB_SUBNET_GROUP" \
    --db-subnet-group-description "Private subnets for Semantic Vector DB" \
    --subnet-ids "$SUBNET_DB" "$SUBNET_DB_2"

echo "✅ DB Subnet Group created: $DB_SUBNET_GROUP"

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
    --vpc-security-group-ids "$SG_RDS" \
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
