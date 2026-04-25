import React from 'react';
import { Card, Statistic, Row, Col, Progress, Tag } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  IssuesCloseOutlined,
  RocketOutlined,
} from '@ant-design/icons';

const SprintOverview = ({ data }) => {
  if (!data) return null;

  const {
    sprintName,
    startDate,
    endDate,
    totalTickets,
    completedTickets,
    inProgressTickets,
    blockedTickets,
    velocityPoints,
    completionPercentage,
    daysRemaining,
  } = data;

  const getProgressStatus = (percentage) => {
    if (percentage >= 80) return 'success';
    if (percentage >= 50) return 'normal';
    return 'exception';
  };

  return (
    <Card title={`Sprint: ${sprintName}`} className="sprint-overview-card">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="Total Tickets"
            value={totalTickets}
            prefix={<IssuesCloseOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Completed"
            value={completedTickets}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="In Progress"
            value={inProgressTickets}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Velocity Points"
            value={velocityPoints}
            prefix={<RocketOutlined />}
          />
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: '24px' }}>
        <Col span={12}>
          <div>
            <div style={{ marginBottom: '8px' }}>
              Sprint Progress: {completionPercentage}%
            </div>
            <Progress
              percent={completionPercentage}
              status={getProgressStatus(completionPercentage)}
            />
          </div>
        </Col>
        <Col span={12}>
          <div style={{ textAlign: 'right' }}>
            <div>Days Remaining: <strong>{daysRemaining}</strong></div>
            <div style={{ marginTop: '8px' }}>
              {blockedTickets > 0 && (
                <Tag color="red">Blocked: {blockedTickets}</Tag>
              )}
            </div>
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default SprintOverview;
