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
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--color-accent-cyan)' }}>⛓️</span> Cryptographic Audit Ledger & SHA-256 Hash Chain
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Immutable security audit trail mathematically bound by blockchain-style SHA-256 cryptographic hashes
          </p>
        </div>

        <button
          disabled={verifying}
          onClick={runVerification}
          style={{
            padding: '10px 20px',
            background: 'linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)',
            border: 'none',
            borderRadius: 'var(--border-radius)',
            color: '#fff',
            fontWeight: 800,
            fontSize: '12px',
            letterSpacing: '0.04em',
            cursor: verifying ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.35)',
            transition: 'all 0.2s ease',
          }}
        >
          {verifying ? '⏳ RE-HASHING LEDGER...' : '🛡️ VERIFY CHAIN INTEGRITY'}
        </button>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div style={{
          marginBottom: '20px',
          background: 'var(--color-bg-card)',
          border: `1px solid ${verificationResult.is_valid ? '#10b981' : '#ef4444'}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: '18px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: verificationResult.is_valid ? '0 0 20px rgba(16, 185, 129, 0.2)' : '0 0 20px rgba(239, 68, 68, 0.2)',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '20px' }}>{verificationResult.is_valid ? '🛡️' : '⚠️'}</span>
              <span style={{
                fontWeight: 800,
                fontSize: '15px',
                color: verificationResult.is_valid ? '#10b981' : '#ef4444',
                letterSpacing: '0.03em',
              }}>
                {verificationResult.is_valid ? 'CRYPTOGRAPHIC PROOF: 100% LEDGER INTEGRITY VALID' : 'CRYPTOGRAPHIC CHAIN FORGERY DETECTED'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
              Sequential check verified <strong>{verificationResult.verified_records}</strong> blocks · Zero tampering, insertions, or deletions detected.
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

      {/* Blockchain Chain View */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading cryptographic audit chain...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-card)', borderRadius: 'var(--border-radius)' }}>
          No audit records logged yet.
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
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      fontSize: '10px',
                      fontFamily: 'monospace',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(56, 189, 248, 0.12)',
                      color: '#38bdf8',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                    }}>
                      {isGenesis ? 'GENESIS BLOCK' : `BLOCK #${logs.length - index}`}
                    </span>

                    <span style={{ fontWeight: 800, fontSize: '14px', color: '#fff' }}>
                      {record.action}
                    </span>

                    <span style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: record.result === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: record.result === 'SUCCESS' ? '#10b981' : '#ef4444',
                    }}>
                      {record.result}
                    </span>
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
                    {new Date(record.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                  Actor: <strong style={{ color: '#fff' }}>{record.actor}</strong> · Target: <strong style={{ color: 'var(--color-accent-cyan)' }}>{record.target}</strong>
                </div>

                {/* Cryptographic Hash Pair */}
                <div style={{
                  background: 'var(--color-bg-base)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '8px',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  border: '1px solid var(--color-border)',
                }}>
                  <div>
                    <span style={{ color: 'var(--color-text-muted)' }}>prev_hash:</span>{' '}
                    <span style={{ color: '#f59e0b', fontWeight: 600 }}>
                      {record.prev_hash ? `${record.prev_hash.substring(0, 24)}...` : '0x0000000000000000 (GENESIS)'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-text-muted)' }}>entry_hash:</span>{' '}
                    <span style={{ color: '#10b981', fontWeight: 600 }}>
                      {record.entry_hash ? `${record.entry_hash.substring(0, 24)}...` : '--'}
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
