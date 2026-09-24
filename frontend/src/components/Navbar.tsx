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
  const isThreatDetected = activeAlertsCount > 0;

  return (
    <header style={{
      background: 'rgba(11, 17, 30, 0.85)',
      backdropFilter: 'blur(12px)',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.35)',
          }}>
            🛡️
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '16px',
                fontWeight: 800,
                letterSpacing: '0.05em',
                color: '#fff',
                textTransform: 'uppercase',
              }}>
                IoT Defense SOC
              </span>
              <span style={{
                fontSize: '10px',
                fontFamily: 'monospace',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                fontWeight: 700,
              }}>
                v2.4 SEC-HARDENED
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '1px' }}>
              Virtual Embedded Security Lab & Autonomous Response Engine
            </div>
          </div>
        </div>

        {/* Status Indicators & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Threat Level Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.04em',
            background: isThreatDetected ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
            color: isThreatDetected ? '#ef4444' : '#10b981',
            border: `1px solid ${isThreatDetected ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.3)'}`,
            boxShadow: isThreatDetected ? '0 0 12px rgba(239, 68, 68, 0.25)' : 'none',
          }}>
            <span style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: isThreatDetected ? '#ef4444' : '#10b981',
              boxShadow: isThreatDetected ? '0 0 8px #ef4444' : '0 0 8px #10b981',
            }} />
            {isThreatDetected ? `THREAT ELEVATED (${activeAlertsCount} ACTIVE)` : 'SECURITY POSTURE: NOMINAL'}
          </div>

          {/* WebSocket Pulse */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            fontFamily: 'monospace',
            color: wsConnected ? 'var(--color-text-secondary)' : '#f97316',
            background: 'var(--color-bg-primary)',
            padding: '6px 10px',
            borderRadius: '6px',
            border: '1px solid var(--color-border)',
          }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: wsConnected ? '#10b981' : '#f97316',
            }} />
            {wsConnected ? 'FEED: LIVE' : 'FEED: DISCONNECTED'}
          </div>

          {/* Simulation Toggle Button */}
          <button
            onClick={onToggleSim}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 18px',
              borderRadius: 'var(--border-radius)',
              background: simRunning
                ? 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)'
                : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              border: 'none',
              color: '#fff',
              fontWeight: 700,
              fontSize: '12px',
              letterSpacing: '0.04em',
              cursor: 'pointer',
              boxShadow: simRunning ? '0 0 14px rgba(239, 68, 68, 0.4)' : '0 0 14px rgba(16, 185, 129, 0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <span>{simRunning ? '⏹' : '▶'}</span>
            <span>{simRunning ? 'HALT FLEET' : 'START FLEET'}</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            title="Refresh Fleet State"
            style={{
              padding: '8px 12px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--border-radius)',
              color: 'var(--color-text-primary)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s ease',
            }}
          >
            🔄
          </button>
        </div>
      </div>
    </header>
  );
};
