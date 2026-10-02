import React, { useState } from 'react'
import {
  Play,
  Send,
  Square,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  BarChart2,
  RotateCcw,
  ArrowRight,
  Layers,
  ChevronDown,
  ChevronUp,
  Award
} from 'lucide-react'
import { INTERVIEW_CATEGORIES } from '../constants/categories'
import { Dashboard } from './Dashboard'

export function InterviewMode({ backendUrl }) {
  const [session, setSession] = useState(null) // { session_id, category, question_number, total_questions, current_question }
  const [category, setCategory] = useState('behavioral')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Current answer evaluation result from backend submit response
  const [currentAnalysis, setCurrentAnalysis] = useState(null)
  const [nextQuestionText, setNextQuestionText] = useState('')
  
  // Final summary report
  const [summaryReport, setSummaryReport] = useState(null)

  // Accordion state for summary Q&A list
  const [expandedIndex, setExpandedIndex] = useState(null)

  const categories = INTERVIEW_CATEGORIES.filter(c => c.id !== 'general')

  // 1. Start Interview Session
  const handleStartInterview = async () => {
    setLoading(true)
    setError(null)
    setSession(null)
    setCurrentAnalysis(null)
    setSummaryReport(null)
    setAnswer('')

    try {
      const response = await fetch(`${backendUrl}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to start interview session.')
      }

      setSession(data)
    } catch (err) {
      console.error('Start interview error:', err)
      setError(err.message || 'Unable to connect to backend server.')
    } finally {
      setLoading(false)
    }
  }

  // 2. Submit Answer for current question
  const handleSubmitAnswer = async () => {
    if (!answer.trim() || answer.trim().length < 10) {
      setError('Please provide an answer with at least 10 characters.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${backendUrl}/api/interview/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          question: session.current_question,
          answer: answer.trim()
        })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to submit answer.')
      }

      setCurrentAnalysis(data.analysis)

      if (data.is_completed) {
        setSummaryReport(data.summary)
        setSession(null)
      } else {
        setNextQuestionText(data.next_question)
        setSession(prev => ({
          ...prev,
          question_number: data.question_number + 1
        }))
      }
    } catch (err) {
      console.error('Submit answer error:', err)
      setError(err.message || 'Failed to analyze answer.')
    } finally {
      setLoading(false)
    }
  }

  // 3. Move to next question after reviewing feedback
  const handleProceedToNextQuestion = () => {
    setSession(prev => ({
      ...prev,
      current_question: nextQuestionText
    }))
    setCurrentAnalysis(null)
    setNextQuestionText('')
    setAnswer('')
    setError(null)
  }

  // 4. Manually finish interview session early
  const handleFinishEarly = async () => {
    if (!session) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${backendUrl}/api/interview/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session.session_id })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to conclude interview session.')
      }

      setSummaryReport(data)
      setSession(null)
      setCurrentAnalysis(null)
    } catch (err) {
      console.error('Finish interview error:', err)
      setError(err.message || 'Failed to finish interview.')
    } finally {
      setLoading(false)
    }
  }

  // 5. Reset to start screen
  const handleReset = () => {
    setSession(null)
    setCurrentAnalysis(null)
    setSummaryReport(null)
    setAnswer('')
    setError(null)
  }

  const toggleAccordion = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx)
  }

  return (
    <div className="interview-mode-container">
      {/* ERROR ALERT */}
      {error && (
        <div className="error-alert">
          <AlertTriangle size={20} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* STATE 1: START INTERVIEW FORM */}
      {!session && !currentAnalysis && !summaryReport && (
        <div className="card interview-start-card">
          <div className="interview-start-header">
            <div className="interview-icon-badge">
              <Play size={24} />
            </div>
            <h2>Interactive Interview Simulation</h2>
            <p>
              Experience a realistic 5-question multi-turn interview. The AI remembers your past answers 
              and asks relevant follow-up questions tailored to your experience.
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">Select Interview Category</label>
            <div className="category-grid">
              {categories.map(cat => (
                <button
                  key={cat.id}
                  type="button"
                  className={`category-card-btn ${category === cat.id ? 'active' : ''}`}
                  onClick={() => setCategory(cat.id)}
                >
                  <div className="category-title">{cat.label}</div>
                  <div className="category-desc">{cat.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <button
            className="btn btn-primary start-interview-btn"
            onClick={handleStartInterview}
            disabled={loading}
          >
            {loading ? (
              <span>Initializing Session...</span>
            ) : (
              <>
                <Play size={18} />
                <span>Start Interview (5 Questions)</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* STATE 2: ACTIVE QUESTION & ANSWERING */}
      {session && !currentAnalysis && (
        <div className="interview-active-container">
          {/* Progress Header */}
          <div className="interview-progress-bar-card">
            <div className="progress-info">
              <span className="question-badge">
                Question {session.question_number} of {session.total_questions}
              </span>
              <span className="category-badge">{session.category.toUpperCase()}</span>
            </div>
            <div className="progress-track">
              <div 
                className="progress-fill"
                style={{ width: `${(session.question_number / session.total_questions) * 100}%` }}
              />
            </div>
          </div>

          {/* Current Question Display */}
          <div className="card question-display-card">
            <div className="question-header">
              <HelpCircle size={20} className="icon-blue" />
              <h3>Current Question</h3>
            </div>
            <p className="question-text">{session.current_question}</p>
          </div>

          {/* Answer Textarea */}
          <div className="card answer-input-card">
            <label className="form-label">Your Answer</label>
            <textarea
              className="form-textarea"
              rows={6}
              placeholder="Type your structured answer here..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={loading}
            />
            <div className="char-count">
              {answer.length} characters (min 10)
            </div>

            <div className="interview-action-buttons">
              <button
                className="btn btn-primary"
                onClick={handleSubmitAnswer}
                disabled={loading || answer.trim().length < 10}
              >
                {loading ? (
                  <span>Evaluating Answer...</span>
                ) : (
                  <>
                    <Send size={18} />
                    <span>Submit Answer</span>
                  </>
                )}
              </button>

              <button
                className="btn btn-secondary"
                onClick={handleFinishEarly}
                disabled={loading}
              >
                <Square size={16} />
                <span>Finish Interview Early</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STATE 3: FEEDBACK & TRANSITION TO NEXT QUESTION */}
      {currentAnalysis && nextQuestionText && (
        <div className="interview-transition-container">
          <div className="next-question-banner card">
            <div className="next-q-header">
              <Sparkles size={20} className="icon-purple" />
              <h3>Answer Submitted! Ready for Question {session.question_number}?</h3>
            </div>
            <p className="next-q-prompt">
              The AI has evaluated your response and generated a follow-up question based on your context.
            </p>
            <button
              className="btn btn-primary proceed-btn"
              onClick={handleProceedToNextQuestion}
            >
              <span>Proceed to Question {session.question_number}</span>
              <ArrowRight size={18} />
            </button>
          </div>

          {/* Answer Feedback Dashboard */}
          <div className="transition-feedback-title">
            <h4>Evaluation Feedback for Last Answer</h4>
          </div>
          <Dashboard 
            result={currentAnalysis} 
            onRetry={() => {}} 
            onAnalyzeAnother={() => {}}
            hideActionButtons={true}
          />
        </div>
      )}

      {/* STATE 4: FINAL INTERVIEW SUMMARY REPORT */}
      {summaryReport && (
        <div className="summary-report-container">
          <div className="card summary-header-card">
            <div className="summary-badge">
              <Award size={24} />
              <span>Session Report</span>
            </div>
            <h2>Interview Performance Summary</h2>
            <p className="summary-meta">
              Completed {summaryReport.total_questions_answered} question(s) in {summaryReport.category.toUpperCase()} interview mode.
            </p>

            <div className="summary-score-dial">
              <div className="score-number-big">{summaryReport.average_score}</div>
              <div className="score-denom">/ 100</div>
              <div className="score-10-badge">{summaryReport.average_score_10} / 10</div>
            </div>
          </div>

          {/* Aggregated Insights Grid */}
          <div className="dashboard-grid grid-2-col">
            <div className="card strengths-card">
              <h3><CheckCircle2 size={18} className="icon-green" /> Key Overall Strengths</h3>
              <ul className="bullet-list">
                {summaryReport.overall_strengths.length > 0 ? (
                  summaryReport.overall_strengths.map((st, i) => (
                    <li key={i}>{st}</li>
                  ))
                ) : (
                  <li>Consistent communication across answers.</li>
                )}
              </ul>
            </div>

            <div className="card improvements-card">
              <h3><AlertTriangle size={18} className="icon-amber" /> Key Areas to Improve</h3>
              <ul className="bullet-list">
                {summaryReport.overall_improvements.length > 0 ? (
                  summaryReport.overall_improvements.map((imp, i) => (
                    <li key={i}>{imp}</li>
                  ))
                ) : (
                  <li>Incorporate more specific quantitative impact metrics.</li>
                )}
              </ul>
            </div>
          </div>

          {/* Q&A Breakdown Accordion */}
          <div className="card qa-breakdown-card">
            <h3><Layers size={20} className="icon-blue" /> Session Question Breakdown</h3>

            <div className="qa-accordion-list">
              {summaryReport.items.map((item, idx) => (
                <div key={idx} className="accordion-item card">
                  <div 
                    className="accordion-header"
                    onClick={() => toggleAccordion(idx)}
                  >
                    <div className="accordion-title-group">
                      <span className="q-number-pill">Q{idx + 1}</span>
                      <span className="q-text-snippet">{item.question}</span>
                    </div>
                    <div className="accordion-right-group">
                      <span className="q-score-badge">{item.calculated_score} / 100</span>
                      {expandedIndex === idx ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </div>

                  {expandedIndex === idx && (
                    <div className="accordion-content">
                      <div className="qa-detail-row">
                        <strong>User Answer:</strong>
                        <p className="user-ans-text">{item.user_answer}</p>
                      </div>

                      <div className="qa-detail-row">
                        <strong>Suggested Improved Wording:</strong>
                        <p className="improved-ans-text">{item.improved_answer}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="summary-actions">
            <button
              className="btn btn-primary"
              onClick={handleReset}
            >
              <RotateCcw size={18} />
              <span>Start New Interview</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
