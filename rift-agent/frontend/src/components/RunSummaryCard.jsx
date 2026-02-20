import React from 'react'
import useAgentStore from '../store/agentStore'

const STAT_CARDS = [
    { key: 'status', label: 'Pipeline Status', icon: '⚡', color: 'var(--accent-primary)' },
    { key: 'branch_name', label: 'Branch', icon: '🌿', color: 'var(--accent-cyan)' },
    { key: 'fixes_count', label: 'Fixes Applied', icon: '🔧', color: 'var(--accent-green)' },
    { key: 'retry_count', label: 'Retries Used', icon: '🔄', color: 'var(--accent-yellow)' },
    { key: 'duration', label: 'Duration', icon: '⏱', color: 'var(--accent-orange)' },
    { key: 'score', label: 'Total Score', icon: '🏆', color: 'var(--accent-secondary)' },
]

function StatusPill({ status }) {
    const map = {
        idle: { label: 'Idle', cls: 'badge-idle' },
        queued: { label: 'Queued', cls: 'badge-pending' },
        running: { label: 'Running', cls: 'badge-running' },
        success: { label: 'Success', cls: 'badge-success' },
        failed: { label: 'Failed', cls: 'badge-failure' },
        partial: { label: 'Partial', cls: 'badge-partial' },
    }
    const { label, cls } = map[status] || { label: status, cls: 'badge-idle' }
    return (
        <span className={`badge ${cls}`}>
            {status === 'running' && <span className="animate-blink">●</span>}
            {label}
        </span>
    )
}

export default function RunSummaryCard() {
    const { status, results } = useAgentStore()
    const r = results

    const getValue = (key) => {
        if (!r) {
            if (key === 'status') return <StatusPill status={status} />
            return <span style={{ color: 'var(--text-muted)' }}>—</span>
        }
        switch (key) {
            case 'status':
                return <StatusPill status={r.status || status} />
            case 'branch_name':
                return (
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', wordBreak: 'break-all' }}>
                        {r.branch_name || '—'}
                    </span>
                )
            case 'fixes_count':
                return (
                    <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-green)' }}>
                        {r.fixes?.filter(f => f.status === 'applied').length ?? 0}
                    </span>
                )
            case 'retry_count':
                return (
                    <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-yellow)' }}>
                        {r.retry_count ?? 0} / {r.retry_limit ?? 5}
                    </span>
                )
            case 'duration':
                return (
                    <span style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-orange)' }}>
                        {r.duration_seconds ? `${r.duration_seconds}s` : '—'}
                    </span>
                )
            case 'score':
                return (
                    <span style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--accent-secondary)' }}>
                        {r.score?.total_score ?? 0}
                        <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>/100</span>
                    </span>
                )
            default:
                return '—'
        }
    }

    return (
        <div className="glass-card animate-fade-up" style={{ padding: '28px', animationDelay: '0.05s' }}>
            <div className="section-header">
                <div className="section-icon" style={{ background: 'rgba(16,185,129,0.15)' }}>📊</div>
                <div>
                    <h2>Run Summary</h2>
                    {r?.run_id && (
                        <p className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
                            {r.run_id.slice(0, 18)}…
                        </p>
                    )}
                </div>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                gap: 14,
            }}>
                {STAT_CARDS.map(({ key, label, icon, color }) => (
                    <div
                        key={key}
                        style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)',
                            padding: '16px',
                            transition: 'border-color var(--transition)',
                        }}
                        onMouseEnter={e => e.currentTarget.style.borderColor = color}
                        onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                    >
                        <div style={{ fontSize: '1.4rem', marginBottom: 8 }}>{icon}</div>
                        <div style={{ minHeight: 36, display: 'flex', alignItems: 'center' }}>
                            {getValue(key)}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                            {label}
                        </div>
                    </div>
                ))}
            </div>

            {/* Commit SHA */}
            {r?.commit_sha && (
                <div style={{
                    marginTop: 18,
                    padding: '10px 14px',
                    background: 'rgba(99,102,241,0.08)',
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    gap: 10,
                    alignItems: 'center',
                }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Commit SHA:</span>
                    <code className="mono" style={{ color: '#818cf8', fontSize: '0.8rem' }}>
                        {r.commit_sha.slice(0, 12)}
                    </code>
                    {r.pr_url && (
                        <a href={r.pr_url} target="_blank" rel="noreferrer"
                            style={{ marginLeft: 'auto', color: 'var(--accent-cyan)', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>
                            View PR ↗
                        </a>
                    )}
                </div>
            )}

            {/* Test summary bar */}
            {r?.test_summary && r.test_summary.total_tests > 0 && (() => {
                const { total_tests, tests_passed, tests_failed } = r.test_summary
                const pct = Math.round((tests_passed / total_tests) * 100)
                return (
                    <div style={{ marginTop: 18 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.8rem' }}>
                            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Test Results</span>
                            <span style={{ color: pct === 100 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 700 }}>
                                {tests_passed}/{total_tests} passed ({pct}%)
                            </span>
                        </div>
                        <div style={{ height: 8, borderRadius: 4, background: 'rgba(239,68,68,0.2)', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%',
                                width: `${pct}%`,
                                borderRadius: 4,
                                background: pct === 100
                                    ? 'linear-gradient(90deg, var(--accent-green), #34d399)'
                                    : 'linear-gradient(90deg, var(--accent-primary), var(--accent-cyan))',
                                transition: 'width 0.8s ease',
                            }} />
                        </div>
                    </div>
                )
            })()}
        </div>
    )
}
