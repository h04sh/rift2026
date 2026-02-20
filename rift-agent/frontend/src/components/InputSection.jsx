import React, { useState } from 'react'
import useAgentStore from '../store/agentStore'

export default function InputSection() {
    const { form, setForm, status, startAgent, reset, error } = useAgentStore()
    const [showToken, setShowToken] = useState(false)
    const isRunning = status === 'running' || status === 'queued'

    const handleSubmit = (e) => {
        e.preventDefault()
        startAgent()
    }

    return (
        <div className="glass-card animate-fade-up" style={{ padding: '28px' }}>
            {/* Header */}
            <div className="section-header">
                <div className="section-icon" style={{ background: 'rgba(99,102,241,0.15)' }}>🚀</div>
                <div>
                    <h2 style={{ marginBottom: 2 }}>Run Agent</h2>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Point the AI agent at any GitHub repo
                    </p>
                </div>
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                {/* Repo URL */}
                <div>
                    <label className="field-label" htmlFor="repo-url">Repository URL *</label>
                    <input
                        id="repo-url"
                        type="url"
                        className="input-field mono"
                        placeholder="https://github.com/owner/repo"
                        value={form.repoUrl}
                        onChange={(e) => setForm('repoUrl', e.target.value)}
                        required
                        disabled={isRunning}
                    />
                </div>

                {/* Team & Leader row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div>
                        <label className="field-label" htmlFor="team-name">Team Name</label>
                        <input
                            id="team-name"
                            type="text"
                            className="input-field"
                            placeholder="RIFT_ORGANISERS"
                            value={form.teamName}
                            onChange={(e) => setForm('teamName', e.target.value)}
                            disabled={isRunning}
                        />
                    </div>
                    <div>
                        <label className="field-label" htmlFor="leader-name">Leader Name</label>
                        <input
                            id="leader-name"
                            type="text"
                            className="input-field"
                            placeholder="SAIYAM_KUMAR"
                            value={form.leaderName}
                            onChange={(e) => setForm('leaderName', e.target.value)}
                            disabled={isRunning}
                        />
                    </div>
                </div>

                {/* Branch preview */}
                {(form.teamName || form.leaderName) && (
                    <div style={{
                        background: 'rgba(99,102,241,0.08)',
                        border: '1px solid rgba(99,102,241,0.2)',
                        borderRadius: 'var(--radius-md)',
                        padding: '10px 14px',
                    }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>
                            Branch Preview
                        </span>
                        <div className="mono" style={{ marginTop: 4, color: '#818cf8', fontSize: '0.82rem', wordBreak: 'break-all' }}>
                            {`${(form.teamName || 'TEAM').toUpperCase().replace(/\s+/g, '_')}_${(form.leaderName || 'LEADER').toUpperCase().replace(/\s+/g, '_')}_AI_Fix`}
                        </div>
                    </div>
                )}

                {/* OpenAI Key */}
                <div>
                    <label className="field-label" htmlFor="openai-key">OpenAI API Key</label>
                    <input
                        id="openai-key"
                        type={showToken ? 'text' : 'password'}
                        className="input-field mono"
                        placeholder="sk-..."
                        value={form.openaiKey}
                        onChange={(e) => setForm('openaiKey', e.target.value)}
                        disabled={isRunning}
                    />
                    <span
                        onClick={() => setShowToken(!showToken)}
                        style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', cursor: 'pointer', marginTop: 4, display: 'block' }}
                    >
                        {showToken ? '🙈 Hide' : '👁 Show'}
                    </span>
                </div>

                {/* GitHub Token */}
                <div>
                    <label className="field-label" htmlFor="github-token">GitHub Token (for private repos & push)</label>
                    <input
                        id="github-token"
                        type="password"
                        className="input-field mono"
                        placeholder="ghp_..."
                        value={form.githubToken}
                        onChange={(e) => setForm('githubToken', e.target.value)}
                        disabled={isRunning}
                    />
                </div>

                {/* Retry limit */}
                <div>
                    <label className="field-label" htmlFor="retry-limit">
                        Retry Limit — <span style={{ color: 'var(--accent-primary)' }}>{form.retryLimit}</span>
                    </label>
                    <input
                        id="retry-limit"
                        type="range"
                        min="1"
                        max="10"
                        value={form.retryLimit}
                        onChange={(e) => setForm('retryLimit', e.target.value)}
                        disabled={isRunning}
                        style={{ width: '100%', accentColor: 'var(--accent-primary)' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
                        <span>1</span><span>5 (default)</span><span>10</span>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div style={{
                        background: 'rgba(239,68,68,0.1)',
                        border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 'var(--radius-md)',
                        padding: '12px 16px',
                        color: '#fca5a5',
                        fontSize: '0.85rem',
                    }}>
                        ⚠ {error}
                    </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: 10 }}>
                    <button
                        id="run-agent-btn"
                        type="submit"
                        className="btn btn-primary"
                        disabled={isRunning}
                        style={{ flex: 1 }}
                    >
                        {isRunning ? (
                            <>
                                <span className="animate-spin" style={{ display: 'inline-block', fontSize: '1rem' }}>⚙</span>
                                {status === 'queued' ? 'Starting…' : 'Running…'}
                            </>
                        ) : '🤖 Run AI Agent'}
                    </button>

                    {status !== 'idle' && (
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={reset}
                            disabled={isRunning}
                        >
                            ↺ Reset
                        </button>
                    )}
                </div>
            </form>
        </div>
    )
}
