// 静态数据（检查指导原则、标准地图）：本地与 Pages 读同一份 JSON，路径相对于页面，与 api-snapshot 一致
import { inject } from 'vue'
import { useRouter } from 'vue-router'

const cache = {}

export function loadData(name) {
  if (!cache[name]) {
    cache[name] = fetch(`data/${name}.json`).then(resp => {
      if (!resp.ok) throw new Error(`数据缺失: data/${name}.json`)
      return resp.json()
    })
  }
  return cache[name]
}

export const GMP = '医疗器械生产质量管理规范'

// 「医疗器械生产质量管理规范附录 无菌医疗器械」→「无菌医疗器械附录」；《规范》本身 →「规范」
export const shortName = name => {
  if (name === GMP) return '规范'
  const appendix = name.match(/^医疗器械生产质量管理规范附录 (.+)$/)?.[1]
  return appendix ? appendix + '附录' : name
}

const DIGITS = '零一二三四五六七八九'
export function cnNum(n) {   // 3 → 三，110 → 一百一十
  if (n < 10) return DIGITS[n]
  if (n < 20) return '十' + (n % 10 ? DIGITS[n % 10] : '')
  if (n < 100) return DIGITS[Math.floor(n / 10)] + '十' + (n % 10 ? DIGITS[n % 10] : '')
  const rest = n % 100
  return DIGITS[Math.floor(n / 100)] + '百' + (rest ? (rest < 10 ? '零' + DIGITS[rest] : rest < 20 ? '一' + cnNum(rest) : cnNum(rest)) : '')
}

// 跳到阅读页的某一条：?article=条号 或 ?clause=编号
export function useOpenLaw() {
  const laws = inject('laws')
  const currentLawId = inject('currentLawId')
  const router = useRouter()
  return (law, query) => {
    const target = laws.value.find(l => l.name === law)
    if (!target) return
    currentLawId.value = target.id
    router.push({ path: '/', query })
  }
}
