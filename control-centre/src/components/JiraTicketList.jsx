import React, { useState } from 'react';
import { Table, Tag, Input, Select, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const { Option } = Select;

const JiraTicketList = ({ tickets }) => {
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const getStatusColor = (status) => {
    const statusMap = {
      'To Do': 'default',
      'In Progress': 'processing',
      'In Review': 'warning',
      'Done': 'success',
      'Blocked': 'error',
    };
    return statusMap[status] || 'default';
  };

  const getPriorityColor = (priority) => {
    const priorityMap = {
      'Highest': 'red',
      'High': 'orange',
      'Medium': 'blue',
      'Low': 'green',
      'Lowest': 'default',
    };
    return priorityMap[priority] || 'default';
  };

  const columns = [
    {
      title: 'Ticket ID',
      dataIndex: 'ticketId',
      key: 'ticketId',
      width: 120,
      render: (text, record) => (
        <a href={record.url} target="_blank" rel="noopener noreferrer">
          {text}
        </a>
      ),
    },
    {
      title: 'Summary',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => <Tag color={getPriorityColor(priority)}>{priority}</Tag>,
    },
    {
      title: 'Assignee',
      dataIndex: 'assignee',
      key: 'assignee',
      width: 150,
    },
    {
      title: 'Story Points',
      dataIndex: 'storyPoints',
      key: 'storyPoints',
      width: 100,
      align: 'center',
    },
  ];

  const filteredTickets = tickets?.filter((ticket) => {
    const matchesSearch =
      ticket.ticketId.toLowerCase().includes(searchText.toLowerCase()) ||
      ticket.summary.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus =
      statusFilter === 'all' || ticket.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="jira-ticket-list">
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Search tickets..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 300 }}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 150 }}
        >
          <Option value="all">All Statuses</Option>
          <Option value="To Do">To Do</Option>
          <Option value="In Progress">In Progress</Option>
          <Option value="In Review">In Review</Option>
          <Option value="Done">Done</Option>
          <Option value="Blocked">Blocked</Option>
        </Select>
      </Space>
      <Table
        columns={columns}
        dataSource={filteredTickets}
        rowKey="ticketId"
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default JiraTicketList;
