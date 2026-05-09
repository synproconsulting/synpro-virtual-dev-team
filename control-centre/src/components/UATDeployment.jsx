import React, { useState, useEffect, useCallback } from 'react';
import { getPipelineStatus, promoteEnvironment, rollbackEnvironment } from '../api/railwayApi';
import './UATDeployment.css';

const STATUS_COLORS = {
  SUCCESS: '#22c55e',
  ACTIVE: '#22c55e',
  BUILDING: '#3b82f6',
  DEPLOYING: '#3b82f6',
  INITIALIZING: '#3b82f6',
  FAILED: '#ef4444',
  CRASHED: '#ef4444',
  QUEUED: '#f59e0b',
};

function statusColor(status) {
  return STATUS_COLORS[status] || '#6b7280';
}

function timeAgo(isoString) {
  if (!isoString) return '';
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const STAGE_LABELS = { dev: 'DEV', test: 'TEST', prod: 'PROD' };
const STAGE_DESCRIPTIONS = {
  dev: 'Auto-deploys on merge to main',
  test: 'Internal QA gate',
  prod: 'Client-facing',
};

const CONFIRM_CONFIGS = {
  promote_test: {
    title: 'Promote to TEST',
    message: 'Redeploy the TEST service with the current build. DEV → TEST.',
    confirmLabel: 'Promote to TEST',
  },
  promote_prod: {
    title: 'Promote to PROD',
    message: 'Redeploy the PROD service with the current build. TEST → PROD.',
    confirmLabel: 'Promote to PROD',
  },
  rollback_dev: {
    title: 'Roll Back DEV',
    message: 'Redeploy DEV to its previous successful build.',
    confirmLabel: 'Roll Back',
  },
  rollback_test: {
    title: 'Roll Back TEST',
    message: 'Redeploy TEST to its previous successful build.',
    confirmLabel: 'Roll Back',
  },
  rollback_prod: {
    title: 'Roll Back PROD',
    message: 'Redeploy PROD to its previous successful build.',
    confirmLabel: 'Roll Back',
  },
};

const UATDeployment = () => {
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [confirmation, setConfirmation] = useState(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPipelineStatus();
      setPipelineStatus(data.environments);
    } catch (err) {
      setError(`Failed to load pipeline status: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const requestAction = (actionKey) => setConfirmation(actionKey);

  const executeAction = async () => {
    if (!confirmation) return;
    const key = confirmation;
    setConfirmation(null);
    setActionLoading(key);
    setError(null);
    setSuccess(null);
    try {
      if (key.startsWith('promote_')) {
        const target = key.replace('promote_', '');
        await promoteEnvironment(target);
        setSuccess(`Promotion to ${STAGE_LABELS[target]} triggered successfully.`);
      } else if (key.startsWith('rollback_')) {
        const stage = key.replace('rollback_', '');
        await rollbackEnvironment(stage);
        setSuccess(`Rollback of ${STAGE_LABELS[stage]} triggered successfully.`);
      }
      await loadStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const renderCard = (stage) => {
    const data = pipelineStatus?.[stage];
    const label = STAGE_LABELS[stage];
    const desc = STAGE_DESCRIPTIONS[stage];
    const lastDep = data?.last_deployment;
    const rollbackKey = `rollback_${stage}`;
    const isRollingBack = actionLoading === rollbackKey;

    return (
      <div className={`pipeline-card pipeline-card--${stage}`} key={stage}>
        <div className="pipeline-card__header">
          <span className="pipeline-card__label">{label}</span>
          <span className="pipeline-card__desc">{desc}</span>
        </div>

        {data?.error ? (
          <div className="pipeline-card__unconfigured">
            <span className="pipeline-card__error-icon">&#x26A0;</span>
            <span>{data.error}</span>
          </div>
        ) : (
          <>
            <div className="pipeline-card__service">
              {data?.service_name || '—'}
            </div>
            <div className="pipeline-card__status">
              {lastDep ? (
                <>
                  <span
                    className="pipeline-card__badge"
                    style={{ backgroundColor: statusColor(lastDep.status) }}
                  >
                    {lastDep.status}
                  </span>
                  <span className="pipeline-card__time">{timeAgo(lastDep.created_at)}</span>
                </>
              ) : (
                <span className="pipeline-card__badge pipeline-card__badge--none">No deployments</span>
              )}
            </div>
          </>
        )}

        <div className="pipeline-card__actions">
          <button
            className="pipeline-btn pipeline-btn--rollback"
            disabled={!data?.configured || !!data?.error || !!actionLoading || loading}
            onClick={() => requestAction(rollbackKey)}
          >
            {isRollingBack ? 'Rolling back…' : 'Rollback'}
          </button>
        </div>
      </div>
    );
  };

  const renderPromoteArrow = (toStage) => {
    const toData = pipelineStatus?.[toStage];
    const actionKey = `promote_${toStage}`;
    const isPromoting = actionLoading === actionKey;
    const disabled = !toData?.configured || !!toData?.error || !!actionLoading || loading;

    return (
      <div className="pipeline-arrow" key={`arrow-${toStage}`}>
        <div className="pipeline-arrow__line" />
        <button
          className="pipeline-btn pipeline-btn--promote"
          disabled={disabled}
          onClick={() => requestAction(actionKey)}
        >
          {isPromoting ? 'Promoting…' : `Promote to ${STAGE_LABELS[toStage]}`}
        </button>
        <div className="pipeline-arrow__line" />
        <div className="pipeline-arrow__head">&#9654;</div>
      </div>
    );
  };

  const confirmConfig = confirmation ? CONFIRM_CONFIGS[confirmation] : null;

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <div className="uat-deployment-header__top">
          <div>
            <h2>Deployment Pipeline</h2>
            <p className="subtitle">DEV &#8594; TEST &#8594; PROD promotion pipeline</p>
          </div>
          <button className="refresh-btn" onClick={loadStatus} disabled={loading}>
            {loading ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)} className="alert-close">&#215;</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <strong>Success:</strong> {success}
          <button onClick={() => setSuccess(null)} className="alert-close">&#215;</button>
        </div>
      )}

      <div className="pipeline-container">
        {renderCard('dev')}
        {renderPromoteArrow('test')}
        {renderCard('test')}
        {renderPromoteArrow('prod')}
        {renderCard('prod')}
      </div>

      {confirmation && confirmConfig && (
        <div className="confirm-overlay">
          <div className="confirm-dialog">
            <h3>{confirmConfig.title}</h3>
            <p>{confirmConfig.message}</p>
            <div className="confirm-actions">
              <button className="pipeline-btn pipeline-btn--cancel" onClick={() => setConfirmation(null)}>
                Cancel
              </button>
              <button className="pipeline-btn pipeline-btn--confirm" onClick={executeAction}>
                {confirmConfig.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UATDeployment;
