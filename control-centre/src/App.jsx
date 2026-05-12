import React, { useState, useEffect } from "react";
import { ProductProvider } from "./contexts/ProductContext";
import { fetchProducts } from "./api/productsApi";
import ProductSelector from "./components/ProductSelector";
import AddProductModal from "./components/AddProductModal";
import DashboardMain from "./components/DashboardMain";
import SprintDashboard from "./components/SprintDashboard";
import GitHubWorkflowMonitor from "./components/GitHubWorkflowMonitor";
import UATDeployment from "./components/UATDeployment";
import SonarCloudTrigger from "./components/SonarCloudTrigger";
import PMAgentChat from "./components/PMAgentChat";
import ProductsTab from "./components/ProductsTab";
import LoginPage from "./components/LoginPage";
import RegisterPage from "./components/RegisterPage";
import ResetRequestPage from "./components/ResetRequestPage";
import ResetCompletePage from "./components/ResetCompletePage";
import UserDashboardPage from "./components/UserDashboardPage";
import ProfilePage from "./components/ProfilePage";
import NotificationsPage from "./components/NotificationsPage";

const TABS = [
  { id: "overview",   label: "Overview",      component: DashboardMain },
  { id: "sprint",     label: "Sprint Status", component: SprintDashboard },
  { id: "workflows",  label: "Workflows",     component: GitHubWorkflowMonitor },
  { id: "deploy",     label: "UAT Deploy",    component: UATDeployment },
  { id: "sonarcloud", label: "SonarCloud",    component: SonarCloudTrigger },
  { id: "pm-agent",   label: "PM Agent",      component: PMAgentChat },
  { id: "products",   label: "Products",      component: null },
];

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token") || "");
  const [activeTab, setActiveTab] = useState("sprint");
  const [activeUserTab, setActiveUserTab] = useState(null);
  const [products, setProducts] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [view, setView] = useState("login");
  const [resetToken, setResetToken] = useState("");
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    if (token) fetchProducts().then(setProducts);
  }, [token]);

  const handleLogin = (newToken) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    setActiveTab("overview");
    setActiveUserTab(null);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken("");
    setView("login");
    setShowUserMenu(false);
    setActiveUserTab(null);
  };

  const handleSwitchView = (newView, tok = "") => {
    if (newView === "reset-complete" && tok) setResetToken(tok);
    setView(newView);
  };

  const handleProductAdded = (newProduct) => {
    setProducts(prev =>
      [...prev, newProduct].sort((a, b) => a.name.localeCompare(b.name))
    );
    setShowAddModal(false);
  };

  const selectCCTab = (tabId) => {
    setActiveTab(tabId);
    setActiveUserTab(null);
  };

  const selectUserTab = (tab) => {
    setActiveUserTab(tab);
    setShowUserMenu(false);
  };

  if (!token) {
    if (view === "register")
      return <RegisterPage onLogin={handleLogin} onSwitchView={handleSwitchView} />;
    if (view === "reset-request")
      return <ResetRequestPage onSwitchView={handleSwitchView} />;
    if (view === "reset-complete")
      return <ResetCompletePage onSwitchView={handleSwitchView} initialToken={resetToken} />;
    return <LoginPage onLogin={handleLogin} onSwitchView={handleSwitchView} />;
  }

  let mainContent;
  if (activeUserTab === "dashboard") {
    mainContent = <UserDashboardPage token={token} />;
  } else if (activeUserTab === "profile") {
    mainContent = <ProfilePage />;
  } else if (activeUserTab === "notifications") {
    mainContent = <NotificationsPage />;
  } else if (activeTab === "products") {
    mainContent = <ProductsTab onProductsChanged={() => fetchProducts().then(setProducts)} />;
  } else {
    const ActiveComponent = TABS.find(t => t.id === activeTab)?.component || SprintDashboard;
    mainContent = <ActiveComponent />;
  }

  return (
    <ProductProvider products={products}>
      <div className="cc-app">
        <header className="cc-header">
          <div className="cc-header-inner">
            <div className="cc-logo">
              <span className="cc-logo-icon">&#x26A1;</span>
              <span className="cc-logo-text">SynPro Control Centre</span>
            </div>
            <ProductSelector onAddProduct={() => setShowAddModal(true)} />
            <nav className="cc-nav">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  className={`cc-nav-btn ${!activeUserTab && activeTab === tab.id ? "active" : ""}`}
                  onClick={() => selectCCTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
            <div className="cc-user-menu">
              <button
                className="cc-user-btn"
                onClick={() => setShowUserMenu(v => !v)}
              >
                &#x1F464; User &#x25BE;
              </button>
              {showUserMenu && (
                <div className="cc-user-dropdown">
                  <button className="cc-user-item" onClick={() => selectUserTab("dashboard")}>
                    Dashboard
                  </button>
                  <button className="cc-user-item" onClick={() => selectUserTab("profile")}>
                    Profile
                  </button>
                  <button className="cc-user-item" onClick={() => selectUserTab("notifications")}>
                    Notifications
                  </button>
                  <hr className="cc-user-divider" />
                  <button className="cc-user-item cc-user-logout" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="cc-main">
          {mainContent}
        </main>
        {showAddModal && (
          <AddProductModal
            onClose={() => setShowAddModal(false)}
            onAdded={handleProductAdded}
          />
        )}
      </div>
    </ProductProvider>
  );
}