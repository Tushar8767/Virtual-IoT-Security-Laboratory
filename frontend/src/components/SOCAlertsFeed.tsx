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
    const interval = setInterval(fetchAlerts, 3000);
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

  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL' && a.status === 'ACTIVE').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH' && a.status === 'ACTIVE').length;
  const resolvedCount = alerts.filter((a) => a.status === 'RESOLVED').length;

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: '#ef4444' };
      case 'HIGH':
        return { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', border: '#f97316' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: '#f59e0b' };
      default:
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: '#10b981' };
    }
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      {/* SOC Triage Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#ef4444' }}>🚨</span> Security Operations Center (SOC) Alert Triage
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Real-time heuristic & behavioral detections with autonomous SOAR response capabilities
          </p>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          {(['ALL', 'ACTIVE', 'RESOLVED'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              style={{
                padding: '6px 14px',
                fontSize: '11px',
                borderRadius: '6px',
                border: filter === tab ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
                background: filter === tab ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-card)',
                color: filter === tab ? '#38bdf8' : 'var(--color-text-secondary)',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {tab === 'ALL' ? 'ALL INCIDENTS' : tab}
            </button>
          ))}
        </div>
      </div>

      {/* Mini Threat Metric Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        marginBottom: '20px',
      }}>
        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '12px' }}>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Critical Threats</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: criticalCount > 0 ? '#ef4444' : '#10b981', marginTop: '2px' }}>
            {criticalCount}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '12px' }}>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>High / Medium Alerts</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: highCount > 0 ? '#f59e0b' : 'var(--color-text-primary)', marginTop: '2px' }}>
            {highCount}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '12px' }}>
          <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Triaged & Resolved</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#10b981', marginTop: '2px' }}>
            {resolvedCount}
          </div>
        </div>
      </div>

      {/* Alert Feed List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading SOC incident queue...
        </div>
      ) : alerts.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '48px 24px',
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--border-radius-lg)',
          color: 'var(--color-text-secondary)',
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🛡️</div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#10b981' }}>ZERO UNRESOLVED SECURITY INCIDENTS</div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '6px' }}>
            The detection engine has not reported any active anomalous telemetry or unauthorized actions.
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
                  background: 'var(--color-bg-card)',
                  border: `1px solid ${isCritical ? '#ef4444' : 'var(--color-border)'}`,
                  borderRadius: 'var(--border-radius-lg)',
                  padding: '16px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  boxShadow: isCritical ? '0 0 16px rgba(239, 68, 68, 0.15)' : 'none',
                  flexWrap: 'wrap',
                  gap: '14px',
                }}
              >
                <div style={{ flex: 1, minWidth: '300px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: sev.bg,
                      color: sev.text,
                      border: `1px solid ${sev.border}`,
                      letterSpacing: '0.04em',
                    }}>
                      {al.severity}
                    </span>

                    <span style={{ fontFamily: 'monospace', fontSize: '13px', fontWeight: 800, color: '#fff' }}>
                      {al.rule_name}
                    </span>

                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: al.status === 'ACTIVE' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
                      color: al.status === 'ACTIVE' ? '#ef4444' : '#10b981',
                      border: `1px solid ${al.status === 'ACTIVE' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      fontWeight: 700,
                    }}>
                      {al.status}
                    </span>
                  </div>

                  <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '10px', lineHeight: 1.4 }}>
                    {al.message}
                  </p>

                  <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--color-text-secondary)', fontFamily: 'monospace', flexWrap: 'wrap' }}>
                    <span>Target Node: <strong style={{ color: '#fff' }}>{al.device_id}</strong></span>
                    {al.correlation_id && <span>Corr ID: <strong style={{ color: 'var(--color-accent-cyan)' }}>{al.correlation_id}</strong></span>}
                    <span>Timestamp: {new Date(al.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* SOAR Action Buttons */}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  {al.status === 'ACTIVE' && (
                    <button
                      onClick={() => onQuarantineDevice(al.device_id)}
                      style={{
                        padding: '8px 14px',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid #ef4444',
                        color: '#ef4444',
                        borderRadius: 'var(--border-radius)',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      🚨 QUARANTINE NODE
                    </button>
                  )}

                  {al.status === 'ACTIVE' ? (
                    <button
                      onClick={() => updateAlertStatus(al.alert_id, 'RESOLVED')}
                      style={{
                        padding: '8px 14px',
                        background: 'var(--color-bg-base)',
                        border: '1px solid var(--color-border)',
                        color: '#10b981',
                        borderRadius: 'var(--border-radius)',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      ✓ Mark Resolved
                    </button>
                  ) : (
                    <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      ✓ CASE CLOSED
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
