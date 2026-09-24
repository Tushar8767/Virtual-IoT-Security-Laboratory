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
import { API_BASE } from '../config';

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

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', label: 'High Severity' };
      case 'HIGH':
        return { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', label: 'Medium-High' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', label: 'Medium' };
      default:
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', label: 'Low' };
    }
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🚨 Security Alerts & Warnings
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Warnings and suspicious activities detected across your connected devices.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          {(['ALL', 'ACTIVE', 'RESOLVED'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              style={{
                padding: '6px 14px',
                fontSize: '12px',
                borderRadius: '6px',
                border: filter === tab ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
                background: filter === tab ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-card)',
                color: filter === tab ? '#38bdf8' : 'var(--color-text-secondary)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {tab === 'ALL' ? 'All Alerts' : tab === 'ACTIVE' ? 'Active' : 'Resolved'}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Counts */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        marginBottom: '20px',
      }}>
        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '14px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Urgent Alerts</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: criticalCount > 0 ? '#ef4444' : '#10b981', marginTop: '2px' }}>
            {criticalCount}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '14px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Standard Alerts</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: highCount > 0 ? '#f59e0b' : 'var(--color-text-primary)', marginTop: '2px' }}>
            {highCount}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '14px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Resolved Cases</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#10b981', marginTop: '2px' }}>
            {resolvedCount}
          </div>
        </div>
      </div>

      {/* Alerts Feed */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading alerts...
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
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#10b981' }}>No Security Alerts</div>
          <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '6px' }}>
            All devices are behaving normally with no suspicious activity detected.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {alerts.map((al) => {
            const sev = getSeverityBadge(al.severity);
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
                  flexWrap: 'wrap',
                  gap: '14px',
                }}
              >
                <div style={{ flex: 1, minWidth: '280px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: sev.bg,
                      color: sev.text,
                    }}>
                      {sev.label}
                    </span>

                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>
                      {al.rule_name.replace(/_/g, ' ')}
                    </span>

                    <span style={{
                      fontSize: '11px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: al.status === 'ACTIVE' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
                      color: al.status === 'ACTIVE' ? '#ef4444' : '#10b981',
                      fontWeight: 600,
                    }}>
                      {al.status === 'ACTIVE' ? 'Active' : 'Resolved'}
                    </span>
                  </div>

                  <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                    {al.message}
                  </p>

                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--color-text-secondary)', flexWrap: 'wrap' }}>
                    <span>Device: <strong style={{ color: '#fff' }}>{al.device_id}</strong></span>
                    <span>Time: {new Date(al.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Actions */}
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
                        fontWeight: 600,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      🚫 Block Device
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
                        fontWeight: 500,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      ✓ Mark as Resolved
                    </button>
                  ) : (
                    <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>
                      ✓ Resolved
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
