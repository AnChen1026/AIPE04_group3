import { onBeforeUnmount, ref } from 'vue'

// 節拍器：用 Web Audio 排程「嗒」聲，每小節第一拍比較高。
// 用 setInterval 每 25 毫秒往後排 0.1 秒內要響的拍子，計時器偶爾慢一點也不會亂拍。
const LOOKAHEAD_MS = 25
const SCHEDULE_AHEAD_SECONDS = 0.1
const CLICK_SECONDS = 0.03

export function useMetronome() {
  const running = ref(false)
  // 正在響的是這小節第幾拍（0 開始），畫面用來閃燈
  const beat = ref(0)
  // 每一拍亮 0.1 秒
  const flash = ref(false)
  let context: AudioContext | null = null
  let timer = 0
  let nextTime = 0
  let count = 0
  let bpm = 120
  let beatsPerBar = 4

  function click(time: number, accent: boolean) {
    const oscillator = context!.createOscillator()
    const gain = context!.createGain()
    oscillator.frequency.value = accent ? 1600 : 1000
    gain.gain.setValueAtTime(0.0001, time)
    gain.gain.exponentialRampToValueAtTime(0.6, time + 0.002)
    gain.gain.exponentialRampToValueAtTime(0.0001, time + CLICK_SECONDS)
    oscillator.connect(gain).connect(context!.destination)
    oscillator.start(time)
    oscillator.stop(time + CLICK_SECONDS + 0.01)
    const shown = count % beatsPerBar
    window.setTimeout(() => {
      beat.value = shown
      flash.value = true
      window.setTimeout(() => (flash.value = false), 100)
    }, Math.max(0, (time - context!.currentTime) * 1000))
  }

  function schedule() {
    while (nextTime < context!.currentTime + SCHEDULE_AHEAD_SECONDS) {
      click(nextTime, count % beatsPerBar === 0)
      nextTime += 60 / bpm
      count += 1
    }
  }

  async function start(tempo: number, beats = 4) {
    stop()
    bpm = tempo
    beatsPerBar = Math.max(1, beats)
    context = context ?? new AudioContext()
    await context.resume()
    count = 0
    nextTime = context.currentTime + 0.05
    schedule()
    timer = window.setInterval(schedule, LOOKAHEAD_MS)
    running.value = true
  }

  function stop() {
    window.clearInterval(timer)
    running.value = false
    beat.value = 0
  }

  onBeforeUnmount(() => {
    stop()
    context?.close()
  })

  return { running, beat, flash, start, stop }
}
