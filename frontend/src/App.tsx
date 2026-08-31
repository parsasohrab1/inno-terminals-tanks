import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./api";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import TankDetail from "./pages/TankDetail";
import Alarms from "./pages/Alarms";
import Predictions from "./pages/Predictions";
import Optimization from "./pages/Optimization";
import Reports from "./pages/Reports";
import Admin from "./pages/Admin";

export default function App() {
  const token = useAuth((s) => s.token);
  if (!token) return <Login />;
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tanks/:id" element={<TankDetail />} />
        <Route path="/alarms" element={<Alarms />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/optimization" element={<Optimization />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  );
}
