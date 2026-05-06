/**
 * validationTestData.js
 * ─────────────────────
 * Test data generator for validation warnings
 * Use this for development and testing when backend is not available
 */

/**
 * Generate mock validation warnings
 * @param {Object} options - Configuration options
 * @returns {Array} Array of mock validation warnings
 */
export function generateMockWarnings({
  criticalCount = 2,
  warningCount = 1,
  infoCount = 2,
  sprintId = null,
} = {}) {
  const warnings = [];

  // Critical warnings (missing execution_order)
  for (let i = 0; i < criticalCount; i++) {
    warnings.push({
      id: `critical-${i}`,
      issue_key: `SDT1-${100 + i}`,
      type: 'MISSING_EXECUTION_ORDER',
      message: `execution_order not set. This story will not be sequenced correctly by the Orchestrator.`,
      suggestion: 'Set execution_order based on dependencies: blockers get lower numbers, blocked stories get higher numbers.',
      severity: 'critical',
      sprint_id: sprintId,
    });
  }

  // Warning level (not used currently but for future)
  for (let i = 0; i < warningCount; i++) {
    warnings.push({
      id: `warning-${i}`,
      issue_key: `SDT1-${200 + i}`,
      type: 'LONG_SUMMARY',
      message: `Summary is ${120 + i * 10} characters (recommended: <100).`,
      suggestion: 'Consider shortening for better readability in Jira views.',
      severity: 'warning',
      sprint_id: sprintId,
    });
  }

  // Info level warnings
  for (let i = 0; i < infoCount; i++) {
    warnings.push({
      id: `info-${i}`,
      issue_key: `SDT1-${300 + i}`,
      type: 'MISSING_EPIC',
      message: 'Story not linked to an Epic.',
      suggestion: 'Consider grouping related stories under an Epic for better organization.',
      severity: 'info',
      sprint_id: sprintId,
    });
  }

  return warnings;
}

/**
 * Mock validation API for development
 */
export const mockValidationApi = {
  fetchValidationWarnings: async () => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      warnings: generateMockWarnings({
        criticalCount: 3,
        warningCount: 2,
        infoCount: 4,
      }),
    };
  },

  fetchSprintValidationWarnings: async (sprintId) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      warnings: generateMockWarnings({
        criticalCount: 2,
        warningCount: 1,
        infoCount: 2,
        sprintId,
      }),
    };
  },

  validateIssue: async (issueKey) => {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Randomly generate warnings for the issue
    const hasWarnings = Math.random() > 0.5;
    
    if (!hasWarnings) {
      return {
        issue_key: issueKey,
        warnings: [],
        valid: true,
      };
    }

    const warnings = [
      {
        id: `${issueKey}-1`,
        issue_key: issueKey,
        type: 'MISSING_EXECUTION_ORDER',
        message: 'execution_order not set.',
        suggestion: 'Set execution_order based on dependencies.',
        severity: 'critical',
      },
    ];

    return {
      issue_key: issueKey,
      warnings,
      valid: false,
    };
  },
};

/**
 * Sample warning objects for reference
 */
export const sampleWarnings = {
  missingExecutionOrder: {
    issue_key: 'SDT1-26',
    type: 'MISSING_EXECUTION_ORDER',
    message: 'execution_order not set. This story will not be sequenced correctly by the Orchestrator.',
    suggestion: 'Set execution_order based on dependencies: blockers get lower numbers, blocked stories get higher numbers.',
    severity: 'critical',
  },

  missingEpic: {
    issue_key: 'SDT1-27',
    type: 'MISSING_EPIC',
    message: 'Story not linked to an Epic.',
    suggestion: 'Consider grouping related stories under an Epic for better organization.',
    severity: 'info',
  },

  longSummary: {
    issue_key: 'SDT1-28',
    type: 'LONG_SUMMARY',
    message: 'Summary is 127 characters (recommended: <100).',
    suggestion: 'Consider shortening for better readability in Jira views.',
    severity: 'info',
  },
};

/**
 * Test scenarios for different states
 */
export const testScenarios = {
  // No warnings - all clear
  allClear: {
    warnings: [],
  },

  // Only critical warnings
  criticalOnly: {
    warnings: generateMockWarnings({
      criticalCount: 3,
      warningCount: 0,
      infoCount: 0,
    }),
  },

  // Mixed warnings
  mixed: {
    warnings: generateMockWarnings({
      criticalCount: 2,
      warningCount: 3,
      infoCount: 4,
    }),
  },

  // Only informational
  infoOnly: {
    warnings: generateMockWarnings({
      criticalCount: 0,
      warningCount: 0,
      infoCount: 5,
    }),
  },

  // Large number of warnings
  manyWarnings: {
    warnings: generateMockWarnings({
      criticalCount: 10,
      warningCount: 5,
      infoCount: 15,
    }),
  },
};

/**
 * Helper to inject mock API for testing
 * Usage: useMockValidationApi() in your component during development
 */
export function useMockValidationApi() {
  if (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_VALIDATION === 'true') {
    console.log('Using mock validation API');
    return mockValidationApi;
  }
  return null;
}

export default {
  generateMockWarnings,
  mockValidationApi,
  sampleWarnings,
  testScenarios,
  useMockValidationApi,
};
