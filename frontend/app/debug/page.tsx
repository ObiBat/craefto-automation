'use client'

import { useState } from 'react'
import { API_BASE_URL } from '@/lib/api'

export default function DebugPage() {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const testConnection = async () => {
    setLoading(true)
    setResult('Testing connection...\n')
    
    try {
      // Test 1: Check API_BASE_URL
      setResult(prev => prev + `API_BASE_URL: ${API_BASE_URL}\n`)
      
      // Test 2: Test fetch to status endpoint
      const response = await fetch(`${API_BASE_URL}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      setResult(prev => prev + `Status response: ${response.status} ${response.statusText}\n`)
      
      if (response.ok) {
        const data = await response.json()
        setResult(prev => prev + `Status data: ${JSON.stringify(data)}\n`)
      } else {
        const text = await response.text()
        setResult(prev => prev + `Error response: ${text}\n`)
      }
      
      // Test 3: Test POST request
      setResult(prev => prev + '\nTesting POST request...\n')
      const postResponse = await fetch(`${API_BASE_URL}/api/generate/social`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'cc6fc50edd48edcdb3e0e9d3fecdb1ed7f27ab5e19d4b226'
        },
        body: JSON.stringify({ topic: 'Test Topic' })
      })
      
      setResult(prev => prev + `POST response: ${postResponse.status} ${postResponse.statusText}\n`)
      
      if (postResponse.ok) {
        const postData = await postResponse.json()
        setResult(prev => prev + `POST success: ${JSON.stringify(postData, null, 2)}\n`)
      } else {
        const postText = await postResponse.text()
        setResult(prev => prev + `POST error: ${postText}\n`)
      }
      
    } catch (error) {
      setResult(prev => prev + `Connection error: ${error}\n`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">API Debug Page</h1>
      
      <button 
        onClick={testConnection}
        disabled={loading}
        className="bg-green-500 text-white px-4 py-2 rounded mb-4 disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test API Connection'}
      </button>
      
      <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto h-96 whitespace-pre-wrap">
        {result || 'Click "Test API Connection" to start debugging...'}
      </pre>
    </div>
  )
}
