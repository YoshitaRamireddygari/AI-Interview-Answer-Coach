import React from 'react'
import { Sparkles, BrainCircuit } from 'lucide-react'

export function Header() {
  return (
    <header className="header">
      <div className="header-badge">
        <Sparkles size={16} />
        <span>AI-Powered Interview Coach</span>
      </div>
      <h1>AI Interview Answer Coach</h1>
      <p>
        Elevate your interview performance with grounded, criteria-weighted AI evaluations, 
        STAR framework breakdown, and actionable improvements.
      </p>
    </header>
  )
}
