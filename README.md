# Define repoistory name

Define description. Test

## Get started

We are currently in the process of standing up [SwaggerHub](https://wwww.swaggerhub.com) to host OpenAPI definitions. More to come.

## Reference implementation

- C# webhook receiver for transfer status events: [src/webhooks/receiver/README.md](src/webhooks/receiver/README.md)
- C# webhook sender example: [src/webhooks/sender/README.md](src/webhooks/sender/README.md)

## AWS deployment action

- Workflow: [.github/workflows/deploy-aws.yml](.github/workflows/deploy-aws.yml)
- Deployment target: **sandbox** Amazon ECS service using an image pushed to Amazon ECR

Configure GitHub repository settings before running deployment:

- Store the sandbox secret and variables below in repository settings (or a GitHub Environment, if preferred)

- Secret
  - `SANDBOX_AWS_ROLE_TO_ASSUME`: IAM role ARN for the sandbox account that GitHub Actions can assume via OIDC
- Variables
  - `SANDBOX_AWS_REGION`: AWS region (example: `us-east-1`)
  - `SANDBOX_ECR_REPOSITORY`: ECR repository name for the webhook receiver image
  - `SANDBOX_ECS_CLUSTER`: sandbox ECS cluster name
  - `SANDBOX_ECS_SERVICE`: sandbox ECS service name
  - `SANDBOX_ECS_TASK_FAMILY`: sandbox ECS task definition family name
  - `SANDBOX_ECS_CONTAINER_NAME`: container definition name in the ECS task to update

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
