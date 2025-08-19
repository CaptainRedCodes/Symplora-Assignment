import { Link } from "react-router-dom";

// Header.jsx
export default function Header() {
  return (
    <header className="bg-black text-white shadow-md">
      <div className="container mx-auto flex justify-between items-center p-4">
        <h1 className="text-xl font-bold">Symplora Dashboard</h1>
        <div className="hidden md:flex space-x-6">
          <span>Welcome, Admin</span>
        </div>
      </div>
    </header>
  );
}

