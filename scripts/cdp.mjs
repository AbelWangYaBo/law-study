// 用本机 Chrome 的 CDP（DevTools 协议）打开网页：取渲染后的 HTML、可见文本、截图，或在页面里执行脚本。
// 不用 Playwright 一类自动化框架：它们启动浏览器时会带 testing 标识，容易被网站拦截。
// 这里只是给普通的 Chrome 开一个调试端口，网站看到的就是一个正常打开的浏览器。
//
// 用法:
//   node scripts/cdp.mjs html <url> [--wait 毫秒]              渲染后的 HTML
//   node scripts/cdp.mjs text <url> [--wait 毫秒]              可见文本
//   node scripts/cdp.mjs shot <url> <输出.png> [--wait 毫秒] [--width 1300] [--height 2200]
//   node scripts/cdp.mjs eval <url> '<js 表达式>' [--wait 毫秒]   输出 { url, value }；表达式可以返回 Promise
//
// 首次运行会用独立的用户数据目录（data/chrome-profile）启动本机 Chrome 并开启调试端口（默认 9333），
// 之后复用这个实例；--port 可换端口。

import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function parseArgs(argv) {
  const [mode, ...rest] = argv
  const opts = { wait: 2500, width: 1300, height: 2200, port: 9333 }
  const positional = []
  for (let i = 0; i < rest.length; i++) {
    if (rest[i].startsWith('--')) opts[rest[i].slice(2)] = Number(rest[++i])
    else positional.push(rest[i])
  }
  return { mode, positional, opts }
}

async function ensureChrome(port) {
  const base = `http://127.0.0.1:${port}`
  const alive = () => fetch(`${base}/json/version`).then(r => r.ok, () => false)
  if (await alive()) return base
  mkdirSync(path.join(ROOT, 'data', 'chrome-profile'), { recursive: true })
  spawn(CHROME, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${path.join(ROOT, 'data', 'chrome-profile')}`,
    '--no-first-run', '--no-default-browser-check', 'about:blank',
  ], { detached: true, stdio: 'ignore' }).unref()
  for (let i = 0; i < 40 && !(await alive()); i++) await new Promise(r => setTimeout(r, 250))
  if (!(await alive())) throw new Error(`Chrome 调试端口 ${port} 没有起来`)
  return base
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl)
    let seq = 0
    const waiting = new Map()
    ws.onopen = () => resolve({
      ws,
      send: (method, params = {}) => new Promise((res, rej) => {
        const id = ++seq
        waiting.set(id, { res, rej })
        ws.send(JSON.stringify({ id, method, params }))
      }),
      waitFor: method => new Promise((res, rej) => {
        const timer = setTimeout(() => { ws.removeEventListener('message', onMessage); rej(new Error(`等待 ${method} 超时`)) }, 30000)
        const onMessage = e => {
          if (JSON.parse(e.data).method === method) { clearTimeout(timer); ws.removeEventListener('message', onMessage); res() }
        }
        ws.addEventListener('message', onMessage)
      }),
    })
    ws.onerror = () => reject(new Error(`连不上 ${wsUrl}`))
    ws.onmessage = e => {
      const msg = JSON.parse(e.data)
      const w = waiting.get(msg.id)
      if (!w) return
      waiting.delete(msg.id)
      msg.error ? w.rej(new Error(`${msg.error.message}（${msg.error.data || ''}）`)) : w.res(msg.result)
    }
  })
}

async function main() {
  const { mode, positional, opts } = parseArgs(process.argv.slice(2))
  const [url, arg2] = positional
  if (!url || !['html', 'text', 'shot', 'eval'].includes(mode)) {
    console.info('用法: node scripts/cdp.mjs <html|text|shot|eval> <url> [参数] [--wait 毫秒] [--width N] [--height N] [--port N]')
    process.exit(2)
  }
  const base = await ensureChrome(opts.port)
  // 每次开一个新标签页，用完关掉
  const target = await fetch(`${base}/json/new?about:blank`, { method: 'PUT' }).then(r => r.json())
  try {
    const cdp = await connect(target.webSocketDebuggerUrl)
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: opts.width, height: opts.height, deviceScaleFactor: 1, mobile: false })
    const loaded = cdp.waitFor('Page.loadEventFired')
    await cdp.send('Page.navigate', { url })
    await loaded
    await new Promise(r => setTimeout(r, opts.wait))   // 等前端把数据取回来、渲染完

    const evaluate = async expression => {
      const { result, exceptionDetails } = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
      if (exceptionDetails) throw new Error(exceptionDetails.exception?.description || exceptionDetails.text)
      return result.value
    }
    if (mode === 'shot') {
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
      writeFileSync(arg2, Buffer.from(data, 'base64'))
      console.log(`截图 → ${arg2}`)
    } else if (mode === 'eval') {
      const value = await evaluate(arg2)
      console.log(JSON.stringify({ url: await evaluate('location.href'), value }, null, 1))
    } else {
      console.log(await evaluate(mode === 'html' ? 'document.documentElement.outerHTML' : 'document.body.innerText'))
    }
    cdp.ws.close()
  } finally {
    await fetch(`${base}/json/close/${target.id}`).catch(() => {})
  }
}

main().catch(e => { console.error(e.message); process.exit(1) })
