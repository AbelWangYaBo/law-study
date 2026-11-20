// 后端 API 封装；后端不可用时自动回退静态快照（只读演示模式）
let snapshotMode = false
// 快照模式下：paragraph_id -> {tokens, text}，供打乱/判分在本地模拟
const paraCache = new Map()

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

async function snapshotFetch(name) {
  const resp = await fetch(`api-snapshot/${name}`)
  if (!resp.ok) throw new Error(`快照数据缺失: ${name}`)
  return resp.json()
}

// 启动探测：后端可达则走动态模式，否则进入快照模式
export async function detectBackend() {
  try {
    const resp = await fetch('api/laws')
    if (resp.ok) return true
  } catch { /* 后端不可达 */ }
  snapshotMode = true
  return false
}

export const isSnapshot = () => snapshotMode

function cacheDetail(detail) {
  for (const a of detail.articles || []) {
    for (const p of a.paragraphs || []) {
      paraCache.set(p.id, { tokens: p.tokens || [], text: p.text })
    }
  }
  return detail
}

// 与后端 shuffle 相同语义：Fisher-Yates 打乱，长度>1 时保证与原序不同
function localShuffle(pid) {
  const cached = paraCache.get(pid)
  const blocks = cached ? cached.tokens.map(t => ({ ...t })) : []
  if (blocks.length > 1) {
    const original = blocks.map(b => b.t).join('\u0000')
    for (let i = 0; i < 20; i++) {
      for (let j = blocks.length - 1; j > 0; j--) {
        const k = Math.floor(Math.random() * (j + 1));
        [blocks[j], blocks[k]] = [blocks[k], blocks[j]]
      }
      if (blocks.map(b => b.t).join('\u0000') !== original) break
    }
  }
  return Promise.resolve({ paragraph_id: pid, text_length: cached ? cached.text.length : 0, blocks })
}

// 与后端 check 相同语义：逐词严格比对（不落库）
function localCheck({ paragraph_id, tokens: got }) {
  const expected = (paraCache.get(paragraph_id)?.tokens || []).map(t => t.t)
  const correct = got.length === expected.length && got.every((g, i) => g === expected[i])
  const detail = []
  for (let i = 0; i < Math.max(got.length, expected.length); i++) {
    detail.push({
      t: i < got.length ? got[i] : null, expected: expected[i],
      ok: i < got.length && got[i] === expected[i],
    })
  }
  return Promise.resolve({ correct, detail })
}

// 快照模式无练习日志，全部为未开始
function localProgress() {
  const paragraphs = [...paraCache.keys()].map(id => ({ id, status: 'new' }))
  return Promise.resolve({ paragraphs, total: paragraphs.length, passed: 0, attempted: 0 })
}

export const api = {
  listLaws: () => snapshotMode ? snapshotFetch('laws.json') : request('/api/laws'),
  lawDetail: (id) => snapshotMode
    ? snapshotFetch(`law-${id}.json`).then(cacheDetail)
    : request(`/api/laws/${id}`),
  lawTerms: (id) => snapshotMode ? snapshotFetch(`law-${id}-terms.json`) : request(`/api/laws/${id}/terms`),
  shuffle: (pid) => snapshotMode ? localShuffle(pid) : request(`/api/practice/paragraphs/${pid}/shuffle`),
  check: (payload) => snapshotMode ? localCheck(payload) : request('/api/practice/check', { method: 'POST', body: JSON.stringify(payload) }),
  progress: (lawId) => snapshotMode ? localProgress() : request(`/api/practice/progress?law_id=${lawId}`),
  lawTree: () => snapshotMode ? snapshotFetch('graph-law-tree.json') : request('/api/graph/law-tree'),
  relationGraph: () => snapshotMode ? snapshotFetch('graph-relations.json') : request('/api/graph/relations'),
  termGraph: (lawId) => snapshotMode ? snapshotFetch(`graph-term-graph-${lawId}.json`) : request(`/api/graph/term-graph?law_id=${lawId}`),
  reading: (payload) => snapshotMode
    ? Promise.reject(new Error('静态快照模式不支持 AI 解读，请本地启动后端使用'))
    : request('/api/ai/reading', { method: 'POST', body: JSON.stringify(payload) }),
}
