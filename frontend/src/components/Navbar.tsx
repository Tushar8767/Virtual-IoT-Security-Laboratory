import React from 'react';

interface NavbarProps {
  simRunning: boolean;
  onToggleSim: () => void;
  onRefresh: () => void;
  wsConnected: boolean;
  activeAlertsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  simRunning,
  onToggleSim,
  onRefresh,
  wsConnected,
  activeAlertsCount,
}) => {
  const hasAlerts = activeAlertsCount > 0;

  return (
    <header style={{
      background: 'rgba(11, 17, 30, 0.9)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid var(--color-border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      padding: '14px 28px',
      marginBottom: '24px',
    }}>
      <div style={{
        maxWidth: '1360px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        {/* Brand & Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
          }}>
            🔒
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '16px',
                fontWeight: 700,
                color: '#fff',
              }}>
                Virtual IoT Security Laboratory
              </span>
              <span style={{
                fontSize: '11px',
                background: 'rgba(56, 189, 248, 0.12)',
                color: '#38bdf8',
                padding: '2px 8px',
                borderRadius: '4px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                fontWeight: 600,
              }}>
                Live System
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Connected Device Monitoring & Security Testing Dashboard
            </div>
          </div>
        </div>

        {/* Status Indicators & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* System Health Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 600,
            background: hasAlerts ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
            color: hasAlerts ? '#ef4444' : '#10b981',
            border: `1px solid ${hasAlerts ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: hasAlerts ? '#ef4444' : '#10b981',
            }} />
            {hasAlerts ? `${activeAlertsCount} Security Alert(s) Detected` : 'System Status: All Good'}
          </div>

          {/* Connection Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: 'var(--color-text-secondary)',
            background: 'var(--color-bg-card)',
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid var(--color-border)',
          }}>
            <span style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: wsConnected ? '#10b981' : '#f59e0b',
            }} />
            {wsConnected ? 'Live Connection: Connected' : 'Live Connection: Reconnecting...'}
          </div>

          {/* Start / Stop Devices Button */}
          <button
            onClick={onToggleSim}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 18px',
              borderRadius: 'var(--border-radius)',
              background: simRunning
                ? '#ef4444'
                : '#10b981',
              border: 'none',
              color: '#fff',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'opacity 0.2s',
            }}
          >
            <span>{simRunning ? '⏹ Stop Devices' : '▶ Start Devices'}</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            style={{
              padding: '8px 14px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--border-radius)',
              color: 'var(--color-text-primary)',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>
    </header>
  );
};
