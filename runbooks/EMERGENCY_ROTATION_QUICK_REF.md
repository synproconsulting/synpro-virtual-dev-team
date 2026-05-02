# Emergency Token Rotation - Quick Reference Card

**⚠️ EMERGENCY USE ONLY - For suspected credential compromise**

> Print this page and keep it accessible for security incidents

---

## Immediate Actions (First 15 Minutes)

### 1. Identify the Compromised Credential

- [ ] JWT_SECRET (user authentication)
- [ ] RAILWAY_API_TOKEN (deployment automation)
- [ ] DATABASE_URL (database access)
- [ ] SMTP_PASSWORD (email service)
- [ ] Other: _______________

### 2. Notify Security Team

**Email**: security@example.com  
**Slack**: #security-incidents  
**Phone**: +1-XXX-XXX-XXXX (on-call)

Include:
- What credential(s) compromised
- When discovered
- How discovered
- Potential impact

---

## Quick Rotation Commands

### JWT Secret (Force all users to re-authenticate)

```bash
# Generate new secret
cd uat/backend
NEW_JWT_SECRET=$(python3 generate_jwt_secret.py | grep -v "Generated" | head -n 1 | tr -d '\n')

# Deploy immediately
railway variables --environment production --set JWT_SECRET="$NEW_JWT_SECRET"

# Verify
railway logs --environment production | grep "JWT secret configured"
```

**Impact**: All users must log in again  
**Downtime**: ~0 seconds  
**Recovery Time**: ~5 minutes

---

### Railway API Token

```bash
# 1. Generate at: https://railway.app/account/tokens
#    Name: emergency-rotation-YYYYMMDD
#    Scopes: Read projects/services/deployments, Trigger deployments

# 2. Deploy new token
railway variables --environment production --set RAILWAY_API_TOKEN="<NEW_TOKEN>"

# 3. Revoke old token immediately at:
#    https://railway.app/account/tokens
```

**Impact**: Deployment operations only  
**Downtime**: ~0 seconds  
**Recovery Time**: ~10 minutes

---

### Database Credentials

```bash
# CRITICAL: This requires database migration or password change
# If your DB supports password change without downtime:

# Option 1: Change password (if supported)
# Contact DBA team immediately: dba@example.com

# Option 2: Temporary measure - restrict access
# Block suspicious IP addresses at firewall/Railway level

# Then follow full database rotation procedure in TOKEN_ROTATION.md
```

**Impact**: Potential brief connection disruption  
**Downtime**: 30-60 seconds  
**Recovery Time**: 1-2 hours

---

### SMTP Credentials

```bash
# 1. Generate new app password at email provider
#    Gmail: https://myaccount.google.com/apppasswords

# 2. Deploy new password
railway variables --environment production --set SMTP_PASSWORD="<NEW_PASSWORD>"

# 3. Revoke old password at email provider
```

**Impact**: Password reset emails only  
**Downtime**: ~0 seconds  
**Recovery Time**: ~5 minutes

---

## Validation Checklist

After rotating any credential:

```bash
# Quick validation
curl https://api.synpro.example.com/api/health
# Expected: 200 OK

# Full validation
cd runbooks/scripts
./validate_rotation.sh production
```

- [ ] Health check returns 200
- [ ] Authentication works (login/register)
- [ ] No error spike in logs
- [ ] No alerts triggered

---

## Rollback (If Rotation Fails)

### Get Backup Credentials

```bash
# Backups are in: runbooks/scripts/backups/
ls -lt runbooks/scripts/backups/ | head -n 5

# View backup (DO NOT log this)
cat runbooks/scripts/backups/env_production_YYYYMMDD_HHMMSS.json
```

### Restore Previous Value

```bash
# Replace with actual value from backup
railway variables --environment production --set JWT_SECRET="<OLD_VALUE>"

# Verify service restarts successfully
railway logs --environment production --tail
```

---

## Incident Documentation Template

Create a ticket immediately with:

