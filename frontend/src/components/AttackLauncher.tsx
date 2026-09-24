import React, { useState, useEffect } from 'react';

export interface AttackScenario {
  id: string;
  name: string;
  category: string;
  description: string;
  target_device: string;
  expected_detection: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  mitre?: string;
}

interface AttackLauncherProps {
  onAttackLaunched?: () => void;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const MITRE_MAP: Record<string, string> = {
  SCENARIO_A: 'MITRE T0814 // Rogue Master/Node Injection',
  SCENARIO_B: 'MITRE T0812 // Credential Brute-Force',
  SCENARIO_C: 'MITRE T0814 // High-Frequency Telemetry DoS',
  SCENARIO_D: 'MITRE T0855 // Unauthorized Sensor Tampering',
  SCENARIO_E: 'MITRE T0885 // Loss of View / Heartbeat Starvation',
  SCENARIO_F: 'MITRE T0857 // Device Identity Impersonation',
  SCENARIO_G: 'MITRE T0855 // Unauthorized Actuation Attempt',
};

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

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: 'rgba(239, 68, 68, 0.35)' };
      case 'HIGH':
        return { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', border: 'rgba(249, 115, 22, 0.35)' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.35)' };
      default:
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: 'rgba(16, 185, 129, 0.35)' };
    }
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#ef4444' }}>⚔️</span> Adversarial Attack Simulation Matrix
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Controlled cyber warfare tests executing live against Gateway, Authentication & Detection Engines
          </p>
        </div>
        <span style={{
          fontSize: '11px',
          fontFamily: 'monospace',
          color: 'var(--color-accent-purple)',
          background: 'rgba(168, 85, 247, 0.12)',
          padding: '4px 10px',
          borderRadius: '6px',
          border: '1px solid rgba(168, 85, 247, 0.25)',
          fontWeight: 700,
        }}>
          {scenarios.length} ATTACK VECTORS ARMED
        </span>
      </div>

      {/* Execution Feedback Terminal Banner */}
      {lastResult && (
        <div style={{
          marginBottom: '22px',
          background: 'var(--color-bg-card)',
          border: `1px solid ${lastResult.detected ? '#10b981' : '#f97316'}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: '18px 20px',
          boxShadow: lastResult.detected ? '0 0 20px rgba(16, 185, 129, 0.2)' : 'none',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px' }}>{lastResult.detected ? '🛡️' : '⚠️'}</span>
              <span style={{
                fontWeight: 800,
                fontSize: '14px',
                color: lastResult.detected ? '#10b981' : '#f97316',
                letterSpacing: '0.04em',
              }}>
                {lastResult.detected ? 'ATTACK INTERCEPTED & MITIGATED BY DETECTION ENGINE' : 'ATTACK SCENARIO EXECUTED'}
              </span>
            </div>
            <button
              onClick={() => setLastResult(null)}
              style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', fontSize: '16px' }}
            >
              ✕
            </button>
          </div>

          <div style={{
            background: 'var(--color-bg-base)',
            padding: '12px 14px',
            borderRadius: '6px',
            fontFamily: 'monospace',
            fontSize: '12px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '8px',
            border: '1px solid var(--color-border)',
          }}>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Vector:</span> <strong style={{ color: '#fff' }}>{lastResult.name || lastResult.scenario_id}</strong></div>
            {lastResult.run_id && <div><span style={{ color: 'var(--color-text-muted)' }}>Run ID:</span> <strong style={{ color: 'var(--color-accent-blue)' }}>{lastResult.run_id}</strong></div>}
            {lastResult.detection_rule && <div><span style={{ color: 'var(--color-text-muted)' }}>Rule Triggered:</span> <strong style={{ color: '#06b6d4' }}>{lastResult.detection_rule}</strong></div>}
            {lastResult.alert_id && <div><span style={{ color: 'var(--color-text-muted)' }}>SOC Alert:</span> <strong style={{ color: '#ef4444' }}>{lastResult.alert_id}</strong></div>}
          </div>
        </div>
      )}

      {/* Scenarios Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading threat catalog...
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '16px',
        }}>
          {scenarios.map((sc) => {
            const sev = getSeverityBadge(sc.severity);
            const isExecuting = runningId === sc.id;
            const mitre = MITRE_MAP[sc.id] || 'MITRE ATT&CK for IoT';

            return (
              <div
                key={sc.id}
                style={{
                  background: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--border-radius-lg)',
                  padding: '18px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <div>
                  {/* MITRE Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '10px',
                      fontFamily: 'monospace',
                      color: 'var(--color-accent-cyan)',
                      background: 'rgba(6, 182, 212, 0.1)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid rgba(6, 182, 212, 0.25)',
                      fontWeight: 700,
                    }}>
                      {mitre}
                    </span>

                    <span style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: sev.bg,
                      color: sev.text,
                      border: `1px solid ${sev.border}`,
                    }}>
                      {sc.severity}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    {sc.name}
                  </h3>

                  <div style={{ fontSize: '11px', color: 'var(--color-accent-purple)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '10px' }}>
                    Category: {sc.category}
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
                    {sc.description}
                  </p>

                  <div style={{
                    background: 'var(--color-bg-base)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    marginBottom: '16px',
                    border: '1px solid var(--color-border-subtle)',
                  }}>
                    <div>Target Node: <strong style={{ color: '#fff', fontFamily: 'monospace' }}>{sc.target_device}</strong></div>
                    <div>Detection Rule: <strong style={{ color: 'var(--color-accent-cyan)', fontFamily: 'monospace' }}>{sc.expected_detection}</strong></div>
                  </div>
                </div>

                <button
                  disabled={isExecuting}
                  onClick={() => launchAttack(sc.id)}
                  style={{
                    background: isExecuting
                      ? 'var(--color-bg-base)'
                      : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    border: 'none',
                    color: '#fff',
                    padding: '10px 16px',
                    borderRadius: 'var(--border-radius)',
                    fontWeight: 700,
                    fontSize: '13px',
                    letterSpacing: '0.03em',
                    cursor: isExecuting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    boxShadow: isExecuting ? 'none' : '0 2px 10px rgba(239, 68, 68, 0.3)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isExecuting ? '⏳ INJECTING ATTACK PAYLOAD...' : '⚡ LAUNCH ATTACK'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
