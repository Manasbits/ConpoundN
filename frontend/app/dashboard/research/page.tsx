export default function ResearchPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Research Report</h1>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Search for a stock..."
            className="w-full p-2 border rounded-lg"
          />
          <div className="min-h-[400px] bg-gray-50 rounded-lg p-4">
            {/* Research content will appear here */}
          </div>
        </div>
      </div>
    </div>
  );
}