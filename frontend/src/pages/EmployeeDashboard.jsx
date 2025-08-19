import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Plus, Users, Edit2, Trash2 } from "lucide-react"
import { Loader2 } from "lucide-react";


export default function EmployeeDashboard() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    emp_name: "",
    email: "",
    phone: "",
    emp_education:"",
    hire_date: "",
    dept_id: "",
    is_active: true
  });
  const [editingEmp, setEditingEmp] = useState(null);

  // Fetch employees
  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/employees/");
      const data = await res.json();
      setEmployees(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch departments for dropdown
  const fetchDepartments = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/Departments/");
      const data = await res.json();
      setDepartments(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchEmployees();
    fetchDepartments();
  }, []);

  // Create or Update employee
  const handleSubmit = async () => {
    try {
      const url = editingEmp
        ? `http://127.0.0.1:8000/api/employees/${editingEmp.emp_id}/`
        : "http://127.0.0.1:8000/api/employees/";

      const method = editingEmp ? "PATCH" : "POST";

      await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      setFormData({
        emp_name: "",
        email: "",
        phone: "",
        emp_education:"",
        hire_date: "",
        dept_id: "",
        is_active: true,
      });
      setEditingEmp(null);
      setIsDialogOpen(false);
      fetchEmployees();
    } catch (err) {
      console.error(err);
    }
  };

  // Delete employee
  const handleDelete = async (emp_id) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/employees/${emp_id}/`, { method: "DELETE" });
      fetchEmployees();
    } catch (err) {
      console.error(err);
    }
  };

  return (
  <div className="p-6">
    {/* Employees Card with Add Button Inside */}
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-xl font-semibold">Employees</CardTitle>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="w-4 h-4 mr-2" />
              Add Employee
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="text-lg font-semibold">
                {editingEmp ? "Edit Employee" : " Create New Employee"}
              </DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Employee Name</label>
                <Input
                  placeholder="Enter employee name"
                  value={formData.emp_name}
                  onChange={(e) => setFormData({ ...formData, emp_name: e.target.value })}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Email</label>
                <Input
                  type="email"
                  placeholder="Enter email address"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Phone</label>
                <Input
                  placeholder="Enter phone number"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Education</label>
                <Input
                  placeholder="Enter Education"
                  value={formData.emp_education}
                  onChange={(e) => setFormData({ ...formData, emp_education: e.target.value })}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>


              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Hire Date</label>
                <Input
                  type="date"
                  value={formData.hire_date}
                  onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                  className="focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Switch
                  checked={formData.is_active}
                  onCheckedChange={(val) => setFormData({ ...formData, is_active: val })}
                />
                <span className="text-sm font-medium text-gray-700">Active Employee</span>
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <Button 
                variant="outline" 
                onClick={() => setIsDialogOpen(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSubmit}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                {editingEmp ? "Update Employee" : "Create Employee"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      
      <CardContent className="pt-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading Employees...</span>
            </div>
        ) : employees.length === 0 ? (
           <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">No Employees Yet</p>
              <p className="text-sm">Add your first employee to get started</p>
            </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="min-w-full">
              {/* Table Header */}
              <div className="grid grid-cols-6 gap-4 p-4 bg-gray-50 rounded-t-lg border font-medium text-sm text-gray-700">
                <div>Name</div>
                <div>Email</div>
                <div>Phone</div>
                <div>Education</div>
                <div>Hire Date</div>
                <div>Status</div>
              </div>

              {/* Table Body */}
              <div className="border border-t-0 rounded-b-lg overflow-hidden">
                {employees.map((emp, index) => (
                  <div
                    key={emp.emp_id}
                    className={`grid grid-cols-6 gap-4 p-4 hover:bg-gray-50 transition-colors ${
                      index !== employees.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                  >
                    <div className="font-medium text-gray-900">{emp.emp_name}</div>
                    <div className="text-sm text-gray-600">{emp.email}</div>
                    <div className="text-sm text-gray-600">{emp.phone}</div>
                    <div className="text-sm text-gray-600">{emp.emp_education}</div>
                    <div className="text-sm text-gray-600">
                      {new Date(emp.hire_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </div>
                    <div className="text-sm font-medium">
                      {emp.is_active ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <div className="w-1.5 h-1.5 bg-green-600 rounded-full mr-1"></div>
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          <div className="w-1.5 h-1.5 bg-red-600 rounded-full mr-1"></div>
                          Inactive
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 justify-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingEmp(emp);
                          setFormData({
                            emp_name: emp.emp_name,
                            email: emp.email,
                            phone: emp.phone,
                            hire_date: emp.hire_date,
                            dept_id: emp.dept?.dept_id || "",
                            is_active: emp.is_active,
                          });
                          setIsDialogOpen(true);
                        }}
                        className="text-xs px-3 py-1 hover:bg-blue-50 hover:border-blue-300"
                      >
                        <Edit2 className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(emp.emp_id)}
                        className="text-xs px-3 py-1 text-red-600 hover:bg-red-50 hover:border-red-300"
                      >
                        <Trash2 className="w-3 h-3 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  </div>
)
}