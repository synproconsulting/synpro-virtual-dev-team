# Token Rotation Quick Reference

## 🚨 Emergency Token Rotation

If a token has been compromised, act immediately:

```bash
# 1. Emergency rotation
./scripts/rotate_token.py --env production --token-type <type> --emergency

# 2. Monitor for issues
./scripts/health_check.py --comprehensive --env production

# 3. Check for unauthorized access
./scripts/audit_token_usage.py --token-id <id> --hours 72
```

## 📅 Scheduled Rotation

### JWT Secret (Every 90 days)

```bash
# 1. Test in staging first
./scripts/rotate_token.py --env staging --token-type jwt --execute --validate

# 2. Execute in production
./scripts/rotate_token.py --env production --token-type jwt --execute --zero-downtime --validate

# 3. Update schedule
./scripts/check_rotation_schedule.py --update jwt

# 4. Verify
./scripts/health_check.py --comprehensive --env production
```

### Database Password (Every 180 days)

```bash
# 1. Generate new password
./scripts/generate_secrets.py --type database

# 2. Create new database user
psql $DATABASE_URL -c "CREATE USER pm_agent_new WITH PASSWORD '<new-password>';"
psql $DATABASE_URL -c "GRANT ALL PRIVILEGES ON DATABASE pm_agent_db TO pm_agent_new;"

# 3. Execute rotation
./scripts/rotate_token.py --env production --token-type database --execute

# 4. Update schedule
./scripts/check_rotation_schedule.py --update database
```

### Railway API Token (Every 60 days)

```bash
# 1. Generate new token at https://railway.app/account/tokens

# 2. Execute rotation
./scripts/rotate_token.py --env production --token-type railway --execute

# 3. Update schedule
./scripts/check_rotation_schedule.py --update railway

# 4. Test deployments
railway deploy --environment production
```

### SMTP Credentials (Every 180 days)

```bash
# 1. Generate new app password at email provider

# 2. Execute rotation
./scripts/rotate_token.py --env production --token-type smtp --execute

# 3. Update schedule
./scripts/check_rotation_schedule.py --update smtp

# 4. Test email sending
./scripts/test_smtp.py --env production
```

### Jira API Token (Every 90 days)

```bash
# 1. Generate new token at https://id.atlassian.com/manage-profile/security/api-tokens

# 2. Execute rotation
./scripts/rotate_token.py --env production --token-type jira --execute

# 3. Update schedule
./scripts/check_rotation_schedule.py --update jira

# 4. Test Jira integration
./scripts/test_jira_connection.py --env production
```

## 🔄 Rollback

If something goes wrong:

```bash
# Immediate rollback
./scripts/rotate_token.py --env production --token-type <type> --rollback

# Verify rollback
./scripts/health_check.py --comprehensive --env production
```

## 📊 Check Rotation Status

```bash
# View rotation schedule
./scripts/check_rotation_schedule.py --report

# Check for upcoming rotations
./scripts/check_rotation_schedule.py --notify

# Send to Slack
./scripts/check_rotation_schedule.py --notify --webhook $SLACK_WEBHOOK_URL
```

## 🛠️ Generate New Secrets

```bash
# JWT secret
./scripts/generate_secrets.py --type jwt

# Database password
./scripts/generate_secrets.py --type database

# API token
./scripts/generate_secrets.py --type api

# All types
./scripts/generate_secrets.py --all
```

## 🔍 Health Checks

```bash
# Quick health check
./scripts/health_check.py --env production

# Comprehensive check
./scripts/health_check.py --comprehensive --env production

# Wait for service (after rotation)
./scripts/health_check.py --wait --timeout 300 --env production

# Database connectivity
./scripts/health_check.py --db-test --env production
```

## 📋 Pre-Rotation Checklist

- [ ] Backup current token to secure location
- [ ] Test new token in staging environment
- [ ] Schedule maintenance window (if needed)
- [ ] Notify team and users
- [ ] Verify rollback procedure is ready
- [ ] Monitor dashboards open
- [ ] Have backup plan ready

## 📋 Post-Rotation Checklist

- [ ] Verify all services are healthy
- [ ] Test critical functionality
- [ ] Monitor error rates (30 minutes)
- [ ] Check authentication works
- [ ] Update rotation schedule
- [ ] Archive old token securely
- [ ] Document any issues
- [ ] Update runbook if needed

## 🆘 Troubleshooting

### Services won't start after rotation

```bash
# Check environment variables
railway variables --env production | grep <TOKEN_NAME>

# Check service logs
railway logs --env production --tail 100

# Force restart
railway up --env production --restart
```

### Database connection errors

```bash
# Test database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE datname = 'pm_agent_db';"

# Verify new user has permissions
psql $DATABASE_URL -c "SELECT * FROM information_schema.role_table_grants WHERE grantee = 'pm_agent_new';"
```

### Authentication failures

```bash
# Check JWT secret is set
railway variables --env production | grep JWT_SECRET

# Verify token generation
./scripts/verify_jwt.py --env production

# Check auth endpoint
curl -X POST https://api.yourapp.com/auth/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}'
```

## 📞 Support Contacts

- **Security Team**: security@yourcompany.com
- **On-Call Engineer**: oncall@yourcompany.com
- **Incident Hotline**: +1-XXX-XXX-XXXX

## 📚 Related Documentation

- [Full Token Rotation Runbook](./TOKEN_ROTATION.md)
- [Security Policies](./SECURITY.md)
- [Incident Response Plan](./INCIDENT_RESPONSE.md)

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0  
**Ticket**: SDT1-70
