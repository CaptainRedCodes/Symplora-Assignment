import React, { useEffect, useState } from "react";
import { Search, User, Briefcase, Calendar, IndianRupee  } from "lucide-react";

export default function EmployeeJob() {
  const [employees, setEmployees] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [assignData, setAssignData] = useState({ job_id: "", start_date: "", salary: "" });
  const [terminateDate, setTerminateDate] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("assign"); // assign, terminate, history

  const API_BASE = "http://127.0.0.1:8000/api";

  useEffect(() => {
    fetchEmployees();
    fetchJobs();
  }, []);

  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_BASE}/employees/`);
      const data = await res.json();
      setEmployees(data);
    } catch (err) {
      setError("Failed to fetch employees.",{err});
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/Jobs/`);
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      setError("Failed to fetch jobs.",{err});
    }
  };

  const fetchJobHistory = async (empId) => {
    try {
      const res = await fetch(`${API_BASE}/employees/${empId}/job_history/`);
      const data = await res.json();
      setJobHistory(data);
    } catch (err) {
      setError("Failed to fetch job history.",{err});
    }
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
    setError("");
    fetchJobHistory(employee.emp_id);
  };

  const handleAssignJob = async () => {
  if (!selectedEmployee) return;

  setLoading(true);
  try {
    console.log("Assigning job:", assignData, "to employee:", selectedEmployee);

    const res = await fetch(`${API_BASE}/employees/${selectedEmployee.emp_id}/assign_job/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(assignData),
    });

    let data;
    try {
      data = await res.json();
    } catch {
      data = null; // handle non-JSON responses
    }

    if (!res.ok) {
      const message = data?.detail || data?.error || res.statusText || "Failed to assign job";
      setError(message); // show error in frontend
      return; // stop further execution
    }

    setJobHistory([data, ...jobHistory]);
    setAssignData({ job_id: "", start_date: "", salary: "" });
    setError(""); // clear previous error

    // Refresh employee data
    const updatedEmployee = await fetch(`${API_BASE}/employees/${selectedEmployee.emp_id}/`);
    const empData = await updatedEmployee.json();
    setSelectedEmployee(empData);

  } catch (err) {
    console.error(err);
    setError(err.message || "Failed to assign job");
  } finally {
    setLoading(false);
  }
};

const handleTerminate = async () => {
  if (!selectedEmployee || !terminateDate) return;

  setLoading(true);
  try {
    console.log("Terminating employee:", selectedEmployee, "on date:", terminateDate);

    const res = await fetch(`${API_BASE}/employees/${selectedEmployee.emp_id}/terminate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ end_date: terminateDate, set_inactive: true }),
    });

    let data;
    try {
      data = await res.json();
    } catch {
      data = null;
    }

    if (!res.ok) {
      const message = data?.detail || data?.error || res.statusText || "Failed to terminate employee";
      setError(message); // show error in frontend
      return;
    }

    await fetchJobHistory(selectedEmployee.emp_id);
    setTerminateDate("");
    setError(""); // clear previous error

    // Refresh employee data
    const updatedEmployee = await fetch(`${API_BASE}/employees/${selectedEmployee.emp_id}/`);
    const empData = await updatedEmployee.json();
    setSelectedEmployee(empData);

  } catch (err) {
    console.error(err);
    setError(err.message || "Failed to terminate employee");
  } finally {
    setLoading(false);
  }
};

  const filteredEmployees = employees.filter(emp =>
    emp.emp_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.emp_id?.toString().includes(searchTerm)
  );

  const getJobTitle = (jobId) => {
    const job = jobs.find(j => j.job_id === jobId);
    return job ? job.job_title : 'Unknown Job';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">HR Employee Management Dashboard</h1>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Employee List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <User className="mr-2" size={20} />
              Employees
            </h2>
            
            <div className="relative mb-4">
              <Search className="absolute left-3 top-3 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search employees..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredEmployees.map((emp) => (
                <div
                  key={emp.emp_id}
                  onClick={() => handleEmployeeSelect(emp)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedEmployee?.emp_id === emp.emp_id
                      ? 'bg-white-100 border-2 border-black'
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                  }`}
                >
                  <div className="font-medium">{emp.emp_name}</div>
                  <div className="text-sm text-gray-600">ID: {emp.emp_id}</div>
                  <div className="text-sm text-gray-600">
                    Status: {emp.is_active ? 'Active' : 'Inactive'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Employee Details & Operations */}
          <div className="lg:col-span-2">
            {selectedEmployee ? (
              <div className="space-y-6">
                {/* Employee Info */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    {selectedEmployee.emp_name} - Employee Details
                  </h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="font-medium">Employee ID:</span> {selectedEmployee.emp_id}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>{' '}
                      <span className={selectedEmployee.is_active ? 'text-green-600' : 'text-red-600'}>
                        {selectedEmployee.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Tab Navigation */}
                <div className="bg-white rounded-lg shadow-md">
                  <div className="flex border-b">
                    <button
                      onClick={() => setActiveTab('assign')}
                      className={`px-6 py-3 font-medium ${
                        activeTab === 'assign'
                          ? 'border-b-2 border-black text-black'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Briefcase className="inline mr-2" size={16} />
                      Assign Job
                    </button>
                    <button
                      onClick={() => setActiveTab('terminate')}
                      className={`px-6 py-3 font-medium ${
                        activeTab === 'terminate'
                          ? 'border-b-2 border-black text-black'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Calendar className="inline mr-2" size={16} />
                      Terminate
                    </button>
                    <button
                      onClick={() => setActiveTab('history')}
                      className={`px-6 py-3 font-medium ${
                        activeTab === 'history'
                          ? 'border-b-2 border-black text-black'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <IndianRupee  className="inline mr-2" size={16} />
                      Job History
                    </button>
                  </div>

                  <div className="p-6">
                    {/* Assign Job Tab */}
                    {activeTab === 'assign' && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Assign New Job</h3>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Select Job
                          </label>
                          <select
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={assignData.job_id}
                            onChange={(e) => setAssignData({ ...assignData, job_id: e.target.value })}
                          >
                            <option value="">Select a job...</option>
                            {jobs.map((job) => (
                              <option key={job.job_id} value={job.job_id}>
                                {job.job_title} (ID: {job.job_id})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Date
                          </label>
                          <input
                            type="date"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={assignData.start_date}
                            onChange={(e) => setAssignData({ ...assignData, start_date: e.target.value })}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Salary
                          </label>
                          <input
                            type="number"
                            placeholder="Enter salary amount"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={assignData.salary}
                            onChange={(e) => setAssignData({ ...assignData, salary: e.target.value })}
                          />
                        </div>

                        <button
                          onClick={handleAssignJob}
                          className="w-full bg-black text-white px-4 py-3 rounded-lg hover:bg-black disabled:opacity-100 disabled:cursor-not-allowed font-medium"
                          disabled={loading || !assignData.job_id || !assignData.start_date || !assignData.salary}
                        >
                          {loading ? 'Assigning...' : 'Assign Job'}
                        </button>
                      </div>
                    )}

                    {/* Terminate Tab */}
                    {activeTab === 'terminate' && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Terminate Current Job</h3>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Termination Date
                          </label>
                          <input
                            type="date"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={terminateDate}
                            onChange={(e) => setTerminateDate(e.target.value)}
                          />
                        </div>

                        <button
                          onClick={handleTerminate}
                          className="w-full bg-red-600 text-white px-4 py-3 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                          disabled={loading || !terminateDate}
                        >
                          {loading ? 'Terminating...' : 'Terminate Employee'}
                        </button>
                      </div>
                    )}

                    {/* Job History Tab */}
                    {activeTab === 'history' && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Job History</h3>
                        
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse border border-gray-300">
                            <thead>
                              <tr className="bg-gray-50">
                                <th className="border border-gray-300 px-4 py-2 text-left">Job Title</th>
                                <th className="border border-gray-300 px-4 py-2 text-left">Start Date</th>
                                <th className="border border-gray-300 px-4 py-2 text-left">End Date</th>
                                <th className="border border-gray-300 px-4 py-2 text-left">Salary</th>
                                <th className="border border-gray-300 px-4 py-2 text-left">Current</th>
                              </tr>
                            </thead>
                            <tbody>
                              {jobHistory.length > 0 ? (
                                jobHistory.map((status) => (
                                  <tr key={status.st_id} className="hover:bg-gray-50">
                                    <td className="border border-gray-300 px-4 py-2">
                                      {status.job?.job_title || getJobTitle(status.job_id)}
                                    </td>
                                    <td className="border border-gray-300 px-4 py-2">{status.start_date}</td>
                                    <td className="border border-gray-300 px-4 py-2">
                                      {status.end_date || '-'}
                                    </td>
                                    <td className="border border-gray-300 px-4 py-2">
                                      ₹{status.salary?.toLocaleString()}
                                    </td>
                                    <td className="border border-gray-300 px-4 py-2">
                                      <span className={`px-2 py-1 rounded-full text-xs ${
                                        status.is_current 
                                          ? 'bg-green-100 text-green-800' 
                                          : 'bg-gray-100 text-gray-800'
                                      }`}>
                                        {status.is_current ? 'Yes' : 'No'}
                                      </span>
                                    </td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan="5" className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                                    No job history found for this employee
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <User size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select an Employee</h3>
                <p className="text-gray-500">Choose an employee from the list to manage their job assignments and history.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}