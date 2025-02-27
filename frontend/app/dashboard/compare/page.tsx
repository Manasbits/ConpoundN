export default function ComparePage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Compare Stocks</h1>
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <input
              type="text"
              placeholder="Enter first stock..."
              className="w-full p-2 border rounded-lg"
            />
          </div>
          <div>
            <input
              type="text"
              placeholder="Enter second stock..."
              className="w-full p-2 border rounded-lg"
            />
          </div>
          <div className="col-span-2 min-h-[400px] bg-gray-50 rounded-lg p-4">
            {/* Comparison results will appear here */}
          </div>
        </div>
      </div>
    </div>
  );
}