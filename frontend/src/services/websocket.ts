/**
 * WebSocket Service — Phase 0
 *
 * Manages WebSocket connection to the backend real-time feed.
 * Full integration in Phase 5.
 */

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws';

type EventHandler = (event: LabEvent) => void;

export interface LabEvent {
  event_type: string;
  timestamp: string;
  [key: string]: unknown;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 3000;
  private isIntentionallyClosed = false;

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.isIntentionallyClosed = false;
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('[WS] Connected to IoT Security Lab');
      this.reconnectDelay = 3000;
    };

    this.ws.onmessage = (event) => {
      try {
        const data: LabEvent = JSON.parse(event.data as string);
        this.dispatch(data.event_type, data);
        this.dispatch('*', data); // wildcard handlers
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onerror = () => {
      console.warn('[WS] Connection error');
    };

    this.ws.onclose = () => {
      if (!this.isIntentionallyClosed) {
        console.log(`[WS] Disconnected. Reconnecting in ${this.reconnectDelay}ms...`);
        this.reconnectTimer = setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
          this.connect();
        }, this.reconnectDelay);
      }
    };
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  on(eventType: string, handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
    return () => this.handlers.get(eventType)?.delete(handler);
  }

  private dispatch(eventType: string, event: LabEvent): void {
    this.handlers.get(eventType)?.forEach((handler) => handler(event));
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
