import React, { useState } from 'react'
import InputSection from './components/InputSection'
import RunSummaryCard from './components/RunSummaryCard'
import ScoreBreakdown from './components/ScoreBreakdown'
import FixesTable from './components/FixesTable'
import CICDTimeline from './components/CICDTimeline'
import useAgentStore from './store/agentStore'

export default function App() {
    const [activeTab, setActiveTab] = useState('dashboard')
    const { status, results } = useAgentStore()

    const isDone = ['success', 'failed', 'partial'].includes(status)

    return (
        <div className="app-wrapper">
            {/* ===== Header ===== */}
            <header className="app-header">
                <div className="logo">
                    <div className="logo-icon">🤖</div>
                    <div>
                        <div className="logo-text">RIFT 2026</div>
                        <span className="logo-sub">Autonomous CI/CD Healing Agent</span>
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    {/* Live status indicator */}
                    {(status === 'running' || status === 'queued') && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>
                            <span className="animate-blink" style={{ fontSize: '1.2rem' }}>●</span>
                            Agent Running…
                        </div>
                    )}

                    {/* Track badge */}
                    <div style={{
                        padding: '6px 14px',
                        borderRadius: 99,
                        background: 'rgba(99,102,241,0.12)',
                        border: '1px solid rgba(99,102,241,0.25)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: '#818cf8',
                        letterSpacing: '0.04em',
                    }}>
                        AI/ML • DevOps • Agentic Systems
                    </div>
                </div>
            </header>

            {/* ===== Content ===== */}
            <main className="app-content">
                {/* Tabs */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                    <div className="tabs-bar">
                        <button
                            id="tab-dashboard"
                            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
                            onClick={() => setActiveTab('dashboard')}
                        >
                            📊 Dashboard
                        </button>
                        <button
                            id="tab-results"
                            className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
                            onClick={() => setActiveTab('results')}
                        >
                            📄 Raw Results
                        </button>
                    </div>

                    {isDone && results?.score?.total_score !== undefined && (
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: 10,
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)',
                            padding: '8px 18px',
                        }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Final Score</span>
                            <span style={{
                                fontSize: '1.4rem', fontWeight: 900,
                                color: results.score.total_score >= 80 ? 'var(--accent-green)'
                                    : results.score.total_score >= 50 ? 'var(--accent-yellow)'
                                        : 'var(--accent-red)',
                            }}>
                                {results.score.total_score.toFixed(1)}
                            </span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>/110</span>
                        </div>
                    )}
                </div>

                {/* ===== Dashboard Tab ===== */}
                {activeTab === 'dashboard' && (
                    <div className="dashboard-grid">
                        {/* Left column */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                            <InputSection />
                            <RunSummaryCard />
                        </div>

                        {/* Right column */}
                        <div className="dashboard-right">
                            <ScoreBreakdown />
                            <CICDTimeline />
                            <FixesTable />
                        </div>
                    </div>
                )}

                {/* ===== Raw Results Tab ===== */}
                {activeTab === 'results' && (
                    <div className="glass-card animate-fade-up" style={{ padding: '28px' }}>
                        <div className="section-header">
                            <div className="section-icon" style={{ background: 'rgba(245,158,11,0.15)' }}>📄</div>
                            <h2>results.json</h2>
                        </div>
                        {results ? (
                            <div style={{
                                background: 'rgba(0,0,0,0.3)',
                                border: '1px solid var(--border)',
                                borderRadius: 'var(--radius-md)',
                                overflowX: 'auto',
                                overflowY: 'auto',
                                maxHeight: 620,
                            }}>
                                <pre className="mono" style={{
                                    padding: '20px',
                                    fontSize: '0.78rem',
                                    lineHeight: 1.7,
                                    color: '#94a3b8',
                                    margin: 0,
                                }}>
                                    {JSON.stringify(results, null, 2)}
                                </pre>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
                                <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>📭</div>
                                <p>No results yet. Run the agent from the Dashboard tab.</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Footer */}
                <footer style={{
                    textAlign: 'center',
                    padding: '24px 0',
                    color: 'var(--text-muted)',
                    fontSize: '0.78rem',
                    borderTop: '1px solid var(--border)',
                    marginTop: 8,
                }}>
                    <span>RIFT 2026 Hackathon — AI/ML • DevOps Automation • Agentic Systems Track &nbsp;|&nbsp;</span>
                    <span>
                        Built with{' '}
                        <span style={{ color: 'var(--accent-primary)' }}>FastAPI</span>,{' '}
                        <span style={{ color: 'var(--accent-secondary)' }}>LangGraph</span>,{' '}
                        <span style={{ color: 'var(--accent-cyan)' }}>React</span>
                    </span>
                </footer>
            </main>
        </div>
    )
}
