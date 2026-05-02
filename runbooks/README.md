# Runbooks

Operational runbooks and procedures for the SynPro Virtual Dev Team platform.

## Available Runbooks

### [Token Rotation Runbook](TOKEN_ROTATION.md)

Comprehensive guide for rotating all authentication tokens, API keys, and credentials in the platform.

**Covers:**
- JWT secret rotation (user authentication)
- Railway API token rotation (deployment automation)
- Database credential rotation
- SMTP credential rotation (email service)
- Emergency rotation procedures
- Rollback procedures
- Post-rotation validation

**When to use:**
- Scheduled rotation (every 90-180 days depending on token type)
- Security incident or suspected compromise
- Employee/contractor offboarding
- Accidental credential exposure
- Compliance audit requirements

## Automation Scripts

Located in `scripts/`:

### `rotate_token.sh`

Automated token rotation script with built-in safety features.

```bash
# Rotate JWT secret in staging
./scripts/rotate_token.sh jwt staging

# Rotate Railway API token in production
./scripts/rotate_token.sh railway production

# Rotate SMTP credentials
./scripts/rotate_token.sh smtp staging

# Rotate all tokens (interactive)
./scripts/rotate_token.sh all production
```

**Features:**
- Interactive prompts with confirmation for production
- Automatic backup of current configuration
- Validation of new credentials before deployment
- Rollback capability
- Audit logging

### `validate_rotation.sh`

Post-rotation validation script.

```bash
# Validate staging environment
./scripts/validate_rotation.sh staging

# Validate production environment
./scripts/validate_rotation.sh production
```

**Tests:**
- API health check
- User registration and authentication (JWT)
- Authenticated endpoints
- Password reset email (SMTP)
- Railway API integration
- Database connectivity
- CORS configuration
- Rate limiting
- Response time performance

## Quick Reference

### JWT Secret Rotation

```bash
# 1. Generate new secret
cd uat/backend
python3 generate_jwt_secret.py

# 2. Update environment variable
railway variables --environment production --set JWT_SECRET="<new-secret>"

# 3. Validate
./runbooks/scripts/validate_rotation.sh production
```

### Railway API Token Rotation

```bash
# 1. Generate token at https://railway.app/account/tokens
# 2. Test token
curl -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ projects { edges { node { id } } } }"}'

# 3. Deploy
railway variables --environment production --set RAILWAY_API_TOKEN="<token>"

# 4. Revoke old token in Railway dashboard
```

### Emergency Rotation

For compromised credentials:

```bash
# 1. Immediately generate and deploy new credential
./scripts/rotate_token.sh <type> production

# 2. Revoke old credential
# 3. Check logs for unauthorized access
railway logs --environment production --recent 1000 | grep -i "401\|403\|unauthorized"

# 4. Document incident (see TOKEN_ROTATION.md for template)
```

## Rotation Schedule

| Token Type | Frequency | Next Due | Owner |
|------------|-----------|----------|-------|
| JWT_SECRET | 90 days | [Date] | Security Team |
| RAILWAY_API_TOKEN | 90 days | [Date] | DevOps Team |
| DATABASE_URL | 180 days | [Date] | DBA Team |
| SMTP_PASSWORD | 180 days | [Date] | DevOps Team |

> **Note**: Set calendar reminders 2 weeks before due date to allow time for planning.

## Prerequisites

### Required Tools

- **Railway CLI**: `npm install -g @railway/cli` or download from [railway.app/cli](https://docs.railway.app/develop/cli)
- **Python 3.11+**: For JWT secret generation and validation
- **jq**: For JSON parsing in scripts (`brew install jq` or `apt install jq`)
- **curl**: For API testing (usually pre-installed)

### Authentication

```bash
# Authenticate with Railway
railway login

# Verify authentication
railway whoami

# Link to project (if needed)
railway link
```

### Environment Variables

Set these for validation scripts:

```bash
# API URLs
export API_URL_STAGING="https://staging-api.synpro.example.com"
export API_URL_PROD="https://api.synpro.example.com"

# Railway token (for validation tests)
export RAILWAY_API_TOKEN="<your-token>"
```

## Security Best Practices

1. **Never commit secrets**: All secrets should be in environment variables, never in code
2. **Use strong secrets**: Generate with `generate_jwt_secret.py` for proper entropy
3. **Rotate regularly**: Follow the schedule, don't wait for an incident
4. **Test in staging first**: Always validate rotations in staging before production
5. **Monitor after rotation**: Watch logs for 24 hours after rotation
6. **Document everything**: Log all rotations in audit log
7. **Separate per environment**: Use different secrets for dev/staging/production
8. **Use least privilege**: Grant minimum required permissions for API tokens
9. **Revoke old credentials**: After confirming new ones work, revoke old ones
10. **Have a rollback plan**: Keep backups and know how to restore quickly

## Troubleshooting

### Common Issues

#### "Railway CLI not found"

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or download from
# https://docs.railway.app/develop/cli
```

#### "Not authenticated with Railway"

```bash
railway login
# Follow the browser authentication flow
```

#### "Failed to generate JWT secret"

```bash
# Ensure you're in the correct directory
cd uat/backend

# Verify Python 3 is available
python3 --version

# Try running directly
python3 generate_jwt_secret.py
```

#### "Validation tests failing after rotation"

1. Check application logs: `railway logs --environment production`
2. Verify environment variables are set: `railway variables --environment production`
3. Test endpoints manually with `curl`
4. Consider rolling back (see TOKEN_ROTATION.md)

### Getting Help

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Production outage | ops-oncall@example.com | 15 minutes |
| Security incident | security@example.com | 30 minutes |
| Rotation questions | devops@example.com | 4 hours |
| Documentation updates | Create PR | N/A |

## Maintenance

### Monthly

- [ ] Review rotation schedule
- [ ] Test rotation scripts in staging
- [ ] Verify monitoring and alerts are working

### Quarterly

- [ ] Perform scheduled token rotations
- [ ] Review and update runbook
- [ ] Audit all active credentials

### Annually

- [ ] Full security audit
- [ ] Test emergency rotation procedures
- [ ] Update this documentation
- [ ] Train new team members

## Contributing

To update these runbooks:

1. Create a feature branch
2. Update documentation and/or scripts
3. Test changes in staging
4. Create pull request with clear description
5. Get review from at least one team member
6. Merge to main

### Runbook Template

When creating new runbooks, include:

1. **Overview**: What, when, why
2. **Prerequisites**: Tools, access, knowledge required
3. **Procedure**: Step-by-step instructions with commands
4. **Validation**: How to verify success
5. **Rollback**: How to undo if needed
6. **Troubleshooting**: Common issues and solutions

## License

These runbooks are proprietary and confidential. For internal use only.

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-XX-XX | Initial token rotation runbook | DevOps Team |

---

**Last Updated**: 2024  
**Maintained By**: DevOps & Security Team  
**Questions**: devops@example.com
