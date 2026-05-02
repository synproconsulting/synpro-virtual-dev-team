# SDT1 Platform Runbooks

This directory contains operational runbooks and procedures for the SDT1 platform.

## Available Runbooks

### Token Rotation

Complete documentation for rotating authentication tokens and secrets:

- **[Token Rotation Runbook](TOKEN_ROTATION.md)** - Complete procedures for rotating all tokens
- **[Quick Reference Card](TOKEN_ROTATION_QUICK_REFERENCE.md)** - Quick access commands for on-call engineers
- **[Rotation Schedule](TOKEN_ROTATION_SCHEDULE.md)** - Tracking and scheduling token rotations
- **[Rotation Checklist Template](templates/token_rotation_checklist.md)** - Printable checklist for rotations
- **[Kubernetes Secret Template](examples/kubernetes-secret-template.yaml)** - Secret structure reference

**Quick Start:**
```bash
# Rotate a token
python3 scripts/rotate_token.py --service jira --token '<NEW_TOKEN>' --environment production

# Verify rotation
python3 scripts/verify_token_rotation.py --environment production --service jira
```

---

## Runbook Structure

Each runbook follows this structure:

1. **Overview** - What the runbook covers
2. **Pre-requisites** - Required access and tools
3. **Procedures** - Step-by-step instructions
4. **Verification** - How to verify success
5. **Rollback** - How to recover from failures
6. **Troubleshooting** - Common issues and solutions
7. **References** - Related documentation

---

## Using These Runbooks

### For On-Call Engineers

1. Start with the **Quick Reference Card** for common operations
2. Refer to the full runbook for detailed procedures
3. Use the checklist template to track your progress
4. Document any issues or improvements

### For New Team Members

1. Read through the complete runbooks to understand procedures
2. Practice in the development environment
3. Shadow an experienced engineer during rotations
4. Review the troubleshooting sections

### For Operations Managers

1. Review the rotation schedule regularly
2. Ensure rotations are happening on time
3. Track metrics and improvements
4. Conduct quarterly runbook reviews

---

## Emergency Procedures

### Compromised Token Response

If a token is suspected to be compromised:

1. **Immediate**: Rotate the token following the [Token Rotation Runbook](TOKEN_ROTATION.md)
2. **Document**: Create a security incident ticket
3. **Analyze**: Review logs for unauthorized access
4. **Notify**: Alert security team via #security-incidents
5. **Review**: Conduct post-incident review

### System Down Recovery

If token rotation causes system downtime:

1. **Rollback**: Restore from backup immediately
2. **Verify**: Confirm services are restored
3. **Incident**: Create incident ticket
4. **Review**: Conduct post-mortem
5. **Update**: Update runbooks with learnings

---

## Maintenance

### Runbook Review Schedule

- **Monthly**: Review rotation schedule and upcoming due dates
- **Quarterly**: Full runbook review for accuracy and improvements
- **After Incidents**: Update runbooks with lessons learned
- **Annually**: Complete audit and major revision if needed

### How to Update Runbooks

1. Create a branch: `git checkout -b update/runbook-name`
2. Make your changes with clear documentation
3. Test procedures in development environment
4. Get review from 2+ team members
5. Merge and notify team of changes

### Document Ownership

| Document | Owner | Backup | Last Review |
|----------|-------|--------|-------------|
| Token Rotation | Operations | Security | YYYY-MM-DD |
| (Future runbooks) | - | - | - |

---

## Templates

The `templates/` directory contains reusable templates:

- **[token_rotation_checklist.md](templates/token_rotation_checklist.md)** - Printable checklist for token rotations

### Using Templates

1. Copy the template to a working location
2. Fill in the specific details for your task
3. Follow the checklist step by step
4. Archive completed checklists for audit trail

---

## Examples

The `examples/` directory contains reference implementations:

- **[kubernetes-secret-template.yaml](examples/kubernetes-secret-template.yaml)** - Kubernetes secret structure

---

## Automation Scripts

Supporting automation scripts are in the `scripts/` directory:

- `rotate_token.py` - Automate token rotation
- `verify_token_rotation.py` - Verify rotation success

See [scripts/README.md](../../scripts/README.md) for details.

---

## Related Documentation

### Internal

- [Architecture Overview](../architecture/) - System architecture
- [Deployment Guide](../deployment/) - Deployment procedures
- [Security Policies](../security/) - Security requirements
- [Incident Response](../incident-response/) - Incident procedures

### External

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Jira API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

## Getting Help

### During Business Hours

- **Slack**: #operations channel
- **Email**: operations@example.com
- **Wiki**: [Internal Operations Wiki]

### After Hours / Emergencies

- **Pagerduty**: [On-call schedule]
- **Emergency**: [Emergency contact list]
- **Escalation**: [Escalation procedures]

### Reporting Issues

Found an issue with a runbook? Report it:

1. Create a Jira ticket with label `runbook-issue`
2. Post in #operations channel
3. Tag the document owner
4. Include specific section and issue details

---

## Contributing

We welcome improvements to runbooks! Please:

1. ✅ Keep procedures clear and concise
2. ✅ Include specific commands and examples
3. ✅ Add troubleshooting for common issues
4. ✅ Test all procedures before committing
5. ✅ Use consistent formatting
6. ✅ Update the revision date

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial token rotation runbook | [Name] |

---

## Future Runbooks

Planned runbooks for future development:

- [ ] Database Backup and Restore
- [ ] Disaster Recovery Procedures
- [ ] Scaling Operations
- [ ] Certificate Rotation
- [ ] Log Analysis and Troubleshooting
- [ ] Performance Tuning
- [ ] Security Incident Response
- [ ] Deployment Rollback Procedures

---

**Maintained by**: Operations Team  
**Contact**: operations@example.com  
**Last Updated**: YYYY-MM-DD
