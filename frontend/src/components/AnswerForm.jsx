import { 
  Send, 
  HelpCircle, 
  MessageSquare, 
  Tag
} from 'lucide-react'
import { INTERVIEW_CATEGORIES } from '../constants/categories'

export function AnswerForm({
  question,
  setQuestion,
  answer,
  setAnswer,
  category,
  setCategory,
  onAnalyze,
  loading
}) {
  const charCount = answer.length
  const maxChars = 5000
  const minAnswerLength = 10
  const minQuestionLength = 5

  const isValid = question.trim().length >= minQuestionLength && answer.trim().length >= minAnswerLength

  const handleSubmit = (e) => {
    e.preventDefault()
    if (isValid && !loading) {
      onAnalyze()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card form-card" aria-label="Interview Answer Analysis Form">
      {/* Category Selector */}
      <div className="form-group">
        <label htmlFor="category-select" className="form-label">
          <Tag size={18} className="icon-accent" />
          <span>Interview Category</span>
        </label>
        <div className="category-grid" role="radiogroup" aria-label="Select Interview Category">
          {INTERVIEW_CATEGORIES.map((cat) => {
            const Icon = cat.icon
            const isSelected = category === cat.id
            return (
              <button
                type="button"
                key={cat.id}
                role="radio"
                aria-checked={isSelected}
                className={`category-chip ${isSelected ? 'selected' : ''}`}
                onClick={() => setCategory(cat.id)}
              >
                <Icon size={16} />
                <span className="chip-label">{cat.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Question Input */}
      <div className="form-group">
        <label htmlFor="question-input" className="form-label">
          <HelpCircle size={18} className="icon-accent" />
          <span>Interview Question</span>
          <span className="required-asterisk" aria-hidden="true">*</span>
        </label>
        <input
          id="question-input"
          type="text"
          className="form-input"
          placeholder="e.g. Tell me about a time you handled a tight project deadline."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          required
          minLength={minQuestionLength}
          maxLength={1000}
          aria-describedby="question-help"
        />
        <div id="question-help" className="field-hint">
          {question.length > 0 && question.trim().length < minQuestionLength && (
            <span className="hint-warning">Question must be at least {minQuestionLength} characters.</span>
          )}
        </div>
      </div>

      {/* Answer Textarea */}
      <div className="form-group">
        <div className="label-row">
          <label htmlFor="answer-input" className="form-label">
            <MessageSquare size={18} className="icon-accent" />
            <span>Your Response</span>
            <span className="required-asterisk" aria-hidden="true">*</span>
          </label>
          <span className={`char-counter ${charCount > maxChars ? 'char-over' : ''}`}>
            {charCount} / {maxChars} characters
          </span>
        </div>
        <textarea
          id="answer-input"
          className="form-textarea"
          rows={7}
          placeholder="Describe your situation, task, specific action steps you took, and measurable results achieved..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          required
          minLength={minAnswerLength}
          maxLength={maxChars}
          aria-describedby="answer-help"
        />
        <div id="answer-help" className="field-hint">
          {answer.length > 0 && answer.trim().length < minAnswerLength && (
            <span className="hint-warning">Answer must be at least {minAnswerLength} characters long.</span>
          )}
        </div>
      </div>

      {/* Action Button */}
      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary btn-large"
          disabled={!isValid || loading}
          aria-busy={loading}
        >
          <Send size={18} />
          <span>{loading ? 'Analyzing Answer...' : 'Analyze Answer'}</span>
        </button>
      </div>
    </form>
  )
}
