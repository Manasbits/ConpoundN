"use client";

import Link from "next/link";
import { MessageSquare, LineChart, BarChart2 } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 h-screen">
      <nav className="p-4 space-y-2">
        <Link 
          href="/dashboard/chat" 
          className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-lg text-black"
        >
          <MessageSquare className="h-5 w-5" />
          <span>Chat with Any Stock</span>
        </Link>
        
        <Link 
          href="/dashboard/research" 
          className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-lg text-black"
        >
          <LineChart className="h-5 w-5" />
          <span>Research Report</span>
        </Link>
        
        <Link 
          href="/dashboard/compare" 
          className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-lg text-black"
        >
          <BarChart2 className="h-5 w-5" />
          <span>Compare Stocks</span>
        </Link>
      </nav>
    </aside>
  );
}