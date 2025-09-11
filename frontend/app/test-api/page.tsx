"use client"

import { useEffect, useState } from "react"

export default function TestApiPage() {
  const [result, setResult] = useState<string>("Loading...")

  useEffect(() => {
    const testApi = async () => {
      try {
        console.log('🔍 Testing API call...')
        const response = await fetch('http://localhost:8000/status')
        console.log('🔍 Response:', response)
        const data = await response.json()
        console.log('🔍 Data:', data)
        setResult(JSON.stringify(data, null, 2))
      } catch (error) {
        console.log('🔍 Error:', error)
        setResult(`Error: ${error}`)
      }
    }
    testApi()
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>
      <pre className="bg-gray-100 p-4 rounded">{result}</pre>
    </div>
  )
}
