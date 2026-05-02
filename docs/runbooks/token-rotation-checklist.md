# Token Rotation Checklist

Use this checklist to track your token rotation activities. Make a copy for each rotation session.

---

## Rotation Information

- **Date:** _______________
- **Environment:** ☐ Staging  ☐ Production
- **Rotation Type:** ☐ Scheduled  ☐ Emergency
- **Performed By:** _______________
- **Backup Person:** _______________
- **Incident Number (if emergency):** _______________

---

## Pre-Rotation Checklist

### Planning
- [ ] Maintenance window scheduled (if required)
- [ ] Team notified of planned rotation
- [ ] Status page updated (if user-facing downtime expected)
- [ ] Backup person identified and on standby
- [ ] Reviewed token rotation runbook
- [ ] Verified access to all required systems

### Prerequisites
- [ ] AWS CLI configured and tested
- [ ] kubectl access verified
- [ ] Jira account access confirmed
- [ ] OpenAI account access confirmed
- [ ] GitHub account access confirmed
- [ ] Database admin access confirmed (if rotating DB password)

### System Health Check
- [ ] All services healthy before rotation
- [ ] No active incidents
- [ ] Recent backups verified
- [ ] Current error rates within normal range
- [ ] Monitoring systems operational

### Documentation
- [ ] Current token metadata documented
- [ ] Last rotation date noted
- [ ] Backup location confirmed

---

## Rotation Execution

### Jira API Token

- [ ] Created new token in Atlassian account
- [ ] Token name: `pm-agent-api-token-____-__-__`
- [ ] Tested new token with API call
- [ ] Updated in AWS Secrets Manager
- [ ] Updated in Kubernetes deployment
- [ ] Verified deployment rollout successful
- [ ] Tested Jira integration through application
- [ ] Old token revoked in Atlassian account
- [ ] **Notes:** _______________

### OpenAI API Key

- [ ] Created new key in OpenAI platform
- [ ] Key name: `pm-agent-____-__-__`
- [ ] Tested new key with API call
- [ ] Updated in AWS Secrets Manager
- [ ] Updated in Kubernetes deployment
- [ ] Verified deployment rollout successful
- [ ] Tested AI functionality through application
- [ ] Old key revoked in OpenAI platform
- [ ] **Notes:** _______________

### GitHub Personal Access Token

- [ ] Created new PAT in GitHub settings
- [ ] Token name: `pm-agent-production-____-__-__`
- [ ] Expiration set: 90 days
- [ ] Required scopes selected (repo, workflow)
- [ ] Tested new token with API call
- [ ] Updated in AWS Secrets Manager
- [ ] Updated in Kubernetes deployment
- [ ] Updated GitHub Actions secrets (if applicable)
- [ ] Verified deployment rollout successful
- [ ] Tested GitHub operations through application
- [ ] Old token revoked in GitHub settings
- [ ] **Notes:** _______________

### Database Password

- [ ] Generated new secure password
- [ ] Backed up current DATABASE_URL
- [ ] Executed ALTER USER SQL command
- [ ] Verified database password changed
- [ ] Built new DATABASE_URL string
- [ ] Updated in AWS Secrets Manager
- [ ] Updated in Kubernetes deployment
- [ ] Verified deployment rollout successful
- [ ] Tested database connectivity
- [ ] Checked connection pool status
- [ ] **Notes:** _______________

### JWT Secret Key

- [ ] ⚠️ Confirmed users notified of session invalidation
- [ ] Generated new JWT secret (256-bit)
- [ ] Backed up current JWT secret
- [ ] Updated JWT_SECRET_KEY in Secrets Manager
- [ ] Updated JWT_SECRET_KEY_PREVIOUS in Secrets Manager
- [ ] Updated both secrets in Kubernetes deployment
- [ ] Verified deployment rollout successful
- [ ] Tested user authentication
- [ ] Scheduled removal of previous secret (after 24 hours)
- [ ] **Notes:** _______________

