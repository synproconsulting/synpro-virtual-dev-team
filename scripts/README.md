# Token Rotation Scripts

This directory contains automated scripts for rotating tokens and secrets used by the PM Agent system.

## Overview

Regular token rotation is a critical security practice. These scripts automate the process while maintaining audit trails and minimizing downtime.

**Related Documentation:**
- [Token Rotation Runbook](../docs/runbooks/TOKEN_ROTATION.md) - Comprehensive rotation procedures
- [Quick Reference Guide](../docs/runbooks/QUICK_REFERENCE.md) - Quick commands and checklists

## Scripts

### `rotate_token.py`

**Primary token rotation script** with safety checks and rollback support.

**Features:**
- Automated rotation for JWT, database, Railway, SMTP, and Jira tokens
- Dry-run mode for safe testing
- Zero-downtime rolling restarts
- Automatic backup creation
- Health validation
- Rollback capability

**Usage:**
```bash
# Dry run (recommended first step)
./scripts/rotate_token.py --env production --token-type jwt --dry-run

# Execute rotation with validation
./scripts/rotate_token.py --env production --token-type jwt --execute --validate

# Zero-downtime rotation
./scripts/rotate_token.py --env production --token-type jwt --execute --zero-downtime

# Emergency rotation (skips some checks)
./scripts/rotate_token.py --env production --token-type jwt --emergency

# Rollback to previous token
./scripts/rotate_token.py --env production --token-type jwt --rollback

# Check prerequisites only
./scripts/rotate_token.py --env production --token-type jwt --check-prerequisites
```

**Token Types Supported:**
- `jwt` - JWT secret key (invalidates user sessions)
- `database` - Database credentials (requires database setup)
- `railway` - Railway API token (must be generated manually)
- `smtp` - SMTP password (must be generated manually)
- `jira` - Jira API token (must be generated manually)

### `generate_secrets.py`

**Generate cryptographically secure secrets** for various purposes.

**Features:**
- Multiple secret types
- Configurable length
- Entropy calculation
- Usage hints and examples

**Usage:**
```bash
# Generate JWT secret
./scripts/generate_secrets.py --type jwt

# Generate database password
./scripts/generate_secrets.py --type database

# Generate API token with custom length
./scripts/generate_secrets.py --type api --length 64

# Generate all common secret types
./scripts/generate_secrets.py --all

# Generate multiple secrets
./scripts/generate_secrets.py --type api --count 5

# Without usage hints (for scripting)
./scripts/generate_secrets.py --type jwt --no-hints
```

**Secret Types:**
- `jwt` - JWT secret key (base64, 512 bits default)
- `database` - Database password (mixed case + symbols, 32 chars)
- `api` - API token (URL-safe base64, 48 bytes)
- `symmetric` - Symmetric encryption key (hex, 32 bytes for AES-256)
- `otp` - OTP/TOTP secret (base32 for authenticator apps)
- `csrf` - CSRF token (URL-safe, 32 bytes)
- `random` - Random string (custom charset)

### `check_rotation_schedule.py`

**Track and monitor rotation schedules**, send notifications for upcoming rotations.

**Features:**
- Track last rotation dates
- Calculate next due dates
- Identify overdue rotations
- Send notifications (console, webhook)
- Generate status reports

**Usage:**
```bash
# Generate rotation status report
./scripts/check_rotation_schedule.py --report

# Check and notify for upcoming rotations
./scripts/check_rotation_schedule.py --notify

# Send notifications to Slack webhook
./scripts/check_rotation_schedule.py --notify --webhook https://hooks.slack.com/...

# Update rotation date for JWT token (today)
./scripts/check_rotation_schedule.py --update jwt

# Update with specific date
./scripts/check_rotation_schedule.py --update database --rotated-date 2024-01-15

# Check upcoming rotations (next 14 days)
./scripts/check_rotation_schedule.py --notify --days-ahead 14
```

