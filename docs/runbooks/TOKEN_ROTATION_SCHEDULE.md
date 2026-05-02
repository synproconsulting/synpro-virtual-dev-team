# Token Rotation Schedule

This document tracks the rotation schedule for all authentication tokens and secrets used by the SDT1 platform.

## Current Rotation Status

| Token/Secret | Current Version | Last Rotated | Next Rotation Due | Rotation Frequency | Owner |
|--------------|----------------|--------------|-------------------|-------------------|-------|
| JIRA_API_TOKEN (Prod) | - | - | - | 90 days | Operations |
| JIRA_API_TOKEN (Staging) | - | - | - | 90 days | Operations |
| OPENAI_API_KEY (Prod) | - | - | - | 90 days | Operations |
| OPENAI_API_KEY (Staging) | - | - | - | 90 days | Operations |
| GITHUB_TOKEN (Prod) | - | - | - | 90 days | Operations |
| GITHUB_TOKEN (Staging) | - | - | - | 90 days | Operations |
| JWT_SECRET_KEY (Prod) | - | - | - | 180 days | Operations |
| JWT_SECRET_KEY (Staging) | - | - | - | 180 days | Operations |
| DATABASE_PASSWORD (Prod) | - | - | - | 90 days | DBA Team |
| DATABASE_PASSWORD (Staging) | - | - | - | 90 days | DBA Team |
| REDIS_PASSWORD (Prod) | - | - | - | 90 days | Operations |
| REDIS_PASSWORD (Staging) | - | - | - | 90 days | Operations |

**Legend:**
- ✅ = Up to date
- ⚠️ = Due within 14 days
- 🚨 = Overdue

---

## Rotation History

### 2024

#### January

| Date | Token | Environment | Engineer | Status | Notes |
|------|-------|-------------|----------|--------|-------|
| YYYY-MM-DD | JIRA_API_TOKEN | Production | Name | ✅ Success | Initial setup |
| YYYY-MM-DD | OPENAI_API_KEY | Production | Name | ✅ Success | Initial setup |
| YYYY-MM-DD | GITHUB_TOKEN | Production | Name | ✅ Success | Initial setup |

#### February

| Date | Token | Environment | Engineer | Status | Notes |
|------|-------|-------------|----------|--------|-------|
| - | - | - | - | - | - |

#### March

| Date | Token | Environment | Engineer | Status | Notes |
|------|-------|-------------|----------|--------|-------|
| - | - | - | - | - | - |

#### April

| Date | Token | Environment | Engineer | Status | Notes |
|------|-------|-------------|----------|--------|-------|
| - | - | - | - | - | - |

---

## Upcoming Rotations (Next 30 Days)

| Due Date | Token | Environment | Assigned To | Reminder Sent | Status |
|----------|-------|-------------|-------------|---------------|--------|
| - | - | - | - | - | - |

---

## Rotation Reminders

### Email Notification Schedule

- **T-30 days**: Advance notice sent to operations team
- **T-14 days**: Initial reminder to assigned engineer
- **T-7 days**: Coordination meeting scheduled
- **T-2 days**: Final confirmation required
- **T-0**: Rotation execution
- **T+1 day**: Post-rotation review

### Calendar Events

Set up recurring calendar events for token rotations:

**Production Environment:**
- **Every 90 days**: API Token Rotation Day (Jira, OpenAI, GitHub)
- **Every 180 days**: JWT Secret Rotation Day
- **Every 90 days**: Database & Redis Password Rotation

**Staging Environment:**
- **Every 90 days**: All tokens (stagger 1 week before production)

---

## Rotation Policies

### Standard Tokens (90-day rotation)

**Covered tokens:**
- Jira API Token
- OpenAI API Key
- GitHub Personal Access Token
- Database Password
- Redis Password

**Process:**
1. Generate new token at source
2. Test in staging environment first
3. Apply to production during business hours
4. Verify all services functioning
5. Revoke old token within 24 hours

### Sensitive Tokens (180-day rotation)

**Covered tokens:**
- JWT Secret Key

**Process:**
1. Use zero-downtime rotation strategy
2. Three-phase rotation (add new, switch primary, remove old)
3. Allow 24-hour transition period
4. Schedule during low-traffic period
5. Monitor for session invalidation issues

### Emergency Rotation (Immediate)

**Triggers:**
- Suspected token compromise
- Security incident
- Token accidentally exposed (logs, public repo, etc.)
- Former team member had access
- Vendor security notification

**Process:**
1. Immediately generate new token
2. Update production without testing (emergency)
3. Revoke old token immediately
4. Create security incident ticket
5. Conduct post-mortem review

---

## Token Expiration Monitoring

