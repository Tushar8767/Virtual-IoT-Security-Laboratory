import React, { useState, useEffect } from 'react';
import { DeviceItem } from './DeviceList';

interface ForensicTimelineProps {
  devices: DeviceItem[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const ForensicTimeline: React.FC<ForensicTimelineProps> = ({ devices }) => {
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>(devices[0]?.device_id || 'PY-TEMP-001');
  const [profile, setProfile] = useState<any | null>(null);
  const [correlationIdInput, setCorrelationIdInput] = useState<string>('');
  const [correlationTimeline, setCorrelationTimeline] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'device' | 'correlation'>('device');

  const fetchDeviceProfile = async (devId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/investigation/device/${devId}`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (err) {
      console.error('Failed to load profile', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCorrelationTimeline = async (corrId: string) => {
    if (!corrId.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/investigation/timeline/${encodeURIComponent(corrId.trim())}`);
      if (res.ok) {
        const data = await res.json();
        setCorrelationTimeline(data);
      }
    } catch (err) {
      console.error('Failed to load correlation timeline', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mode === 'device' && selectedDeviceId) {
      fetchDeviceProfile(selectedDeviceId);
    }
  }, [selectedDeviceId, mode]);

  const exportDossierJSON = () => {
    const dataToExport = mode === 'device' ? profile : correlationTimeline;
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incident_report_${mode === 'device' ? selectedDeviceId : correlationIdInput}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🔍 Incident Investigation & History
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Look at the complete history of events for any device to understand what happened.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setMode('device')}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: mode === 'device' ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
              background: mode === 'device' ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-card)',
              color: mode === 'device' ? '#38bdf8' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            By Device
          </button>
          <button
            onClick={() => setMode('correlation')}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: mode === 'correlation' ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
              background: mode === 'correlation' ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-card)',
              color: mode === 'correlation' ? '#38bdf8' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            By Incident ID
          </button>
          <button
            onClick={exportDossierJSON}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg-card)',
              color: 'var(--color-text-primary)',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            💾 Download Report (JSON)
          </button>
        </div>
      </div>

      {/* Control Bar */}
      {mode === 'device' ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--color-bg-card)',
          padding: '12px 16px',
          borderRadius: 'var(--border-radius)',
          marginBottom: '20px',
          border: '1px solid var(--color-border)',
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Select Device:
          </span>
          <select
            value={selectedDeviceId}
            onChange={(e) => setSelectedDeviceId(e.target.value)}
            style={{
              background: 'var(--color-bg-base)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
              padding: '6px 12px',
              borderRadius: 'var(--border-radius)',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            {devices.map((d) => (
              <option key={d.device_id} value={d.device_id}>
                {d.device_name} ({d.device_id})
              </option>
            ))}
          </select>
          <button
            onClick={() => fetchDeviceProfile(selectedDeviceId)}
            style={{
              padding: '6px 14px',
              background: 'var(--color-accent-blue)',
              border: 'none',
              borderRadius: 'var(--border-radius)',
              color: '#070a11',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Refresh History
          </button>
        </div>
      ) : (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--color-bg-card)',
          padding: '12px 16px',
          borderRadius: 'var(--border-radius)',
          marginBottom: '20px',
          border: '1px solid var(--color-border)',
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Enter Incident ID:
          </span>
          <input
            type="text"
            placeholder="e.g. corr-scenario-d-12345"
            value={correlationIdInput}
            onChange={(e) => setCorrelationIdInput(e.target.value)}
            style={{
              background: 'var(--color-bg-base)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
              padding: '6px 12px',
              borderRadius: 'var(--border-radius)',
              fontSize: '13px',
              fontFamily: 'monospace',
              width: '320px',
            }}
          />
          <button
            onClick={() => fetchCorrelationTimeline(correlationIdInput)}
            style={{
              padding: '6px 14px',
              background: 'var(--color-accent-blue)',
              border: 'none',
              borderRadius: 'var(--border-radius)',
              color: '#070a11',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Find Events
          </button>
        </div>
      )}

      {/* Stats Summary */}
      {mode === 'device' && profile && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}>
          {[
            { label: 'Security Events', value: profile.total_security_events, color: '#f59e0b' },
            { label: 'Alerts Triggered', value: profile.total_alerts, color: '#ef4444' },
            { label: 'Data Packets Saved', value: (profile.recent_telemetry || []).length, color: '#38bdf8' },
            { label: 'Audit Records', value: (profile.audit_trail || []).length, color: '#10b981' },
          ].map((m, i) => (
            <div key={i} style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '14px' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>{m.label}</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: m.color, marginTop: '2px' }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Output */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading incident history...
        </div>
      ) : mode === 'correlation' ? (
        correlationTimeline ? (
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px', color: '#38bdf8' }}>
              Timeline for Incident: {correlationTimeline.total_correlated_items} event(s) found
            </div>
            {correlationTimeline.timeline.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', background: 'var(--color-bg-card)', borderRadius: 'var(--border-radius)' }}>
                No events found matching this ID.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {correlationTimeline.timeline.map((item: any, idx: number) => (
                  <div key={idx} style={{
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderLeft: `4px solid ${item.type === 'SECURITY_ALERT' ? '#ef4444' : item.type === 'SECURITY_EVENT' ? '#f59e0b' : '#38bdf8'}`,
                    borderRadius: 'var(--border-radius)',
                    padding: '12px 16px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                        Step #{idx + 1} · {item.type.replace(/_/g, ' ')}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '--'}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>
                      {item.summary}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: '36px', textAlign: 'center', background: 'var(--color-bg-card)', borderRadius: 'var(--border-radius)', color: 'var(--color-text-secondary)' }}>
            Enter an Incident ID above to see how the security event unfolded.
          </div>
        )
      ) : profile ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '10px', color: '#ef4444' }}>
              Security Alerts for {selectedDeviceId} ({profile.alerts?.length || 0})
            </h3>
            {profile.alerts?.length === 0 ? (
              <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', background: 'var(--color-bg-card)', padding: '14px', borderRadius: '6px' }}>
                No active security alerts for this device.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {profile.alerts.map((al: any) => (
                  <div key={al.alert_id} style={{ background: 'var(--color-bg-card)', padding: '14px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600 }}>
                      <span style={{ color: '#ef4444' }}>{al.rule_name.replace(/_/g, ' ')}</span>
                      <span>{new Date(al.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginTop: '4px' }}>{al.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '10px', color: '#38bdf8' }}>
              Recent Activity History ({profile.audit_trail?.length || 0})
            </h3>
            <div style={{ background: 'var(--color-bg-card)', padding: '14px', borderRadius: '6px', border: '1px solid var(--color-border)', maxHeight: '220px', overflowY: 'auto' }}>
              {profile.audit_trail?.length === 0 ? (
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>No actions recorded yet for this device.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {profile.audit_trail.map((ad: any, i: number) => (
                    <div key={i} style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>{ad.action.replace(/_/g, ' ')}</strong> ({ad.result === 'SUCCESS' ? 'Success' : 'Failed'})</span>
                      <span style={{ color: 'var(--color-text-muted)' }}>{new Date(ad.timestamp).toLocaleTimeString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