**Cron Setup:**
```bash
# Add to crontab for monthly check (1st of month, 9 AM)
0 9 1 * * /path/to/scripts/check_rotation_schedule.py --notify --webhook $SLACK_WEBHOOK
```

### `health_check.py`

**Comprehensive health checks** for services after token rotation.

**Features:**
- Health endpoint checks
- Database connectivity tests
- Authentication endpoint validation
- Response time monitoring
- Wait-for-healthy capability

**Usage:**
```bash
# Quick health check
./scripts/health_check.py --env production

# Comprehensive checks
./scripts/health_check.py --comprehensive --env production

# Wait for service to become healthy (after rotation)
./scripts/health_check.py --wait --timeout 300 --env production

# Database connectivity test
./scripts/health_check.py --db-test --env production

# Check staging environment
./scripts/health_check.py --env staging --comprehensive
```

## Installation

### Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Railway CLI** (for production rotations)
   ```bash
   npm install -g @railway/cli
   railway login
   ```

3. **PostgreSQL Client** (for database rotations)
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql-client
   ```

4. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Setup

1. **Create required directories:**
   ```bash
   mkdir -p logs backups/secrets config
   ```

2. **Initialize rotation schedule:**
   ```bash
   ./scripts/check_rotation_schedule.py --report
   ```

3. **Set up notifications (optional):**
   ```bash
   # Add to .env
   echo "ROTATION_NOTIFICATION_WEBHOOK=https://hooks.slack.com/..." >> .env
   ```

4. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.py
   ```

## Token Rotation Quick Start

### First-Time Setup

1. **Check current status:**
   ```bash
   ./scripts/check_rotation_schedule.py --report
   ```

2. **Test in staging first:**
   ```bash
   ./scripts/rotate_token.py --env staging --token-type jwt --execute --validate
   ```

3. **Update schedule after rotation:**
   ```bash
   ./scripts/check_rotation_schedule.py --update jwt
   ```

### Production Rotation

Follow this workflow for all production rotations:

1. **Dry run:**
   ```bash
   ./scripts/rotate_token.py --env production --token-type jwt --dry-run
   ```

2. **Execute with validation:**
   ```bash
   ./scripts/rotate_token.py --env production --token-type jwt --execute --zero-downtime --validate
   ```

3. **Monitor health:**
   ```bash
   ./scripts/health_check.py --comprehensive --env production
   ```

4. **Update schedule:**
   ```bash
   ./scripts/check_rotation_schedule.py --update jwt
   ```

## Default Rotation Frequencies

| Token Type | Frequency | Impact Level |
|------------|-----------|--------------|
| JWT Secret | 90 days | High - Invalidates user sessions |
| Database | 180 days | Medium - Brief service interruption |
| Railway API | 60 days | Low - No user impact |
| SMTP | 180 days | Low - Email sending only |
| Jira API | 90 days | Low - Background operations |

## Directory Structure

```
scripts/
├── README.md                      # This file
├── rotate_token.py                # Main rotation script
├── generate_secrets.py            # Secret generation utility
├── check_rotation_schedule.py     # Schedule tracking
├── health_check.py                # Health validation
└── tests/                         # Test suite (when added)

logs/                              # Rotation logs (created automatically)
├── rotation-20240115-120000.log
└── ...

backups/secrets/                   # Token backups (created automatically)
├── jwt_production_20240115_120000.json
└── ...

config/
└── rotation_schedule.json         # Rotation schedule tracking
```

## Security Best Practices

### 1. Token Storage

- ✅ **DO**: Store in environment variables or secret management systems
- ✅ **DO**: Use Railway variables for production secrets
- ❌ **DON'T**: Commit secrets to git
- ❌ **DON'T**: Store in configuration files

### 2. Access Control

- Limit who can run production rotations
- Use MFA for Railway account
- Audit all rotation activities
- Review backup files regularly

### 3. Rotation Workflow

- Always test in staging first
- Use dry-run mode before execution
- Monitor services for 30 minutes after rotation
- Keep backups for 90 days minimum

### 4. Emergency Procedures

