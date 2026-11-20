<script setup>
import { computed, inject, onMounted, reactive, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { api } from '../api'

const currentLawId = inject('currentLawId')

const detail = ref(null)
const progressMap = ref({})        // paragraph_id -> status
const currentArticleId = ref(null)
const currentParaId = ref(null)

const pool = ref([])               // 词块池 [{t, term_id, key}]
const answer = ref([])             // 组句区
const judged = ref(null)           // 判分结果 [{t, expected, ok}]
const judging = ref(false)
const showSource = ref(false)
const startAt = ref(0)
let keySeq = 0

async function load() {
  detail.value = await api.lawDetail(currentLawId.value)
  await refreshProgress()
  // 默认定位到第一个未通过的段落
  const flat = flatParagraphs.value
  const firstOpen = flat.find(p => progressMap.value[p.id] !== 'passed') || flat[0]
  selectPara(firstOpen.article_id, firstOpen.id)
}

async function refreshProgress() {
  const prog = await api.progress(currentLawId.value)
  progressMap.value = Object.fromEntries(prog.paragraphs.map(p => [p.id, p.status]))
}

// 扁平段落列表（按条号、段序）
const flatParagraphs = computed(() =>
  (detail.value?.articles || []).flatMap(a =>
    a.paragraphs.map(p => ({ ...p, article_id: a.id, article_label: a.label, article_order: a.order_no }))
  )
)
const currentIndex = computed(() => flatParagraphs.value.findIndex(p => p.id === currentParaId.value))
const currentPara = computed(() => flatParagraphs.value[currentIndex.value])
const currentArticle = computed(() => detail.value?.articles.find(a => a.id === currentArticleId.value))
const allBlocks = computed(() => pool.value.length + answer.value.length)

async function selectPara(articleId, paraId) {
  currentArticleId.value = articleId
  currentParaId.value = paraId
  judged.value = null
  showSource.value = false
  const sh = await api.shuffle(paraId)
  keySeq = 0
  pool.value = sh.blocks.map(b => ({ ...b, key: keySeq++ }))
  answer.value = []
  startAt.value = Date.now()
  initSnapshot.value = pool.value.map(b => ({ ...b }))
}

function nextPara() {
  if (currentIndex.value < flatParagraphs.value.length - 1) {
    const nxt = flatParagraphs.value[currentIndex.value + 1]
    selectPara(nxt.article_id, nxt.id)
  }
}
function prevPara() {
  if (currentIndex.value > 0) {
    const pre = flatParagraphs.value[currentIndex.value - 1]
    selectPara(pre.article_id, pre.id)
  }
}

// 点击词块：池 → 组句区
function pickFromPool(idx) {
  if (judged.value) judged.value = null
  answer.value.push(pool.value.splice(idx, 1)[0])
}
// 点击组句区词块：退回池
function backToPool(idx) {
  pool.value.push(answer.value.splice(idx, 1)[0])
}

const initSnapshot = ref([])

function reset() {
  judged.value = null
  // 恢复初始打乱顺序（保存在快照里）
  pool.value = initSnapshot.value.map(b => ({ ...b, key: b.key }))
  answer.value = []
}

async function reshuffle() {
  const sh = await api.shuffle(currentParaId.value)
  keySeq = 0
  pool.value = sh.blocks.map(b => ({ ...b, key: keySeq++ }))
  answer.value = []
  judged.value = null
  initSnapshot.value = pool.value.map(b => ({ ...b }))
}

// 组满自动判分
watch(() => answer.value.length, async (n) => {
  if (!currentPara.value || n === 0) return
  if (n === allBlocks.value && n > 0 && !judging.value) {
    judging.value = true
    const duration = Date.now() - startAt.value
    try {
      const r = await api.check({ paragraph_id: currentParaId.value, tokens: answer.value.map(b => b.t), duration_ms: duration })
      judged.value = r
      await refreshProgress()
    } finally {
      judging.value = false
    }
  }
})

// 判分着色：answer[i] 对 judged.detail[i]
function blockClass(block, idx) {
  if (!judged.value) return 'in-answer'
  const d = judged.value.detail[idx]
  return d && d.t === block.t && d.ok ? 'ok' : 'bad'
}

// 条级状态聚合
function articleStatus(a) {
  const sts = a.paragraphs.map(p => progressMap.value[p.id] || 'new')
  if (sts.every(s => s === 'passed')) return 'passed'
  if (sts.some(s => s !== 'new')) return 'attempted'
  return ''
}

onMounted(load)
</script>

<template>
  <div v-if="detail">
    <!-- 条选择网格 -->
    <div class="card" style="margin-bottom:14px;">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
        <b>条款进度</b>
        <span class="muted">第一条 → 最后一条，逐条逐段拼句</span>
        <span style="flex:1"></span>
        <span class="muted">
          <span style="color:var(--ok);">■</span> 已拼对
          　<span style="color:#a8863d;">■</span> 练过未全对
          　<span style="color:var(--mute);">■</span> 未开始
        </span>
      </div>
      <div class="art-grid">
        <div
          v-for="a in detail.articles" :key="a.id"
          class="art-chip" :class="[articleStatus(a), { active: a.id === currentArticleId }]"
          :title="a.label"
          @click="selectPara(a.id, a.paragraphs[0].id)"
        >{{ a.order_no }}</div>
      </div>
    </div>

    <!-- 练习区 -->
    <div class="card" v-if="currentPara">
      <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:14px;">
        <h2 class="serif" style="margin:0; font-size:18px;">{{ currentPara.article_label }}</h2>
        <div v-if="currentArticle.paragraphs.length > 1" style="display:flex; gap:6px;">
          <button
            v-for="(p, i) in currentArticle.paragraphs" :key="p.id"
            :class="{ primary: p.id === currentParaId }"
            style="font-size:12px; padding:3px 12px;"
            @click="selectPara(currentArticleId, p.id)"
          >第{{ i + 1 }}段</button>
        </div>
        <span style="flex:1"></span>
        <span class="muted">{{ currentIndex + 1 }} / {{ flatParagraphs.length }} 段</span>
      </div>

      <!-- 组句区 -->
      <div style="margin-bottom:6px; color:var(--mute); font-size:13px;">
        点击下方词块按序组句，或直接拖拽排列；点击已组词块可退回：
      </div>
      <draggable
        v-model="answer" item-key="key"
        :group="{ name: 'words' }"
        class="drop-zone serif" :class="{ filled: answer.length }"
        style="margin-bottom:16px;"
      >
        <template #item="{ element, index }">
          <span class="block" :class="blockClass(element, index)" @click="backToPool(index)">
            {{ element.t }}<span v-if="!judged" class="idx">{{ index + 1 }}</span>
          </span>
        </template>
      </draggable>

      <!-- 词块池 -->
      <draggable
        v-model="pool" item-key="key"
        :group="{ name: 'words' }"
        class="drop-zone"
        style="min-height:58px; margin-bottom:16px;"
      >
        <template #item="{ element, index }">
          <span class="block" @click="pickFromPool(index)">{{ element.t }}</span>
        </template>
      </draggable>

      <!-- 结果反馈 -->
      <div v-if="judged" style="margin-bottom:12px;">
        <div v-if="judged.correct" style="color:var(--ok); font-weight:600;">
          ✓ 全对！与原文一致（{{ judged.detail.length }} 词）
        </div>
        <div v-else style="color:var(--bad); font-weight:600;">
          ✗ 有 {{ judged.detail.filter(d => !d.ok).length }} 处不一致（红色标出），点击红色词块退回调整
        </div>
      </div>

      <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
        <button :disabled="currentIndex <= 0" @click="prevPara">← 上一段</button>
        <button @click="reshuffle">重新打乱</button>
        <button @click="reset" :disabled="!answer.length && !judged">重置</button>
        <button @click="showSource = !showSource">{{ showSource ? '隐藏' : '查看' }}原文</button>
        <span style="flex:1"></span>
        <span v-if="judging" class="muted"><span class="spin"></span> 判分中</span>
        <button class="primary" :disabled="currentIndex >= flatParagraphs.length - 1" @click="nextPara">
          下一段 →
        </button>
      </div>

      <div v-if="showSource" class="reading-panel serif" style="margin-top:14px;">
        {{ currentPara.text }}
      </div>
    </div>
  </div>
</template>
