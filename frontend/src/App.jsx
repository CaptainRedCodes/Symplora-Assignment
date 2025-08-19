import { Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import DepartmentDashboard from "./pages/DepartmentDashboard";
import LeaveTypeDashboard from "./pages/LeaveTypeDashboard"; // create later
import Home from "./pages/Home"; // simple homepage
import EmployeeDashboard from "./pages/EmployeeDashboard";
import EmployeeJob from "./pages/AssignJob";
import JobDashboard from "./pages/JobDashboard";
import LeaveDashboard from "./pages/LeaveDashboard";
import EmployeeJobInfo from "./pages/EmployeeJobInfo";
import EmployeeLeaveBalance from "./pages/EmployeeLeaveBalance";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/departments" element={<DepartmentDashboard />} />
        <Route path="/jobs" element={<JobDashboard />} />
        <Route path="/employees" element={<EmployeeDashboard />} />
        <Route path="/employees/job" element={<EmployeeJob/>}/>
        <Route path = "/leave/type" element={<LeaveTypeDashboard/>}/>
        <Route path = "/leave/dashboard" element={<LeaveDashboard/>}/>
        <Route path = "/assigned" element={<EmployeeJobInfo/>}/>
        <Route path = "/leave/balance" element={<EmployeeLeaveBalance/>}/>
      </Route>
    </Routes>
  );
}
