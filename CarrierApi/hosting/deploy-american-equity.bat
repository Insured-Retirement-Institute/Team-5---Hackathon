@echo off
setlocal

set ACCOUNT_ID=533267258893
set REGION=us-east-1
set REPO_NAME=carrier-api
set IMAGE_TAG=latest
set STACK_NAME=carrier-api-american-equity
set CARRIER_NAME=American Equity
set CARRIER_ID=american-equity

echo Building Docker image...
cd /d "%~dp0.."
docker build -t %REPO_NAME%:%IMAGE_TAG% -f hosting/Dockerfile.apprunner .

echo Logging into ECR...
aws ecr get-login-password --region %REGION% | docker login --username AWS --password-stdin %ACCOUNT_ID%.dkr.ecr.%REGION%.amazonaws.com

echo Tagging image...
docker tag %REPO_NAME%:%IMAGE_TAG% %ACCOUNT_ID%.dkr.ecr.%REGION%.amazonaws.com/%REPO_NAME%:%IMAGE_TAG%

echo Pushing to ECR...
docker push %ACCOUNT_ID%.dkr.ecr.%REGION%.amazonaws.com/%REPO_NAME%:%IMAGE_TAG%

echo Deploying CloudFormation stack for %CARRIER_NAME%...
aws cloudformation deploy ^
    --template-file hosting/apprunner-stack.yaml ^
    --stack-name %STACK_NAME% ^
    --parameter-overrides ImageUri=%ACCOUNT_ID%.dkr.ecr.%REGION%.amazonaws.com/%REPO_NAME%:%IMAGE_TAG% CarrierName="%CARRIER_NAME%" CarrierId=%CARRIER_ID% ^
    --capabilities CAPABILITY_IAM ^
    --region %REGION%

echo Getting API Gateway URL...
aws cloudformation describe-stacks ^
    --stack-name %STACK_NAME% ^
    --region %REGION% ^
    --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" ^
    --output text

endlocal
