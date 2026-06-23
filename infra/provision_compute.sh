#!/bin/bash
# INDIA RUNS Hackathon - TrioLogic Compute & IAM Provisioning
# Establishes Zero-Trust IAM roles, SSM access, and launches the IMDSv2-hardened EC2 node.

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

# 4. Launch the Nitro-Attested EC2 Instance
# NOTE: Replace 'ami-XXXXXXX', 'subnet-XXXXXXX', and 'sg-XXXXXXX' with the actual IDs from your provision_network.sh output.
# We are utilizing an Amazon Linux 2023 AMI which supports NitroTPM natively.

echo "🚀 Launching EC2 Compute Node..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.xlarge \
    --subnet-id subnet-04c4ed24d6af8d75a \
    --security-group-ids sg-049c6175bba321723 \
    --iam-instance-profile Name=$PROFILE_NAME \
    --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2,HttpEndpoint=enabled" \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=TrioLogic-Semantic-Engine}]' \
    --query 'Instances[0].InstanceId' --output text)

echo "🎉 Compute Node Launched: $INSTANCE_ID"
echo "🔒 IMDSv2 Enforced with Hop Limit = 2. Container metadata access is secured."

# Cleanup temp files
rm ec2-trust-policy.json app-permissions-policy.json
