import React from 'react';
import { Table, Tag, Avatar, Space, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  CommentOutlined,
} from '@ant-design/icons';

const PullRequestList = ({ pullRequests }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'changes_requested':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'pending':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      default:
        return null;
    }
  };

  const columns = [
    {
      title: 'PR #',
      dataIndex: 'prNumber',
      key: 'prNumber',
      width: 80,
      render: (text, record) => (
        <a href={record.url} target="_blank" rel="noopener noreferrer">
          #{text}
        </a>
      ),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
      width: 120,
      render: (author) => (
        <Space>
          <Avatar size="small" src={author.avatar}>
            {author.name?.[0]}
          </Avatar>
          {author.name}
        </Space>
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
          <span style={{ textTransform: 'capitalize' }}>
            {status.replace('_', ' ')}
          </span>
        </Space>
      ),
    },
    {
      title: 'Reviews',
      dataIndex: 'reviews',
      key: 'reviews',
      width: 100,
      render: (reviews) => (
        <Space>
          <Tooltip title="Approvals">
            <Tag color="green">{reviews.approved}</Tag>
          </Tooltip>
          <Tooltip title="Changes Requested">
            <Tag color="red">{reviews.changesRequested}</Tag>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: 'Comments',
      dataIndex: 'commentCount',
      key: 'commentCount',
      width: 100,
      render: (count) => (
        <Space>
          <CommentOutlined />
          {count}
        </Space>
      ),
    },
    {
      title: 'Branch',
      dataIndex: 'branch',
      key: 'branch',
      width: 150,
      ellipsis: true,
      render: (branch) => <Tag>{branch}</Tag>,
    },
  ];

  return (
    <div className="pull-request-list">
      <Table
        columns={columns}
        dataSource={pullRequests}
        rowKey="prNumber"
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default PullRequestList;
