import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

const EmployeeLeaveBalance = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmpId, setSelectedEmpId] = useState("");
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [loadingBalances, setLoadingBalances] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all employees for dropdown
  useEffect(() => {
    const fetchEmployees = async () => {
      setLoadingEmployees(true);
      try {
        const res = await axios.get("http://localhost:8000/api/employees/");
        setEmployees(res.data);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch employees.");
      } finally {
        setLoadingEmployees(false);
      }
    };
    fetchEmployees();
  }, []);

  // Fetch selected employee's leave balances
  useEffect(() => {
    if (!selectedEmpId) return;

    const fetchLeaveBalances = async () => {
      setLoadingBalances(true);
      try {
        const res = await axios.get(
          `http://localhost:8000/api/leave-balances/${selectedEmpId}/?year=${new Date().getFullYear()}`
        );
        setLeaveBalances([res.data]); // wrap in array to keep table mapping
      } catch (err) {
        console.error(err);
        setLeaveBalances([]);
        setError("Failed to fetch leave balances.");
      } finally {
        setLoadingBalances(false);
      }
    };

    fetchLeaveBalances();
  }, [selectedEmpId]);

  const getSelectedEmployeeName = () => {
    const employee = employees.find(emp => emp.emp_id === selectedEmpId);
    return employee ? employee.emp_name : "";
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
              Employee Leave Balances {selectedEmpId && `- ${getSelectedEmployeeName()}`}
            </CardTitle>
            <div className="text-sm text-gray-600">
              Year: {new Date().getFullYear()}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Employee Dropdown */}
          {loadingEmployees ? (
            <Skeleton className="h-10 w-full mb-6" />
          ) : employees.length > 0 ? (
            <Select
              onValueChange={setSelectedEmpId}
              value={selectedEmpId}
              className="mb-6 w-full"
            >
              <SelectTrigger>
                <SelectValue placeholder="Select an Employee" />
              </SelectTrigger>
              <SelectContent>
                {employees.map((emp) => (
                  <SelectItem key={emp.emp_id} value={emp.emp_id}>
                    {emp.emp_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">No employees found</p>
              <p className="text-sm">Please check your connection or try again</p>
            </div>
          )}

          {/* Leave Balances Display */}
          {loadingBalances ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading Leave Balances...</span>
            </div>
          ) : leaveBalances.length > 0 && leaveBalances[0]?.balances ? (
            <div className="overflow-x-auto">
              <div className="min-w-full">
                {/* Table Header */}
                <div className="grid grid-cols-4 gap-4 p-3 bg-gray-50 border-b font-medium text-sm">
                  <div>Leave Type</div>
                  <div>Allocated Days</div>
                  <div>Used Days</div>
                  <div>Available Days</div>
                </div>
                
                {/* Table Body */}
                {leaveBalances[0].balances.map((lb) => (
                  <div 
                    key={lb.leave_type_id} 
                    className="grid grid-cols-4 gap-4 p-3 border-b hover:bg-gray-50 transition-colors"
                  >
                    <div className="font-medium">{lb.leave_type_name}</div>
                    <div className="text-sm text-gray-600">{lb.allocated_days}</div>
                    <div className="text-sm text-gray-600">{lb.used_days}</div>
                    <div className={`text-sm font-medium ${
                      lb.available_days > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {lb.available_days}
                    </div>
                  </div>
                ))}
                
                {/* Summary Row */}
                <div className="grid grid-cols-4 gap-4 p-3 bg-blue-50 border-t-2 border-blue-200 font-medium text-sm">
                  <div className="text-blue-800">Total</div>
                  <div className="text-blue-700">
                    {leaveBalances[0].balances.reduce((sum, lb) => sum + lb.allocated_days, 0)}
                  </div>
                  <div className="text-blue-700">
                    {leaveBalances[0].balances.reduce((sum, lb) => sum + lb.used_days, 0)}
                  </div>
                  <div className="text-blue-700">
                    {leaveBalances[0].balances.reduce((sum, lb) => sum + lb.available_days, 0)}
                  </div>
                </div>
              </div>
            </div>
          ) : selectedEmpId ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">No leave balances found</p>
              <p className="text-sm">This employee may not have any leave allocations for {new Date().getFullYear()}</p>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg font-medium">Select an employee</p>
              <p className="text-sm">Choose an employee from the dropdown to view their leave balances</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EmployeeLeaveBalance;