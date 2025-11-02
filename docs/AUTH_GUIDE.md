# Authentication & Authorization Guide

This guide explains the API authentication and authorization features.

## Overview

The application supports multiple authentication methods:
- **JWT Tokens** - JSON Web Tokens for session-based auth
- **API Keys** - Long-lived keys for service-to-service auth
- **Role-Based Access Control (RBAC)** - Fine-grained permissions

## Authentication Methods

### 1. JWT Token Authentication

**Usage**: Send token in `Authorization` header

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8080/protected
```

**Features**:
- Expires after configured hours (default: 24 hours)
- Contains user and role information
- Signed with secret key

### 2. API Key Authentication

**Usage**: Send API key in `X-API-Key` header

```bash
curl -H "X-API-Key: <api_key>" http://localhost:8080/api-key-test
```

**Features**:
- Long-lived credentials
- Generated per user
- Can be revoked

## Authentication Endpoints

### POST `/auth/login`

Login and receive authentication tokens.

**Request**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "api_key": "abc123xyz...",
  "user": "admin",
  "roles": ["admin", "user"],
  "expires_in": 86400
}
```

**Demo Credentials**:
- Admin: `username=admin`, `password=admin123`
- User: `username=user`, `password=user123`

### GET `/auth/validate`

Validate current authentication token.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "status": "valid",
  "user": "admin",
  "roles": ["admin", "user"],
  "authenticated": true
}
```

### GET `/auth/api-keys`

List all API keys (admin only).

**Headers**: `Authorization: Bearer <admin_token>`

**Response**:
```json
{
  "status": "success",
  "api_keys": [
    {
      "user": "admin",
      "roles": ["admin", "user"],
      "created_at": "2025-11-02T01:00:00",
      "key_preview": "abc12345..."
    }
  ],
  "total": 1
}
```

## Protected Endpoints

### GET `/protected`

Requires JWT authentication.

```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}' \
  | jq -r '.token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/protected
```

### GET `/admin`

Requires admin role.

```bash
# Use admin token
ADMIN_TOKEN=$(curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8080/admin
```

### GET `/api-key-test`

Requires API key authentication.

```bash
# Get API key from login
API_KEY=$(curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}' \
  | jq -r '.api_key')

curl -H "X-API-Key: $API_KEY" http://localhost:8080/api-key-test
```

## Rate Limiting

Endpoints have configurable rate limits:

```python
@auth.rate_limit(max_requests=60, window_seconds=60)
```

**Example**: Maximum 60 requests per 60 seconds

**Response when exceeded**:
```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 60 requests per 60 seconds",
  "retry_after": 60
}
```
**Status Code**: `429 Too Many Requests`

## Role-Based Access Control

### Roles

- **admin**: Full access to all endpoints
- **user**: Standard user access

### Protecting Endpoints

```python
# Require any authentication
@auth.require_auth(jwt_required=True)

# Require specific role
@auth.require_auth(jwt_required=True, roles=['admin'])

# Require API key
@auth.require_auth(api_key_required=True)
```

### Accessing User Info

In protected endpoints:
```python
@app.route('/my-endpoint')
@auth.require_auth(jwt_required=True)
def my_endpoint():
    user = g.current_user  # Current user
    roles = g.user_roles    # User roles
    authenticated = g.authenticated  # Auth status
```

## Usage Examples

### Complete Authentication Flow

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

# 2. Extract token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')
API_KEY=$(echo $LOGIN_RESPONSE | jq -r '.api_key')

# 3. Use token for protected endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/protected

# 4. Use API key for another endpoint
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api-key-test

# 5. Validate token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/auth/validate
```

### Testing Rate Limiting

```bash
# Make rapid requests
for i in {1..70}; do
  curl http://localhost:8080/ > /dev/null 2>&1
done

# 61st request should return 429
curl http://localhost:8080/
```

## Security Best Practices

### 1. Environment Variables

**Never hardcode secrets**:
```python
# ? Bad
JWT_SECRET = "my-secret-key"

# ? Good
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
```

### 2. Token Expiration

Set appropriate expiration:
```python
JWT_EXPIRATION_HOURS = 24  # Adjust based on security requirements
```

### 3. HTTPS Only

In production, always use HTTPS:
```python
# Enforce HTTPS
@app.before_request
def enforce_https():
    if not request.is_secure and app.env != 'development':
        return redirect(request.url.replace('http://', 'https://'))
```

### 4. Rate Limiting with Redis

For distributed systems, use Redis:
```python
# Instead of in-memory storage
# Use Redis for rate limiting
@auth.rate_limit(redis_client=redis_client, ...)
```

### 5. Secure Password Storage

In production:
- Never store plain passwords
- Use bcrypt/Argon2 for hashing
- Compare with `hmac.compare_digest()` for timing safety

### 6. API Key Management

- Store in database with expiration
- Support key rotation
- Implement revocation endpoint
- Log API key usage

## Troubleshooting

### Token Invalid

**Symptoms**: `401 Unauthorized`

**Check**:
```bash
# Verify token format
echo $TOKEN | cut -d. -f1-3 | wc -w  # Should be 3 parts

# Check expiration
# Decode payload and check 'exp' field
```

### Rate Limit Exceeded

**Symptoms**: `429 Too Many Requests`

**Solutions**:
- Wait for window to reset
- Reduce request frequency
- Increase rate limit if appropriate
- Use different IP/user if testing

### Role Denied

**Symptoms**: `403 Forbidden`

**Check**:
```bash
# Verify user roles
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/auth/validate

# Ensure correct role required
# Check endpoint requires: roles=['admin']
```

## Production Considerations

### 1. Use PyJWT Library

Replace simplified JWT with PyJWT:
```python
import jwt
token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
```

### 2. Database-Backed Auth

- Store users in database
- Hash passwords with bcrypt
- Store API keys in database
- Implement token refresh

### 3. OAuth2/OpenID Connect

For enterprise, consider:
- OAuth2 authorization server
- OpenID Connect for identity
- Integration with LDAP/Active Directory

### 4. Monitoring

- Log authentication failures
- Monitor rate limit hits
- Track token usage patterns
- Alert on suspicious activity

## Next Steps

- Implement password reset
- Add token refresh endpoint
- Integrate with database for user management
- Add multi-factor authentication (MFA)
- Implement API key rotation
