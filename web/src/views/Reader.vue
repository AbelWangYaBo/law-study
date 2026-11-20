<script setup>
import { computed, inject, reactive, ref } from 'vue'
import { marked } from 'marked'
import { api } from '../api'

const currentLawId = inject('currentLawId')
const snapshot = inject('snapshot', false)
const detail = ref(null)
const termsById = ref({})
const readings = reactive({})   // key: `${articleId}:${kind}`

async function load() {
  detail.value = await api.lawDetail(currentLawId.value)
  const terms = await api.lawTerms(currentLawId.value)
  termsById.value = Object.fromEntries(terms.map(t => [t.id, t]))
}
load()

async function toggleReading(article, kind) {
  const key = `${article.id}:${kind}`
  if (readings[key]?.open && !readings[key]?.content) return
  if (readings[key]?.open) { readings[key].open = false; return }
  const state = readings[key] || (readings[key] = { open: false, loading: false, content: '', error: '' })
  state.open = true
  if (!state.content && !state.loading) {
    state.loading = true
    try {
      const r = await api.reading({ article_id: article.id, kind })
      state.content = r.content
    } catch (e) {
      state.error = String(e.message || e)
    } finally {
      state.loading = false
    }
  }
}

async function regenerate(article, kind) {
  const key = `${article.id}:${kind}`
  const state = readings[key]
  state.content = ''
  state.error = ''
  state.loading = true
  try {
    const r = await api.reading({ article_id: article.id, kind, force: true })
    state.content = r.content
  } catch (e) {
    state.error = String(e.message || e)
  } finally {
    state.loading = false
  }
}

function renderMd(text) {
  return marked.parse(text, { breaks: true })
}

const kindLabel = { interpret: 'AI 解读', scenario: '场景分析' }
const law = computed(() => detail.value)
</script>

<template>
  <div v-if="law">
    <div class="card" style="text-align:center; margin-bottom:18px;">
      <h1 class="serif" style="margin:4px 0 10px; letter-spacing:.12em;">{{ law.name }}</h1>
      <div class="muted">
        <span v-if="law.level" class="tag">{{ law.level }}</span>
        <span v-if="law.doc_number" class="tag">{{ law.doc_number }}</span>
        <span v-if="law.authority">{{ law.authority }}</span>
        <span v-if="law.effective_date">　施行：{{ law.effective_date }}</span>
      </div>
    </div>

    <div v-for="a in law.articles" :key="a.id" class="card" style="margin-bottom:14px;">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
        <h2 class="serif" style="margin:0; font-size:18px; letter-spacing:.1em;">{{ a.label }}</h2>
        <span style="flex:1"></span>
        <button :disabled="snapshot" :title="snapshot ? '静态快照模式不可用' : ''" @click="toggleReading(a, 'interpret')">AI 解读</button>
        <button :disabled="snapshot" :title="snapshot ? '静态快照模式不可用' : ''" @click="toggleReading(a, 'scenario')">场景分析</button>
      </div>

      <p
        v-for="p in a.paragraphs" :key="p.id"
        class="serif" style="margin:0 0 8px; font-size:17px; line-height:2; text-indent:2em; text-align:justify; color:var(--ink-2);"
      >
        <template v-for="(tok, i) in p.tokens" :key="i">
          <span v-if="tok.term_id && termsById[tok.term_id]" class="term-hit" :title="termsById[tok.term_id].definition">{{ tok.t }}</span>
          <template v-else>{{ tok.t }}</template>
        </template>
      </p>

      <div v-for="kind in ['interpret', 'scenario']" :key="kind">
        <div v-if="readings[`${a.id}:${kind}`]?.open" class="reading-panel">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
            <b>{{ kindLabel[kind] }}</b>
            <span class="muted">{{ a.label }}</span>
            <span style="flex:1"></span>
            <button v-if="readings[`${a.id}:${kind}`].content" @click="regenerate(a, kind)" style="font-size:12px; padding:3px 12px;">重新生成</button>
            <button @click="readings[`${a.id}:${kind}`].open = false" style="font-size:12px; padding:3px 12px;">收起</button>
          </div>
          <div v-if="readings[`${a.id}:${kind}`].loading" class="muted"><span class="spin"></span> 生成中，约需十几秒…</div>
          <div v-else-if="readings[`${a.id}:${kind}`].error" class="error-box">{{ readings[`${a.id}:${kind}`].error }}</div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div v-else class="md serif" v-html="renderMd(readings[`${a.id}:${kind}`].content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>
