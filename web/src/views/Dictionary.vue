<script setup>
import { inject, onMounted, ref } from 'vue'
import { api } from '../api'

const currentLawId = inject('currentLawId')
const terms = ref([])

onMounted(async () => {
  terms.value = await api.lawTerms(currentLawId.value)
})

const typeLabel = { definition: '定义术语', short_name: '简称', abbreviation: '英文缩写' }
</script>

<template>
  <div>
    <div class="card">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
        <b>术语字典</b>
        <span class="muted">从法规文本规则抽取，词块拼句时整词出现、不做拆分</span>
        <span style="flex:1"></span>
        <span class="tag">{{ terms.length }} 个</span>
      </div>
      <table v-if="terms.length" style="width:100%; border-collapse:collapse; font-size:15px;">
        <thead>
          <tr style="text-align:left; color:var(--mute); font-size:13px;">
            <th style="padding:8px 10px; border-bottom:1px solid var(--line);">术语</th>
            <th style="padding:8px 10px; border-bottom:1px solid var(--line);">类型</th>
            <th style="padding:8px 10px; border-bottom:1px solid var(--line);">定义 / 全称</th>
            <th style="padding:8px 10px; border-bottom:1px solid var(--line);">来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in terms" :key="t.id">
            <td class="serif" style="padding:10px; border-bottom:1px solid var(--line); font-weight:600; white-space:nowrap;">{{ t.name }}</td>
            <td style="padding:10px; border-bottom:1px solid var(--line);"><span class="tag">{{ typeLabel[t.term_type] || t.term_type }}</span></td>
            <td class="serif" style="padding:10px; border-bottom:1px solid var(--line); color:var(--ink-2); line-height:1.8;">
              {{ t.definition || t.full_name || '—' }}
            </td>
            <td style="padding:10px; border-bottom:1px solid var(--line); white-space:nowrap;">{{ t.article_label }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="muted" style="padding:20px 0; text-align:center;">暂无术语</div>
    </div>
  </div>
</template>
