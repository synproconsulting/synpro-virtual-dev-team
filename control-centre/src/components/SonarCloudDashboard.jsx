import React, { useState } from 'react';
import SonarCloudTrigger from './SonarCloudTrigger';
import SonarCloudResults from './SonarCloudResults';

const SonarCloudDashboard = () => {
  const [selectedRepository, setSelectedRepository] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const handleAnalysisTriggered = (data) => {
    if (data.repository) {
      setSelectedRepository(data.repository);
      setAutoRefresh(true);
      setTimeout(() => setAutoRefresh(false), 120000); // Auto-refresh for 2 minutes
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">SonarCloud Analysis</h1>
        <p className="text-muted-foreground">
          Trigger on-demand code quality analysis and view results
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SonarCloudTrigger onAnalysisTriggered={handleAnalysisTriggered} />
        <SonarCloudResults 
          repository={selectedRepository} 
          autoRefresh={autoRefresh}
        />
      </div>
    </div>
  );
};

export default SonarCloudDashboard;
