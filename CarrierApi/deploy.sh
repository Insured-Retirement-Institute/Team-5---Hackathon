#!/bin/bash

# Build and deploy the Lambda function with API Gateway
sam build
sam deploy --guided