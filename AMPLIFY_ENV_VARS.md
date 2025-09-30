# AWS CLI Commands to Set Environment Variables for Amplify

## Set Environment Variables for DEV Branch
```bash
aws amplify update-branch \
    --app-id dn1hdu83qdv9u \
    --branch-name dev \
    --environment-variables \
        "REACT_APP_COGNITO_USER_POOL_ID=us-east-1_ZXccV9Ntq" \
        "REACT_APP_COGNITO_CLIENT_ID=3u5hedl2mp0bvg5699l16dj4oe" \
        "AWS_BRANCH=dev" \
        "REACT_APP_AMPLIFY_ENV=dev" \
        "REACT_APP_AWS_REGION=us-east-1" \
    --region us-east-1
```

## Set Environment Variables for TEST Branch (when created)
```bash
aws amplify update-branch \
    --app-id dn1hdu83qdv9u \
    --branch-name test \
    --environment-variables \
        "REACT_APP_COGNITO_USER_POOL_ID=us-east-1_epXBgyusk" \
        "REACT_APP_COGNITO_CLIENT_ID=7h6q69gsuoo77200knu88dmoe4" \
        "AWS_BRANCH=test" \
        "REACT_APP_AMPLIFY_ENV=test" \
        "REACT_APP_AWS_REGION=us-east-1" \
    --region us-east-1
```

## Set Environment Variables for MAIN Branch (when created)
```bash
aws amplify update-branch \
    --app-id dn1hdu83qdv9u \
    --branch-name main \
    --environment-variables \
        "REACT_APP_COGNITO_USER_POOL_ID=us-east-1_KD9IBTRJl" \
        "REACT_APP_COGNITO_CLIENT_ID=4eq1gmn394e8ct1gpjra89vgak" \
        "AWS_BRANCH=main" \
        "REACT_APP_AMPLIFY_ENV=main" \
        "REACT_APP_AWS_REGION=us-east-1" \
    --region us-east-1
```

## Verify Environment Variables
```bash
# Check current environment variables for dev branch
aws amplify get-branch --app-id dn1hdu83qdv9u --branch-name dev --region us-east-1

# List all branches and their environment variables
aws amplify list-branches --app-id dn1hdu83qdv9u --region us-east-1
```

## Force New Deployment After Setting Variables
```bash
# Start a new job to rebuild with new environment variables
aws amplify start-job \
    --app-id dn1hdu83qdv9u \
    --branch-name dev \
    --job-type RELEASE \
    --region us-east-1
```