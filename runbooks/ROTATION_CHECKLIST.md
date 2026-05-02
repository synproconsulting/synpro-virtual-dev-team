# Token Rotation Checklist

Use this checklist for scheduled token rotations to ensure all steps are completed.

---

## Pre-Rotation Planning

**Rotation Date**: _______________  
**Token Type**: [ ] JWT_SECRET [ ] RAILWAY_API_TOKEN [ ] DATABASE_URL [ ] SMTP_PASSWORD  
**Environment**: [ ] Staging [ ] Production  
**Performed By**: _______________  

### Two Weeks Before

- [ ] **Schedule rotation** in team calendar
- [ ] **Notify team** of upcoming rotation via email/Slack
- [ ] **Review runbook** for any updates (see [TOKEN_ROTATION.md](TOKEN_ROTATION.md))
- [ ] **Check dependencies** - any services that might be affected?
- [ ] **Verify prerequisites**:
  - [ ] Railway CLI installed and authenticated
  - [ ] Python 3.11+ available
  - [ ] Access to production environment
  - [ ] Backup directory accessible
- [ ] **Schedule maintenance window** (low-traffic time)
- [ ] **Assign backup person** in case primary is unavailable

### One Week Before

- [ ] **Send reminder** to team
- [ ] **Test rotation in staging** first
- [ ] **Verify monitoring and alerting** is working
- [ ] **Review rollback procedure**
- [ ] **Prepare communication templates**:
  - [ ] User notification (if needed)
  - [ ] Team update
  - [ ] Post-rotation summary
- [ ] **Check for any ongoing incidents** - reschedule if necessary

### One Day Before

- [ ] **Final team reminder**
- [ ] **Verify maintenance window** is clear
- [ ] **Test backup/restore process** in staging
- [ ] **Review expected impact**:
  - Will users need to re-authenticate? _______________
  - Will there be any downtime? _______________
  - Which services are affected? _______________
- [ ] **Prepare rollback credentials** (have them ready but secured)
- [ ] **Ensure team is available** during rotation window

---

## Rotation Day - Pre-Execution

**Date**: _______________  
**Time**: _______________ UTC  

### Setup (15 minutes before)

- [ ] **Log in to Railway**: `railway login`
- [ ] **Verify authentication**: `railway whoami`
- [ ] **Check service health**: 
  ```bash
  curl https://api.synpro.example.com/api/health
  # Expected: 200 OK
  ```
- [ ] **Review current configuration**:
  ```bash
  railway variables --environment production
  ```
- [ ] **Notify team**: Rotation starting in 15 minutes

### Backup Current Configuration

- [ ] **Create backup directory**: `mkdir -p runbooks/scripts/backups`
- [ ] **Export environment variables**:
  ```bash
  railway variables --environment production --json > \
    runbooks/scripts/backups/env_production_$(date +%Y%m%d_%H%M%S).json
  ```
- [ ] **Verify backup file** exists and is not empty
- [ ] **Record backup location**: _______________

---

## Rotation Execution

### For JWT Secret Rotation

- [ ] **Generate new secret**:
  ```bash
  cd uat/backend
  python3 generate_jwt_secret.py
  ```
- [ ] **Copy generated secret** (secure location): _______________
- [ ] **Validate new secret**:
  ```bash
  python3 generate_jwt_secret.py --validate "NEW_SECRET_HERE"
  ```
  - Expected: "✓ Secret appears to be strong"
- [ ] **Update environment variable**:
  ```bash
  railway variables --environment production --set JWT_SECRET="NEW_SECRET_HERE"
  ```
- [ ] **Record deployment time**: _______________ UTC
- [ ] **Wait for service restart** (monitor logs):
  ```bash
  railway logs --environment production --tail
  ```
- [ ] **Look for**: "✓ JWT secret configured"
- [ ] **Time when service is back up**: _______________ UTC

### For Railway API Token Rotation

- [ ] **Generate new token** at https://railway.app/account/tokens
  - Token name: `synpro-vdt-production-YYYYMMDD`
  - Scopes: ✓ Read projects/services/deployments, ✓ Trigger deployments
- [ ] **Copy token** (secure location): _______________
- [ ] **Test new token**:
  ```bash
  curl -X POST https://backboard.railway.app/graphql/v2 \
    -H "Authorization: Bearer NEW_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"{ projects { edges { node { id } } } }"}'
  ```
  - Expected: Returns list of projects
