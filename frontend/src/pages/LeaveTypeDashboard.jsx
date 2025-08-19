import { useState, useEffect } from "react";
import axios from "axios";

import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus } from "lucide-react";
import { Switch } from "@/components/ui/switch";

export default function LeaveTypeDashboard() {
  const API_URL = "http://127.0.0.1:8000/api/leave-types/";

  const [leaveTypes, setLeaveTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLeave, setEditingLeave] = useState(null);
  const [form, setForm] = useState({
    leave_name: "",
    max_consecutive_days: "",
    annual_allocation: "",
    carry_forward: false,
    min_notice_days: 0,
    is_active: true,
  });
  const [error, setError] = useState("");

  // --- Fetch Leave Types ---
  const fetchLeaveTypes = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get(API_URL);
      setLeaveTypes(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch leave types.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaveTypes();
  }, []);

  // --- Form Handling ---
  useEffect(() => {
    if (editingLeave) setForm(editingLeave);
    else
      setForm({
        leave_name: "",
        max_consecutive_days: "",
        annual_allocation: "",
        carry_forward: false,
        min_notice_days: 0,
        is_active: true,
      });
    setError("");
  }, [editingLeave]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (editingLeave) {
        await axios.put(`${API_URL}${editingLeave.leave_type_id}/`, form);
      } else {
        await axios.post(API_URL, form);
      }
      setModalOpen(false);
      setEditingLeave(null);
      fetchLeaveTypes();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Error saving leave type.");
    }
  };

  const handleDelete = async (id) => {
    setError("");
    try {
      await axios.delete(`${API_URL}${id}/`);
      fetchLeaveTypes();
    } catch (err) {
      console.error(err);
      setError("Error deleting leave type.");
    }
  };

  if (loading) return <div className="p-5">Loading...</div>;
return (
  <div className="p-6">
    {/* Error Alert */}
    {error && (
      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center">
          <div className="ml-3">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        </div>
      </div>
    )}

    {/* Main Card Container */}
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
        <div>
          <CardTitle className="text-xl font-semibold text-gray-900">Leave Types</CardTitle>
        </div>
        <Dialog open={modalOpen} onOpenChange={setModalOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Leave Type
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="text-lg font-semibold">
                {editingLeave ? "Edit Leave Type" : "Add Leave Type"}
              </DialogTitle>
            </DialogHeader>

            <form className="space-y-4 py-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="leave_name" className="text-sm font-medium text-gray-700">
                  Leave Name
                </Label>
                <Input
                  id="leave_name"
                  name="leave_name"
                  placeholder="e.g., Annual Leave, Sick Leave"
                  value={form.leave_name}
                  onChange={handleChange}
                  className="focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_consecutive_days" className="text-sm font-medium text-gray-700">
                    Max Consecutive Days
                  </Label>
                  <Input
                    id="max_consecutive_days"
                    type="number"
                    name="max_consecutive_days"
                    placeholder="0"
                    value={form.max_consecutive_days}
                    onChange={handleChange}
                    className="focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="annual_allocation" className="text-sm font-medium text-gray-700">
                    Annual Allocation
                  </Label>
                  <Input
                    id="annual_allocation"
                    type="number"
                    name="annual_allocation"
                    placeholder="0"
                    value={form.annual_allocation}
                    onChange={handleChange}
                    className="focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="min_notice_days" className="text-sm font-medium text-gray-700">
                  Minimum Notice Days
                </Label>
                <Input
                  id="min_notice_days"
                  type="number"
                  name="min_notice_days"
                  placeholder="0"
                  value={form.min_notice_days}
                  onChange={handleChange}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between pt-2">
                <Label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                  Active
                </Label>
                <Switch
                  id="is_active"
                  checked={form.is_active}
                  onCheckedChange={(checked) => setForm(prev => ({ ...prev, is_active: checked }))}
                />
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <Checkbox
                  id="carry_forward"
                  name="carry_forward"
                  checked={form.carry_forward}
                  onCheckedChange={(checked) => setForm(prev => ({ ...prev, carry_forward: checked }))}
                />
                <Label htmlFor="carry_forward" className="text-sm font-medium text-gray-700">
                  Allow carry forward to next year
                </Label>
              </div>

              <DialogFooter className="flex gap-3 pt-6">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => {
                    setModalOpen(false);
                    setEditingLeave(null);
                    setError("");
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  {editingLeave ? "Update Leave Type" : "Create Leave Type"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </CardHeader>

      <CardContent>
        {leaveTypes.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-lg font-medium">No Leave Type Yet</p>
            <p className="text-sm">Create your first leave type to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {leaveTypes.map((leave) => (
              <Card key={leave.leave_type_id} className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg font-semibold text-gray-900 flex items-center justify-between">
                    {leave.leave_name}
                    <div className="flex gap-1">
                      {leave.carry_forward && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
                          Carry Forward
                        </span>
                      )}
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        leave.is_active 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {leave.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </CardTitle>
                </CardHeader>

                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="font-medium text-gray-600">Max Days</p>
                      <p className="text-lg font-semibold text-gray-900">{leave.max_consecutive_days}</p>
                    </div>
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="font-medium text-gray-600">Annual Days</p>
                      <p className="text-lg font-semibold text-gray-900">{leave.annual_allocation}</p>
                    </div>
                  </div>

                  <div className="pt-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-600">Notice Required:</span>
                      <span className="font-semibold text-gray-900">
                        {leave.min_notice_days} {leave.min_notice_days === 1 ? 'day' : 'days'}
                      </span>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="pt-3 border-t border-gray-100">
                  <div className="flex gap-2 w-full">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingLeave(leave);
                        setModalOpen(true);
                      }}
                      className="flex-1 hover:bg-blue-50 hover:border-blue-300"
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(leave.leave_type_id)}
                      className="flex-1 text-red-600 hover:bg-red-50 hover:border-red-300"
                    >
                      Delete
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  </div>
);
}