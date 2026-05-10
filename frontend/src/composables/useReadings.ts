import { ref, onMounted, onUnmounted, type Ref } from 'vue'

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

export interface UseReadings {
  readings: Ref<Map<string, Reading>>
  connected: Ref<boolean>
}

/**
 * Subscribes to /ws/sensors and exposes a reactive map of the latest reading
 * per sensor. Auto-reconnects with a fixed back-off if the socket drops.
 */
export function useReadings(reconnectMs = 2000): UseReadings {
  const readings = ref(new Map<string, Reading>())
  const connected = ref(false)

  let socket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  function connect(): void {
    if (stopped) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/ws/sensors`
    socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value = true
    }

    socket.onclose = () => {
      connected.value = false
      socket = null
      if (!stopped) {
        reconnectTimer = setTimeout(connect, reconnectMs)
      }
    }

    socket.onerror = () => {
      // No-op — the close handler will arrange the reconnect.
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

  onMounted(connect)
  onUnmounted(() => {
    stopped = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (socket) socket.close()
  })

  return { readings, connected }
}
