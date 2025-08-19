export default function Home() {
  return (
    <div className="min-h-screen bg-white relative overflow-hidden flex items-center justify-center">
      {/* Background Pattern */}
      <div className="absolute inset-0">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(circle at 75% 25%, #000 2px, transparent 2px),
            radial-gradient(circle at 75% 75%, #000 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          opacity: 0.05
        }} />
        <div className="absolute inset-0" style={{
          backgroundImage: `
            linear-gradient(45deg, #000 25%, transparent 25%),
            linear-gradient(-45deg, #000 25%, transparent 25%),
            linear-gradient(45deg, transparent 75%, #000 75%),
            linear-gradient(-45deg, transparent 75%, #000 75%)
          `,
          backgroundSize: '40px 40px',
          opacity: 0.03
        }} />
        <div className="absolute inset-0" style={{
          backgroundImage: `
            repeating-linear-gradient(0deg, transparent, transparent 10px, #000 10px, #000 11px),
            repeating-linear-gradient(90deg, transparent, transparent 10px, #000 10px, #000 11px)
          `,
          opacity: 0.02
        }} />
      </div>

      {/* Floating Elements */}
      <div className="absolute top-20 left-20 w-32 h-32 bg-black/5 rounded-full animate-pulse" />
      <div className="absolute bottom-32 right-32 w-24 h-24 bg-black/3 rounded-full animate-bounce" style={{ animationDuration: '3s' }} />
      <div className="absolute top-1/3 right-1/4 w-16 h-16 bg-black/5 rotate-45 animate-spin" style={{ animationDuration: '15s' }} />

      {/* Main Content */}
      <div className="text-center z-10 px-6">
        <h1 className="text-6xl md:text-8xl font-bold mb-8 text-black">
          Symplora
        </h1>
        
        <p className="text-2xl md:text-3xl text-gray-600 mb-12 font-light max-w-2xl mx-auto">
          Manage departments, jobs, and employees 
          <span className="block text-black font-normal">all in one place</span>
        </p>
      </div>
    </div>
  );
} 