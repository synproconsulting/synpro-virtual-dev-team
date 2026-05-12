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
  const [activeTab, setActiveTab] = useState("sprint");
  const [products, setProducts] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchProducts().then(setProducts);
  }, []);

  const handleProductAdded = (newProduct) => {
    setProducts(prev =>
      [...prev, newProduct].sort((a, b) => a.name.localeCompare(b.name))
    );
    setShowAddModal(false);
  };

  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component || SprintDashboard;

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
                  className={`cc-nav-btn ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </header>
        <main className="cc-main">
          {activeTab === "products"
            ? <ProductsTab onProductsChanged={() => fetchProducts().then(setProducts)} />
            : <ActiveComponent />
          }
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
