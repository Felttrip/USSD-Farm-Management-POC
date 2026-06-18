#!/usr/bin/env python3
import argparse
import json

import boto3


def invoke_claude(prompt: str, model_id: str = "us.anthropic.claude-sonnet-4-6-20250514-v1:0", region: str = "us-east-1") -> str:
    client = boto3.client("bedrock-runtime", region_name=region)

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    })

    response = client.invoke_model(modelId=model_id, body=body)
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="Invoke Claude on AWS Bedrock")
    parser.add_argument("prompt", help="The prompt to send to Claude")
    parser.add_argument("--model", default="us.anthropic.claude-sonnet-4-6-20250514-v1:0", help="Bedrock model ID")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    response = invoke_claude(args.prompt, model_id=args.model, region=args.region)
    print(response)


if __name__ == "__main__":
    main()