- Use `--emergency` flag for compromised tokens
- Document reason in incident log
- Notify security team
- Review audit logs for unauthorized access

## Troubleshooting

### Issue: "Railway CLI not found"

```bash
# Install Railway CLI
npm install -g @railway/cli

# Verify installation
railway --version

# Login
railway login
```

### Issue: "psql: command not found"

```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install postgresql-client

# Verify
psql --version
```

### Issue: "Permission denied" when running scripts

```bash
# Make scripts executable
chmod +x scripts/*.py

# Or run with python explicitly
python scripts/rotate_token.py --help
```

### Issue: Services fail to start after rotation

```bash
# Check environment variables were updated
railway variables --env production | grep <TOKEN_NAME>

# Check service logs
railway logs --env production --tail 100

# Rollback if needed
./scripts/rotate_token.py --env production --token-type <type> --rollback
```

### Issue: Database connection errors after rotation

```bash
# Test new database credentials
psql "<new-database-url>" -c "SELECT 1;"

# Check connection pool
psql "<new-database-url>" -c "SELECT * FROM pg_stat_activity;"

# Verify user permissions
psql "<new-database-url>" -c "\\du"
```

### Issue: "No backup available for rollback"

```bash
# List available backups
ls -la backups/secrets/<token-type>_<env>_*.json

# The rollback command will automatically find the most recent backup
# Or manually specify a backup file (requires code modification)
```

## Monitoring and Alerting

### Post-Rotation Monitoring

Monitor these metrics for 30 minutes after rotation:

1. **Service Health**
   ```bash
   watch -n 10 './scripts/health_check.py --env production'
   ```

2. **Error Logs**
   ```bash
   railway logs --env production | grep -i error
   ```

3. **Response Times**
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s https://api.yourapp.com/health
   ```

### Setting Up Alerts

Add to monitoring system:
- Authentication failures > 10/minute
- Service health check failures
- Database connection pool exhaustion
- Response time > 2 seconds

## Compliance and Auditing

### Audit Trail

All rotations are logged to:
1. `logs/rotation-*.log` - Detailed operation logs
2. `backups/secrets/*.json` - Token backups with timestamps
3. `config/rotation_schedule.json` - Rotation history
4. Railway audit logs (automatic)

### Required Documentation

For each rotation, maintain:
- Date and time
- Environment
- Token type rotated
- Operator name
- Reason (scheduled/emergency)
- Any issues encountered
- Verification results

### Compliance Reports

```bash
# Generate rotation status report
./scripts/check_rotation_schedule.py --report

# Check for overdue rotations
./scripts/check_rotation_schedule.py --report | grep "overdue"

# List all rotations in last 90 days
grep "rotation completed" logs/rotation-*.log | tail -20
```

## Testing

### Unit Tests (To Be Implemented)

```bash
# Run all tests
pytest scripts/tests/

# With coverage
pytest --cov=scripts scripts/tests/

# Specific test
pytest scripts/tests/test_token_rotation.py -v
```

### Manual Testing Checklist

Before using scripts in production:

- [ ] Test dry-run mode in staging
- [ ] Test actual rotation in staging
- [ ] Verify rollback works in staging
- [ ] Test health checks
- [ ] Verify backup creation
- [ ] Test schedule tracking
- [ ] Test notification system

## Contributing

When contributing to these scripts:

1. **Test thoroughly in staging**
2. **Add error handling** for all external calls
3. **Include type hints** on all functions
4. **Add docstrings** for public functions
5. **Update README** with new features
6. **Follow existing code style**
7. **Consider security implications**

## Support

For issues or questions:

- **Documentation**: See [Token Rotation Runbook](../docs/runbooks/TOKEN_ROTATION.md)
- **Quick Reference**: See [Quick Reference Guide](../docs/runbooks/QUICK_REFERENCE.md)
- **Security Team**: security@yourcompany.com
- **DevOps Team**: devops@yourcompany.com
- **On-Call**: Check PagerDuty

## License

Internal use only - PM Agent system

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0  
**Ticket**: SDT1-70
