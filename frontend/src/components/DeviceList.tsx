import React from 'react';

export interface DeviceItem {
  device_id: string;
  device_name: string;
  device_type: string;
  status: string;
  trust_state: string;
  firmware_version: string;
  heartbeat_interval_seconds: number;
  last_seen: string | null;
  capabilities: string[];
}

interface DeviceListProps {
  devices: DeviceItem[];
  onAction: (deviceId: string, action: 'suspend' | 'reinstate' | 'revoke') => void;
  onInspect?: (device: DeviceItem) => void;
  loading: boolean;
}

export const DeviceList: React.FC<DeviceListProps> = ({ devices, onAction, onInspect, loading }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ONLINE': return 'var(--color-status-online)';
      case 'PROVISIONED': return '#58a6ff';
      case 'SUSPENDED': return 'var(--color-status-suspended)';
      case 'REVOKED': return 'var(--color-status-revoked)';
      default: return 'var(--color-status-offline)';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ONLINE': return 'Online';
      case 'PROVISIONED': return 'Ready / New';
      case 'SUSPENDED': return 'Blocked';
      case 'REVOKED': return 'Revoked';
      default: return status;
    }
  };

  if (loading) {
    return <div style={{ color: 'var(--color-text-secondary)', padding: '20px' }}>Loading devices...</div>;
  }

  if (devices.length === 0) {
    return <div style={{ color: 'var(--color-text-secondary)', padding: '20px' }}>No devices registered yet.</div>;
  }

  return (
    <div style={{
      background: 'var(--color-bg-secondary)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--border-radius)',
      overflowX: 'auto',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
            <th style={{ padding: '12px 16px' }}>Device ID</th>
            <th style={{ padding: '12px 16px' }}>Device Name & Type</th>
            <th style={{ padding: '12px 16px' }}>Status</th>
            <th style={{ padding: '12px 16px' }}>Features & Roles</th>
            <th style={{ padding: '12px 16px' }}>Last Seen</th>
            <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((d) => (
            <tr key={d.device_id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontWeight: 600 }}>
                {d.device_id}
                {d.device_id.startsWith('LPC') && (
                  <span style={{
                    marginLeft: '8px',
                    fontSize: '10px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: '#238636',
                    color: '#fff',
                  }}>
                    PROTEUS HW
                  </span>
                )}
              </td>
              <td style={{ padding: '12px 16px' }}>
                <div style={{ fontWeight: 500 }}>{d.device_name}</div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{d.device_type}</div>
              </td>
              <td style={{ padding: '12px 16px' }}>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 600,
                  fontSize: '12px',
                  color: getStatusColor(d.status),
                }}>
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: getStatusColor(d.status),
                  }} />
                  {getStatusLabel(d.status)}
                </span>
              </td>
              <td style={{ padding: '12px 16px' }}>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {d.capabilities.slice(0, 2).map((c) => (
                    <span key={c} style={{
                      fontSize: '11px',
                      background: 'var(--color-bg-card)',
                      border: '1px solid var(--color-border)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      color: 'var(--color-text-secondary)',
                    }}>
                      {c.replace(/_/g, ' ')}
                    </span>
                  ))}
                  {d.capabilities.length > 2 && (
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>+{d.capabilities.length - 2}</span>
                  )}
                </div>
              </td>
              <td style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                {d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : 'Never'}
              </td>
              <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                  {onInspect && (
                    <button
                      onClick={() => onInspect(d)}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        background: 'rgba(47, 129, 247, 0.1)',
                        border: '1px solid var(--color-accent-blue)',
                        color: 'var(--color-accent-blue)',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: 500,
                      }}
                    >
                      🔍 View Details
                    </button>
                  )}
                  {d.status !== 'SUSPENDED' && d.status !== 'REVOKED' && (
                    <button
                      onClick={() => onAction(d.device_id, 'suspend')}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        background: 'transparent',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-severity-medium)',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      Block
                    </button>
                  )}
                  {d.status === 'SUSPENDED' && (
                    <button
                      onClick={() => onAction(d.device_id, 'reinstate')}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        background: 'transparent',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-severity-low)',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      Unblock
                    </button>
                  )}
                  {d.status !== 'REVOKED' && (
                    <button
                      onClick={() => onAction(d.device_id, 'revoke')}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        background: 'transparent',
                        border: '1px solid var(--color-severity-critical)',
                        color: 'var(--color-severity-critical)',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};