- [ ] **Update environment variable**:
  ```bash
  railway variables --environment production --set RAILWAY_API_TOKEN="NEW_TOKEN"
  ```
- [ ] **Record deployment time**: _______________ UTC
- [ ] **Verify service restart**: Watch logs
- [ ] **Test deployment operation** via UAT Deploy tab

### For Database Credentials Rotation

> Note: Follow detailed procedure in TOKEN_ROTATION.md

- [ ] **Verify database backup** completed within last 24 hours
- [ ] **Create new database user** (or generate new password)
- [ ] **Grant all required permissions** to new user
- [ ] **Test connection** with new credentials
- [ ] **Update DATABASE_URL**:
  ```bash
  railway variables --environment production --set \
    DATABASE_URL="postgresql://newuser:newpass@host:port/db"
  ```
- [ ] **Monitor for connection errors**
- [ ] **Verify database operations** work (registration, login, etc.)
- [ ] **Schedule old user removal** (after 48 hours of stability)

### For SMTP Credentials Rotation

- [ ] **Generate new app password** at email provider
- [ ] **Copy password** (secure location): _______________
- [ ] **Test SMTP connection**:
  ```bash
  python3 -c "
  import smtplib
  import os
  smtp = smtplib.SMTP('smtp.gmail.com', 587)
  smtp.starttls()
  smtp.login('your-email@example.com', 'NEW_PASSWORD')
  print('✓ SMTP authenticated')
  "
  ```
- [ ] **Update environment variable**:
  ```bash
  railway variables --environment production --set SMTP_PASSWORD="NEW_PASSWORD"
  ```
- [ ] **Test password reset** email flow
- [ ] **Verify email received**
- [ ] **Revoke old app password** at email provider

---

## Post-Rotation Validation

### Immediate Validation (Within 5 Minutes)

- [ ] **Health check**:
  ```bash
  curl https://api.synpro.example.com/api/health
  ```
  Status: _______________
  
- [ ] **Check logs** for errors:
  ```bash
  railway logs --environment production --recent 100
  ```
  Errors found: [ ] None [ ] Yes (describe): _______________

- [ ] **Run validation script**:
  ```bash
  cd runbooks/scripts
  ./validate_rotation.sh production
  ```
  Result: [ ] All tests passed [ ] Some tests failed

### Detailed Validation (Within 30 Minutes)

- [ ] **User registration** works
  - Test email: _______________
  - Result: [ ] Success [ ] Failed
  
- [ ] **User login** works
  - Result: [ ] Success [ ] Failed
  
- [ ] **Authenticated requests** work
  - Result: [ ] Success [ ] Failed
  
- [ ] **Password reset** email sent
  - Result: [ ] Success [ ] Failed
  
- [ ] **Railway API** operations work (if rotated)
  - Result: [ ] Success [ ] Failed [ ] N/A

### Monitoring (First Hour)

- [ ] **Check error rate** in monitoring dashboard
  - Before rotation: _______________
  - After rotation: _______________
  - Change: [ ] Acceptable [ ] Concerning
  
- [ ] **Check API response times**
  - Before: _______________ ms
  - After: _______________ ms
  - Change: [ ] Acceptable [ ] Concerning
  
- [ ] **Review authentication metrics**
  - Failed login attempts: _______________
  - 401 error rate: _______________
  - Assessment: [ ] Normal [ ] Elevated

---

## Rollback Decision Point

### If Validation Fails

**Did validation tests pass?** [ ] Yes [ ] No

If **No**, answer these questions:

1. **What failed?** _______________
2. **Is the service down?** [ ] Yes [ ] No
3. **Are users unable to authenticate?** [ ] Yes [ ] No
4. **Error rate > 10%?** [ ] Yes [ ] No
5. **Can issue be fixed forward?** [ ] Yes [ ] No

**Decision**: [ ] Continue with rotation [ ] Rollback immediately

### Rollback Procedure (If Needed)

- [ ] **Get backup file path**: _______________
- [ ] **Extract old credential** from backup
- [ ] **Restore old credential**:
  ```bash
  railway variables --environment production --set TOKEN_NAME="OLD_VALUE"
  ```
