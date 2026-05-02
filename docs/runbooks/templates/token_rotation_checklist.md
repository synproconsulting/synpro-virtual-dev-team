# Token Rotation Checklist

**Service**: ________________  
**Environment**: ________________  
**Date**: ________________  
**Engineer**: ________________  
**Ticket**: ________________  

---

## Pre-Rotation (T-7 days)

- [ ] Review recent logs for unusual activity
- [ ] Identify all services using the token
- [ ] Schedule maintenance window (if required)
- [ ] Notify team on Slack (#operations)
- [ ] Test rotation in staging environment
- [ ] Review and confirm rollback plan

**Notes**:
```




```

---

## Preparation (T-1 day)

- [ ] Backup current environment configuration
- [ ] Generate new token/credential
- [ ] Verify new token works in isolated test
- [ ] Document current token (last 4 chars only): `____`
- [ ] Ensure monitoring and alerting are active
- [ ] Have incident response team on standby

**New Token Last 4 Chars**: `____`

**Test Results**:
```




```

---

## Execution (T-0)

### Backup

- [ ] Backup current secrets to file: `backup-secrets-$(date +%Y%m%d).yaml`
- [ ] Verify backup file created successfully
- [ ] Store backup in secure location

**Backup Location**: ________________

### Rotation

- [ ] Update Kubernetes secret with new token
- [ ] Verify secret updated successfully
- [ ] Restart affected deployments
- [ ] Wait for rollout to complete
- [ ] Verify all pods are running

**Deployments Restarted**:
- [ ] uat-backend
- [ ] pm-agent
- [ ] dev-agent
- [ ] (other): ________________

### Verification

- [ ] Run verification script: `python3 scripts/verify_token_rotation.py`
- [ ] Check service health endpoints
- [ ] Review logs for authentication errors
- [ ] Test key functionality manually

**Verification Status**: ☐ PASSED  ☐ FAILED

**Issues Found**:
```




```

---

## Post-Rotation (T+0 to T+1 hour)

### Service Health

- [ ] All deployments showing ready (T+5 min)
- [ ] No authentication errors in logs (T+10 min)
- [ ] Agent tasks executing successfully (T+30 min)
- [ ] Jira integration working (T+30 min)
- [ ] GitHub integration working (T+30 min)
- [ ] OpenAI API calls succeeding (T+30 min)

### Revoke Old Token

- [ ] Return to token source (Jira/GitHub/OpenAI)
- [ ] Revoke/delete old token
- [ ] Verify revocation
- [ ] Confirm no services using old token

**Old Token Revoked**: ☐ YES  ☐ NO

### Monitoring

- [ ] Check error rates in monitoring dashboard
- [ ] Verify no spike in failed requests
- [ ] Check service latency metrics
- [ ] Review recent alerts

**Dashboard Link**: ________________

---

## Extended Monitoring (T+24 hours)

- [ ] Review 24-hour logs for issues
- [ ] Verify no recurring authentication errors
- [ ] Check agent success rates
- [ ] Confirm all integrations stable

---

## Documentation & Cleanup

- [ ] Update token rotation log
- [ ] Document any issues or learnings
- [ ] Update runbook with improvements
- [ ] Post completion notice in #operations
- [ ] Schedule next rotation reminder
- [ ] Archive backup file

**Next Rotation Due**: ________________

---

## Rollback (if needed)

**Rollback Executed**: ☐ YES  ☐ NO

If YES, complete below:

- [ ] Restored from backup: `backup-secrets-$(date +%Y%m%d).yaml`
- [ ] Restarted all affected deployments
- [ ] Verified services recovered
- [ ] Documented rollback reason
- [ ] Created incident ticket

**Rollback Reason**:
```




```

**Incident Ticket**: ________________

---

## Sign-Off

**Rotation Status**: ☐ SUCCESSFUL  ☐ ROLLED BACK  ☐ FAILED

**Engineer Signature**: ________________  
**Date/Time Completed**: ________________  

**Reviewer Signature**: ________________  
**Date/Time Reviewed**: ________________  

---

## Notes & Lessons Learned

```








```

---

## Attachments

- [ ] Backup file archived
- [ ] Verification results saved
- [ ] Screenshots (if applicable)
- [ ] Log snippets (if issues occurred)

**Attachment Location**: ________________
