import React, { useEffect, useState } from 'react';
import { DeviceItem } from './DeviceList';

interface DeviceDetailModalProps {
  device: DeviceItem | null;
  onClose: () => void;
  onAction: (deviceId: string, action: 'suspend' | 'reinstate' | 'revoke') => void;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const DeviceDetailModal: React.FC<DeviceDetailModalProps> = ({
  device,
  onClose,
  onAction,
}) => {
  const [history, setHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'telemetry' | 'security' | 'raw'>('telemetry');
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);

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

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--border-radius-lg)',
        width: '100%',
        maxWidth: '780px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 16px 32px rgba(0,0,0,0.5)',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'monospace' }}>
                {device.device_id}
              </h2>
              <span style={{
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '12px',
                background: device.status === 'ONLINE' ? 'rgba(63, 185, 80, 0.15)' : 'rgba(139, 148, 158, 0.15)',
                color: device.status === 'ONLINE' ? 'var(--color-status-online)' : 'var(--color-status-offline)',
                fontWeight: 600,
              }}>
                {device.status}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
              {device.device_name} · <span style={{ fontFamily: 'monospace' }}>{device.device_type}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-secondary)',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--color-border)',
          background: 'var(--color-bg-primary)',
          padding: '0 20px',
          gap: '16px',
        }}>
          {[
            { id: 'telemetry', label: '📊 Recent Readings' },
            { id: 'security', label: '🔒 Permissions & Controls' },
            { id: 'raw', label: '📄 Technical Data' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--color-accent-blue)' : '2px solid transparent',
                color: activeTab === tab.id ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
                fontWeight: 600,
                fontSize: '13px',
                padding: '12px 4px',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Body Content */}
        <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
          {activeTab === 'telemetry' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>Latest Telemetry Samples</span>
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                  {history.length} records retrieved
                </span>
              </div>

              {loadingHistory ? (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  Loading telemetry logs...
                </div>
              ) : !Array.isArray(history) || history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-muted)' }}>
                  No telemetry recorded yet. Start the fleet simulation to populate data.
                </div>
              ) : (
                <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: 'var(--border-radius)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'var(--color-bg-primary)', color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border)' }}>
                        <th style={{ padding: '8px 12px' }}>Timestamp</th>
                        <th style={{ padding: '8px 12px' }}>Metrics Payload</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((row, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                          <td style={{ padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                            {new Date(row.timestamp).toLocaleTimeString()}
                          </td>
                          <td style={{ padding: '8px 12px', fontFamily: 'monospace', color: 'var(--color-text-primary)' }}>
                            {JSON.stringify(row.data || row)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'security' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'var(--color-bg-primary)', padding: '16px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-accent-blue)', marginBottom: '8px' }}>
                  Allowed Permissions & Roles
                </h4>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {device.capabilities && device.capabilities.length > 0 ? (
                    device.capabilities.map((cap) => (
                      <span key={cap} style={{
                        fontSize: '11px',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        background: 'rgba(47, 129, 247, 0.15)',
                        color: 'var(--color-accent-blue)',
                        border: '1px solid rgba(47, 129, 247, 0.3)',
                        fontWeight: 600,
                      }}>
                        🔑 {cap.replace(/_/g, ' ')}
                      </span>
                    ))
                  ) : (
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>No permissions assigned.</span>
                  )}
                </div>
              </div>

              <div style={{ background: 'var(--color-bg-primary)', padding: '16px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                  Send Test Command
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                  Test if this device responds properly to remote commands.
                </p>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => sendTestCommand('SET_STATE')}
                    style={{
                      padding: '8px 14px',
                      background: 'var(--color-accent-blue)',
                      border: 'none',
                      borderRadius: 'var(--border-radius)',
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Toggle Power / State
                  </button>
                  <button
                    onClick={() => sendTestCommand('SET_TARGET_TEMP')}
                    style={{
                      padding: '8px 14px',
                      background: 'var(--color-bg-secondary)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--border-radius)',
                      color: 'var(--color-text-primary)',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Set Temperature (24°C)
                  </button>
                </div>
                {commandFeedback && (
                  <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--color-accent-yellow)', fontFamily: 'monospace' }}>
                    {commandFeedback}
                  </div>
                )}
              </div>

              <div style={{ background: 'var(--color-bg-primary)', padding: '16px', borderRadius: 'var(--border-radius)', border: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                  Device Management
                </h4>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {device.status === 'SUSPENDED' ? (
                    <button
                      onClick={() => onAction(device.device_id, 'reinstate')}
                      style={{ padding: '6px 12px', background: 'var(--color-status-online)', border: 'none', borderRadius: '4px', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Unblock Device
                    </button>
                  ) : (
                    <button
                      onClick={() => onAction(device.device_id, 'suspend')}
                      style={{ padding: '6px 12px', background: 'var(--color-status-suspended)', border: 'none', borderRadius: '4px', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Block Device
                    </button>
                  )}
                  <button
                    onClick={() => onAction(device.device_id, 'revoke')}
                    style={{ padding: '6px 12px', background: 'var(--color-severity-critical)', border: 'none', borderRadius: '4px', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Revoke Access
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div>
              <pre style={{
                background: 'var(--color-bg-primary)',
                padding: '16px',
                borderRadius: 'var(--border-radius)',
                border: '1px solid var(--color-border)',
                fontSize: '12px',
                color: 'var(--color-accent-teal)',
                overflowX: 'auto',
              }}>
                {JSON.stringify(device, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'flex-end',
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--border-radius)',
              color: 'var(--color-text-primary)',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
