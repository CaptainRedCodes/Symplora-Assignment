import React, { useState, useEffect, useMemo } from 'react';
import { Calendar, Plus, Search, Check, X, Trash2, Eye, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const LeaveDashboard = () => {
  const [leaves, setLeaves] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState(null);
  const [activeTab, setActiveTab] = useState('my-leaves');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    leave_type: '',
    search: ''
  });

  const [newLeave, setNewLeave] = useState({
    employee: '',
    leave_type: '',
    start_date: '',
    end_date: '',
    reason: '',
    comments: ''
  });

  const [approvalData, setApprovalData] = useState({
    comments: '',
    rejection_reason: ''
  });

  const API_BASE_URL = 'http://localhost:8000/api';

  // -------- Alerts auto-clear --------
  useEffect(() => {
    if (error || success) {
      const t = setTimeout(() => {
        setError('');
        setSuccess('');
      }, 5000);
      return () => clearTimeout(t);
    }
  }, [error, success]);

  // -------- Generic API helper --------
  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          // Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        // credentials: 'include',
        ...options,
      });

      if (!response.ok) {
        let details = '';
        try {
          const body = await response.json();
          details = body?.detail || JSON.stringify(body);
        } catch (_) {}
        throw new Error(`HTTP ${response.status} ${response.statusText}${details ? ` - ${details}` : ''}`);
      }
      // some endpoints may return 204
      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error('API call failed:', err);
      throw err;
    }
  };

  // -------- Fetchers --------
  const fetchLeaves = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.leave_type) params.append('leave_type', filters.leave_type);
      if (filters.search) params.append('search', filters.search);
      const qs = params.toString();
      const data = await apiCall(`/leave-applications/${qs ? `?${qs}` : ''}`);
      setLeaves(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to fetch leaves');
    }
  };


  const fetchEmployees = async () => {
    try {
      const data = await apiCall('/employees/');
      setEmployees(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch employees:', err);
      setError('Failed to load employees. Please check permissions.');
    }
  };

  const fetchLeaveTypes = async () => {
    try {
      const data = await apiCall('/leave-types/');
      setLeaveTypes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch leave types:', err);
    }
  };

  // -------- Date formatting --------
  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const dt = new Date(dateString);
    if (isNaN(dt)) return '—';
    return dt.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  // -------- Actions --------
  const handleCreateLeave = async () => {
    if (newLeave.start_date && newLeave.end_date) {
      const s = new Date(newLeave.start_date);
      const e = new Date(newLeave.end_date);
      if (e < s) {
        setError('End date cannot be before start date.');
        return;
      }
    }
    try {
      setLoading(true);
      await apiCall('/leave-applications/', {
        method: 'POST',
        body: JSON.stringify(newLeave),
      });
      setSuccess('Leave application submitted successfully!');
      setShowCreateModal(false);
      setNewLeave({
        employee: '',
        leave_type: '',
        start_date: '',
        end_date: '',
        reason: '',
        comments: '',
      });
      await fetchLeaves();
    } catch (err) {
      setError('Failed to submit leave application.');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveLeave = async () => {
    if (!selectedLeave) return;
    try {
      setLoading(true);
      await apiCall(`/leave-applications/${selectedLeave.leave_id}/approve/`, {
        method: 'POST',
        body: JSON.stringify({ comments: approvalData.comments }),
      });
      setSuccess('Leave approved successfully!');
      setShowApprovalModal(false);
      setSelectedLeave(null);
      await fetchLeaves();
    } catch (err) {
      setError('Failed to approve leave.');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectLeave = async () => {
    if (!selectedLeave) return;
    if (!approvalData.rejection_reason?.trim()) {
      setError('Rejection reason is required.');
      return;
    }
    try {
      setLoading(true);
      await apiCall(`/leave-applications/${selectedLeave.leave_id}/reject/`, {
        method: 'POST',
        body: JSON.stringify({ rejection_reason: approvalData.rejection_reason }),
      });
      setSuccess('Leave rejected successfully!');
      setShowApprovalModal(false);
      setSelectedLeave(null);
      await fetchLeaves();
    } catch (err) {
      setError('Failed to reject leave.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelLeave = async (leaveId) => {
    if (!window.confirm('Are you sure you want to cancel this leave?')) return;
    try {
      setLoading(true);
      await apiCall(`/leave-applications/${leaveId}/cancel/`, { method: 'POST' });
      setSuccess('Leave cancelled successfully!');
      await fetchLeaves();
    } catch (err) {
      setError('Failed to cancel leave.');
    } finally {
      setLoading(false);
    }
  };

  // -------- Effects: initial load --------
  useEffect(() => {
    // load everything initially
    (async () => {
      setLoading(true);
      try {
        await Promise.all([fetchEmployees(), fetchLeaveTypes(), fetchLeaves()]);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

const [debouncedSearch, setDebouncedSearch] = useState(filters.search);

// Debounce search separately
useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(filters.search);
  }, 350);
  return () => clearTimeout(timer);
}, [filters.search]);

useEffect(() => {
  fetchLeaves();
}, [filters.status, filters.leave_type, debouncedSearch]);

  // -------- UI Parts --------
  const LeaveCard = ({ leave }) => (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all duration-300">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-black to-gray-400 flex items-center justify-center text-white font-semibold text-lg shadow-sm">
            {leave?.employee_details?.emp_name?.charAt(0) || 'U'}
          </div>
          <div>
            <h3 className="text-base font-semibold text-gray-900">
              {leave?.leave_type_details?.leave_name || 'Unknown Leave Type'}
            </h3>
            <p className="text-sm font-medium text-gray-700">
              {leave?.employee_details?.emp_name || 'Unknown Employee'}
            </p>
            <p className="text-xs text-gray-500">{leave?.employee_details?.email || 'No email'}</p>
          </div>
        </div>

        <span
          className={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide border 
            ${
              leave?.status === 'APPROVED'
                ? 'bg-green-50 text-green-700 border-green-200'
                : leave?.status === 'REJECTED'
                ? 'bg-red-50 text-red-700 border-red-200'
                : leave?.status === 'CANCELLED'
                ? 'bg-gray-50 text-gray-700 border-gray-200'
                : 'bg-yellow-50 text-yellow-700 border-yellow-200'
            }`}
        >
          {leave?.status}
        </span>
      </div>

      <div className="space-y-3 mb-6 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Duration:</span>
          <span className="font-medium text-gray-800">
            {formatDate(leave?.start_date)} – {formatDate(leave?.end_date)}
            <span className="ml-1 text-gray-500">({leave?.days_requested ?? '—'} days)</span>
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Applied:</span>
          <span className="text-gray-800">{formatDate(leave?.applied_on)}</span>
        </div>
        {leave?.validated_on && (
          <div className="flex justify-between">
            <span className="text-gray-500">Processed:</span>
            <span className="text-gray-800">{formatDate(leave?.validated_on)}</span>
          </div>
        )}
      </div>

      <div className="bg-gray-50 rounded-xl p-4 mb-6">
        <p className="text-sm text-gray-700">
          <span className="font-medium">Reason:</span> {leave?.reason || '—'}
        </p>
        {leave?.comments && (
          <p className="text-sm text-gray-700 mt-2">
            <span className="font-medium">Comments:</span> {leave.comments}
          </p>
        )}
      </div>

      <div className="flex gap-2">
        {leave?.can_cancel && (
          <button
            onClick={() => handleCancelLeave(leave.leave_id)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition"
          >
            <Trash2 size={14} /> Cancel Leave
          </button>
        )}

        {leave?.status === 'PENDING' && (
          <button
            onClick={() => {
              setSelectedLeave(leave);
              setShowApprovalModal(true);
              setApprovalData({ comments: '', rejection_reason: '' });
            }}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-50 text-green-600 rounded-md hover:bg-green-100 transition"
          >
            <Eye size={14} /> Review
          </button>
        )}
      </div>
    </div>
  );

  const CreateLeaveModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Apply for Leave</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Employee</label>
            <select
              value={newLeave.employee}
              onChange={(e) => setNewLeave({ ...newLeave, employee: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Employee</option>
              {employees.map((emp) => (
                <option key={emp.emp_id} value={emp.emp_id}>
                  {emp.emp_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Leave Type</label>
            <select
              value={newLeave.leave_type}
              onChange={(e) => setNewLeave({ ...newLeave, leave_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Leave Type</option>
              {leaveTypes.map((type) => (
                <option key={type.leave_type_id} value={type.leave_type_id}>
                  {type.leave_name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={newLeave.start_date}
                onChange={(e) => setNewLeave({ ...newLeave, start_date: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={newLeave.end_date}
                onChange={(e) => setNewLeave({ ...newLeave, end_date: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
            <textarea
              value={newLeave.reason}
              onChange={(e) => setNewLeave({ ...newLeave, reason: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Please provide reason for leave"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Comments</label>
            <textarea
              value={newLeave.comments}
              onChange={(e) => setNewLeave({ ...newLeave, comments: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
              placeholder="Additional comments (optional)"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCreateLeave}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Application'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const ApprovalModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-xl font-semibold mb-4">Review Leave Application</h2>
        {selectedLeave && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium">{selectedLeave.employee_details?.emp_name}</h3>
              <p className="text-sm text-gray-600">{selectedLeave.employee_details?.email}</p>
              <p className="text-sm">
                {formatDate(selectedLeave.start_date)} - {formatDate(selectedLeave.end_date)} (
                {selectedLeave.days_requested ?? '—'} days)
              </p>
              <p className="text-sm mt-2">
                <span className="font-medium">Reason:</span> {selectedLeave.reason}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Comments (for approval)</label>
              <textarea
                value={approvalData.comments}
                onChange={(e) => setApprovalData({ ...approvalData, comments: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="2"
                placeholder="Optional comments for approval"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rejection Reason (if rejecting)</label>
              <textarea
                value={approvalData.rejection_reason}
                onChange={(e) => setApprovalData({ ...approvalData, rejection_reason: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="2"
                placeholder="Required if rejecting the application"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowApprovalModal(false);
                  setSelectedLeave(null);
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectLeave}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                <X size={16} className="inline mr-1" /> Reject
              </button>
              <button
                onClick={handleApproveLeave}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                <Check size={16} className="inline mr-1" /> Approve
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              Leave Management System
            </h1>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        </div>
      )}
      {success && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <Alert className="border-green-200 bg-green-50">
            <Check className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
          <button
            onClick={() => setActiveTab('my-leaves')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md ${
              activeTab === 'my-leaves' ? 'bg-white text-black shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Leaves Approval and Application ({leaves.length})
          </button>
        </div>

        {/* Filters + Actions */}
       <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6">
  {/* Left side (can hold filters later if needed) */}
  <div className="flex-1"></div>

  {/* Right side actions */}
  {activeTab === 'my-leaves' && (
    <button
      onClick={() => setShowCreateModal(true)}
      className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 flex items-center gap-2"
    >
      <Plus size={20} />
      Apply Leave
    </button>
  )}
</div>


        {/* Content */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activeTab === 'my-leaves'
              ? leaves.map((leave) => <LeaveCard key={leave.leave_id} leave={leave} />)
              : pendingLeaves.map((leave) => <LeaveCard key={leave.leave_id} leave={leave} />)}
          </div>
        )}

        {((activeTab === 'my-leaves' && leaves.length === 0) ||
          (activeTab === 'approvals' && pendingLeaves.length === 0)) &&
          !loading && (
            <div className="text-center py-12">
              <Calendar className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                {activeTab === 'my-leaves' ? 'No leave applications' : 'No pending approvals'}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {activeTab === 'my-leaves'
                  ? 'Get started by applying for a new leave.'
                  : 'All caught up! No leaves pending your approval.'}
              </p>
            </div>
          )}
      </div>

      {/* Modals */}
      {showCreateModal && <CreateLeaveModal />}
      {showApprovalModal && <ApprovalModal />}
    </div>
  );
};

export default LeaveDashboard;
