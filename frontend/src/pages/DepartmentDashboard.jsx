import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Plus } from "lucide-react";
import { Loader2 } from "lucide-react";

export default function DepartmentDashboard() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ dept_name: "" });
  const [editingDept, setEditingDept] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Fetch all departments with error handling
  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/Departments/");
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setDepartments(data);
    } catch (err) {
      console.error("Failed to fetch departments:", err);
      setError("Failed to load departments. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  // Reset form and close dialog
  const resetForm = () => {
    setFormData({ dept_name: "" });
    setEditingDept(null);
    setDialogOpen(false);
    setError("");
  };

  // Handle create or update
  const handleSubmit = async () => {
    if (!formData.dept_name.trim()) {
      setError("Department name is required");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const url = editingDept 
        ? `http://127.0.0.1:8000/api/Departments/${editingDept.dept_id}/`
        : "http://127.0.0.1:8000/api/Departments/";
      
      const method = editingDept ? "PUT" : "POST";
      const body = editingDept 
        ? { ...editingDept, dept_name: formData.dept_name.trim() }
        : { dept_name: formData.dept_name.trim() };

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      resetForm();
      await fetchDepartments();
    } catch (err) {
      console.error("Failed to save department:", err);
      setError("Failed to save department. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // Handle delete with confirmation
  const handleDelete = async (dept_id, dept_name) => {
    if (!window.confirm(`Are you sure you want to delete "${dept_name}"?`)) {
      return;
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/Departments/${dept_id}/`, {
        method: "DELETE",
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      await fetchDepartments();
    } catch (err) {
      console.error("Failed to delete department:", err);
      setError("Failed to delete department. Please try again.");
    }
  };

  // Handle edit button click
  const handleEdit = (dept) => {
    setEditingDept(dept);
    setFormData({ dept_name: dept.dept_name });
    setDialogOpen(true);
    setError("");
  };

  // Handle add button click
  const handleAdd = () => {
    resetForm();
    setDialogOpen(true);
  };

  // Handle key press in input
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}
      
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-xl font-bold">
              Departments ({departments.length})
            </CardTitle>
            <Dialog open={dialogOpen} onOpenChange={handleAdd}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Add Department
              </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>
                    {editingDept ? "Edit Department" : "Create New Department"}
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Department Name"
                    value={formData.dept_name}
                    onChange={(e) => setFormData({ dept_name: e.target.value })}
                    onKeyPress={handleKeyPress}
                    disabled={submitting}
                    autoFocus
                  />
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={handleSubmit}
                      disabled={submitting || !formData.dept_name.trim()}
                      className="flex-1"
                    >
                      {submitting ? "Saving..." : (editingDept ? "Update" : "Create")}
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={resetForm}
                      disabled={submitting}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading Departments...</span>
            </div>
          ) : departments.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">No departments found</p>
              <p className="text-sm">Add your first department to get started</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-full">
                {/* Table Header */}
                <div className="grid grid-cols-5 gap-4 p-3 bg-gray-50 border-b font-medium text-sm">
                  <div>Name</div>
                  <div>Created</div>
                  <div>Updated</div>
                  <div>Actions</div>
                </div>
                
                {/* Table Body */}
                {departments.map((dept) => (
                  <div 
                    key={dept.dept_id} 
                    className="grid grid-cols-5 gap-4 p-3 border-b hover:bg-gray-50 transition-colors"
                  >
                    <div className="font-medium">{dept.dept_name}</div>
                    <div className="text-sm text-gray-600">
                      {new Date(dept.created_at).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-gray-600">
                      {new Date(dept.updated_at).toLocaleDateString()}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(dept)}
                        className="text-xs px-3 py-1"
                      >
                        Edit
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(dept.dept_id, dept.dept_name)}
                        className="text-xs px-3 py-1"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}