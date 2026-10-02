import React, { useState } from 'react'
import { Header } from './components/Header'
import { AnswerForm } from './components/AnswerForm'
import { LoadingState } from './components/LoadingState'
import { ErrorAlert } from './components/ErrorAlert'
import { Dashboard } from './components/Dashboard'
import { InterviewMode } from './components/InterviewMode'
import { ProgressTracker } from './components/ProgressTracker'
import { MessageSquare, PlayCircle, TrendingUp } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('single') // 'single' | 'interview' | 'tracker'

  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [category, setCategory] = useState('behavioral')
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // Read backend API URL from Vite environment variable
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

  const handleAnalyze = async () => {
    if (!question.trim() || !answer.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${backendUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: question.trim(),
          answer: answer.trim(),
          category: category
        })
      })

      const data = await response.json()

      if (!response.ok) {
        let errMessage = data.message || data.detail || `Server error (${response.status})`
        if (data.details && Array.isArray(data.details)) {
          errMessage += ': ' + data.details.map(d => `${d.field}: ${d.message}`).join(', ')
        }
        throw new Error(errMessage)
      }

      setResult(data)
    } catch (err) {
      console.error('Analysis request error:', err)
      setError(err.message || 'Failed to submit answer for analysis. Please ensure the backend server is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeAnother = () => {
    setResult(null)
    setQuestion('')
    setAnswer('')
    setError(null)
  }

  const handleDismissError = () => {
    setError(null)
  }

  return (
    <div className="app-container">
      <Header />

      {/* Mode Navigation Tabs */}
      <div className="mode-nav-tabs">
        <button
          type="button"
          className={`nav-tab ${activeTab === 'single' ? 'active' : ''}`}
          onClick={() => setActiveTab('single')}
        >
          <MessageSquare size={18} />
          <span>Single Answer Analysis</span>
        </button>

        <button
          type="button"
          className={`nav-tab ${activeTab === 'interview' ? 'active' : ''}`}
          onClick={() => setActiveTab('interview')}
        >
          <PlayCircle size={18} />
          <span>Interactive Interview Mode</span>
        </button>

        <button
          type="button"
          className={`nav-tab ${activeTab === 'tracker' ? 'active' : ''}`}
          onClick={() => setActiveTab('tracker')}
        >
          <TrendingUp size={18} />
          <span>Progress & Weaknesses</span>
        </button>
      </div>

      <main className="main-content">
        {activeTab === 'single' && (
          <>
            {!result && (
              <AnswerForm
                question={question}
                setQuestion={setQuestion}
                answer={answer}
                setAnswer={setAnswer}
                category={category}
                setCategory={setCategory}
                onAnalyze={handleAnalyze}
                loading={loading}
              />
            )}

            <ErrorAlert 
              error={error} 
              onRetry={handleAnalyze} 
              onDismiss={handleDismissError} 
            />

            {loading && <LoadingState />}

            {!loading && result && (
              <Dashboard 
                result={result} 
                onRetry={handleAnalyze} 
                onAnalyzeAnother={handleAnalyzeAnother} 
              />
            )}
          </>
        )}

        {activeTab === 'interview' && (
          <InterviewMode backendUrl={backendUrl} />
        )}

        {activeTab === 'tracker' && (
          <ProgressTracker backendUrl={backendUrl} />
        )}
      </main>
    </div>
  )
}

export default App
