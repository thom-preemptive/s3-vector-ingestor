# Authentication Flow - ID Token vs Access Token

## The Issue (Diagnostic Test #5)

```json
{
  "status": 401,
  "detail": "Invalid authentication credentials: Failed to get user info: An error occurred (NotAuthorizedException) when calling the GetUser operation: Invalid Access Token"
}
```

## Root Cause

The backend had a **token type mismatch**:

1. **Frontend**: Correctly sends ID Token in `Authorization: Bearer <id_token>` header
2. **Backend**: 
   - ✅ Verifies the ID token using JWT validation (correct)
   - ❌ Tries to call `cognito_client.get_user(AccessToken=id_token)` (wrong!)
   - The AWS Cognito `GetUser` API requires an **access token**, not an ID token

## Understanding Token Types

### ID Token
- **Purpose**: Contains user identity information (claims)
- **Contents**: `sub`, `email`, `cognito:username`, etc.
- **Use case**: Client-side verification of user identity
- **Format**: JWT that can be verified against Cognito JWKS

### Access Token
- **Purpose**: Grants access to AWS resources
- **Contents**: Scopes, permissions, client ID
- **Use case**: Calling AWS APIs like GetUser, accessing resources
- **Format**: JWT for API authorization

## The Fix

**Before** (incorrect):
```python
async def get_current_user(credentials):
    token = credentials.credentials
    token_payload = await cognito_service.verify_token(token)  # ✅ Works with ID token
    user_info = await cognito_service.get_user_info(token)      # ❌ Needs access token!
    return {...}
```

**After** (correct):
```python
async def get_current_user(credentials):
    token = credentials.credentials
    token_payload = await cognito_service.verify_token(token)  # ✅ Verify ID token
    
    # Extract user info directly from ID token payload
    return {
        "user_id": token_payload.get("sub"),
        "username": token_payload.get("cognito:username", token_payload.get("email")),
        "email": token_payload.get("email"),
        "token_payload": token_payload
    }
```

## Why This Works

The ID token already contains all the user information we need:
- `sub` - User ID (unique identifier)
- `email` - User's email address
- `cognito:username` - Username in Cognito
- Other claims as configured in the User Pool

**No need to make an additional API call to GetUser!**

## Benefits of This Approach

1. ✅ **Faster**: No additional AWS API call
2. ✅ **Simpler**: Direct extraction from JWT payload
3. ✅ **Correct**: Uses ID token for its intended purpose
4. ✅ **Secure**: Token is already verified via JWT signature check

## When You Would Need Access Token

You'd need the access token if you were:
- Calling `GetUser` API to get real-time user attributes
- Accessing user pools or identity pools
- Making calls to AWS services on behalf of the user

But for simple authentication/authorization, the ID token is sufficient.

## Deployment

- ✅ Backend deployed to Lambda
- ✅ Changes committed and pushed

## Testing

Run diagnostics again - Test #5 should now pass with status 200! 🎉
