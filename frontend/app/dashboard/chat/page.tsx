"use client";

import React, { useState } from 'react';

export default function StockChatPage() {
  const [stockName, setStockName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isChatReady, setIsChatReady] = useState(false);
  const [error, setError] = useState('');

  const handleProcessStock = async () => {
    if (!stockName.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/process-stock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stockName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process stock');
      }

      setIsChatReady(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setIsChatReady(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-center mb-4">Stock Analysis Chat</h1>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {/* Stock Name Input Stage */}
          {!isLoading && !isChatReady && (
            <div className="space-y-4">
              <input
                type="text"
                value={stockName}
                onChange={(e) => setStockName(e.target.value)}
                placeholder="Enter Stock Name (e.g., AAPL)"
                className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleProcessStock}
                className="w-full bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 transition"
              >
                Process Stock
              </button>
            </div>
          )}

          {/* Loading Stage */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-blue-500"></div>
              <p className="text-gray-600">Processing {stockName}...</p>
              <p className="text-sm text-gray-500">This may take up to 10 seconds</p>
            </div>
          )}

          {/* Chat Interface Stage */}
          {isChatReady && (
            <div className="flex flex-col h-[500px]">
              <div className="flex-1 overflow-y-auto bg-gray-50 p-4 rounded-lg mb-4">
                <div className="mb-2 p-3 rounded-lg max-w-[80%] bg-blue-100 text-blue-800 ml-auto">
                  User message
                </div>
                <div className="mb-2 p-3 rounded-lg max-w-[80%] bg-green-100 text-green-800 mr-auto">
                  AI response
                </div>
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Ask about the stock..."
                  className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  className="bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 transition"
                >
                  Send
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}