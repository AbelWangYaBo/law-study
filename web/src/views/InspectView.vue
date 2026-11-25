<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cnNum, loadData, shortName, useOpenLaw } from '../data'

const route = useRoute()
const laws = inject('laws')
const openLaw = useOpenLaw()

const data = ref(null)
const error = ref('')
loadData('inspection').then(d => { data.value = d }).catch(e => { error.value = String(e.message || e) })

const LEVELS = ['关键', '主要', '一般']
const LEVEL_CLASS = { 关键: 'high', 主要: 'mid', 一般: 'low' }
// 从阅读页带着条款进来时看全部文档，否则默认看通用版
const docId = ref(route.query.law ? 'all' : 'general')
const chapter = ref('')
const levels = ref([...LEVELS])
const keyword = ref('')

// 进入时按某法规的某一条筛选：?law=<法规ID>&article=<条号> 或 &clause=<编号>
const lawName = computed(() => laws.value.find(l => l.id === Number(route.query.law))?.name || '')
const article = computed(() => Number(route.query.article) || 0)
const clause = computed(() => String(route.query.clause || ''))
const matchesTarget = it => !lawName.value || it.refs.some(r => r.law === lawName.value
  && ((article.value && r.articles.includes(article.value)) || (clause.value && r.clauses.includes(clause.value))))

const scopedDocs = computed(() => (data.value?.docs || []).map(d => ({ ...d, items: d.items.filter(matchesTarget) })))
const docs = computed(() => scopedDocs.value.filter(d => docId.value === 'all' || d.id === docId.value))
const chapters = computed(() => [...new Set(docs.value.flatMap(d => d.items.map(it => it.chapter)))])
const items = computed(() => docs.value
  .flatMap(d => d.items.map(it => ({ ...it, scope: d.scope })))
  .filter(it => !chapter.value || it.chapter === chapter.value)
  .filter(it => levels.value.includes(it.level))
  .filter(it => !keyword.value || `${it.clause} ${it.content}`.includes(keyword.value)))
</script>

<template>
  <div>
    <div class="card" style="margin-bottom:16px;">
      <h1 class="serif" style="margin:0 0 6px; font-size:20px; letter-spacing:.08em;">医疗器械 GMP 检查指导原则（2026 版）</h1>
      <div class="muted">每个检查项对应哪条规范、哪条附录，风险等级多高。读 GMP 条文时点「检查项」就会跳到这里。</div>
      <template v-if="data">
        <div class="filters">
          <button v-for="d in [{ id: 'all', scope: '全部', items: scopedDocs.flatMap(x => x.items) }, ...scopedDocs]" :key="d.id"
                  :class="{ primary: docId === d.id }" @click="docId = d.id; chapter = ''">{{ d.scope }} {{ d.items.length }}</button>
        </div>
        <div class="filters">
          <select v-model="chapter">
            <option value="">全部章节</option>
            <option v-for="c in chapters" :key="c" :value="c">{{ c }}</option>
          </select>
          <label v-for="lv in LEVELS" :key="lv" class="check"><input v-model="levels" type="checkbox" :value="lv" /> {{ lv }}</label>
          <input v-model="keyword" placeholder="搜索条款号或检查内容" style="flex:1; min-width:180px;" />
        </div>
        <div v-if="lawName && (article || clause)" class="muted" style="margin-top:8px;">
          只看《{{ lawName }}》{{ clause || `第${cnNum(article)}条` }} 的检查项，<router-link to="/inspect">查看全部</router-link>
        </div>
      </template>
    </div>

    <div v-if="error" class="card error-box">{{ error }}</div>
    <div v-else-if="!data" class="card muted">加载中…</div>
    <table v-else class="data-table card">
      <thead>
        <tr><th>条款</th><th>范围</th><th>风险</th><th>章节</th><th>检查内容</th><th>对应条款</th></tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="`${it.scope}-${it.no}`">
          <td class="nowrap">{{ it.clause }}</td>
          <td class="nowrap">{{ it.scope }}</td>
          <td class="nowrap"><span class="level-badge" :class="LEVEL_CLASS[it.level]">{{ it.level }}</span></td>
          <td class="nowrap">{{ it.chapter }}</td>
          <td>{{ it.content }}</td>
          <td class="nowrap">
            <template v-for="r in it.refs" :key="r.law">
              <a v-for="n in r.articles" :key="`${r.law}-${n}`" class="ref" href="#" @click.prevent="openLaw(r.law, { article: n })">{{ shortName(r.law) }} 第{{ cnNum(n) }}条</a>
              <a v-for="c in r.clauses" :key="`${r.law}-${c}`" class="ref" href="#" @click.prevent="openLaw(r.law, { clause: c })">{{ shortName(r.law) }} {{ c }}</a>
            </template>
            <span v-if="!it.refs.length" class="muted">{{ it.refs_raw }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="data && !items.length" class="card muted">没有符合条件的检查项。</div>
  </div>
</template>
