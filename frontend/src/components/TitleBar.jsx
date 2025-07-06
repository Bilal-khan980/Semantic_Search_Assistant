import { Database } from "lucide-react"

export function TitleBar() {
  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between select-none">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-primary-600" />
          <h1 className="text-lg font-semibold text-gray-900">Local Document Search</h1>
        </div>
        <div className="text-sm text-gray-500">Privacy-first semantic search</div>
      </div>

      <div className="flex items-center space-x-2 text-sm text-gray-500">
        <span>v1.0.0</span>
      </div>
    </div>
  )
}
