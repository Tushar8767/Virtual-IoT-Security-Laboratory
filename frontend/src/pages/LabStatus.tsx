/**
 * Phase 0 — Lab Status Dashboard Page
 *
 * Shows the current health state of the lab infrastructure.
 * Full dashboard implemented in Phase 5.
 */

import { useState, useEffect } from 'react';
import { getHealth, getLabStatus } from '../services/api';

interface ServiceStatus {
  connected: boolean;
  database?: string;
  broker_host?: string;
  broker_port?: number;
}

interface HealthData {
  status: string;
  version: string;
  services: {
    database: ServiceStatus;
    mqtt: ServiceStatus;
  };
}

function ServiceIndicator({ name, connected }: { name: string; connected: boolean }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '12px 16px',
      background: 'var(--color-bg-secondary)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--border-radius)',
      marginBottom: '8px',
    }}>
      <span
        className={`status-dot ${connected ? 'online' : 'offline'}`}
        style={{ width: '10px', height: '10px', flexShrink: 0 }}
      />
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{name}</span>
      <span style={{
        marginLeft: 'auto',
        fontSize: 'var(--font-size-sm)',
        color: connected ? 'var(--color-status-online)' : 'var(--color-status-offline)',
        fontWeight: 600,
      }}>
        {connected ? 'CONNECTED' : 'DISCONNECTED'}
      </span>
    </div>
  );
}

const PHASES = [
  { phase: '0', name: 'Project Foundation', status: 'complete', desc: 'Repo, stack, DB, MQTT, health checks' },
  { phase: '1', name: 'Device Domain', status: 'pending', desc: 'Device model, registry, state machine' },
  { phase: '2', name: 'Device Simulator', status: 'pending', desc: 'Virtual devices, telemetry, heartbeat' },
  { phase: '3', name: 'MQTT Communication', status: 'pending', desc: 'Broker, topics, validation' },
  { phase: '4', name: 'Telemetry Pipeline', status: 'pending', desc: 'MQTT → processing → DB → WebSocket' },
  { phase: '5', name: 'Dashboard', status: 'pending', desc: 'React UI, device list, live monitoring' },
  { phase: '6', name: 'Auth & Authorization', status: 'pending', desc: 'Device credentials, capabilities' },
  { phase: '7', name: 'Security Engine', status: 'pending', desc: 'Detection rules, events, alerts' },
  { phase: '8', name: 'Attack Simulation', status: 'pending', desc: '7 security scenarios' },
  { phase: '9', name: 'Investigation', status: 'pending', desc: 'Event correlation, timelines' },
  { phase: '10', name: 'Audit Logging', status: 'pending', desc: 'Immutable audit trail' },
];

export function LabStatusPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        // Fetch both but only use health for display in Phase 0
        const [h] = await Promise.all([getHealth(), getLabStatus()]);
        setHealth(h as HealthData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    }

    void fetchStatus();
    const interval = setInterval(() => { void fetchStatus(); }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '32px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <span style={{ fontSize: '28px' }}>🔬</span>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Virtual IoT Security Laboratory
          </h1>
        </div>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Phase 0 — Project Foundation · Infrastructure Status
        </p>
      </div>

      {loading && (
        <div style={{ color: 'var(--color-text-secondary)', padding: '20px 0' }}>
          Connecting to backend...
        </div>
      )}

      {error && (
        <div style={{
          padding: '16px',
          background: 'rgba(248, 81, 73, 0.1)',
          border: '1px solid var(--color-severity-critical)',
          borderRadius: 'var(--border-radius)',
          color: 'var(--color-severity-critical)',
          marginBottom: '24px',
        }}>
          <strong>Backend Unreachable</strong>
          <p style={{ marginTop: '4px', fontSize: 'var(--font-size-sm)' }}>{error}</p>
          <p style={{ marginTop: '8px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Start the backend: <code>python scripts/start_lab.py</code>
          </p>
        </div>
      )}

      {health && (
        <div style={{
          padding: '16px 20px',
          background: health.status === 'healthy' ? 'rgba(63, 185, 80, 0.08)' : 'rgba(210, 153, 34, 0.08)',
          border: `1px solid ${health.status === 'healthy' ? 'var(--color-severity-low)' : 'var(--color-severity-medium)'}`,
          borderRadius: 'var(--border-radius)',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <span style={{ fontSize: '20px' }}>{health.status === 'healthy' ? '✅' : '⚠️'}</span>
          <div>
            <div style={{
              fontWeight: 700,
              color: health.status === 'healthy' ? 'var(--color-severity-low)' : 'var(--color-severity-medium)',
              textTransform: 'uppercase',
              fontSize: 'var(--font-size-sm)',
              letterSpacing: '0.5px',
            }}>
              {health.status === 'healthy' ? 'All Systems Operational' : 'Degraded — Some services unavailable'}
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              Version {health.version}
            </div>
          </div>
        </div>
      )}

      {health && (
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: '12px', color: 'var(--color-text-primary)' }}>
            Infrastructure Services
          </h2>
          <ServiceIndicator name="MongoDB Database" connected={health.services.database?.connected ?? false} />
          <ServiceIndicator name="MQTT Broker (Mosquitto)" connected={health.services.mqtt?.connected ?? false} />
          <ServiceIndicator name="Backend API (FastAPI)" connected={true} />
        </div>
      )}

      <div style={{
        padding: '20px',
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--border-radius)',
      }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: '16px', color: 'var(--color-text-primary)' }}>
          Implementation Phases
        </h2>
        {PHASES.map(({ phase, name, status, desc }) => (
          <div key={phase} style={{
            display: 'flex',
            gap: '12px',
            paddingBottom: '10px',
            marginBottom: '10px',
            borderBottom: '1px solid var(--color-border-subtle)',
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: status === 'complete' ? 'var(--color-severity-low)' : 'var(--color-bg-card)',
              border: `2px solid ${status === 'complete' ? 'var(--color-severity-low)' : 'var(--color-border)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 700,
              color: status === 'complete' ? '#000' : 'var(--color-text-muted)',
              flexShrink: 0,
            }}>
              {status === 'complete' ? '✓' : phase}
            </div>
            <div>
              <div style={{ fontWeight: 600, color: status === 'complete' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                Phase {phase} — {name}
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
