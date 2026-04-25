import React from 'react';
import SprintTrigger from './SprintTrigger';
import AutoReviewStatus from './AutoReviewStatus';

const SprintDashboard = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Sprint Control Centre</h1>
        <p className="text-muted-foreground mt-2">
          Manage sprint executions and monitor auto-review processes
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <SprintTrigger />
        </div>
        <div>
          <AutoReviewStatus />
        </div>
      </div>
    </div>
  );
};

export default SprintDashboard;