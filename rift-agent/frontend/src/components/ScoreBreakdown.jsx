import React, { useEffect, useRef } from 'react'
import useAgentStore from '../store/agentStore'

/* ---- Animated radial ring (SVG) ---- */
function RadialRing({ value, max = 100, size = 140, color, label, sub }) {
    const r = 56
    const circ = 2 * Math.PI * r
    const pct = Math.min(1, value / max)
    const offset = circ * (1 - pct)

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <div style={{ position: 'relative', width: size, height: size }}>
                <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx={size / 2} cy={size / 2} r={r} fill="none"
                        stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                    <circle cx={size / 2} cy={size / 2} r={r} fill="none"
                        stroke={color} strokeWidth="10"
                        strokeDasharray={circ} strokeDashoffset={offset}
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)' }}
                    />
                </svg>
                <div style={{
                    position: 'absolute', inset: 0,
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: 900, color }}>{value}</span>
                    {sub && <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 1 }}>{sub}</span>}
                </div>
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'center' }}>
                {label}
            </span>
        </div>
    )
}

/* ---- Score row in breakdown table ---- */
function ScoreRow({ label, icon, value, max, color, description }) {
    const pct = Math.min(100, (value / max) * 100)
    return (
        <div style={{ padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {icon} {label}
                </span>
                <span style={{ fontWeight: 800, fontSize: '1rem', color }}>
                    {value.toFixed(1)}<span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.8rem' }}>/{max}</span>
                </span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{
                    height: '100%',
                    width: `${pct}%`,
                    borderRadius: 3,
                    background: `linear-gradient(90deg, ${color}aa, ${color})`,
                    transition: 'width 1s ease',
                }} />
            </div>
            {description && (
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{description}</p>
            )}
        </div>
    )
}

export default function ScoreBreakdown() {
    const { results } = useAgentStore()
    const score = results?.score

    const empty = {
        tests_passed_pct: 0,
        fixes_applied: 0,
        fix_quality_score: 0,
        ci_success_bonus: 0,
        base_score: 0,
        speed_bonus: 0,
        efficiency_penalty: 0,
        total_score: 0,
    }
    const s = score ?? empty

    const totalColor = s.total_score >= 80
        ? 'var(--accent-green)'
        : s.total_score >= 50
            ? 'var(--accent-yellow)'
            : 'var(--accent-red)'

    return (
        <div className="glass-card animate-fade-up" style={{ padding: '28px', animationDelay: '0.1s' }}>
            <div className="section-header">
                <div className="section-icon" style={{ background: 'rgba(139,92,246,0.15)' }}>🏆</div>
                <h2>Score Breakdown</h2>
            </div>

            {/* Radial rings row */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-around',
                flexWrap: 'wrap',
                gap: 24,
                marginBottom: 28,
                padding: '16px 0',
                borderBottom: '1px solid var(--border)',
            }}>
                <RadialRing
                    value={Math.round(s.total_score)}
                    max={110}
                    size={148}
                    color={totalColor}
                    label="Total Score"
                    sub="out of 110"
                />
                <RadialRing
                    value={Math.round(s.tests_passed_pct)}
                    max={100}
                    size={120}
                    color="var(--accent-cyan)"
                    label="Tests Passed"
                    sub="%"
                />
                <RadialRing
                    value={s.fixes_applied}
                    max={Math.max(s.fixes_applied, 10)}
                    size={120}
                    color="var(--accent-primary)"
                    label="Fixes Applied"
                    sub="files"
                />
            </div>

            {/* Breakdown rows */}
            <div>
                <ScoreRow
                    label="Tests Passed"
                    icon="🧪"
                    value={parseFloat(((s.tests_passed_pct / 100) * 40).toFixed(2))}
                    max={40}
                    color="var(--accent-cyan)"
                    description={`${s.tests_passed_pct.toFixed(1)}% of test suite passing`}
                />
                <ScoreRow
                    label="Fix Quality"
                    icon="🔧"
                    value={parseFloat(s.fix_quality_score.toFixed(2))}
                    max={40}
                    color="var(--accent-primary)"
                    description={`${s.fixes_applied} fix(es) successfully applied`}
                />
                <ScoreRow
                    label="CI/CD Success"
                    icon="✅"
                    value={s.ci_success_bonus}
                    max={20}
                    color="var(--accent-green)"
                    description={s.ci_success_bonus === 20 ? 'CI pipeline passed ✓' : 'CI pipeline not yet passing'}
                />
                
                {/* Base Score Summary */}
                <div style={{ 
                    padding: '12px 0', 
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                    marginTop: 8,
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            📊 Base Score
                        </span>
                        <span style={{ fontWeight: 900, fontSize: '1.1rem', color: 'var(--accent-secondary)' }}>
                            {s.base_score?.toFixed(1) || '0.0'}<span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.8rem' }}>/100</span>
                        </span>
                    </div>
                </div>

                {/* Speed Bonus */}
                {s.speed_bonus > 0 && (
                    <div style={{ 
                        padding: '10px 14px', 
                        marginTop: 12,
                        background: 'rgba(34,197,94,0.1)',
                        border: '1px solid rgba(34,197,94,0.3)',
                        borderRadius: 'var(--radius-md)',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#4ade80' }}>
                                ⚡ Speed Bonus (&lt; 5 minutes)
                            </span>
                            <span style={{ fontWeight: 800, fontSize: '1rem', color: '#4ade80' }}>
                                +{s.speed_bonus}
                            </span>
                        </div>
                    </div>
                )}

                {/* Efficiency Penalty */}
                {s.efficiency_penalty > 0 && (
                    <div style={{ 
                        padding: '10px 14px', 
                        marginTop: 12,
                        background: 'rgba(239,68,68,0.1)',
                        border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 'var(--radius-md)',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f87171' }}>
                                ⚠️ Efficiency Penalty (&gt; 20 commits)
                            </span>
                            <span style={{ fontWeight: 800, fontSize: '1rem', color: '#f87171' }}>
                                -{s.efficiency_penalty}
                            </span>
                        </div>
                    </div>
                )}

                {/* Final Score */}
                <div style={{ 
                    padding: '16px 0', 
                    marginTop: 16,
                    borderTop: '2px solid rgba(139,92,246,0.3)',
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                            🎯 Final Total Score
                        </span>
                        <span style={{ fontWeight: 900, fontSize: '1.6rem', color: totalColor }}>
                            {s.total_score.toFixed(1)}<span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.9rem' }}>/110</span>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}
