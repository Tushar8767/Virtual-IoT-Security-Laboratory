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

const FRIENDLY_NAMES: Record<string, { title: string; category: string; description: string; expected: string }> = {
  SCENARIO_A: {
    title: 'Test 1: Unregistered Device Attack',
    category: 'Fake Device Test',
    description: 'An unknown rogue device (ROGUE-999) tries to connect and send data without registration.',
    expected: 'System blocks the unknown device',
  },
  SCENARIO_B: {
    title: 'Test 2: Repeated Wrong Passwords',
    category: 'Password Guessing Test',
    description: 'Rapidly sends invalid passwords to test if the system detects repeated login failures.',
    expected: 'System detects failed login flood',
  },
  SCENARIO_C: {
    title: 'Test 3: Network Traffic Overload (DoS)',
    category: 'Traffic Flood Test',
    description: 'Sends a large burst of data packets per second to test if the system catches rate limit violations.',
    expected: 'System detects excessive data rate',
  },
  SCENARIO_D: {
    title: 'Test 4: Extreme High Temperature (105°C)',
    category: 'Dangerous Reading Test',
    description: 'Injects a fake 105°C temperature reading to test if the high-temperature alert triggers immediately.',
    expected: 'System triggers critical high-temperature alert',
  },
  SCENARIO_E: {
    title: 'Test 5: Device Goes Silent (Offline)',
    category: 'Connection Loss Test',
    description: 'A device abruptly stops sending check-in pings to verify the system notices missing devices.',
    expected: 'System alerts on missed check-in timeout',
  },
  SCENARIO_F: {
    title: 'Test 6: Identity Theft (Impersonation)',
    category: 'Identity Test',
    description: 'A sensor pretends to be another device to inject data or commands under a false identity.',
    expected: 'System detects device impersonation',
  },
  SCENARIO_G: {
    title: 'Test 7: Unauthorized Control Command',
    category: 'Permission Test',
    description: 'A sensor without permission tries to issue an actuator control command.',
    expected: 'System rejects command due to missing permissions',
  },
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
      setLastResult({ error: err.message || 'Test execution failed' });
    } finally {
      setRunningId(null);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', label: 'High Priority' };
      case 'HIGH':
        return { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', label: 'Medium-High Priority' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', label: 'Medium Priority' };
      default:
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', label: 'Low Priority' };
    }
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🧪 Security Tests & Attack Simulations
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Run controlled security tests to verify that the system detects and blocks unauthorized activity.
          </p>
        </div>
        <span style={{
          fontSize: '12px',
          color: 'var(--color-accent-blue)',
          background: 'rgba(56, 189, 248, 0.1)',
          padding: '4px 10px',
          borderRadius: '6px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          fontWeight: 600,
        }}>
          {scenarios.length} Tests Ready
        </span>
      </div>

      {/* Execution Result Banner */}
      {lastResult && (
        <div style={{
          marginBottom: '20px',
          background: 'var(--color-bg-card)',
          border: `1px solid ${lastResult.detected ? '#10b981' : '#f97316'}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: '16px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px' }}>{lastResult.detected ? '✅' : '⚠️'}</span>
              <span style={{
                fontWeight: 700,
                fontSize: '14px',
                color: lastResult.detected ? '#10b981' : '#f97316',
              }}>
                {lastResult.detected ? 'Security Test Passed: Attack Successfully Detected & Blocked!' : 'Test Completed'}
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
            padding: '10px 14px',
            borderRadius: '6px',
            fontSize: '12px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '8px',
          }}>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Test:</span> <strong>{lastResult.name || lastResult.scenario_id}</strong></div>
            {lastResult.detection_rule && <div><span style={{ color: 'var(--color-text-muted)' }}>Detection Rule:</span> <strong style={{ color: 'var(--color-accent-blue)' }}>{lastResult.detection_rule}</strong></div>}
            {lastResult.alert_id && <div><span style={{ color: 'var(--color-text-muted)' }}>Alert ID:</span> <strong style={{ color: '#ef4444' }}>{lastResult.alert_id}</strong></div>}
          </div>
        </div>
      )}

      {/* Grid of Tests */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading tests catalog...
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '16px',
        }}>
          {scenarios.map((sc) => {
            const sev = getSeverityBadge(sc.severity);
            const isExecuting = runningId === sc.id;
            const friendly = FRIENDLY_NAMES[sc.id] || {
              title: sc.name,
              category: sc.category,
              description: sc.description,
              expected: sc.expected_detection,
            };

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
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '11px',
                      color: 'var(--color-accent-blue)',
                      fontWeight: 600,
                    }}>
                      {friendly.category}
                    </span>

                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: sev.bg,
                      color: sev.text,
                    }}>
                      {sev.label}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>
                    {friendly.title}
                  </h3>

                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
                    {friendly.description}
                  </p>

                  <div style={{
                    background: 'var(--color-bg-base)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: 'var(--color-text-secondary)',
                    marginBottom: '16px',
                  }}>
                    <div>Target Device: <strong style={{ color: '#fff' }}>{sc.target_device}</strong></div>
                    <div>Expected Result: <strong style={{ color: '#10b981' }}>{friendly.expected}</strong></div>
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
                    cursor: isExecuting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    transition: 'opacity 0.2s',
                  }}
                >
                  {isExecuting ? '⏳ Running Test...' : '▶ Run Test'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
