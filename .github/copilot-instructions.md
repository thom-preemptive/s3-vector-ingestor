# Copilot Instructions: agent2_ingestor Project

This file tracks the systematic setup and development of the cloud-ready, multi-user agent2_ingestor for AWS. Check off each item as you complete it.

## Coding Standards
- Use TypeScript with strict mode; no `any` types.
- Follow ESLint (airbnb) and Prettier for formatting.
- React: Use functional components, hooks, and memoization.
- Backend: Express with RESTful routes; validate inputs with Joi.
- Infrastructure: AWS SAM for IaC; separate resources per environment (dev, test, main).
- CI/CD: GitHub Actions for automated testing and deployment.
- Documentation: Maintain clear README and inline comments.
- Testing: Jest for unit tests (80%+ coverage); Cypress for end-to-end tests.
- Security: Use AWS IAM roles and policies; secure sensitive data with AWS Secrets Manager or Parameter Store.
- Monitoring: Integrate AWS CloudWatch for logging and monitoring.
- Version Control: Use Git with feature branching and pull requests.
- Code Reviews: Mandatory for all pull requests.
- Environment Variables: Use `.env` files and AWS Systems Manager Parameter Store.
- Error Handling: Implement global error handling middleware in Express.
- Performance: Optimize React components and backend endpoints for performance.
- Accessibility: Ensure frontend complies with WCAG standards.
- Responsive Design: Ensure the frontend is mobile-friendly and responsive.
- Localization: Prepare the app for future localization (i18n).
- API Documentation: Use Swagger for documenting backend APIs.
- Database: Use DynamoDB with proper indexing and partitioning strategies. Respect environment segregation.
- File Structure: Maintain a clear and organized file structure for both frontend and backend.
- Deployment: Use AWS SAM CLI for deploying infrastructure and applications.
- Testing Environments: Maintain separate AWS environments for development (DEV), testing (TEST), and production (MAIN).
- Backup and Recovery: Implement backup strategies for DynamoDB and S3.
- Logging: Ensure all services log appropriately to AWS CloudWatch.
- Use camelCase for variables, PascalCase for components.
- Include JSDoc for public functions.
- Commit messages: "type(scope): description" (e.g., `feat(auth): add OAuth flow`).
- When coding in Python, follow PEP 8 guidelines, and assume Python 3.13.3 or later.

## Notes
- Update this checklist as you complete each step.
- Add additional requirements or steps as needed.

## Best Practices
- Always test code locally before pushing.
- Use environment variables for configuration.
- Regularly update dependencies to avoid security vulnerabilities.
- Keep functions small and focused on a single task.
- Use async/await for asynchronous operations.
- Document complex logic and decisions in code comments.
- Regularly review and refactor code for maintainability.
- Ensure all AWS resources are tagged appropriately for cost tracking.
- Always use IAM roles with the least privilege necessary.
- Regularly back up critical data and configurations.
- Use AWS CloudFormation or SAM templates for infrastructure as code.
- Regularly monitor application performance and error rates.
- Use AWS X-Ray for tracing and debugging distributed applications.
- Always review security settings for AWS services.
- Prefer concise explanations before code.
- Prioritize type safety and error handling in suggestions.
- When checking the status of an Amplify deployment, provide the Job ID, but do NOT monitor the status continuously if you detect that there is a build already running.

## Constraints
- Always place all work in the environment us-east-1.
- Always ensure that function, tables, and buckets are environment-specific (dev, test, main).
