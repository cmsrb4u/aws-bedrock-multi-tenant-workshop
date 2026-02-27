"""
Lab: Application Inference Profiles (AIP) Setup

Let's set up our AWS SDK (boto3) clients for working with Bedrock Application Inference Profiles.

What we're initializing:
- bedrock_client: For AIP management (create, read, update, delete)
- bedrock_runtime: For model inference (we'll use this in Lab 03)
- Configuration from lab helpers (Region, ModelId, Tags)
"""

import boto3
from datetime import datetime
import sys
from lab_helpers.config import Region, ModelId, tenant_a_tags, tenant_b_tags

print("=" * 80)
print("🚀 Setting up AWS Bedrock Clients for Application Inference Profiles")
print("=" * 80)

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock', region_name=Region)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=Region)

print(f"\n✅ Bedrock Client initialized")
print(f"   Region: {Region}")
print(f"   Service: bedrock (for AIP management)")

print(f"\n✅ Bedrock Runtime Client initialized")
print(f"   Region: {Region}")
print(f"   Service: bedrock-runtime (for model inference)")

print(f"\n📋 Configuration loaded:")
print(f"   Default Model: {ModelId.DEFAULT}")
print(f"   Tenant A Tags: {tenant_a_tags}")
print(f"   Tenant B Tags: {tenant_b_tags}")

print("\n" + "=" * 80)
print("✅ Setup complete! Ready to work with Application Inference Profiles")
print("=" * 80)
