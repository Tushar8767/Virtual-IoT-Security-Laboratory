import React, { useState, useEffect } from 'react';

export interface SecurityAlert {
  alert_id: string;
  device_id: string;
  rule_name: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'ACTIVE' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';
  message: string;
  correlation_id?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface SOCAlertsFeedProps {
  onQuarantineDevice: (deviceId: string) => void;
  refreshTrigger?: number;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const SOCAlertsFeed: React.FC<SOCAlertsFeedProps> = ({
  onQuarantineDevice,
  refreshTrigger = 0,
}) => {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'RESOLVED'>('ALL');
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const url = filter === 'ALL'
        ? `${API_BASE}/api/security/alerts?limit=50`
        : `${API_BASE}/api/security/alerts?status=${filter}&limit=50`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('Failed to fetch security alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 4000);
    return () => clearInterval(interval);
  }, [filter, refreshTrigger]);

  const updateAlertStatus = async (alertId: string, newStatus: string) => {
    try {
      await fetch(`${API_BASE}/api/security/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: newStatus }),
      });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to update alert', err);
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(248, 81, 73, 0.15)', text: 'var(--color-severity-critical)', border: 'var(--color-severity-critical)' };
      case 'HIGH':
        return { bg: 'rgba(240, 136, 62, 0.15)', text: 'var(--color-severity-high)', border: 'var(--color-severity-high)' };
      case 'MEDIUM':
        return { bg: 'rgba(210, 153, 34, 0.15)', text: 'var(--color-severity-medium)', border: 'var(--color-severity-medium)' };
      default:
        return { bg: 'rgba(63, 185, 80, 0.15)', text: 'var(--color-severity-low)', border: 'var(--color-severity-low)' };
    }
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🚨 Security Operations Center (SOC) Alerts
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Real-time detections from anomaly detection, rate-limiting, and cryptographic verification engines.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {(['ALL', 'ACTIVE', 'RESOLVED'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              style={{
                padding: '6px 12px',
                fontSize: '12px',
                borderRadius: 'var(--border-radius)',
                border: filter === tab ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
                background: filter === tab ? 'rgba(47, 129, 247, 0.15)' : 'var(--color-bg-secondary)',
                color: filter === tab ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
          Loading security alerts...
        </div>
      ) : alerts.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--border-radius)',
          color: 'var(--color-text-secondary)',
        }}>
          🛡️ No security alerts detected. Laboratory operations are nominal.
          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '6px' }}>
            Trigger an attack from the Attack Simulator to test alerting & quarantine workflows.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {alerts.map((al) => {
            const sev = getSeverityStyle(al.severity);
            const isCritical = al.severity === 'CRITICAL';

            return (
              <div
                key={al.alert_id}
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: `1px solid ${isCritical ? 'var(--color-severity-critical)' : 'var(--color-border)'}`,
                  borderRadius: 'var(--border-radius)',
                  padding: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  boxShadow: isCritical ? '0 0 10px rgba(248, 81, 73, 0.15)' : 'none',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: sev.bg,
                      color: sev.text,
                      border: `1px solid ${sev.border}`,
                    }}>
                      {al.severity}
                    </span>
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      {al.rule_name}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: al.status === 'ACTIVE' ? 'rgba(248, 81, 73, 0.15)' : 'rgba(63, 185, 80, 0.15)',
                      color: al.status === 'ACTIVE' ? 'var(--color-severity-critical)' : 'var(--color-status-online)',
                      fontWeight: 600,
                    }}>
                      {al.status}
                    </span>
                  </div>

                  <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                    {al.message}
                  </p>

                  <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                    <span>Target Node: <strong>{al.device_id}</strong></span>
                    {al.correlation_id && <span>Correlation ID: <strong>{al.correlation_id}</strong></span>}
                    <span>Timestamp: {new Date(al.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', flexDirection: 'column', alignItems: 'flex-end' }}>
                  {al.status === 'ACTIVE' && (
                    <button
                      onClick={() => onQuarantineDevice(al.device_id)}
                      style={{
                        padding: '6px 12px',
                        background: 'rgba(248, 81, 73, 0.2)',
                        border: '1px solid var(--color-severity-critical)',
                        color: 'var(--color-severity-critical)',
                        borderRadius: 'var(--border-radius)',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      🚨 Quarantine Node
                    </button>
                  )}
                  {al.status === 'ACTIVE' ? (
                    <button
                      onClick={() => updateAlertStatus(al.alert_id, 'RESOLVED')}
                      style={{
                        padding: '4px 10px',
                        background: 'transparent',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-status-online)',
                        borderRadius: 'var(--border-radius)',
                        fontSize: '11px',
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      ✓ Mark Resolved
                    </button>
                  ) : (
                    <span style={{ fontSize: '11px', color: 'var(--color-status-online)', fontWeight: 600 }}>
                      ✓ Case Closed
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
