import React from 'react';
import { Table, Tag, Space, Progress, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import moment from 'moment';

const CIPipelineStatus = ({ pipelines }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    const colorMap = {
      success: 'success',
      failed: 'error',
      running: 'processing',
      pending: 'warning',
    };
    return colorMap[status] || 'default';
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const duration = moment.duration(seconds, 'seconds');
    const minutes = Math.floor(duration.asMinutes());
    const secs = duration.seconds();
    return `${minutes}m ${secs}s`;
  };

  const columns = [
    {
      title: 'Pipeline',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <a href={record.url} target="_blank" rel="noopener noreferrer">
          {text}
        </a>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>
            {status.toUpperCase()}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Branch',
      dataIndex: 'branch',
      key: 'branch',
      width: 150,
      render: (branch) => <Tag>{branch}</Tag>,
    },
    {
      title: 'Commit',
      dataIndex: 'commit',
      key: 'commit',
      width: 100,
      render: (commit) => (
        <Tooltip title={commit.message}>
          <code>{commit.sha.substring(0, 7)}</code>
        </Tooltip>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration) => formatDuration(duration),
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress, record) => {
        if (record.status !== 'running') return null;
        return <Progress percent={progress} size="small" />;
      },
    },
    {
      title: 'Started',
      dataIndex: 'startedAt',
      key: 'startedAt',
      width: 150,
      render: (time) => moment(time).fromNow(),
    },
  ];

  const expandedRowRender = (record) => {
    if (!record.stages || record.stages.length === 0) return null;

    const stageColumns = [
      {
        title: 'Stage',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: 'Status',
        dataIndex: 'status',
        key: 'status',
        render: (status) => (
          <Space>
            {getStatusIcon(status)}
            <span>{status}</span>
          </Space>
        ),
      },
      {
        title: 'Duration',
        dataIndex: 'duration',
        key: 'duration',
        render: (duration) => formatDuration(duration),
      },
    ];

    return (
      <Table
        columns={stageColumns}
        dataSource={record.stages}
        pagination={false}
        rowKey="name"
        size="small"
      />
    );
  };

  return (
    <div className="ci-pipeline-status">
      <Table
        columns={columns}
        dataSource={pipelines}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        expandable={{
          expandedRowRender,
          rowExpandable: (record) => record.stages && record.stages.length > 0,
        }}
      />
    </div>
  );
};

export default CIPipelineStatus;
