<script setup>
import { computed, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, detectBackend, isSnapshot } from './api'

const laws = ref([])
const currentLawId = ref(Number(localStorage.getItem('lawId')) || null)
const snapshot = ref(false)
const route = useRoute()

async function load() {
  await detectBackend()
  snapshot.value = isSnapshot()
  laws.value = await api.listLaws()
  applyLawFromQuery()
  if (laws.value.length && !laws.value.some(l => l.id === currentLawId.value)) {
    currentLawId.value = laws.value[0].id
  }
}
load()

watch(currentLawId, v => v && localStorage.setItem('lawId', v))

// 链接里带 ?law=<法规ID> 时切到该法规（粘贴链接、书签进入阅读页）
function applyLawFromQuery() {
  const id = Number(route.query.law)
  if (laws.value.some(l => l.id === id)) currentLawId.value = id
}
watch(() => route.query.law, applyLawFromQuery)

// 法规多了以后按三类分组显示；分组由法规名推导，不新增字段
const groups = computed(() => {
  const g = { law: [], gmp: [], history: [] }
  for (const l of laws.value) {
    if (l.name.includes('已被替代')) g.history.push(l)
    else if (l.name.includes('质量管理规范')) g.gmp.push(l)
    else g.law.push(l)
  }
  return [
    { label: '法律法规', list: g.law },
    { label: '质量管理规范', list: g.gmp },
    { label: '历史版本（备查）', list: g.history },
  ].filter(x => x.list.length)
})

provide('laws', laws)
provide('currentLawId', currentLawId)
provide('snapshot', snapshot)
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <a class="brand" href="#/">法规学习</a>
      <nav>
        <router-link to="/">阅读</router-link>
        <router-link to="/recite">拼句背诵</router-link>
        <router-link to="/dictionary">术语字典</router-link>
        <router-link to="/graph">知识图谱</router-link>
        <router-link to="/inspect">检查指导原则</router-link>
        <router-link to="/standards">标准地图</router-link>
      </nav>
      <select
        v-if="laws.length > 1"
        v-model="currentLawId"
        style="margin-left:auto; border:1px solid var(--line); border-radius:16px; padding:4px 10px; background:var(--paper);"
      >
        <optgroup v-for="g in groups" :key="g.label" :label="g.label">
          <option v-for="l in g.list" :key="l.id" :value="l.id">{{ l.name }}</option>
        </optgroup>
      </select>
    </header>

    <div v-if="snapshot" class="snapshot-banner">
      静态演示快照（只读）—— AI 解读与练习进度记录不可用，拼句判分在本地进行。完整功能请本地启动：<code>./run.sh</code>
    </div>

    <div v-if="!laws.length" class="card muted">
      数据库为空。请先导入法规：
      <code>uv run python scripts/import_law.py &lt;法规.html|md&gt;</code>
    </div>
    <router-view v-else :key="currentLawId" />
  </div>
</template>
