import React, { useState, useEffect } from 'react';

export interface AttackScenario {
  id: string;
  name: string;
  category: string;
  description: string;
  target_device: string;
  expected_detection: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

interface AttackLauncherProps {
  onAttackLaunched?: () => void;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const AttackLauncher: React.FC<AttackLauncherProps> = ({ onAttackLaunched }) => {
  const [scenarios, setScenarios] = useState<AttackScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any | null>(null);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/scenarios/`);
        if (res.ok) {
          const data = await res.json();
          setScenarios(data.scenarios || []);
        }
      } catch (err) {
        console.error('Failed to fetch scenarios', err);
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, []);

  const launchAttack = async (scenarioId: string) => {
    setRunningId(scenarioId);
    setLastResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/launch`, {
        method: 'POST',
      });
      const data = await res.json();
      setLastResult(data);
      if (onAttackLaunched) {
        onAttackLaunched();
      }
    } catch (err: any) {
      setLastResult({ error: err.message || 'Execution failed' });
    } finally {
      setRunningId(null);
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
            ⚔️ Attack Simulation Control Center
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Trigger controlled cyber attacks to test the Gateway, Authentication layer, and Security Detection Engine.
          </p>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-card)', padding: '4px 10px', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
          {scenarios.length} Scenarios Available
        </span>
      </div>

      {/* Execution Feedback Banner */}
      {lastResult && (
        <div style={{
          marginBottom: '20px',
          background: 'var(--color-bg-secondary)',
          border: `1px solid ${lastResult.detected ? 'var(--color-status-online)' : 'var(--color-severity-high)'}`,
          borderRadius: 'var(--border-radius)',
          padding: '16px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{
              fontWeight: 700,
              fontSize: '14px',
              color: lastResult.detected ? 'var(--color-status-online)' : 'var(--color-severity-high)',
            }}>
              {lastResult.detected ? '✅ ATTACK DETECTED & BLOCKED BY ENGINE' : '⚠️ ATTACK EXECUTION RESULT'}
            </span>
            <button
              onClick={() => setLastResult(null)}
              style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>
            <div><strong>Scenario:</strong> {lastResult.name || lastResult.scenario_id}</div>
            {lastResult.run_id && <div><strong>Run ID:</strong> {lastResult.run_id}</div>}
            {lastResult.detection_rule && <div><strong>Detection Rule Triggered:</strong> <span style={{ color: 'var(--color-accent-teal)' }}>{lastResult.detection_rule}</span></div>}
            {lastResult.alert_id && <div><strong>Security Alert Created:</strong> {lastResult.alert_id}</div>}
            {lastResult.summary && <div style={{ marginTop: '6px', color: 'var(--color-text-secondary)' }}>{lastResult.summary}</div>}
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
          Loading attack scenarios catalog...
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '16px',
        }}>
          {scenarios.map((sc) => {
            const sev = getSeverityStyle(sc.severity);
            const isExecuting = runningId === sc.id;

            return (
              <div
                key={sc.id}
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--border-radius)',
                  padding: '18px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      fontSize: '12px',
                      color: 'var(--color-accent-blue)',
                    }}>
                      {sc.id}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: sev.bg,
                      color: sev.text,
                      border: `1px solid ${sev.border}`,
                    }}>
                      {sc.severity}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                    {sc.name}
                  </h3>

                  <div style={{ fontSize: '11px', color: 'var(--color-accent-purple)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px' }}>
                    {sc.category}
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
                    {sc.description}
                  </p>

                  <div style={{
                    background: 'var(--color-bg-primary)',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    marginBottom: '16px',
                  }}>
                    <div>Target Node: <strong style={{ color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>{sc.target_device}</strong></div>
                    <div>Detection Rule: <strong style={{ color: 'var(--color-accent-teal)', fontFamily: 'monospace' }}>{sc.expected_detection}</strong></div>
                  </div>
                </div>

                <button
                  disabled={isExecuting}
                  onClick={() => launchAttack(sc.id)}
                  style={{
                    background: isExecuting ? 'var(--color-bg-hover)' : 'var(--color-severity-critical)',
                    border: 'none',
                    color: '#fff',
                    padding: '10px 14px',
                    borderRadius: 'var(--border-radius)',
                    fontWeight: 600,
                    fontSize: '13px',
                    cursor: isExecuting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    transition: 'opacity 0.2s',
                  }}
                >
                  {isExecuting ? '⏳ Infiltrating & Executing...' : '⚡ Launch Attack'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
