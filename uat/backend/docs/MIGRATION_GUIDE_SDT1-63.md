# Migration Guide: JWT Secret Key Hardening (SDT1-63)

## Overview

This guide helps you migrate your deployment to use the new hardened JWT secret key handling introduced in SDT1-63.

## What Changed?

### Before (Insecure)
```python
# Hardcoded default - insecure!
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
```

### After (Secure)
```python
# Validated configuration - fails fast if insecure
from config import get_jwt_config
jwt_config = get_jwt_config()
JWT_SECRET = jwt_config["secret"]
```

## Impact Assessment

### ⚠️ Breaking Changes

1. **Production environments MUST have a strong JWT_SECRET**
   - Application will fail to start if secret is missing or weak
   - Default/example secrets are no longer allowed

2. **Environment variable validation**
   - `JWT_SECRET` is now validated for length, entropy, and known weak values
   - Weak secrets will cause startup failure in production

### ✅ Non-Breaking Changes

1. **Development environments are flexible**
   - Auto-generates secret if missing (tokens won't persist across restarts)
   - Weak secrets can be allowed with `ALLOW_WEAK_JWT_SECRET=true` flag

2. **Environment variable names unchanged**
   - `JWT_SECRET` remains the same
   - `JWT_EXPIRY_HOURS` remains the same

## Migration Steps

### Step 1: Generate New Secrets

Generate a unique secret for **each environment** (dev, staging, production):

```bash
# Run this for each environment
python generate_jwt_secret.py
```

**Output:**
```
Generated secure JWT secret (64 bytes, ~512 bits entropy):
h8Kx2Vp9M3Qr5Ts7Uv9Wx1Yz3Ab5Cd7Ef9Gh1Ij3Kl5Mn7Op9Qr1St3Uv5Wx7Yz9Ab1Cd3Ef5Gh7Ij9==

To use this secret, add it to your environment variables:
export JWT_SECRET="h8Kx2Vp9M3Qr5Ts7Uv9Wx1Yz3Ab5Cd7Ef9Gh1Ij3Kl5Mn7Op9Qr1St3Uv5Wx7Yz9Ab1Cd3Ef5Gh7Ij9=="
```

**⚠️ Important:** 
- Save each secret securely (password manager, secrets manager)
- **NEVER** commit secrets to git
- Use **different** secrets for dev, staging, and production

### Step 2: Validate Existing Secret (Optional)

If you already have a secret, validate it:

```bash
python generate_jwt_secret.py --validate "your-existing-secret"
```

**Example output for weak secret:**
```
❌ Secret is weak: Secret is too short (minimum 32 characters recommended, got 15)
Generate a secure secret using: python generate_jwt_secret.py
```

**Example output for strong secret:**
```
✓ Secret appears to be strong
Recommendations:
  - Store securely
  - Never commit to version control
  - Rotate regularly
```

### Step 3: Update Environment Variables

Update your deployment configuration for each environment:

#### Local Development (.env file)

```bash
# .env (add to .gitignore!)
ENVIRONMENT=development
JWT_SECRET=<your-generated-dev-secret>
JWT_EXPIRY_HOURS=24
```

#### Docker

```bash
# Pass as environment variable
docker run \
  -e ENVIRONMENT=production \
  -e JWT_SECRET="<your-generated-secret>" \
  -e JWT_EXPIRY_HOURS=24 \
  your-app:latest
```

#### Docker Compose

```yaml
# docker-compose.yml
services:
  api:
    environment:
      ENVIRONMENT: production
      JWT_SECRET: ${JWT_SECRET}  # From .env or environment
      JWT_EXPIRY_HOURS: 24
```

```bash
# .env (add to .gitignore!)
JWT_SECRET=<your-generated-secret>
```

#### Kubernetes

```bash
# Create secret
kubectl create secret generic jwt-secret \
  --from-literal=JWT_SECRET='<your-generated-secret>'

# Or from file (recommended)
echo -n '<your-generated-secret>' > /tmp/jwt-secret
kubectl create secret generic jwt-secret \
  --from-file=JWT_SECRET=/tmp/jwt-secret
rm /tmp/jwt-secret  # Clean up
```

```yaml
# deployment.yaml
spec:
  containers:
  - name: api
    env:
    - name: ENVIRONMENT
      value: "production"
    - name: JWT_SECRET
      valueFrom:
        secretKeyRef:
          name: jwt-secret
          key: JWT_SECRET
    - name: JWT_EXPIRY_HOURS
      value: "24"
```

#### AWS (ECS/Fargate)

Use AWS Secrets Manager:

```bash
# Store secret in Secrets Manager
aws secretsmanager create-secret \
  --name production/jwt-secret \
  --secret-string '<your-generated-secret>'
```

```json
// Task definition
{
  "containerDefinitions": [{
    "name": "api",
    "environment": [
      {"name": "ENVIRONMENT", "value": "production"},
      {"name": "JWT_EXPIRY_HOURS", "value": "24"}
    ],
    "secrets": [
      {
        "name": "JWT_SECRET",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:production/jwt-secret"
      }
    ]
  }]
}
```

#### Heroku

```bash
# Set config var
heroku config:set ENVIRONMENT=production
heroku config:set JWT_SECRET='<your-generated-secret>'
heroku config:set JWT_EXPIRY_HOURS=24
```

#### Azure

```bash
# Store in Key Vault
az keyvault secret set \
  --vault-name "your-keyvault" \
  --name "JWT-SECRET" \
  --value '<your-generated-secret>'

# Reference in App Service
az webapp config appsettings set \
  --name your-app \
  --resource-group your-rg \
  --settings \
    ENVIRONMENT=production \
    JWT_SECRET="@Microsoft.KeyVault(SecretUri=https://your-keyvault.vault.azure.net/secrets/JWT-SECRET/)" \
    JWT_EXPIRY_HOURS=24
```

### Step 4: Test the Configuration

Before deploying, test that the configuration is valid:

```bash
# Method 1: Direct test
python -c "from config import get_jwt_config; print('✓ JWT config is valid')"

# Method 2: With specific environment
ENVIRONMENT=production JWT_SECRET='<your-secret>' python -c "from config import get_jwt_config; print('✓ Config OK')"

# Method 3: Run full test suite
pytest tests/test_jwt_config.py -v
```

### Step 5: Deploy

Deploy to each environment, starting with development:

1. **Development**
   ```bash
   # Update .env
   # Restart application
   # Verify logs: "✓ JWT configuration validated successfully"
   ```

2. **Staging**
   ```bash
   # Update environment variables
   # Deploy
   # Verify application starts
   # Test authentication flows
   ```

3. **Production**
   ```bash
   # Update environment variables (use secrets manager!)
   # Deploy with rolling update or blue-green
   # Monitor logs for errors
   # Verify authentication works
   ```

### Step 6: Verify

After deployment, verify everything works:

1. **Check application logs**
   ```
   ✓ JWT configuration validated successfully
   ✓ JWT secret configured (86 characters, ~515 bits entropy)
   ```

2. **Test authentication**
   - Register a new user
   - Login and receive JWT
   - Access protected endpoints with JWT
   - Verify token expiry works

3. **Monitor for errors**
   - Check error logs for JWT-related issues
   - Monitor authentication success/failure rates
   - Set up alerts for auth failures

## Rollback Plan

If you need to rollback:

### Quick Rollback (Emergency)

1. **Revert to previous deployment**
   ```bash
   # Docker
   docker run your-app:previous-tag
   
   # Kubernetes
   kubectl rollout undo deployment/api
   
   # Heroku
   heroku releases:rollback
   ```

2. **Keep the new secret in place**
   - The old code will still use it
   - Just won't validate it as strictly

### Planned Rollback

If you need to rollback code but keep the new secret:

1. **Ensure secret is strong** (old code will use it without validation)
2. **Revert code changes**
3. **Keep `JWT_SECRET` environment variable**
4. **Monitor authentication**

## Troubleshooting

### Error: "JWT_SECRET environment variable must be set in production"

**Cause:** `JWT_SECRET` is not set or is empty.

**Solution:**
```bash
# Generate a secret
python generate_jwt_secret.py

# Set environment variable
export JWT_SECRET="<generated-secret>"

# Or update your deployment config
```

### Error: "Insecure JWT secret detected in production"

**Cause:** Your secret is too weak (short, low entropy, common value).

**Solution:**
```bash
# Generate a new secure secret
python generate_jwt_secret.py

# Replace the old secret
export JWT_SECRET="<new-secret>"
```

### Error: Application starts but users can't login

**Cause:** Secret might have changed, invalidating existing tokens.

**Solution:**
- This is expected when rotating secrets
- Users will need to login again
- Consider adding a user notification: "Please login again for security"

### Error: Tokens from development don't work in staging

**Cause:** Different environments should have different secrets (this is correct behavior).

**Solution:**
- This is **intended** - each environment should be isolated
- Users must login separately in each environment
- Never share secrets across environments

### Error: "JWT_EXPIRY_HOURS must be an integer"

**Cause:** Invalid value for `JWT_EXPIRY_HOURS`.

**Solution:**
```bash
# Use integer value
export JWT_EXPIRY_HOURS=24
```

## Security Checklist

Before considering migration complete:

- [ ] Strong secret generated for each environment (dev, staging, prod)
- [ ] Secrets stored securely (secrets manager, not in code/git)
- [ ] Different secrets used for different environments
- [ ] `.env` files added to `.gitignore`
- [ ] Application starts successfully in all environments
- [ ] Authentication flows tested and working
- [ ] Error logs checked for JWT-related issues
- [ ] Team members trained on secret handling
- [ ] Secret rotation schedule established (every 90 days)
- [ ] Documentation updated with new process

## Timeline Recommendation

### Week 1: Preparation
- Generate secrets for all environments
- Store in secrets manager
- Test in development
- Review with team

### Week 2: Staging
- Deploy to staging
- Full QA testing
- Monitor for issues
- Train support team

### Week 3: Production
- Schedule deployment window
- Deploy with rolling update
- Monitor closely
- Send user notification if needed

### Week 4: Cleanup
- Remove old default secrets from docs
- Update runbooks
- Schedule first secret rotation (90 days out)

## Post-Migration

### Establish Secret Rotation

Set up a process to rotate secrets every 90 days:

1. **Generate new secret**
   ```bash
   python generate_jwt_secret.py
   ```

2. **Update secret in secrets manager**
3. **Deploy application** (rolling update)
4. **Users will need to re-login** (tokens become invalid)
5. **Monitor authentication metrics**
6. **Document rotation in change log**

### Monitor and Alert

Set up monitoring:

```yaml
# Example: Prometheus alert
- alert: HighAuthFailureRate
  expr: rate(auth_failures_total[5m]) > 10
  annotations:
    summary: High authentication failure rate
    description: May indicate secret rotation or security issue
```

### Document for Team

Update your team documentation:

- Where secrets are stored (e.g., AWS Secrets Manager)
- How to rotate secrets (runbook)
- Who has access to secrets
- Emergency contact for secret-related issues

## FAQ

**Q: Do existing user sessions need to re-login after migration?**

A: Only if you change the `JWT_SECRET` value. If you're just adding validation to an existing strong secret, users won't notice.

**Q: Can I use the same secret across environments?**

A: **No!** Each environment should have a unique secret for security isolation.

**Q: What happens if I forget the production secret?**

A: You'll need to generate a new one. All existing user sessions will be invalidated and users will need to re-login.

**Q: Can I temporarily disable validation?**

A: In development, set `ALLOW_WEAK_JWT_SECRET=true`. In production, **never** disable validation.

**Q: How do I know if my current secret is strong enough?**

A: Run: `python generate_jwt_secret.py --validate "your-secret"`

**Q: The application won't start in development. What do I do?**

A: Set `ENVIRONMENT=development` or set a valid `JWT_SECRET`.

## Support

If you encounter issues:

1. Check the [JWT Security Documentation](./JWT_SECURITY.md)
2. Review [test examples](../tests/test_jwt_config.py)
3. Run the test suite: `pytest tests/test_jwt_config.py -v`
4. Check application logs for specific error messages
5. Contact the security team

## Related Documentation

- [JWT_SECURITY.md](./JWT_SECURITY.md) - Full JWT security documentation
- [test_jwt_config.py](../tests/test_jwt_config.py) - Test examples
- [generate_jwt_secret.py](../generate_jwt_secret.py) - Secret generator tool
- [.env.example](../.env.example) - Example environment configuration