### Automated Checks

Set up automated monitoring to alert on:
- Tokens expiring within 30 days
- Tokens that have expired
- Failed authentication attempts
- Unusual API usage patterns

### Monitoring Dashboard

Link to monitoring dashboard: [Dashboard URL]

**Metrics to track:**
- Days until token expiration
- Failed authentication rate
- API request success rate
- Service health after rotation

---

## Compliance & Audit

### Audit Requirements

- All rotations must be logged in this document
- Rotation checklist must be completed for each rotation
- Security team must review logs quarterly
- Annual audit of rotation procedures

### Audit Trail

Maintained in:
- This document (rotation history)
- `token_rotation_log.json` (automated log)
- Security incident tracker (for emergency rotations)
- Kubernetes audit logs (for secret changes)

---

## Rotation Best Practices

### Pre-Rotation

✅ **DO:**
- Test in staging first
- Notify team 48 hours in advance
- Backup current configuration
- Schedule during business hours
- Have rollback plan ready
- Review recent incidents

❌ **DON'T:**
- Rotate multiple tokens simultaneously (production)
- Rotate on Friday afternoons or before holidays
- Skip testing in staging
- Forget to notify team
- Rotate without backup

### During Rotation

✅ **DO:**
- Follow documented runbook
- Use automation scripts
- Monitor logs in real-time
- Keep team informed
- Document any issues

❌ **DON'T:**
- Deviate from runbook
- Rush through verification
- Ignore warning signs
- Skip verification steps

### Post-Rotation

✅ **DO:**
- Verify all services healthy
- Revoke old token promptly
- Update documentation
- Conduct brief retro if issues
- Schedule next rotation

❌ **DON'T:**
- Leave old tokens active
- Skip verification
- Forget to document
- Ignore lessons learned

---

## Emergency Contacts

### On-Call Rotation

- **Primary**: [Pagerduty/Schedule Link]
- **Secondary**: [Backup Contact]
- **Manager**: [Escalation Contact]

### Team Distribution Lists

- **Operations**: operations@example.com
- **Security**: security@example.com
- **On-Call**: oncall@example.com

### Slack Channels

- **#operations**: General operations
- **#security-incidents**: Security issues
- **#oncall**: On-call coordination

---

## Related Documents

- [Token Rotation Runbook](TOKEN_ROTATION.md) - Complete procedures
- [Quick Reference Card](TOKEN_ROTATION_QUICK_REFERENCE.md) - Quick commands
- [Rotation Checklist](templates/token_rotation_checklist.md) - Checklist template
- [Kubernetes Secret Template](examples/kubernetes-secret-template.yaml) - Secret structure

---

## Token Generation Quick Links

| Service | Generation URL | Documentation |
|---------|----------------|---------------|
| **Jira** | https://id.atlassian.com/manage-profile/security/api-tokens | [Atlassian Docs](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) |
| **OpenAI** | https://platform.openai.com/api-keys | [OpenAI Docs](https://platform.openai.com/docs/api-reference/authentication) |
| **GitHub** | https://github.com/settings/tokens | [GitHub Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) |
| **JWT** | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` | Internal |

---

## Rotation Metrics

### Target Metrics

- **On-time rotation rate**: >95%
- **Failed rotations**: <5%
- **Time to rotate**: <30 minutes per token
- **Zero-downtime rotations**: 100% (JWT)

### Current Metrics (Updated Monthly)

| Metric | Current Month | Previous Month | Target | Status |
|--------|---------------|----------------|--------|--------|
| On-time rotation rate | - | - | >95% | - |
| Failed rotations | - | - | <5% | - |
| Average rotation time | - | - | <30 min | - |
| Zero-downtime success | - | - | 100% | - |

---

## Continuous Improvement

### Quarterly Review Topics

- [ ] Review rotation frequency (are 90/180 days appropriate?)
- [ ] Evaluate automation effectiveness
- [ ] Identify recurring issues
- [ ] Update runbooks with lessons learned
- [ ] Consider new security tools/services
- [ ] Review team training needs

### Proposed Improvements

| Improvement | Priority | Owner | Target Date | Status |
|-------------|----------|-------|-------------|--------|
| Automate rotation reminders | High | Ops | Q1 2024 | Pending |
| Integrate with Vault | Medium | Security | Q2 2024 | Planned |
| Add Slack notifications | High | Ops | Q1 2024 | Pending |
| Implement auto-rotation | Low | DevOps | Q3 2024 | Future |

---

**Document Owner**: Operations Team  
**Last Updated**: YYYY-MM-DD  
**Next Review**: YYYY-MM-DD (Quarterly)  
**Version**: 1.0
