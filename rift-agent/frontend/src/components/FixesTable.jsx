import React, { useState, useMemo } from 'react'
import useAgentStore from '../store/agentStore'

const BUG_COLORS = {
    LINTING: { bg: 'rgba(99,102,241,0.12)', color: '#818cf8' },
    SYNTAX: { bg: 'rgba(239,68,68,0.12)', color: '#f87171' },
    LOGIC: { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24' },
    TYPE_ERROR: { bg: 'rgba(139,92,246,0.12)', color: '#a78bfa' },
    IMPORT: { bg: 'rgba(6,182,212,0.12)', color: '#22d3ee' },
    INDENTATION: { bg: 'rgba(16,185,129,0.12)', color: '#34d399' },
}

function BugPill({ type }) {
    const { bg, color } = BUG_COLORS[type] || { bg: 'rgba(255,255,255,0.08)', color: '#94a3b8' }
    return (
        <span style={{
            background: bg, color, padding: '3px 10px',
            borderRadius: 99, fontSize: '0.7rem', fontWeight: 700,
            letterSpacing: '0.05em',
        }}>
            {type}
        </span>
    )
}

function StatusDot({ status }) {
    if (status === 'applied') return <span style={{ color: 'var(--accent-green)', fontSize: '0.8rem' }}>✔ Applied</span>
    return <span style={{ color: 'var(--accent-red)', fontSize: '0.8rem' }}>✖ Failed</span>
}

export default function FixesTable() {
    const { results } = useAgentStore()
    const fixes = results?.fixes ?? []
    const formatted = results?.fixes_formatted_output ?? []

    const [sortKey, setSortKey] = useState('line')
    const [sortDir, setSortDir] = useState('asc')
    const [filter, setFilter] = useState('ALL')

    const BUG_TYPES = ['ALL', 'LINTING', 'SYNTAX', 'LOGIC', 'TYPE_ERROR', 'IMPORT', 'INDENTATION']

    const sorted = useMemo(() => {
        const filtered = filter === 'ALL' ? fixes : fixes.filter(f => f.bug_type === filter)
        return [...filtered].sort((a, b) => {
            let av = a[sortKey], bv = b[sortKey]
            if (typeof av === 'string') av = av.toLowerCase()
            if (typeof bv === 'string') bv = bv.toLowerCase()
            if (av < bv) return sortDir === 'asc' ? -1 : 1
            if (av > bv) return sortDir === 'asc' ? 1 : -1
            return 0
        })
    }, [fixes, sortKey, sortDir, filter])

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortKey(key); setSortDir('asc') }
    }

    const sortIcon = (key) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''

    return (
        <div className="glass-card animate-fade-up" style={{ padding: '28px', animationDelay: '0.15s' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                <div className="section-header" style={{ marginBottom: 0 }}>
                    <div className="section-icon" style={{ background: 'rgba(6,182,212,0.15)' }}>🔧</div>
                    <h2>Fixes Applied <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.9rem' }}>({fixes.length})</span></h2>
                </div>

                {/* Bug type filter */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {BUG_TYPES.map(t => (
                        <button
                            key={t}
                            onClick={() => setFilter(t)}
                            style={{
                                padding: '4px 12px',
                                borderRadius: 99,
                                border: filter === t ? `1px solid ${BUG_COLORS[t]?.color || 'var(--accent-primary)'}` : '1px solid var(--border)',
                                background: filter === t ? (BUG_COLORS[t]?.bg || 'rgba(99,102,241,0.12)') : 'transparent',
                                color: filter === t ? (BUG_COLORS[t]?.color || 'var(--accent-primary)') : 'var(--text-muted)',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                                fontFamily: 'var(--font-sans)',
                                transition: 'all 0.2s',
                            }}
                        >{t}</button>
                    ))}
                </div>
            </div>

            {fixes.length === 0 ? (
                <div style={{
                    textAlign: 'center', padding: '48px 24px',
                    color: 'var(--text-muted)',
                }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🔍</div>
                    <p>No fixes yet. Run the agent to see results here.</p>
                </div>
            ) : (
                <>
                    <div style={{ overflowX: 'auto' }}>
                        <table className="rift-table">
                            <thead>
                                <tr>
                                    <th onClick={() => handleSort('bug_type')}>Bug Type{sortIcon('bug_type')}</th>
                                    <th onClick={() => handleSort('file')}>File{sortIcon('file')}</th>
                                    <th onClick={() => handleSort('line')}>Line{sortIcon('line')}</th>
                                    <th>Fix Description</th>
                                    <th onClick={() => handleSort('status')}>Status{sortIcon('status')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sorted.map((fix, i) => (
                                    <tr key={i}>
                                        <td><BugPill type={fix.bug_type} /></td>
                                        <td>
                                            <code className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                                {fix.file}
                                            </code>
                                        </td>
                                        <td>
                                            <code className="mono" style={{ fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>
                                                :{fix.line}
                                            </code>
                                        </td>
                                        <td style={{ maxWidth: 320, fontSize: '0.82rem' }}>
                                            {fix.fix_description}
                                        </td>
                                        <td><StatusDot status={fix.status} /></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Formatted output (exact required format) */}
                    {formatted.length > 0 && (
                        <div style={{ marginTop: 24 }}>
                            <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
                                📋 Exact Output Format
                            </p>
                            <div style={{
                                background: 'rgba(0,0,0,0.3)',
                                border: '1px solid var(--border)',
                                borderRadius: 'var(--radius-md)',
                                padding: '14px 18px',
                                overflowX: 'auto',
                            }}>
                                {formatted.map((line, i) => (
                                    <div key={i} className="mono" style={{ fontSize: '0.78rem', color: '#94a3b8', padding: '3px 0', lineHeight: 1.7 }}>
                                        <span style={{ color: 'var(--accent-primary)', userSelect: 'none' }}>{String(i + 1).padStart(2, '0')} │ </span>
                                        {line}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
