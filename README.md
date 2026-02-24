# Define repoistory name

Define description. Test

## Get started

We are currently in the process of standing up [SwaggerHub](https://wwww.swaggerhub.com) to host OpenAPI definitions. More to come.

## AWS deployment action (Sandbox Lambda)

- Workflow: [.github/workflows/deploy-aws.yml](.github/workflows/deploy-aws.yml)
- Deployment target: Sandbox AWS Lambda function

Configure GitHub repository settings before running deployment:

- Secret
  - `SANDBOX_AWS_ROLE_TO_ASSUME`: IAM role ARN that GitHub Actions can assume via OIDC
- Variables
  - `SANDBOX_AWS_REGION`: AWS region (example: `us-east-1`)
  - `SANDBOX_LAMBDA_FUNCTION_NAME`: existing sandbox Lambda function name

## Reference implementation

- Python webhook receiver for transfer status events: [src/webhooks/receiver/README.md](src/webhooks/receiver/README.md)
- Python webhook sender example: [src/webhooks/sender/README.md](src/webhooks/sender/README.md)

Please refer to the [style guide](https://github.com/Insured-Retirement-Institute/Style-Guide) for technical governance of standards, data dictionary, and the code of conduct.

## Business Case

Define your business case for the specification.

## User Stories, personna - supporting documents for the business case

- Load your user stories, personna - supporting documents for the business case.

## Business Owners

- Carrier Business Owner: contact
- Distributor Business Owner: contact
- Solution Provider Business Owner: contact

## How to engage, contribute, and give feedback

- These working groups are occuring on ....
- Please contact the business owners or IRI (hpikus@irionline.org) to get added to the working group discussions.

## Change subsmissions and reporting issues and bugs

Security issues and bugs should be reported directly to Katherine Dease kdease@irionline.org. Issues and bugs can be reported directly within the issues tab of a repository. Change requests should follow the standards governance workflow outlined on the [main page](https://github.com/Insured-Retirement-Institute).

## Code of conduct

See [style guide](https://github.com/Insured-Retirement-Institute/Style-Guide)
