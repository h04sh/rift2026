import React, { useEffect, useRef, useState } from 'react'
import useAgentStore from '../store/agentStore'
import { fetchTimeline } from '../api/agentApi'

const EVENT_META = {
    clone_started: { icon: '📦', color: 'var(--accent-cyan)', label: 'Clone Started' },
    clone_success: { icon: '✅', color: 'var(--accent-green)', label: 'Clone Successful' },
    clone_failed: { icon: '❌', color: 'var(--accent-red)', label: 'Clone Failed' },
    analysis_started: { icon: '🔍', color: 'var(--accent-primary)', label: 'Analysis Started' },
    analysis_complete: { icon: '📋', color: 'var(--accent-cyan)', label: 'Analysis Complete' },
    analysis_error: { icon: '⚠', color: 'var(--accent-yellow)', label: 'Analysis Error' },
    fix_started: { icon: '🤖', color: 'var(--accent-secondary)', label: 'AI Fix Generation' },
    fix_complete: { icon: '✔', color: 'var(--accent-green)', label: 'Fixes Applied' },
    git_started: { icon: '🌿', color: 'var(--accent-primary)', label: 'Git Branch Created' },
    git_pushed: { icon: '🚀', color: 'var(--accent-green)', label: 'Code Pushed' },
    git_failed: { icon: '❌', color: 'var(--accent-red)', label: 'Git Push Failed' },
    git_nothing_to_commit: { icon: '📭', color: 'var(--text-muted)', label: 'Nothing to Commit' },
    cicd_polling_started: { icon: '🔄', color: 'var(--accent-cyan)', label: 'CI/CD Polling' },
    cicd_queued: { icon: '⏳', color: 'var(--accent-yellow)', label: 'Workflow Queued' },
    cicd_in_progress: { icon: '⚙', color: 'var(--accent-cyan)', label: 'Workflow Running' },
    cicd_completed: { icon: '🏁', color: 'var(--accent-green)', label: 'Workflow Completed' },
    cicd_simulated: { icon: '🧪', color: 'var(--text-secondary)', label: 'CI Simulated' },
    cicd_skipped: { icon: '⏭', color: 'var(--text-muted)', label: 'CI Skipped' },
    cicd_no_workflow: { icon: '📭', color: 'var(--text-muted)', label: 'No Workflow Found' },
    cicd_error: { icon: '❌', color: 'var(--accent-red)', label: 'CI/CD Error' },
    cicd_timeout: { icon: '⏱', color: 'var(--accent-red)', label: 'CI Timed Out' },
    score_calculated: { icon: '🏆', color: 'var(--accent-secondary)', label: 'Score Calculated' },
}

function getEventMeta(key) {
    return EVENT_META[key] || { icon: '●', color: 'var(--text-secondary)', label: key }
}

function formatTime(iso) {
    if (!iso) return ''
    try {
        return new Date(iso).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch { return iso }
}

export default function CICDTimeline() {
    const { status, results } = useAgentStore()
    const [liveEvents, setLiveEvents] = useState([])
    const bottomRef = useRef(null)

    const isRunning = status === 'running' || status === 'queued'

    // Use live polling while running, results when done
    const timeline =
        results?.cicd_timeline?.length > 0
            ? results.cicd_timeline
            : liveEvents

    useEffect(() => {
        if (!isRunning) return
        const id = setInterval(async () => {
            try {
                const data = await fetchTimeline()
                setLiveEvents(data.timeline || [])
            } catch { /* silently ignore */ }
        }, 2000)
        return () => clearInterval(id)
    }, [isRunning])

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [timeline.length])

    return (
        <div className="glass-card animate-fade-up" style={{ padding: '28px', animationDelay: '0.2s' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div className="section-header" style={{ marginBottom: 0 }}>
                    <div className="section-icon" style={{ background: 'rgba(245,158,11,0.15)' }}>📡</div>
                    <h2>CI/CD Timeline</h2>
                </div>
                {isRunning && (
                    <span className="badge badge-running">
                        <span className="animate-blink">●</span>
                        Live
                    </span>
                )}
            </div>

            {timeline.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>📡</div>
                    <p>{isRunning ? 'Waiting for pipeline events…' : 'No pipeline events yet. Run the agent to see the timeline.'}</p>
                    {isRunning && <div className="animate-spin" style={{ display: 'inline-block', marginTop: 16, fontSize: '1.5rem' }}>⚙</div>}
                </div>
            ) : (
                <div style={{
                    maxHeight: 520,
                    overflowY: 'auto',
                    paddingRight: 4,
                    position: 'relative',
                }}>
                    {/* Vertical line */}
                    <div style={{
                        position: 'absolute',
                        left: 23,
                        top: 8,
                        bottom: 8,
                        width: 2,
                        background: 'linear-gradient(180deg, var(--accent-primary), rgba(99,102,241,0.1))',
                        borderRadius: 1,
                    }} />

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                        {timeline.map((event, i) => {
                            const meta = getEventMeta(event.event)
                            const isLast = i === timeline.length - 1

                            return (
                                <div
                                    key={i}
                                    style={{
                                        display: 'flex',
                                        gap: 16,
                                        paddingBottom: isLast ? 0 : 18,
                                        animation: `fadeSlideUp 0.3s ease ${i * 0.04}s both`,
                                    }}
                                >
                                    {/* Dot */}
                                    <div style={{
                                        flexShrink: 0,
                                        width: 46,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: 4,
                                    }}>
                                        <div style={{
                                            width: 36,
                                            height: 36,
                                            borderRadius: '50%',
                                            background: `${meta.color}20`,
                                            border: `2px solid ${meta.color}60`,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '1rem',
                                            boxShadow: isLast && isRunning ? `0 0 12px ${meta.color}60` : 'none',
                                            zIndex: 1,
                                            position: 'relative',
                                            flexShrink: 0,
                                        }}>
                                            {meta.icon}
                                        </div>
                                    </div>

                                    {/* Content */}
                                    <div style={{
                                        flex: 1,
                                        background: 'rgba(255,255,255,0.02)',
                                        border: `1px solid ${event.status === 'failure' ? 'rgba(239,68,68,0.2)' : 'var(--border)'}`,
                                        borderRadius: 'var(--radius-md)',
                                        padding: '10px 14px',
                                        marginTop: 4,
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, gap: 10 }}>
                                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: meta.color }}>
                                                {meta.label}
                                            </span>
                                            <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', flexShrink: 0 }}>
                                                {formatTime(event.timestamp)}
                                            </span>
                                        </div>
                                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                            {event.detail}
                                        </p>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    <div ref={bottomRef} />
                </div>
            )}
        </div>
    )
}
