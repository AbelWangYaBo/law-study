<script setup>
import { provide, ref, watch } from 'vue'
import { api, detectBackend, isSnapshot } from './api'

const laws = ref([])
const currentLawId = ref(Number(localStorage.getItem('lawId')) || null)
const snapshot = ref(false)

async function load() {
  await detectBackend()
  snapshot.value = isSnapshot()
  laws.value = await api.listLaws()
  if (laws.value.length && !laws.value.some(l => l.id === currentLawId.value)) {
    currentLawId.value = laws.value[0].id
  }
}
load()

watch(currentLawId, v => v && localStorage.setItem('lawId', v))
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
      </nav>
      <select
        v-if="laws.length > 1"
        v-model="currentLawId"
        style="margin-left:auto; border:1px solid var(--line); border-radius:16px; padding:4px 10px; background:var(--paper);"
      >
        <option v-for="l in laws" :key="l.id" :value="l.id">{{ l.name }}</option>
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
