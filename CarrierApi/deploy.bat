@echo off

aws cloudformation delete-stack --stack-name CarrierApi --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name CarrierApi --region us-east-1
aws cloudformation create-stack --stack-name CarrierApi --template-body file://template.yaml --capabilities CAPABILITY_IAM --region us-east-1