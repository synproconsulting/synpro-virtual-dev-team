import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spin, Alert, Tabs } from 'antd';
import SprintOverview from './SprintOverview';
import JiraTicketList from './JiraTicketList';
import PullRequestList from './PullRequestList';
import CIPipelineStatus from './CIPipelineStatus';
import './SprintStatusDashboard.css';

const { TabPane } = Tabs;

const SprintStatusDashboard = ({ sprintId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sprintData, setSprintData] = useState(null);

  useEffect(() => {
    fetchSprintStatus();
    const interval = setInterval(fetchSprintStatus, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [sprintId]);

  const fetchSprintStatus = async () => {
    try {
      const response = await fetch(`/api/sprint-status/${sprintId}`);
      if (!response.ok) throw new Error('Failed to fetch sprint status');
      const data = await response.json();
      setSprintData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="sprint-dashboard-loading">
        <Spin size="large" tip="Loading sprint status..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error Loading Sprint Status"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div className="sprint-status-dashboard">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <SprintOverview data={sprintData?.overview} />
        </Col>
      </Row>
      
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col span={24}>
          <Card>
            <Tabs defaultActiveKey="jira">
              <TabPane tab="Jira Tickets" key="jira">
                <JiraTicketList tickets={sprintData?.jiraTickets} />
              </TabPane>
              <TabPane tab="Pull Requests" key="prs">
                <PullRequestList pullRequests={sprintData?.pullRequests} />
              </TabPane>
              <TabPane tab="CI/CD Status" key="ci">
                <CIPipelineStatus pipelines={sprintData?.pipelines} />
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SprintStatusDashboard;
