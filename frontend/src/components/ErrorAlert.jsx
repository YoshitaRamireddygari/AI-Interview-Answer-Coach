import React from 'react'
import { AlertCircle, RefreshCw, X } from 'lucide-react'

export function ErrorAlert({ error, onRetry, onDismiss }) {
  if (!error) return null

  return (
    <div className="error-alert" role="alert">
      <div className="error-icon">
        <AlertCircle size={24} />
      </div>
      <div className="error-content">
        <h3 className="error-title">Analysis Request Failed</h3>
        <p className="error-message">{error}</p>
      </div>
      <div className="error-actions">
        {onRetry && (
          <button type="button" onClick={onRetry} className="btn-retry">
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        )}
        {onDismiss && (
          <button type="button" onClick={onDismiss} className="btn-dismiss" aria-label="Dismiss error">
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  )
}
