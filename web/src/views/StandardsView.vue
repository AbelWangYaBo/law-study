<script setup>
import { computed, inject, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cnNum, loadData, shortName, useOpenLaw } from '../data'

const route = useRoute()
const laws = inject('laws')
const openLaw = useOpenLaw()

const data = ref(null)
const error = ref('')
loadData('standards').then(d => { data.value = d }).catch(e => { error.value = String(e.message || e) })

const STATUS_CLASS = { 现行: 'low', 即将实施: 'mid', 已废止: 'high' }
const lawFilter = ref('')       // '' = 全部
const keyword = ref('')

// 进入时只列某法规某一条相关的标准：?law=<法规ID>&article=<条号> 或 &clause=<编号>
const lawName = computed(() => laws.value.find(l => l.id === Number(route.query.law))?.name || '')
const article = computed(() => Number(route.query.article) || 0)
const clause = computed(() => String(route.query.clause || ''))
const chapters = computed(() => data.value?.chapters || [])
const chapterArticles = (law, title) => chapters.value.find(c => c.law === law && c.title === title)?.articles || []

const matched = computed(() => (data.value?.standards || []).filter(s => {
  if (lawName.value) {
    const hit = s.gmp.some(g => g.law === lawName.value && (
      g.articles.includes(article.value) || g.articles.includes(clause.value)
      || g.chapters.some(t => article.value && chapterArticles(g.law, t).includes(article.value))))
    if (!hit) return false
  }
  return !keyword.value || `${s.number} ${s.name} ${s.themes.join(' ')} ${s.usage}`.includes(keyword.value)
}))

const scopeLaw = computed(() => lawName.value || lawFilter.value)
const rangeText = articles => (articles.length > 1 ? `第${articles[0]}–${articles[articles.length - 1]}条` : `第${articles[0]}条`)
// 分节：指定了法规就按它的章排列，没指定就合成一节
const sections = computed(() => {
  // 带着某一条进来：不按章分组，免得映射到多章的同一标准重复出现
  if (lawName.value) return [{ title: '相关标准', note: '', standards: matched.value }]
  if (!scopeLaw.value) return [{ title: '全部标准', note: '', standards: matched.value }]
  const used = new Set()
  const out = chapters.value.filter(c => c.law === scopeLaw.value).map(ch => {
    const list = matched.value.filter(s => s.gmp.some(g => g.law === scopeLaw.value
      && (g.chapters.includes(ch.title) || g.articles.some(n => ch.articles.includes(n)))))
    list.forEach(s => used.add(s.number))
    return { title: ch.title, note: rangeText(ch.articles), standards: list }
  })
  const rest = matched.value.filter(s => !used.has(s.number))
  if (rest.length) out.push({ title: '其他相关标准', note: '服务于附录、跨章使用，或未映射到具体章节', standards: rest })
  return out
})

const expanded = reactive({})
const LINK_LIMIT = 8
// 一项标准可能对应几十个条款：默认只列前几项，点开再看全部
const linksOf = s => s.gmp.flatMap(g => [
  ...g.chapters.map(c => ({ law: g.law, label: `${shortName(g.law)} ${c}`, chapter: c })),
  ...g.articles.map(n => ({ law: g.law, label: `${shortName(g.law)} ${typeof n === 'string' ? n : `第${cnNum(n)}条`}`,
    query: typeof n === 'string' ? { clause: n } : { article: n } })),
])
const shownLinks = s => (expanded[s.number] ? linksOf(s) : linksOf(s).slice(0, LINK_LIMIT))
function openLink(link) {
  if (link.chapter) openChapter(link.law, link.chapter)
  else openLaw(link.law, link.query)
}
function openChapter(law, title) {
  const first = chapterArticles(law, title)[0]
  if (first) openLaw(law, { article: first })
}
</script>

<template>
  <div>
    <div class="card" style="margin-bottom:16px;">
      <h1 class="serif" style="margin:0 0 6px; font-size:20px; letter-spacing:.08em;">GMP 标准地图</h1>
      <div class="muted">支撑 GMP 各章要求的国家标准、行业标准、计量规范：用在哪一步、产出什么记录、现行状态和替代关系。</div>
      <template v-if="data">
        <div class="filters">
          <select v-if="!lawName" v-model="lawFilter">
            <option value="">全部法规</option>
            <option v-for="l in data.laws" :key="l.name" :value="l.name">{{ l.short }}</option>
          </select>
          <input v-model="keyword" placeholder="搜索标准号、名称、主题或用途" style="flex:1; min-width:200px;" />
        </div>
        <div v-if="lawName" class="muted" style="margin-top:8px;">
          只看《{{ lawName }}》{{ clause || (article ? `第${cnNum(article)}条` : '') }} 相关的标准，<router-link to="/standards">查看全部</router-link>
        </div>
      </template>
    </div>

    <div v-if="error" class="card error-box">{{ error }}</div>
    <div v-else-if="!data" class="card muted">加载中…</div>
    <template v-else>
      <section v-for="sec in sections" :key="sec.title" class="card" style="margin-bottom:16px;">
        <h2 class="serif" style="margin:0; padding:16px 22px 10px; font-size:17px;">
          {{ sec.title }}
          <span v-if="sec.note" class="muted" style="font-size:13px; margin-left:10px;">{{ sec.note }} · {{ sec.standards.length }} 项</span>
        </h2>
        <div v-if="!sec.standards.length" class="muted" style="padding:0 22px 16px;">无直接对应标准。</div>
        <div v-else class="table-wrap">
        <table class="data-table" style="table-layout:fixed;">
          <colgroup><col style="width:24%" /><col style="width:17%" /><col style="width:41%" /><col style="width:18%" /></colgroup>
          <thead><tr><th>标准</th><th>状态</th><th>用途</th><th>对应条款</th></tr></thead>
          <tbody>
            <tr v-for="s in sec.standards" :key="s.number">
              <td>
                <a v-if="s.url" :href="s.url" target="_blank" rel="noopener" class="std-no">{{ s.number }}</a>
                <b v-else class="std-no">{{ s.number }}</b>
                <div>{{ s.name }}</div>
                <div class="muted">
                  {{ s.kind }}<template v-if="s.international"> · {{ s.international }}</template><template v-if="s.effective_date"> · {{ s.status }} {{ s.effective_date }}</template>
                </div>
                <div v-if="s.replaces.length" class="muted">代替：{{ s.replaces.join('、') }}</div>
              </td>
              <td>
                <span class="level-badge" :class="STATUS_CLASS[s.status] || 'mid'">{{ s.status }}</span>
                <div class="muted" style="margin-top:4px;">{{ s.access }}</div>
              </td>
              <td>
                {{ s.usage }}
                <div v-if="s.outputs" class="muted">产出：{{ s.outputs }}</div>
                <div v-if="s.note" class="muted">提示：{{ s.note }}</div>
              </td>
              <td>
                <a v-for="l in shownLinks(s)" :key="l.label" class="ref" href="#" @click.prevent="openLink(l)">{{ l.label }}</a>
                <a v-if="linksOf(s).length > LINK_LIMIT" class="ref" href="#" @click.prevent="expanded[s.number] = !expanded[s.number]">{{ expanded[s.number] ? '收起' : `展开全部 ${linksOf(s).length} 项` }}</a>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </section>
      <div v-if="!matched.length" class="card muted">没有符合条件的标准。</div>
    </template>
  </div>
</template>
