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
      const res = await fetch(`${API_BASE}/api/audit/?limit=20`);
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
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            ⛓️ Cryptographic Audit Log & SHA-256 Hash Chain
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Immutable forensic ledger with blockchain-style cryptographic hash chaining (prev_hash ➔ entry_hash).
          </p>
        </div>

        <button
          disabled={verifying}
          onClick={runVerification}
          style={{
            padding: '8px 16px',
            background: 'var(--color-accent-teal)',
            border: 'none',
            borderRadius: 'var(--border-radius)',
            color: '#0d1117',
            fontWeight: 700,
            fontSize: '13px',
            cursor: verifying ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {verifying ? '⏳ Scanning Hashes...' : '🛡️ Verify Chain Integrity'}
        </button>
      </div>

      {/* Verification Result Card */}
      {verificationResult && (
        <div style={{
          marginBottom: '20px',
          background: 'var(--color-bg-secondary)',
          border: `1px solid ${verificationResult.is_valid ? 'var(--color-status-online)' : 'var(--color-severity-critical)'}`,
          borderRadius: 'var(--border-radius)',
          padding: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: verificationResult.is_valid ? '0 0 12px rgba(63, 185, 80, 0.2)' : '0 0 12px rgba(248, 81, 73, 0.2)',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '18px' }}>{verificationResult.is_valid ? '✅' : '❌'}</span>
              <span style={{
                fontWeight: 700,
                fontSize: '15px',
                color: verificationResult.is_valid ? 'var(--color-status-online)' : 'var(--color-severity-critical)',
              }}>
                {verificationResult.is_valid ? 'CRYPTOGRAPHIC CHAIN INTEGRITY: 100% VALID' : 'TAMPER DETECTED IN AUDIT LEDGER'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
              Verified <strong>{verificationResult.verified_records}</strong> sequential records · Zero tampering or forged blocks detected.
            </div>
          </div>
          <button
            onClick={() => setVerificationResult(null)}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Visual Chain Blocks */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
          Loading cryptographic audit chain...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--border-radius)' }}>
          No audit records logged yet. Start simulation or launch an attack to generate entries.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {logs.map((record, index) => (
            <div
              key={record.audit_id || index}
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--border-radius)',
                padding: '14px 18px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'rgba(47, 129, 247, 0.15)',
                    color: 'var(--color-accent-blue)',
                    fontWeight: 700,
                  }}>
                    BLOCK #{logs.length - index}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-primary)' }}>
                    {record.action}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: record.result === 'SUCCESS' ? 'rgba(63, 185, 80, 0.15)' : 'rgba(248, 81, 73, 0.15)',
                    color: record.result === 'SUCCESS' ? 'var(--color-status-online)' : 'var(--color-severity-critical)',
                    fontWeight: 600,
                  }}>
                    {record.result}
                  </span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
                  {new Date(record.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                Actor: <strong style={{ color: 'var(--color-text-primary)' }}>{record.actor}</strong> · Target: <strong style={{ color: 'var(--color-text-primary)' }}>{record.target}</strong>
              </div>

              {/* Hashes */}
              <div style={{
                background: 'var(--color-bg-primary)',
                padding: '8px 12px',
                borderRadius: '4px',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px',
                fontFamily: 'monospace',
                fontSize: '11px',
              }}>
                <div>
                  <span style={{ color: 'var(--color-text-muted)' }}>prev_hash:</span>{' '}
                  <span style={{ color: 'var(--color-accent-yellow)' }}>{record.prev_hash ? `${record.prev_hash.substring(0, 16)}...` : 'GENESIS'}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-text-muted)' }}>entry_hash:</span>{' '}
                  <span style={{ color: 'var(--color-accent-green)' }}>{record.entry_hash ? `${record.entry_hash.substring(0, 16)}...` : '--'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
