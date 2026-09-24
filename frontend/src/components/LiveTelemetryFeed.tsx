import React from 'react';

export interface FeedEvent {
  id: string;
  type: string;
  timestamp: string;
  device_id?: string;
  data: Record<string, unknown>;
}

interface LiveTelemetryFeedProps {
  events: FeedEvent[];
  wsConnected: boolean;
}

export const LiveTelemetryFeed: React.FC<LiveTelemetryFeedProps> = ({ events, wsConnected }) => {
  return (
    <div style={{
      background: 'var(--color-bg-secondary)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--border-radius)',
      padding: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
          📡 Live Telemetry & Event Stream
        </h3>
        <span style={{
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          color: wsConnected ? 'var(--color-status-online)' : 'var(--color-status-offline)',
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: wsConnected ? 'var(--color-status-online)' : 'var(--color-status-offline)',
          }} />
          {wsConnected ? 'WebSocket LIVE' : 'WebSocket Disconnected'}
        </span>
      </div>

      <div style={{
        height: '240px',
        overflowY: 'auto',
        fontFamily: 'monospace',
        fontSize: '12px',
        background: '#0a0d12',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: '4px',
        padding: '8px',
      }}>
        {events.length === 0 ? (
          <div style={{ color: 'var(--color-text-muted)', padding: '8px' }}>
            Listening for live telemetry, heartbeats, and security events...
          </div>
        ) : (
          events.map((e) => (
            <div key={e.id} style={{ marginBottom: '6px', lineHeight: '1.4' }}>
              <span style={{ color: 'var(--color-text-muted)', marginRight: '8px' }}>
                {new Date(e.timestamp).toLocaleTimeString()}
              </span>
              <span style={{
                color: e.type.includes('alert') ? 'var(--color-severity-critical)' : '#58a6ff',
                fontWeight: 600,
                marginRight: '8px',
              }}>
                [{e.type.toUpperCase()}]
              </span>
              {e.device_id && (
                <span style={{ color: '#7ee787', marginRight: '8px' }}>
                  {e.device_id}:
                </span>
              )}
              <span style={{ color: 'var(--color-text-secondary)' }}>
                {JSON.stringify(e.data)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};