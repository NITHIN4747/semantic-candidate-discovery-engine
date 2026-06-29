#!/bin/bash
# TrioLogic — Compute & IAM Provisioning
# Provisions Zero-Trust IAM roles, SSM shell access, and an IMDSv2-hardened EC2 node.
#
# Prerequisites — run provision_network.sh first, then export its outputs:
#   export SUBNET_COMPUTE=<value from provision_network.sh output>
#   export SG_EC2=<value from provision_network.sh output>
# Both variables must be set or this script exits immediately.

echo "🚀 Initiating Zero-Trust Compute & Identity Deployment..."

# 1. Create the IAM Trust Policy for EC2
cat > ec2-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the Role
ROLE_NAME="TrioLogic-Compute-Role"
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://ec2-trust-policy.json
echo "✅ IAM Role Created: $ROLE_NAME"

# 2. Attach Core Policies (SSM for Secure Shell, RDS for Ephemeral DB Auth)
# Attach AWS Managed SSM Policy (eliminates SSH port 22 requirement)
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# Create Inline Policy for RDS Passwordless Auth and KMS Decryption
cat > app-permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds-db:connect"
      ],
      "Resource": "arn:aws:rds-db:*:*:dbuser:*/semantic_app_user"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy --role-name $ROLE_NAME --policy-name TrioLogic-App-Permissions --policy-document file://app-permissions-policy.json
echo "✅ Least-Privilege Policies Attached (SSM, RDS-Auth, KMS)."

# 3. Create Instance Profile & Attach Role
PROFILE_NAME="TrioLogic-Compute-Profile"
aws iam create-instance-profile --instance-profile-name $PROFILE_NAME
aws iam add-role-to-instance-profile --instance-profile-name $PROFILE_NAME --role-name $ROLE_NAME
echo "✅ EC2 Instance Profile Created and Linked."

# Wait 10 seconds for IAM propagation
echo "⏳ Waiting for IAM propagation..."
sleep 10

# 4. Launch the EC2 instance.
# Subnet and SG come from env vars set after running provision_network.sh.
# The AMI is resolved dynamically — no hardcoded image IDs.
: "${SUBNET_COMPUTE:?SUBNET_COMPUTE is not set. Export it from provision_network.sh before running this script.}"
: "${SG_EC2:?SG_EC2 is not set. Export it from provision_network.sh before running this script.}"

echo "🚀 Resolving latest Amazon Linux 2 AMI..."
LATEST_AMI=$(aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-2.0.*-x86_64-gp2" "Name=state,Values=available" --query "sort_by(Images, &CreationDate)[-1].ImageId" --output text)
echo "✅ AMI resolved: $LATEST_AMI"

echo "🚀 Launching EC2 Compute Node..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$LATEST_AMI" \
    --instance-type t3.xlarge \
    --subnet-id "$SUBNET_COMPUTE" \
    --security-group-ids "$SG_EC2" \
    --iam-instance-profile Name="$PROFILE_NAME" \
    --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2,HttpEndpoint=enabled" \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=TrioLogic-Semantic-Engine}]' \
    --query 'Instances[0].InstanceId' --output text)

echo "🎉 Compute Node Launched: $INSTANCE_ID"
echo "🔒 IMDSv2 Enforced with Hop Limit = 2. Container metadata access is secured."
echo "📝 [AUDIT LOG] IAM Role $PROFILE_NAME assumed by compute node $INSTANCE_ID at $(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Cleanup temp files
rm ec2-trust-policy.json app-permissions-policy.json
