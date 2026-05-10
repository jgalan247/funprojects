import { ref } from 'vue'

export interface Reading {
  sensor_id: string
  device_id: string
  metric: string
  value: number
  unit: string
  quality: string
  ts: string
  received_at: string
}

interface SnapshotMessage {
  type: 'snapshot'
  readings: Reading[]
}

interface ReadingMessage {
  type: 'reading'
  reading: Reading
}

type Message = SnapshotMessage | ReadingMessage

/* Singleton — every view that calls useReadings() shares the same Map and
   WebSocket. The connection is opened on first call and lives for the
   lifetime of the page (the kiosk runs forever). */

const readings = ref(new Map<string, Reading>())
const connected = ref(false)

let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let started = false

const RECONNECT_MS = 2000

function connect(): void {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${proto}://${window.location.host}/ws/sensors`
  socket = new WebSocket(url)

  socket.onopen = () => {
    connected.value = true
  }

  socket.onclose = () => {
    connected.value = false
    socket = null
    reconnectTimer = setTimeout(connect, RECONNECT_MS)
  }

  socket.onerror = () => {
    /* close handler will reconnect */
  }

  socket.onmessage = (event: MessageEvent<string>) => {
    let msg: Message
    try {
      msg = JSON.parse(event.data) as Message
    } catch {
      return
    }
    if (msg.type === 'snapshot') {
      const next = new Map<string, Reading>()
      for (const r of msg.readings) next.set(r.sensor_id, r)
      readings.value = next
    } else if (msg.type === 'reading') {
      const next = new Map(readings.value)
      next.set(msg.reading.sensor_id, msg.reading)
      readings.value = next
    }
  }
}

export function useReadings() {
  if (!started) {
    started = true
    connect()
  }
  return { readings, connected }
}

/** Cancel pending reconnects (for unit tests). Production never calls this. */
export function _resetForTests(): void {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (socket) socket.close()
  started = false
  connected.value = false
  readings.value = new Map()
}