```markdown
**Incident ID**: INC-YYYYMMDD-XXX
**Severity**: Critical
**Credential**: <JWT_SECRET|RAILWAY_API_TOKEN|DATABASE_URL|SMTP_PASSWORD>
**Discovered**: YYYY-MM-DD HH:MM UTC
**Discovered By**: <Name>

**Timeline**:
- HH:MM - Credential compromise discovered
- HH:MM - Security team notified
- HH:MM - New credential generated
- HH:MM - New credential deployed
- HH:MM - Old credential revoked
- HH:MM - Validation completed
- HH:MM - Incident resolved

**How Discovered**: 
<Description>

**Scope**: 
- Systems affected: <List>
- Data accessed: <Unknown|Description>
- Duration exposed: <Time period>

**Actions Taken**:
1. <Action 1>
2. <Action 2>

**Status**: Resolved / Ongoing
```

---

## Post-Incident Actions (First 24 Hours)

- [ ] Monitor logs for 24 hours: `railway logs --environment production --follow`
- [ ] Check for unauthorized access in logs
- [ ] Review how credential was compromised
- [ ] Update security procedures to prevent recurrence
- [ ] Complete incident report (see TOKEN_ROTATION.md)
- [ ] Schedule post-mortem meeting

---

## Log Analysis Commands

### Check for Unauthorized Access

```bash
# Authentication failures
railway logs --environment production --recent 1000 | grep -i "401\|403\|unauthorized"

# Unusual API calls
railway logs --environment production --recent 1000 | grep -i "railway\|deployment"

# Database connection attempts
railway logs --environment production --recent 1000 | grep -i "database\|postgres"

# Export logs for analysis
railway logs --environment production --recent 5000 > incident_logs_$(date +%Y%m%d_%H%M%S).log
```

---

## Escalation Path

1. **< 5 minutes**: On-call engineer
2. **5-15 minutes**: Security lead
3. **15-30 minutes**: CTO/VP Engineering
4. **30+ minutes**: CEO (for major breach)

### Contact Information

| Role | Contact | When |
|------|---------|------|
| On-call | ops-oncall@example.com | Immediately |
| Security Lead | security-lead@example.com | Within 5 min |
| CTO | cto@example.com | If ongoing after 15 min |

---

## Don't Panic Checklist

✓ **Take a breath** - You have time to respond correctly  
✓ **Follow this guide** - Steps are tested and safe  
✓ **Ask for help** - Notify security team immediately  
✓ **Document everything** - Keep notes of all actions  
✓ **Validate before declaring success** - Run validation scripts  

---

## Common Mistakes to Avoid

❌ **Don't** rotate without backup  
❌ **Don't** skip validation  
❌ **Don't** forget to revoke old credential  
❌ **Don't** panic and make hasty decisions  
❌ **Don't** keep incident secret - notify team  

✅ **Do** follow this guide step-by-step  
✅ **Do** notify security team immediately  
✅ **Do** backup before rotating  
✅ **Do** validate after rotating  
✅ **Do** document everything  

---

## Quick Reference URLs

- **Railway Dashboard**: https://railway.app
- **Railway Tokens**: https://railway.app/account/tokens
- **Gmail App Passwords**: https://myaccount.google.com/apppasswords
- **Full Runbook**: [TOKEN_ROTATION.md](TOKEN_ROTATION.md)
- **Validation Script**: `runbooks/scripts/validate_rotation.sh`
- **Rotation Script**: `runbooks/scripts/rotate_token.sh`

---

## Emergency Contact Card

```
╔══════════════════════════════════════════════════════════╗
║  SECURITY INCIDENT - EMERGENCY CONTACTS                  ║
╠══════════════════════════════════════════════════════════╣
║  On-call Engineer:  ops-oncall@example.com               ║
║  Security Team:     security@example.com                 ║
║  Phone (24/7):      +1-XXX-XXX-XXXX                      ║
║                                                          ║
║  Slack Channel:     #security-incidents                  ║
║  Incident Hotline:  +1-XXX-XXX-XXXX                      ║
╚══════════════════════════════════════════════════════════╝
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Keep This Accessible**: Print and post near workstation or bookmark in browser

---

## After Using This Guide

1. Mark incident in tracking system
2. Update audit log: `runbooks/scripts/audit.log`
3. Schedule post-mortem within 48 hours
4. Update this guide if procedure needs improvement
5. Thank the team members who helped 👏
