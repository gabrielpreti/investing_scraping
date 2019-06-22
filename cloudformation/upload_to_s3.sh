#!/usr/bin/env bash

rm -rf lambda.zip
zip -j -X lambda.zip scheduler.py investingscrapping_aws.yaml
aws s3 cp lambda.zip s3://preti-lambda-triggers/scripts/lambda.zip

aws cloudformation update-stack --stack-name lambda-triggers --template-body file://./lambda_triggers.yaml --capabilities CAPABILITY_NAMED_IAM
