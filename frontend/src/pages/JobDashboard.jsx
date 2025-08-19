import { useEffect, useState, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Plus, Edit, Trash2 } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const initialFormData = { job_title: "", dept: "", is_active: true, job_description: "" };

export default function JobsDashboard() {
  const [jobs, setJobs] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState(initialFormData);
  const [editingJob, setEditingJob] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState("");

  // Fetch jobs
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/Jobs/`);
      if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.status}`);
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch departments
  const fetchDepartments = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/Departments/`);
      if (!res.ok) throw new Error(`Failed to fetch departments: ${res.status}`);
      const data = await res.json();
      setDepartments(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load departments.");
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchDepartments();
  }, [fetchJobs, fetchDepartments]);

  // Form validation
  const isFormValid = useMemo(() => {
    return formData.job_title.trim() && formData.dept;
  }, [formData]);

  const resetForm = useCallback(() => {
    setFormData(initialFormData);
    setEditingJob(null);
    setError("");
  }, []);

  // Handle input changes
  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError("");
  }, [error]);

  // Handle dialog close
  const handleDialogClose = useCallback((open) => {
    setDialogOpen(open);
    if (!open) resetForm();
  }, [resetForm]);

  // Handle edit
  const handleEdit = useCallback((job) => {
    setEditingJob(job);
    setFormData({
      job_title: job.job_title,
      dept: job.dept?.dept_id || "",
      is_active: job.is_active,
      job_description: job.job_description || "",
    });
    setDialogOpen(true);
  }, []);

  // Handle delete
  const handleDelete = useCallback(async (jobId, jobTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${jobTitle}"?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/Jobs/${jobId}/`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      await fetchJobs();
    } catch (err) {
      console.error(err);
      setError("Failed to delete job.");
    }
  }, [fetchJobs]);

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (!isFormValid) {
      setError("Please fill in all required fields.");
      return;
    }
    setSubmitting(true);
    setError("");

    const payload = {
      job_title: formData.job_title.trim(),
      department_id: formData.dept, // send dept id to backend
      is_active: formData.is_active,
      job_description: formData.job_description,
    };

    try {
      const url = editingJob
        ? `${API_BASE_URL}/Jobs/${editingJob.job_id}/`
        : `${API_BASE_URL}/Jobs/`;
      const method = editingJob ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.department_id?.[0] || errorData?.detail || `Request failed: ${res.status}`);
      }
      resetForm();
      setDialogOpen(false);
      await fetchJobs();
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to save job.");
    } finally {
      setSubmitting(false);
    }
  }, [formData, editingJob, isFormValid, resetForm, fetchJobs]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => setError("")}>Dismiss</Button>
          </CardContent>
        </Card>
      )}

      <Card className="shadow-lg">
        <CardHeader className="flex justify-between items-center">
          {/* Left: Title */}
<CardTitle className="text-xl font-bold text-left">
  Jobs Management   ({jobs.length})
</CardTitle>


          {/* Right: Add Job Button */}
          <Dialog open={dialogOpen} onOpenChange={handleDialogClose}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Add Job
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <CardHeader>
                <CardTitle>{editingJob ? "Edit Job" : "Create New Job"}</CardTitle>
              </CardHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Job Title *</label>
                  <Input
                    placeholder="Enter job title"
                    value={formData.job_title}
                    onChange={(e) => handleInputChange("job_title", e.target.value)}
                    disabled={submitting}
                  />
                </div>


                <div className="grid gap-2">
                  <label className="text-sm font-medium">Department *</label>
                  <Select
                    value={formData.dept}
                    onValueChange={(val) => handleInputChange("dept", val)}
                    disabled={submitting}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      {departments.map((dept) => (
                        <SelectItem key={dept.dept_id} value={dept.dept_id}>
                          {dept.dept_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid gap-2">
                  <label className="text-sm font-medium">Job Description</label>
                  <Input
                    placeholder="Enter description"
                    value={formData.job_description}
                    onChange={(e) => handleInputChange("job_description", e.target.value)}
                    disabled={submitting}
                  />
                </div>

                <div className="flex items-center gap-3">
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(val) => handleInputChange("is_active", val)}
                    disabled={submitting}
                  />
                  <label className="text-sm font-medium">Active</label>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={handleSubmit}
                    disabled={!isFormValid || submitting}
                    className="flex-1"
                  >
                    {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {editingJob ? "Update Job" : "Create Job"}
                  </Button>
                  <Button variant="outline" onClick={() => handleDialogClose(false)} disabled={submitting}>
                    Cancel
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading jobs...</span>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">No jobs found</p>
              <p className="text-sm">Create your first job to get started</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Title</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead className="w-24">Status</TableHead>
                    <TableHead className="w-32 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.job_id} className="hover:bg-gray-50">
                      <TableCell className="font-medium">{job.job_title}</TableCell>
                      <TableCell>{job.dept?.dept_name || "No Department"}</TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${job.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                            }`}
                        >
                          {job.is_active ? "Active" : "Inactive"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(job)} className="h-8 w-8 p-0" title="Edit job">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(job.job_id, job.job_title)} className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50" title="Delete job">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
