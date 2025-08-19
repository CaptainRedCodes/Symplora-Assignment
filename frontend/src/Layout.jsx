// Layout.jsx
import Header from "./components/header";
import { Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header at the top */}
      <Header />

      {/* Main area with sidebar + content */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 bg-black text-white flex flex-col p-4">
          <h2 className="text-lg font-bold mb-6">Navigation</h2>
          <nav className="flex flex-col space-y-3"> 
            <a href="/" className="hover:bg-gray-700 px-3 py-2 rounded">Home</a>
            <a href="/departments" className="hover:bg-gray-700 px-3 py-2 rounded">Departments Dashboard</a>
            <a href="/jobs" className="hover:bg-gray-700 px-3 py-2 rounded">Jobs Dashboard</a>
            <a href="/employees" className="hover:bg-gray-700 px-3 py-2 rounded">Employees Dashboard</a>
            <a href="/employees/job" className="hover:bg-gray-700 px-3 py-2 rounded">HR Employee Management Dashboard</a>
            <a href="/leave/type" className="hover:bg-gray-700 px-3 py-2 rounded">Add Leave Type</a>
            <a href="/leave/dashboard" className="hover:bg-gray-700 px-3 py-2 rounded">Leave Management System</a>
            <a href="/assigned" className="hover:bg-gray-700 px-3 py-2 rounded">All Employees</a>
            <a href="/leave/balance" className="hover:bg-gray-700 px-3 py-2 rounded">Employee Leave Balances</a>


          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6 bg-gray-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
