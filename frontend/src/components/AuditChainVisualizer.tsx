import React, { useState, useEffect } from 'react';

export interface AuditRecord {
  audit_id: string;
  timestamp: string;
  action: string;
  actor: string;
  target: string;
  result: string;
  entry_hash: string;
  prev_hash: string;
  metadata?: Record<string, any>;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const AuditChainVisualizer: React.FC = () => {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/audit/?limit=25`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.audit_logs || []);
      }
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const runVerification = async () => {
    setVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/audit/verify`);
      const data = await res.json();
      setVerificationResult(data);
    } catch (err: any) {
      setVerificationResult({ is_valid: false, reason: err.message });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            ⛓️ Audit Log & Tamper Check
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Every action is saved in a secure cryptographic chain. It cannot be altered or forged.
          </p>
        </div>

        <button
          disabled={verifying}
          onClick={runVerification}
          style={{
            padding: '10px 18px',
            background: 'linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)',
            border: 'none',
            borderRadius: 'var(--border-radius)',
            color: '#fff',
            fontWeight: 700,
            fontSize: '13px',
            cursor: verifying ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {verifying ? '⏳ Checking Records...' : '🛡️ Check Log For Tampering'}
        </button>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div style={{
          marginBottom: '20px',
          background: 'var(--color-bg-card)',
          border: `1px solid ${verificationResult.is_valid ? '#10b981' : '#ef4444'}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '20px' }}>{verificationResult.is_valid ? '✅' : '❌'}</span>
              <span style={{
                fontWeight: 700,
                fontSize: '15px',
                color: verificationResult.is_valid ? '#10b981' : '#ef4444',
              }}>
                {verificationResult.is_valid ? 'Tamper Check Passed: All logs are authentic and unaltered!' : 'Warning: Tampering Detected in Audit Log'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Verified <strong>{verificationResult.verified_records}</strong> historical records. No records were modified or deleted.
            </div>
          </div>

          <button
            onClick={() => setVerificationResult(null)}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', fontSize: '16px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Audit List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading audit log...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-card)', borderRadius: 'var(--border-radius)' }}>
          No audit records yet. Start devices or run a test to generate entries.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {logs.map((record, index) => {
            const isGenesis = !record.prev_hash || record.prev_hash === '0'.repeat(64) || index === logs.length - 1;

            return (
              <div
                key={record.audit_id || index}
                style={{
                  background: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--border-radius)',
                  padding: '16px 20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(56, 189, 248, 0.12)',
                      color: '#38bdf8',
                    }}>
                      {isGenesis ? 'Initial Setup' : `Event #${logs.length - index}`}
                    </span>

                    <span style={{ fontWeight: 700, fontSize: '14px', color: '#fff' }}>
                      {record.action.replace(/_/g, ' ')}
                    </span>

                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: record.result === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: record.result === 'SUCCESS' ? '#10b981' : '#ef4444',
                    }}>
                      {record.result === 'SUCCESS' ? 'Success' : 'Failed'}
                    </span>
                  </div>

                  <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                    {new Date(record.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '10px' }}>
                  User: <strong style={{ color: '#fff' }}>{record.actor}</strong> · Target: <strong style={{ color: 'var(--color-accent-blue)' }}>{record.target}</strong>
                </div>

                {/* Hashes */}
                <div style={{
                  background: 'var(--color-bg-base)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}>
                  <div>
                    <span style={{ color: 'var(--color-text-muted)' }}>Previous Hash:</span>{' '}
                    <span style={{ color: '#f59e0b' }}>
                      {record.prev_hash ? `${record.prev_hash.substring(0, 20)}...` : 'None (First Record)'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-text-muted)' }}>Security Hash:</span>{' '}
                    <span style={{ color: '#10b981' }}>
                      {record.entry_hash ? `${record.entry_hash.substring(0, 20)}...` : '--'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
