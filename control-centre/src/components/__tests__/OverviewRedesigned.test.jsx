import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OverviewRedesigned from "../OverviewRedesigned";
import * as sprintApi from "../../api/sprintApi";

// Mock the API module
vi.mock("../../api/sprintApi");

describe("OverviewRedesigned Component", () => {
  const mockSprintData = {
    prs: [
      {
        number: 123,
        title: "Add new feature",
        user: { login: "testuser" },
        created_at: new Date().toISOString(),
      },
    ],
    runs: [
      {
        name: "CI Pipeline",
        created_at: new Date().toISOString(),
        conclusion: "success",
        head_commit: { message: "Test commit" },
      },
    ],
    jiraIssues: [
      {
        key: "SDT1-59",
        summary: "Overview tab redesign",
        status: "Done",
        points: 5,
      },
      {
        key: "SDT1-60",
        summary: "Another ticket",
        status: "In Progress",
        points: 3,
      },
      {
        key: "SDT1-61",
        summary: "Future ticket",
        status: "To Do",
        points: 2,
      },
    ],
    metrics: {
      velocity: 5,
      totalPoints: 10,
      donePoints: 5,
      openPRs: 1,
      ciSuccessRate: 90,
    },
  };

  const mockSprints = [
    {
      id: 1,
      name: "Sprint 1",
      state: "active",
      startDate: "2024-01-01",
      endDate: "2024-01-15",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    sprintApi.fetchSprintData.mockResolvedValue(mockSprintData);
    sprintApi.fetchSprints.mockResolvedValue(mockSprints);
    sprintApi.fetchWorkflowRuns.mockResolvedValue(mockSprintData.runs);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it("renders the overview dashboard with hero section", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("SynPro Control Centre")).toBeInTheDocument();
      expect(
        screen.getByText(/AI-Powered Development Workflow/i)
      ).toBeInTheDocument();
    });
  });

  it("displays key metrics correctly", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("Sprint Velocity")).toBeInTheDocument();
      expect(screen.getByText("Story Points")).toBeInTheDocument();
      expect(screen.getByText("Open Pull Requests")).toBeInTheDocument();
      expect(screen.getByText("CI/CD Success")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("5")).toBeInTheDocument(); // velocity
      expect(screen.getByText("5/10")).toBeInTheDocument(); // story points
      expect(screen.getByText("1")).toBeInTheDocument(); // open PRs
      expect(screen.getByText("90%")).toBeInTheDocument(); // CI success rate
    });
  });

  it("displays active sprint information", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText(/Active Sprint:/i)).toBeInTheDocument();
      expect(screen.getByText("Sprint 1")).toBeInTheDocument();
    });
  });

  it("calculates sprint completion rate correctly", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      // 1 out of 3 tickets done = 33% (rounded)
      expect(screen.getByText(/33% complete/i)).toBeInTheDocument();
    });
  });

  it("displays sprint progress with correct statistics", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("Current Sprint Progress")).toBeInTheDocument();
      expect(screen.getByText("Total Issues")).toBeInTheDocument();
      expect(screen.getByText("Completed")).toBeInTheDocument();
      expect(screen.getByText("In Progress")).toBeInTheDocument();
      expect(screen.getByText("To Do")).toBeInTheDocument();
    });

    await waitFor(() => {
      // Check issue counts
      const allText = screen.getByText("Current Sprint Progress").closest("div").textContent;
      expect(allText).toMatch(/3/); // total issues
      expect(allText).toMatch(/1/); // completed
      expect(allText).toMatch(/1/); // in progress
      expect(allText).toMatch(/1/); // to do
    });
  });

  it("renders quick action buttons", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("View Sprint Board")).toBeInTheDocument();
      expect(screen.getByText("PM Agent Chat")).toBeInTheDocument();
      expect(screen.getByText("CI/CD Workflows")).toBeInTheDocument();
      expect(screen.getByText("UAT Deployment")).toBeInTheDocument();
    });
  });

  it("displays recent activity feed", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/PR #123: Add new feature/i)).toBeInTheDocument();
      expect(screen.getByText(/CI Pipeline/i)).toBeInTheDocument();
      expect(screen.getByText(/SDT1-59: Overview tab redesign/i)).toBeInTheDocument();
    });
  });

  it("displays system health indicators", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("System Health")).toBeInTheDocument();
      expect(screen.getByText("CI/CD Pipeline")).toBeInTheDocument();
      expect(screen.getByText("Pull Request Queue")).toBeInTheDocument();
      expect(screen.getByText("Sprint Velocity")).toBeInTheDocument();
    });
  });

  it("shows healthy status for high CI success rate", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      const healthSection = screen.getByText("CI/CD Pipeline").closest("div");
      expect(healthSection.textContent).toMatch(/90%/);
      expect(healthSection.textContent).toMatch(/Healthy/i);
    });
  });

  it("displays team summary statistics", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("Team Summary")).toBeInTheDocument();
      expect(screen.getByText("Active Contributors")).toBeInTheDocument();
      expect(screen.getByText("Commits Today")).toBeInTheDocument();
      expect(screen.getByText("Workflow Runs")).toBeInTheDocument();
    });
  });

  it("shows loading state initially", () => {
    render(<OverviewRedesigned />);

    expect(screen.getAllByText("...").length).toBeGreaterThan(0);
  });

  it("refreshes data automatically", async () => {
    vi.useFakeTimers();
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(sprintApi.fetchSprintData).toHaveBeenCalledTimes(1);
      expect(sprintApi.fetchSprints).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 45 seconds
    vi.advanceTimersByTime(45000);

    await waitFor(() => {
      expect(sprintApi.fetchSprintData).toHaveBeenCalledTimes(2);
      expect(sprintApi.fetchSprints).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });

  it("handles empty data gracefully", async () => {
    sprintApi.fetchSprintData.mockResolvedValue({
      prs: [],
      runs: [],
      jiraIssues: [],
      metrics: {},
    });
    sprintApi.fetchSprints.mockResolvedValue([]);

    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("No recent activity")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    sprintApi.fetchSprintData.mockRejectedValue(new Error("API Error"));
    sprintApi.fetchSprints.mockRejectedValue(new Error("API Error"));

    render(<OverviewRedesigned />);

    // Should not crash, should show loading or empty state
    await waitFor(() => {
      expect(screen.getByText("SynPro Control Centre")).toBeInTheDocument();
    });
  });

  it("calculates correct health status for different CI success rates", async () => {
    // Test warning status (60-79%)
    const warningData = { ...mockSprintData, metrics: { ...mockSprintData.metrics, ciSuccessRate: 70 } };
    sprintApi.fetchSprintData.mockResolvedValue(warningData);

    const { rerender } = render(<OverviewRedesigned />);

    await waitFor(() => {
      const healthSection = screen.getByText("CI/CD Pipeline").closest("div");
      expect(healthSection.textContent).toMatch(/Warning/i);
    });

    // Test error status (<60%)
    const errorData = { ...mockSprintData, metrics: { ...mockSprintData.metrics, ciSuccessRate: 50 } };
    sprintApi.fetchSprintData.mockResolvedValue(errorData);

    rerender(<OverviewRedesigned />);

    await waitFor(() => {
      const healthSection = screen.getByText("CI/CD Pipeline").closest("div");
      expect(healthSection.textContent).toMatch(/Critical/i);
    });
  });

  it("displays pro tips section", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("Pro Tips")).toBeInTheDocument();
      expect(screen.getByText(/Sprint Status/i)).toBeInTheDocument();
      expect(screen.getByText(/PM Agent/i)).toBeInTheDocument();
    });
  });

  it("formats time ago correctly", async () => {
    const recentTime = new Date();
    recentTime.setMinutes(recentTime.getMinutes() - 5);

    const dataWithRecentActivity = {
      ...mockSprintData,
      prs: [
        {
          ...mockSprintData.prs[0],
          created_at: recentTime.toISOString(),
        },
      ],
    };

    sprintApi.fetchSprintData.mockResolvedValue(dataWithRecentActivity);

    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText(/5 min ago/i)).toBeInTheDocument();
    });
  });

  it("displays progress ring with correct percentage", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      const progressText = screen.getByText("33%"); // 1 out of 3 done
      expect(progressText).toBeInTheDocument();
      expect(progressText.parentElement.textContent).toMatch(/Complete/i);
    });
  });

  it("shows correct story point breakdown", async () => {
    render(<OverviewRedesigned />);

    await waitFor(() => {
      expect(screen.getByText("5/10 points")).toBeInTheDocument();
    });
  });
});