---

## Post-Rotation Verification

### Immediate Checks (0-5 minutes)

- [ ] All pods running successfully
- [ ] No pod restarts detected
- [ ] No critical errors in logs
- [ ] Health endpoint responding
- [ ] API responding to requests

### Functional Tests (5-15 minutes)

- [ ] Jira integration working
  - [ ] Can read issues
  - [ ] Can write/update issues
  - [ ] Custom fields accessible
- [ ] OpenAI integration working
  - [ ] Can list models
  - [ ] Can generate completions
  - [ ] Rate limits OK
- [ ] GitHub integration working
  - [ ] Can read repositories
  - [ ] Can create branches
  - [ ] Can create pull requests
- [ ] Database connectivity working
  - [ ] Can execute queries
  - [ ] Connection pool healthy
  - [ ] No connection errors
- [ ] User authentication working
  - [ ] Can log in
  - [ ] JWT tokens valid
  - [ ] Session management working

### Monitoring Checks (15-30 minutes)

- [ ] Error rates normal
- [ ] Response times normal
- [ ] CPU/Memory usage normal
- [ ] No authentication failures
- [ ] No API quota issues
- [ ] External API calls succeeding

### Verification Script

- [ ] Ran `./verify_rotation.sh <environment>`
- [ ] All tests passed
- [ ] Generated verification report
- [ ] Verification log saved

---

## Documentation

### Audit Trail

- [ ] Rotation logged in audit log
- [ ] Token metadata updated
- [ ] Next rotation date calculated: _______________
- [ ] Incident ticket updated (if emergency)

### Reports Generated

- [ ] Rotation execution report
- [ ] Verification test results
- [ ] Error logs reviewed and saved
- [ ] Audit log saved to permanent storage

### Communication

- [ ] Team notified of completion
- [ ] Status page updated (if applicable)
- [ ] Incident closed (if emergency)
- [ ] Post-mortem scheduled (if issues occurred)

---

## 24-Hour Follow-Up

**Date:** _______________

### Extended Monitoring

- [ ] No increase in error rates
- [ ] No user-reported issues
- [ ] All automated jobs successful
- [ ] No unexpected behavior detected

### Cleanup Tasks

- [ ] JWT_SECRET_KEY_PREVIOUS removed (if JWT was rotated)
- [ ] Temporary backup files secured/deleted
- [ ] Old tokens confirmed revoked

---

## Issues and Notes

### Issues Encountered

| Issue | Time | Resolution | Duration |
|-------|------|------------|----------|
|       |      |            |          |
|       |      |            |          |
|       |      |            |          |

### Rollback Required

- [ ] No rollback required
- [ ] Rollback performed
  - Tokens rolled back: _______________
  - Rollback time: _______________
  - Rollback reason: _______________

### Additional Notes

```
[Space for additional notes, observations, or lessons learned]





```

---

## Sign-Off

### Primary Operator

- **Name:** _______________
- **Signature:** _______________
- **Date/Time:** _______________

### Backup Operator

- **Name:** _______________
- **Signature:** _______________
- **Date/Time:** _______________

### Manager Approval (for Production)

- **Name:** _______________
- **Signature:** _______________
- **Date/Time:** _______________

---

## Next Scheduled Rotation

- **Date:** _______________
- **Assigned To:** _______________
- **Calendar Reminder Set:** [ ]

---

## Attachments

- [ ] Rotation execution log
- [ ] Verification test results
- [ ] Screenshots (if applicable)
- [ ] Incident report (if emergency)

---

## References

- [Token Rotation Runbook](./token-rotation.md)
- [Emergency Rotation Procedure](./token-rotation.md#emergency-procedures)
- [Rollback Procedures](./token-rotation.md#rollback-procedures)

---

**Document Version:** 1.0  
**Template Last Updated:** 2024  
**Next Review:** Quarterly
