<script setup>
import { computed, inject, nextTick, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { api } from '../api'
import { loadData } from '../data'

const currentLawId = inject('currentLawId')
const snapshot = inject('snapshot', false)
const route = useRoute()
const detail = ref(null)
const termsById = ref({})
const readings = reactive({})   // key: `${articleId}:${kind}`
const storedReadings = ref({})  // 快照/后端已有解读，key 同上（取最新一条）
const hasReadings = ref(false)
const inspectCount = reactive({})    // 条号或编号 → 检查项数
const standardsCount = reactive({})  // 条号或编号 → 相关标准数

const law = computed(() => detail.value)
// 快照模式下整部法规没有解读时（如历史版本），不显示解读按钮
const showReadings = computed(() => !snapshot || hasReadings.value)
// 编号类法规（如 GMP 附录）按「2.1.1」这样的编号定位，其余按条号
const clauseMode = computed(() => /^\d+\.\d+/.test(law.value?.articles?.[0]?.label || ''))
const linkQuery = a => (clauseMode.value ? { law: currentLawId.value, clause: a.label } : { law: currentLawId.value, article: a.order_no })
const inspectCountOf = a => inspectCount[a.order_no] || inspectCount[a.label] || 0
const standardsCountOf = a => standardsCount[a.order_no] || standardsCount[a.label] || 0

async function load() {
  detail.value = await api.lawDetail(currentLawId.value)
  const terms = await api.lawTerms(currentLawId.value)
  termsById.value = Object.fromEntries(terms.map(t => [t.id, t]))
  try {
    const rs = await api.lawReadings(currentLawId.value)
    const map = {}
    for (const r of rs) map[`${r.article_id}:${r.kind}`] = r   // 后写覆盖 = 最新
    storedReadings.value = map
    hasReadings.value = rs.length > 0
  } catch { /* 老后端或快照缺失：无历史解读 */ hasReadings.value = false }
  await Promise.all([loadInspectCount(), loadStandardsCount()])
  await nextTick()
  scrollToTarget()
}
load()

// 检查指导原则：按「法规名 + 条号或编号」数每条条款对应几个检查项
async function loadInspectCount() {
  try {
    const { docs } = await loadData('inspection')
    for (const d of docs) for (const it of d.items) {
      const keys = it.refs.filter(r => r.law === law.value.name).flatMap(r => [...r.articles, ...r.clauses])
      for (const k of new Set(keys)) inspectCount[k] = (inspectCount[k] || 0) + 1
    }
  } catch { /* 没有检查指导原则数据 */ }
}

// 标准地图：标准映射到整章的，算进该章每一条
async function loadStandardsCount() {
  try {
    const { chapters, standards } = await loadData('standards')
    const chapterArticles = (lawName, title) => chapters.find(c => c.law === lawName && c.title === title)?.articles || []
    for (const s of standards) {
      const keys = s.gmp.filter(g => g.law === law.value.name)
        .flatMap(g => [...g.articles, ...g.chapters.flatMap(t => chapterArticles(g.law, t))])
      for (const k of new Set(keys)) standardsCount[k] = (standardsCount[k] || 0) + 1
    }
  } catch { /* 没有标准地图数据 */ }
}

// 从检查指导原则页、标准地图页跳转过来：?article=条号 或 ?clause=编号，滚动到对应条款
function scrollToTarget() {
  const clause = String(route.query.clause || '')
  const target = Number(route.query.article) || law.value.articles.find(a => a.label === clause)?.order_no
  if (target) document.getElementById(`art-${target}`)?.scrollIntoView({ block: 'start' })
}

async function toggleReading(article, kind) {
  const key = `${article.id}:${kind}`
  if (readings[key]?.open && !readings[key]?.content) return
  if (readings[key]?.open) { readings[key].open = false; return }
  const state = readings[key] || (readings[key] = { open: false, loading: false, content: '', error: '' })
  state.open = true
  if (!state.content && !state.loading) {
    if (snapshot) {
      const s = storedReadings.value[key]
      if (s) { state.content = s.content; state.model = s.model; state.date = s.created_at }
      else state.error = '静态快照暂无此条解读：本地生成并重新发布快照后可见'
      return
    }
    state.loading = true
    try {
      const r = await api.reading({ article_id: article.id, kind })
      state.content = r.content
      state.model = r.model
      state.date = new Date().toLocaleString('zh-CN', { hour12: false })
    } catch (e) {
      state.error = String(e.message || e)
    } finally {
      state.loading = false
    }
  }
}

async function regenerate(article, kind) {
  if (snapshot) return   // 静态模式不可再生成
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

    <div v-for="a in law.articles" :key="a.id" :id="`art-${a.order_no}`" class="card" style="margin-bottom:14px;">
      <div style="display:flex; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:8px;">
        <h2 class="serif" style="margin:0; font-size:18px; letter-spacing:.1em;">{{ a.label }}</h2>
        <router-link v-if="inspectCountOf(a)" class="link-chip" :to="{ path: '/inspect', query: linkQuery(a) }">检查项 {{ inspectCountOf(a) }}</router-link>
        <router-link v-if="standardsCountOf(a)" class="link-chip" :to="{ path: '/standards', query: linkQuery(a) }">相关标准 {{ standardsCountOf(a) }}</router-link>
        <span style="flex:1"></span>
        <template v-if="showReadings">
          <button :title="snapshot ? '展示快照中已生成的解读' : ''" @click="toggleReading(a, 'interpret')">AI 解读</button>
          <button :title="snapshot ? '展示快照中已生成的场景分析' : ''" @click="toggleReading(a, 'scenario')">场景分析</button>
        </template>
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
            <span v-if="readings[`${a.id}:${kind}`].model" class="muted" style="font-size:12px;">{{ readings[`${a.id}:${kind}`].model }}<template v-if="readings[`${a.id}:${kind}`].date"> · {{ readings[`${a.id}:${kind}`].date }}</template></span>
            <span style="flex:1"></span>
            <button v-if="!snapshot && readings[`${a.id}:${kind}`].content" @click="regenerate(a, kind)" style="font-size:12px; padding:3px 12px;">重新生成</button>
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
