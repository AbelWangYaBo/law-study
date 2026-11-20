// 后端 API 封装
async function request(url, options = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let detail = `${resp.status}`
    try { detail = (await resp.json()).detail || detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  return resp.json()
}

export const api = {
  listLaws: () => request('/api/laws'),
  lawDetail: (id) => request(`/api/laws/${id}`),
  lawTerms: (id) => request(`/api/laws/${id}/terms`),
  shuffle: (pid) => request(`/api/practice/paragraphs/${pid}/shuffle`),
  check: (payload) => request('/api/practice/check', { method: 'POST', body: JSON.stringify(payload) }),
  progress: (lawId) => request(`/api/practice/progress?law_id=${lawId}`),
  lawTree: () => request('/api/graph/law-tree'),
  relationGraph: () => request('/api/graph/relations'),
  termGraph: (lawId) => request(`/api/graph/term-graph?law_id=${lawId}`),
  reading: (payload) => request('/api/ai/reading', { method: 'POST', body: JSON.stringify(payload) }),
}