- [ ] **Wait for service restart**
- [ ] **Verify health** returns 200 OK
- [ ] **Run validation again**
- [ ] **Document rollback** reason: _______________
- [ ] **Schedule retry** for: _______________

---

## Post-Rotation Activities

### Within 24 Hours

- [ ] **Monitor logs** continuously
  ```bash
  railway logs --environment production --follow
  ```
- [ ] **Review error rates** every 4 hours
  - 4 hours: _______________ (Status: _______ )
  - 8 hours: _______________ (Status: _______ )
  - 12 hours: _______________ (Status: _______ )
  - 24 hours: _______________ (Status: _______ )
  
- [ ] **Check for unauthorized access** attempts in logs
- [ ] **Verify no user complaints** (check support channels)
- [ ] **Update audit log**:
  ```bash
  echo "$(date '+%Y-%m-%d %H:%M:%S'),TOKEN_TYPE,production,YOUR_EMAIL,success,PREVIEW" \
    >> runbooks/scripts/audit.log
  ```

### Cleanup (After 48 Hours of Stability)

- [ ] **Revoke old credentials** (if not already done):
  - JWT_SECRET: Not applicable (old secret just stops working)
  - Railway token: Revoke at https://railway.app/account/tokens
  - Database user: Drop old user from database
  - SMTP password: Revoke at email provider
  
- [ ] **Delete backup file** (after 30 days):
  ```bash
  # DO NOT delete immediately - wait 30 days
  rm runbooks/scripts/backups/env_production_YYYYMMDD_HHMMSS.json
  ```
  
- [ ] **Update rotation schedule**:
  - Next rotation date: _______________
  - Set calendar reminder: [ ] Done
  
- [ ] **Send completion notification** to team

---

## Documentation

### Audit Log Entry

- [ ] **Record rotation** in audit log
- [ ] **Include**: date, token type, environment, performer, status
- [ ] **Add notes** about any issues or deviations from procedure

### Incident Ticket (If Created)

- [ ] **Update ticket** with completion status
- [ ] **Attach validation results**
- [ ] **Document any issues** encountered
- [ ] **Close ticket**

### Lessons Learned

**What went well:**
_______________________________________________________________
_______________________________________________________________

**What could be improved:**
_______________________________________________________________
_______________________________________________________________

**Action items:**
- [ ] _______________________________________________________________
- [ ] _______________________________________________________________
- [ ] _______________________________________________________________

---

## Team Communication

### Completion Notification Template

```markdown
Subject: [COMPLETED] Token Rotation - [TOKEN_TYPE] - Production

Team,

The scheduled token rotation for [TOKEN_TYPE] in production has been completed successfully.

**Details:**
- Token Type: [TOKEN_TYPE]
- Environment: Production
- Date/Time: [YYYY-MM-DD HH:MM UTC]
- Performed By: [YOUR_NAME]
- Downtime: [X seconds / None]
- Validation: [All tests passed / See notes]

**Impact:**
[Describe any user impact, e.g., "Users were required to log in again"]

**Monitoring:**
The service is being monitored for the next 24 hours. Current metrics are normal.

**Next Rotation:**
Scheduled for [YYYY-MM-DD] (in 90 days)

**Issues:**
[None / Describe any issues and resolutions]

Thank you for your patience during this maintenance.

[YOUR_NAME]
```

---

## Sign-Off

### Completion Sign-Off

**Rotation Completed By**: _______________  
**Date**: _______________  
**Signature**: _______________  

**Reviewed By**: _______________  
**Date**: _______________  
**Signature**: _______________  

**Status**: [ ] Success [ ] Success with issues [ ] Rolled back  

**Notes**: 
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

## Appendix: Quick Command Reference

```bash
# Generate JWT secret
cd uat/backend && python3 generate_jwt_secret.py

# Validate JWT secret
python3 generate_jwt_secret.py --validate "SECRET"

# Backup environment variables
railway variables --environment production --json > backup.json

# Set environment variable
railway variables --environment production --set VAR_NAME="VALUE"

# View logs
railway logs --environment production --tail

# Run validation
cd runbooks/scripts && ./validate_rotation.sh production

# Health check
curl https://api.synpro.example.com/api/health

# Test Railway token
curl -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ projects { edges { node { id } } } }"}'
```

---

**Checklist Version**: 1.0  
**Last Updated**: 2024  
**Next Review**: [Date]
