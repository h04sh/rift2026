/**
 * Zustand store – Global state management for the RIFT Agent Dashboard
 */

import { create } from 'zustand'
import { runAgent, pollStatus, fetchResults, resetPipeline } from '../api/agentApi'

const useAgentStore = create((set, get) => ({
    // --- Form inputs ---
    form: {
        repoUrl: '',
        teamName: '',
        leaderName: '',
        openaiKey: '',
        githubToken: '',
        retryLimit: 5,
    },

    // --- Pipeline state ---
    status: 'idle',   // idle | queued | running | success | failed | partial
    results: null,
    error: null,
    pollingTimer: null,

    // --- Form updater ---
    setForm: (field, value) =>
        set((state) => ({ form: { ...state.form, [field]: value } })),

    // --- Start pipeline ---
    startAgent: async () => {
        const { form } = get()

        if (!form.repoUrl.trim()) {
            set({ error: 'Repository URL is required.' })
            return
        }

        set({ status: 'queued', results: null, error: null })

        try {
            await runAgent({
                repo_url: form.repoUrl.trim(),
                team_name: form.teamName.trim() || 'RIFT_TEAM',
                leader_name: form.leaderName.trim() || 'LEADER',
                openai_key: form.openaiKey.trim(),
                github_token: form.githubToken.trim(),
                retry_limit: Number(form.retryLimit) || 5,
            })

            // Start polling
            set({ status: 'running' })
            get()._startPolling()
        } catch (err) {
            set({
                status: 'failed',
                error: err?.response?.data?.detail || err.message || 'Failed to start agent.',
            })
        }
    },

    // --- Internal polling ---
    _startPolling: () => {
        const { pollingTimer } = get()
        if (pollingTimer) clearInterval(pollingTimer)

        const timer = setInterval(async () => {
            try {
                const statusData = await pollStatus()
                const currentStatus = statusData.status

                if (['success', 'failed', 'partial'].includes(currentStatus)) {
                    clearInterval(timer)
                    set({ pollingTimer: null, status: currentStatus })

                    // Fetch full results
                    try {
                        const res = await fetchResults()
                        set({ results: res })
                    } catch (e) {
                        set({ error: 'Pipeline finished but could not fetch results.' })
                    }
                } else {
                    set({ status: currentStatus })
                }
            } catch (err) {
                clearInterval(timer)
                set({ pollingTimer: null, status: 'failed', error: err.message })
            }
        }, 3000)

        set({ pollingTimer: timer })
    },

    // --- Reset ---
    reset: async () => {
        const { pollingTimer } = get()
        if (pollingTimer) clearInterval(pollingTimer)
        
        // Call backend reset endpoint
        try {
            await resetPipeline()
        } catch (err) {
            console.error('Failed to reset backend:', err)
        }
        
        set({ status: 'idle', results: null, error: null, pollingTimer: null })
    },
}))

export default useAgentStore
