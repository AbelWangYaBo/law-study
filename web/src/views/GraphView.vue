<script setup>
import * as echarts from 'echarts'
import { inject, onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../api'

const currentLawId = inject('currentLawId')
const tab = ref('tree')       // tree / relations / terms
const elTree = ref(null), elRelations = ref(null), elTerms = ref(null)
const containers = { tree: elTree, relations: elRelations, terms: elTerms }
const charts = {}

async function renderTree() {
  const data = await api.lawTree()
  charts.tree.setOption({
    tooltip: { trigger: 'item', formatter: p => {
      const extra = p.data.extra || {}
      return `${p.name}${extra.level ? `<br/>层级：${extra.level}` : ''}${extra.virtual ? '<br/>（被引用法规）' : ''}`
    } },
    series: [{
      type: 'tree', data: [data],
      left: '8%', right: '16%', top: '5%', bottom: '5%',
      symbolSize: 14, orient: 'LR',
      label: { position: 'left', verticalAlign: 'middle', align: 'right', fontSize: 13, color: '#55504a' },
      leaves: { label: { position: 'right', align: 'left' } },
      lineStyle: { color: '#c9c1b2' },
      itemStyle: { color: '#8a6d3b' },
    }],
  })
}

async function renderRelations() {
  const data = await api.relationGraph()
  charts.relations.setOption({
    tooltip: { formatter: p => p.dataType === 'edge' ? `${p.data.source} —${p.data.value}→ ${p.data.target}` : p.name },
    legend: [{ data: data.categories.map(c => c.name), bottom: 10, textStyle: { color: '#8c8579' } }],
    series: [{
      type: 'graph', layout: 'force', roam: true,
      data: data.nodes.map(n => ({ ...n, category: n.category })),
      links: data.links,
      categories: data.categories,
      force: { repulsion: 260, edgeLength: [90, 160] },
      label: { show: true, fontSize: 12, color: '#2f2b26' },
      edgeLabel: { show: true, fontSize: 11, formatter: '{c}', color: '#8c8579' },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 8,
      lineStyle: { color: '#c9a86a', width: 2, curveness: 0.1 },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
    }],
  })
}

async function renderTermGraph() {
  const data = await api.termGraph(currentLawId.value)
  charts.terms.setOption({
    tooltip: { formatter: p => p.dataType === 'node' ? `${p.name}<br/>${p.data.definition || ''}` : `${p.data.source} ↔ ${p.data.target}（同条款共现 ${p.data.value} 次）` },
    series: [{
      type: 'graph', layout: 'force', roam: true,
      data: data.nodes, links: data.links,
      force: { repulsion: 200, edgeLength: [70, 150] },
      label: { show: true, fontSize: 13, color: '#2f2b26' },
      edgeSymbol: 'none',
      lineStyle: { color: '#d8d0c0', width: 2 },
      itemStyle: { color: '#8a6d3b', borderColor: '#fff', borderWidth: 1 },
    }],
  })
}

const renderers = { tree: renderTree, relations: renderRelations, terms: renderTermGraph }

async function switchTab(t) {
  tab.value = t
  await Promise.resolve()
  if (!charts[t]) {
    charts[t] = echarts.init(containers[t].value)
    window.addEventListener('resize', charts[t].resize)
  }
  charts[t].resize()
  await renderers[t]()
}

onMounted(() => switchTab('tree'))
onBeforeUnmount(() => Object.values(charts).forEach(c => c.dispose()))
</script>

<template>
  <div>
    <div class="card" style="padding:16px 22px;">
      <div style="display:flex; gap:8px; margin-bottom:12px;">
        <button :class="{ primary: tab === 'tree' }" @click="switchTab('tree')">法规层级树</button>
        <button :class="{ primary: tab === 'relations' }" @click="switchTab('relations')">法规引用图</button>
        <button :class="{ primary: tab === 'terms' }" @click="switchTab('terms')">术语共现图</button>
        <span class="muted" style="margin-left:auto; align-self:center;">可拖拽、滚轮缩放</span>
      </div>
      <div ref="elTree" v-show="tab === 'tree'" style="height:520px;"></div>
      <div ref="elRelations" v-show="tab === 'relations'" style="height:520px;"></div>
      <div ref="elTerms" v-show="tab === 'terms'" style="height:520px;"></div>
    </div>
  </div>
</template>
