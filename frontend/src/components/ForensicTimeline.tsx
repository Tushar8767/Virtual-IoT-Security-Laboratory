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
      console.error('Failed to load forensic profile', err);
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
    a.download = `forensic_dossier_${mode === 'device' ? selectedDeviceId : correlationIdInput}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🔍 Cyber Forensic Investigation & Incident Timeline
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Reconstruct end-to-end attack chains and correlate security events across telemetry, auth, and audit logs.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setMode('device')}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: mode === 'device' ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
              background: mode === 'device' ? 'rgba(47, 129, 247, 0.15)' : 'var(--color-bg-secondary)',
              color: mode === 'device' ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            By Device Dossier
          </button>
          <button
            onClick={() => setMode('correlation')}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: mode === 'correlation' ? '1px solid var(--color-accent-blue)' : '1px solid var(--color-border)',
              background: mode === 'correlation' ? 'rgba(47, 129, 247, 0.15)' : 'var(--color-bg-secondary)',
              color: mode === 'correlation' ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            By Correlation ID
          </button>
          <button
            onClick={exportDossierJSON}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              borderRadius: 'var(--border-radius)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg-secondary)',
              color: 'var(--color-text-primary)',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            💾 Export JSON Dossier
          </button>
        </div>
      </div>

      {/* Control Bar */}
      {mode === 'device' ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--color-bg-secondary)',
          padding: '12px 16px',
          borderRadius: 'var(--border-radius)',
          marginBottom: '20px',
          border: '1px solid var(--color-border)',
        }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Select Target Device:
          </span>
          <select
            value={selectedDeviceId}
            onChange={(e) => setSelectedDeviceId(e.target.value)}
            style={{
              background: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
              padding: '6px 12px',
              borderRadius: 'var(--border-radius)',
              fontSize: '13px',
              fontFamily: 'monospace',
              cursor: 'pointer',
            }}
          >
            {devices.map((d) => (
              <option key={d.device_id} value={d.device_id}>
                {d.device_id} — {d.device_name}
              </option>
            ))}
          </select>
          <button
            onClick={() => fetchDeviceProfile(selectedDeviceId)}
            style={{
              padding: '6px 12px',
              background: 'var(--color-accent-blue)',
              border: 'none',
              borderRadius: 'var(--border-radius)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Refresh Profile
          </button>
        </div>
      ) : (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--color-bg-secondary)',
          padding: '12px 16px',
          borderRadius: 'var(--border-radius)',
          marginBottom: '20px',
          border: '1px solid var(--color-border)',
        }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Correlation ID:
          </span>
          <input
            type="text"
            placeholder="e.g. corr-scenario-d-12345"
            value={correlationIdInput}
            onChange={(e) => setCorrelationIdInput(e.target.value)}
            style={{
              background: 'var(--color-bg-primary)',
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
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Reconstruct Timeline
          </button>
        </div>
      )}

      {/* Forensic Metrics */}
      {mode === 'device' && profile && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}>
          {[
            { label: 'Security Events', value: profile.total_security_events, color: 'var(--color-severity-high)' },
            { label: 'Total Alerts', value: profile.total_alerts, color: 'var(--color-severity-critical)' },
            { label: 'Telemetry Packets', value: (profile.recent_telemetry || []).length, color: 'var(--color-accent-teal)' },
            { label: 'Audit Trail Entries', value: (profile.audit_trail || []).length, color: 'var(--color-accent-blue)' },
          ].map((m, i) => (
            <div key={i} style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', padding: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>{m.label}</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: m.color, marginTop: '4px' }}>{m.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Timeline Output */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Reconstructing forensic timeline...
        </div>
      ) : mode === 'correlation' ? (
        correlationTimeline ? (
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px', color: 'var(--color-accent-teal)' }}>
              Correlated Incident Flow: {correlationTimeline.total_correlated_items} sequential event(s)
            </div>
            {correlationTimeline.timeline.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', background: 'var(--color-bg-secondary)', borderRadius: 'var(--border-radius)' }}>
                No events matched correlation ID "{correlationTimeline.correlation_id}".
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {correlationTimeline.timeline.map((item: any, idx: number) => (
                  <div key={idx} style={{
                    background: 'var(--color-bg-secondary)',
                    border: '1px solid var(--color-border)',
                    borderLeft: `4px solid ${item.type === 'SECURITY_ALERT' ? 'var(--color-severity-critical)' : item.type === 'SECURITY_EVENT' ? 'var(--color-severity-high)' : 'var(--color-accent-blue)'}`,
                    borderRadius: 'var(--border-radius)',
                    padding: '12px 16px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                        STEP #{idx + 1} · {item.type}
                      </span>
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '--'}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {item.summary}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontFamily: 'monospace', marginTop: '6px' }}>
                      <pre style={{ overflowX: 'auto', background: 'var(--color-bg-primary)', padding: '8px', borderRadius: '4px' }}>
                        {JSON.stringify(item.details, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', background: 'var(--color-bg-secondary)', borderRadius: 'var(--border-radius)', color: 'var(--color-text-secondary)' }}>
            Enter a Correlation ID above to reconstruct the complete attack narrative.
          </div>
        )
      ) : profile ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--color-severity-critical)' }}>
              Associated Security Alerts ({profile.alerts?.length || 0})
            </h3>
            {profile.alerts?.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', background: 'var(--color-bg-secondary)', padding: '12px', borderRadius: '4px' }}>
                No active security alerts linked to {selectedDeviceId}.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {profile.alerts.map((al: any) => (
                  <div key={al.alert_id} style={{ background: 'var(--color-bg-secondary)', padding: '12px', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600 }}>
                      <span style={{ color: 'var(--color-severity-critical)' }}>{al.rule_name}</span>
                      <span style={{ fontFamily: 'monospace' }}>{new Date(al.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--color-text-primary)', marginTop: '4px' }}>{al.message}</p>
                    {al.correlation_id && (
                      <button
                        onClick={() => {
                          setMode('correlation');
                          setCorrelationIdInput(al.correlation_id);
                          fetchCorrelationTimeline(al.correlation_id);
                        }}
                        style={{ marginTop: '8px', fontSize: '11px', background: 'none', border: 'none', color: 'var(--color-accent-blue)', cursor: 'pointer', padding: 0 }}
                      >
                        🔗 Trace Correlation Timeline: {al.correlation_id} →
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--color-accent-blue)' }}>
              Audit History ({profile.audit_trail?.length || 0})
            </h3>
            <div style={{ background: 'var(--color-bg-secondary)', padding: '12px', borderRadius: '4px', border: '1px solid var(--color-border)', maxHeight: '240px', overflowY: 'auto' }}>
              {profile.audit_trail?.length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>No audit actions recorded for this device.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {profile.audit_trail.map((ad: any, i: number) => (
                    <div key={i} style={{ fontSize: '11px', fontFamily: 'monospace', display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>{ad.action}</strong> by {ad.actor} ({ad.result})</span>
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
