import React, { useEffect, useState } from 'react';
import { DeviceItem } from './DeviceList';

interface DeviceDetailModalProps {
  device: DeviceItem | null;
  onClose: () => void;
  onAction: (deviceId: string, action: 'suspend' | 'reinstate' | 'revoke') => void;
}
import { API_BASE } from '../config';

export const DeviceDetailModal: React.FC<DeviceDetailModalProps> = ({
  device,
  onClose,
  onAction,
}) => {
  const [history, setHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'telemetry' | 'security' | 'raw'>('telemetry');
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
  const [copiedRaw, setCopiedRaw] = useState(false);

  useEffect(() => {
    if (!device) return;
    const fetchHistory = async () => {
      setLoadingHistory(true);
      try {
        const res = await fetch(`${API_BASE}/api/telemetry/device/${device.device_id}?limit=15`);
        if (res.ok) {
          const data = await res.json();
          const items = Array.isArray(data)
            ? data
            : Array.isArray(data.telemetry)
            ? data.telemetry
            : Array.isArray(data.items)
            ? data.items
            : [];
          setHistory(items);
        }
      } catch (err) {
        console.error('Failed to load history', err);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [device]);

  if (!device) return null;

  const toggleRowExpanded = (idx: number) => {
    setExpandedRows(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(JSON.stringify(device, null, 2));
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const sendTestCommand = async (commandName: string) => {
    setCommandFeedback('Dispatching...');
    try {
      const res = await fetch(`${API_BASE}/api/devices/${device.device_id}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: commandName,
          parameters: { target_state: 'TOGGLE' },
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setCommandFeedback(`Command "${commandName}" dispatched successfully!`);
      } else {
        setCommandFeedback(`Rejected: ${data.detail || 'Authorization failure'}`);
      }
    } catch (e: any) {
      setCommandFeedback(`Error: ${e.message}`);
    }
  };

  const renderReadableMetrics = (row: any) => {
    const payload = row.values || row.data?.values || row.data || row;
    if (!payload || typeof payload !== 'object') {
      return <span style={{ fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>{String(payload)}</span>;
    }

    // Temperature Sensor readings
    if (payload.temperature_c !== undefined || payload.temperature_f !== undefined) {
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          <span style={{
            background: 'rgba(56, 189, 248, 0.15)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            padding: '3px 8px',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '12px',
          }}>
            🌡️ {payload.temperature_c !== undefined ? `${payload.temperature_c}°C` : ''}
            {payload.temperature_f !== undefined ? ` (${payload.temperature_f}°F)` : ''}
          </span>
          {payload.ambient_variance !== undefined && (
            <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
              ±{payload.ambient_variance} var
            </span>
          )}
          {payload.sensor_health && (
            <span style={{ fontSize: '11px', color: 'var(--color-accent-green)' }}>
              ✓ {payload.sensor_health}
            </span>
          )}
        </div>
      );
    }

    // Motion Sensor readings
    if (payload.motion_detected !== undefined) {
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          <span style={{
            background: payload.motion_detected ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.15)',
            color: payload.motion_detected ? '#ef4444' : '#10b981',
            border: `1px solid ${payload.motion_detected ? 'rgba(239, 68, 68, 0.35)' : 'rgba(16, 185, 129, 0.3)'}`,
            padding: '3px 8px',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '12px',
          }}>
            {payload.motion_detected ? '🚨 Motion Detected' : '✅ Clear (No Motion)'}
          </span>
          {payload.ambient_lux !== undefined && (
            <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
              💡 {payload.ambient_lux} lx
            </span>
          )}
        </div>
      );
    }

    // Smart Lock readings
    if (payload.lock_state !== undefined || payload.locked !== undefined) {
      const isLocked = payload.lock_state === 'LOCKED' || payload.locked === true;
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          <span style={{
            background: isLocked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            color: isLocked ? '#10b981' : '#f59e0b',
            border: `1px solid ${isLocked ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            padding: '3px 8px',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '12px',
          }}>
            {isLocked ? '🔒 Secured / Locked' : '🔓 Unlocked'}
          </span>
          {payload.battery_level !== undefined && (
            <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
              🔋 {payload.battery_level}%
            </span>
          )}
        </div>
      );
    }

    // HVAC / Actuator readings
    if (payload.power_state !== undefined || payload.current_power_w !== undefined || payload.target_temperature_c !== undefined) {
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          {payload.power_state && (
            <span style={{
              background: payload.power_state === 'ON' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 116, 139, 0.15)',
              color: payload.power_state === 'ON' ? '#10b981' : '#94a3b8',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '3px 8px',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '12px',
            }}>
              ⚡ Power: {payload.power_state}
            </span>
          )}
          {payload.target_temperature_c !== undefined && (
            <span style={{ fontSize: '12px', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
              🎯 Target: {payload.target_temperature_c}°C
            </span>
          )}
          {payload.current_power_w !== undefined && (
            <span style={{ fontSize: '11px', color: 'var(--color-accent-yellow)' }}>
              ⚡ {payload.current_power_w} W
            </span>
          )}
        </div>
      );
    }

    // Fallback: key-value chips
    const entries = Object.entries(payload).filter(([k]) => !['event_id', 'device_id', 'device_type', 'timestamp', 'telemetry_type', 'firmware_version'].includes(k));
    if (entries.length > 0) {
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
          {entries.slice(0, 4).map(([k, v]) => (
            <span key={k} style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '2px 7px',
              borderRadius: '5px',
              fontSize: '11px',
              color: 'var(--color-text-secondary)',
            }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>{k}:</strong> {String(v)}
            </span>
          ))}
        </div>
      );
    }

    return (
      <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
        {JSON.stringify(payload)}
      </span>
    );
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(5, 8, 15, 0.82)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-bright)',
        borderRadius: 'var(--border-radius-lg)',
        width: '100%',
        maxWidth: '820px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0,0,0,0.65), 0 0 1px 1px rgba(255,255,255,0.05)',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--color-border)',
          background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.35) 0%, rgba(15, 23, 42, 0) 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'monospace', letterSpacing: '0.02em', color: 'var(--color-text-primary)' }}>
                {device.device_id}
              </h2>
              <span style={{
                fontSize: '11px',
                padding: '3px 10px',
                borderRadius: '12px',
                background: device.status === 'ONLINE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 116, 139, 0.15)',
                color: device.status === 'ONLINE' ? 'var(--color-status-online)' : 'var(--color-status-offline)',
                border: `1px solid ${device.status === 'ONLINE' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(100, 116, 139, 0.3)'}`,
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: device.status === 'ONLINE' ? '#10b981' : '#64748b',
                  display: 'inline-block',
                }} />
                {device.status}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
              {device.device_name} · <span style={{ fontFamily: 'monospace', color: 'var(--color-accent-blue)' }}>{device.device_type}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--color-border)',
              borderRadius: '8px',
              color: 'var(--color-text-secondary)',
              fontSize: '14px',
              cursor: 'pointer',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
              e.currentTarget.style.color = '#ef4444';
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.color = 'var(--color-text-secondary)';
              e.currentTarget.style.borderColor = 'var(--color-border)';
            }}
          >
            ✕
          </button>
        </div>

        {/* Modern Segmented Pill Tab Navigation */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--color-border)',
          background: 'var(--color-bg-primary)',
          padding: '10px 20px',
          gap: '8px',
          alignItems: 'center',
        }}>
          {[
            {
              id: 'telemetry',
              icon: '📊',
              label: 'Recent Readings',
              count: history.length > 0 ? history.length : undefined,
            },
            {
              id: 'security',
              icon: '🔒',
              label: 'Permissions & Controls',
              count: device.capabilities?.length || undefined,
            },
            {
              id: 'raw',
              icon: '📄',
              label: 'Technical Data',
              count: 'JSON',
            },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid transparent',
                  borderRadius: '8px',
                  color: isActive ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  padding: '7px 14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.18s ease',
                  boxShadow: isActive ? '0 2px 8px rgba(56, 189, 248, 0.12)' : 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                    e.currentTarget.style.color = 'var(--color-text-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--color-text-secondary)';
                  }
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span style={{
                    fontSize: '10px',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    background: isActive ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.08)',
                    color: isActive ? '#38bdf8' : 'var(--color-text-muted)',
                    fontWeight: 700,
                    letterSpacing: '0.02em',
                  }}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Body Content */}
        <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
          {activeTab === 'telemetry' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Latest Telemetry Samples</span>
                  <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', margin: '2px 0 0 0' }}>
                    Formatted live sensor values with expandable JSON payload
                  </p>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '4px' }}>
                  {history.length} records retrieved
                </span>
              </div>

              {loadingHistory ? (
                <div style={{ textAlign: 'center', padding: '36px', color: 'var(--color-text-secondary)' }}>
                  <div style={{ display: 'inline-block', width: '20px', height: '20px', border: '2px solid rgba(56, 189, 248, 0.2)', borderTopColor: '#38bdf8', borderRadius: '50%', animation: 'spinSlow 1s linear infinite', marginBottom: '8px' }} />
                  <div>Loading telemetry stream...</div>
                </div>
              ) : !Array.isArray(history) || history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '36px', color: 'var(--color-text-muted)', border: '1px dashed var(--color-border)', borderRadius: 'var(--border-radius)' }}>
                  No telemetry recorded yet. Start the fleet simulation in the header to stream live data.
                </div>
              ) : (
                <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)', background: 'var(--color-bg-base)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'var(--color-bg-primary)', color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border)' }}>
                        <th style={{ padding: '10px 14px', width: '110px' }}>Timestamp</th>
                        <th style={{ padding: '10px 14px' }}>Sensor Metrics</th>
                        <th style={{ padding: '10px 14px', width: '70px', textAlign: 'right' }}>Payload</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((row, idx) => {
                        const isExpanded = !!expandedRows[idx];
                        return (
                          <React.Fragment key={idx}>
                            <tr style={{
                              borderBottom: isExpanded ? 'none' : '1px solid var(--color-border-subtle)',
                              background: idx % 2 === 0 ? 'rgba(255, 255, 255, 0.01)' : 'rgba(255, 255, 255, 0.03)',
                              transition: 'background 0.15s ease',
                            }}>
                              <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                                {row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : 'N/A'}
                              </td>
                              <td style={{ padding: '10px 14px' }}>
                                {renderReadableMetrics(row)}
                              </td>
                              <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                                <button
                                  onClick={() => toggleRowExpanded(idx)}
                                  title="View raw JSON payload"
                                  style={{
                                    background: isExpanded ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                                    border: isExpanded ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid var(--color-border)',
                                    borderRadius: '4px',
                                    color: isExpanded ? '#38bdf8' : 'var(--color-text-secondary)',
                                    fontSize: '11px',
                                    padding: '2px 7px',
                                    cursor: 'pointer',
                                    fontFamily: 'monospace',
                                  }}
                                >
                                  {isExpanded ? 'Hide' : '{ }'}
                                </button>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)', background: 'rgba(0, 0, 0, 0.3)' }}>
                                <td colSpan={3} style={{ padding: '8px 14px 12px 14px' }}>
                                  <pre style={{
                                    background: 'var(--color-bg-primary)',
                                    padding: '10px 12px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border-subtle)',
                                    fontSize: '11px',
                                    color: 'var(--color-accent-teal)',
                                    overflowX: 'auto',
                                    margin: 0,
                                    fontFamily: 'monospace',
                                    lineHeight: 1.4,
                                  }}>
                                    {JSON.stringify(row, null, 2)}
                                  </pre>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'security' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'var(--color-bg-primary)', padding: '16px 20px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-accent-blue)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>🔒</span> Assigned Device Capabilities & Roles
                </h4>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
                  {device.capabilities && device.capabilities.length > 0 ? (
                    device.capabilities.map((cap) => (
                      <span key={cap} style={{
                        fontSize: '11px',
                        padding: '5px 10px',
                        borderRadius: '6px',
                        background: 'rgba(56, 189, 248, 0.12)',
                        color: 'var(--color-accent-blue)',
                        border: '1px solid rgba(56, 189, 248, 0.3)',
                        fontWeight: 600,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}>
                        🔑 {cap.replace(/_/g, ' ')}
                      </span>
                    ))
                  ) : (
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>No permissions assigned to this device ID.</span>
                  )}
                </div>
              </div>

              <div style={{ background: 'var(--color-bg-primary)', padding: '16px 20px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>📡</span> Remote Command Dispatch
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
                  Transmit authenticated actuator control frames directly to this endpoint.
                </p>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => sendTestCommand('SET_STATE')}
                    style={{
                      padding: '8px 16px',
                      background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                      border: '1px solid rgba(56, 189, 248, 0.4)',
                      borderRadius: 'var(--border-radius)',
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    ⚡ Toggle Power / State
                  </button>
                  <button
                    onClick={() => sendTestCommand('SET_TARGET_TEMP')}
                    style={{
                      padding: '8px 16px',
                      background: 'var(--color-bg-secondary)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--border-radius)',
                      color: 'var(--color-text-primary)',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    🎯 Target Temperature (24°C)
                  </button>
                </div>
                {commandFeedback && (
                  <div style={{
                    marginTop: '12px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    background: commandFeedback.includes('successfully') ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                    color: commandFeedback.includes('successfully') ? '#10b981' : '#f59e0b',
                    border: `1px solid ${commandFeedback.includes('successfully') ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                    fontFamily: 'monospace',
                  }}>
                    {commandFeedback}
                  </div>
                )}
              </div>

              <div style={{ background: 'var(--color-bg-primary)', padding: '16px 20px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>🛡️</span> Zero-Trust Access Quarantine
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
                  Instantly block or revoke edge credentials if anomalous behaviors or intrusion signs occur.
                </p>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {device.status === 'SUSPENDED' ? (
                    <button
                      onClick={() => onAction(device.device_id, 'reinstate')}
                      style={{
                        padding: '7px 14px',
                        background: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid rgba(16, 185, 129, 0.4)',
                        borderRadius: '6px',
                        color: '#10b981',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      ✓ Unblock & Re-admit Device
                    </button>
                  ) : (
                    <button
                      onClick={() => onAction(device.device_id, 'suspend')}
                      style={{
                        padding: '7px 14px',
                        background: 'rgba(245, 158, 11, 0.15)',
                        border: '1px solid rgba(245, 158, 11, 0.35)',
                        borderRadius: '6px',
                        color: '#f59e0b',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      ⚠️ Block / Quarantine Device
                    </button>
                  )}
                  <button
                    onClick={() => onAction(device.device_id, 'revoke')}
                    style={{
                      padding: '7px 14px',
                      background: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid rgba(239, 68, 68, 0.35)',
                      borderRadius: '6px',
                      color: '#ef4444',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ✕ Revoke Credentials Permanently
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  Device Registration Schema & Attributes
                </span>
                <button
                  onClick={handleCopyRaw}
                  style={{
                    background: copiedRaw ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                    border: `1px solid ${copiedRaw ? 'rgba(16, 185, 129, 0.4)' : 'var(--color-border)'}`,
                    color: copiedRaw ? '#10b981' : 'var(--color-text-primary)',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '11px',
                    cursor: 'pointer',
                    fontWeight: 600,
                    transition: 'all 0.15s ease',
                  }}
                >
                  {copiedRaw ? '✓ Copied to Clipboard' : '📋 Copy JSON'}
                </button>
              </div>
              <pre style={{
                background: 'var(--color-bg-primary)',
                padding: '16px',
                borderRadius: 'var(--border-radius)',
                border: '1px solid var(--color-border)',
                fontSize: '12px',
                color: '#38bdf8',
                overflowX: 'auto',
                fontFamily: 'monospace',
                lineHeight: 1.5,
              }}>
                {JSON.stringify(device, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--color-border)',
          background: 'rgba(15, 23, 42, 0.5)',
          display: 'flex',
          justifyContent: 'flex-end',
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 20px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--border-radius)',
              color: 'var(--color-text-primary)',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border-bright)';
              e.currentTarget.style.background = 'var(--color-bg-card-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.background = 'var(--color-bg-card)';
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
