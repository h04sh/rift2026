/**
 * API layer – communicates with the FastAPI backend
 */

import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: BASE,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
})

/** POST /api/run-agent – Start the pipeline */
export async function runAgent(payload) {
    const { data } = await api.post('/api/run-agent', payload)
    return data
}

/** GET /api/status – Poll pipeline status */
export async function pollStatus() {
    const { data } = await api.get('/api/status')
    return data
}

/** GET /api/results – Fetch full results.json */
export async function fetchResults() {
    const { data } = await api.get('/api/results')
    return data
}

/** GET /api/timeline – Lightweight timeline for live updates */
export async function fetchTimeline() {
    const { data } = await api.get('/api/timeline')
    return data
}

/** GET /health */
export async function checkHealth() {
    const { data } = await api.get('/health')
    return data
}

/** POST /api/reset – Reset pipeline state */
export async function resetPipeline() {
    const { data } = await api.post('/api/reset')
    return data
}
