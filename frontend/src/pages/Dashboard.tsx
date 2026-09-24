import React, { useState, useEffect } from 'react';
import { DeviceList, DeviceItem } from '../components/DeviceList';
import { LiveTelemetryFeed, FeedEvent } from '../components/LiveTelemetryFeed';
import { TelemetryGauges } from '../components/TelemetryGauges';
import { DeviceDetailModal } from '../components/DeviceDetailModal';
import { AttackLauncher } from '../components/AttackLauncher';
import { SOCAlertsFeed } from '../components/SOCAlertsFeed';
import { AuditChainVisualizer } from '../components/AuditChainVisualizer';
import { ForensicTimeline } from '../components/ForensicTimeline';
import { wsService } from '../services/websocket';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const DashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'operations' | 'attacks' | 'soc' | 'audit' | 'forensics'>('operations');
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [summary, setSummary] = useState({ total: 0, online: 0, suspended: 0, provisioned: 0 });
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, any>>({});
  const [selectedDevice, setSelectedDevice] = useState<DeviceItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [simRunning, setSimRunning] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchDevices = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/devices/`);
      const data = await res.json();
      setDevices(data.devices || []);

      const sumRes = await fetch(`${API_BASE}/api/devices/summary`);
      const sumData = await sumRes.json();
      setSummary(sumData);

      const labRes = await fetch(`${API_BASE}/api/lab/status`);
      const labData = await labRes.json();
      setSimRunning(labData?.simulation?.running || false);

      const telemRes = await fetch(`${API_BASE}/api/telemetry/latest`);
      if (telemRes.ok) {
        const telemData = await telemRes.json();
        const map: Record<string, any> = {};
        (telemData.records || telemData.telemetry || telemData || []).forEach((item: any) => {
          if (item.device_id) {
            map[item.device_id] = item;
          }
        });
        setTelemetryMap((prev) => ({ ...map, ...prev }));
      }
    } catch (err) {
      console.error('Failed to fetch devices', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 5000);

    wsService.connect();
    setWsConnected(wsService.isConnected);

    const unsubscribe = wsService.on('*', (evt) => {
      setWsConnected(true);
      const feedItem: FeedEvent = {
        id: Math.random().toString(36).substring(7),
        type: evt.event_type || 'event',
        timestamp: evt.timestamp || new Date().toISOString(),
        device_id: evt.device_id as string | undefined,
        data: evt,
      };
      setEvents((prev) => [feedItem, ...prev].slice(0, 50));

      if (evt.event_type === 'telemetry_received' && evt.device_id) {
        const dId = String(evt.device_id);
        setTelemetryMap((prev) => ({
          ...prev,
          [dId]: evt.data || evt,
        }));
      }

      if (evt.event_type === 'device_status_changed' || evt.event_type === 'security_alert_created') {
        fetchDevices();
        setRefreshTrigger((prev) => prev + 1);
      }
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  const handleDeviceAction = async (deviceId: string, action: 'suspend' | 'reinstate' | 'revoke') => {
    try {
      await fetch(`${API_BASE}/api/devices/${deviceId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: `Action via Dashboard: ${action}` }),
      });
      await fetchDevices();
      setRefreshTrigger((prev) => prev + 1);
      if (selectedDevice && selectedDevice.device_id === deviceId) {
        setSelectedDevice((prev) => prev ? { ...prev, status: action === 'suspend' ? 'SUSPENDED' : action === 'revoke' ? 'REVOKED' : 'ONLINE' } : null);
      }
    } catch (err) {
      console.error(`Failed to ${action} device`, err);
    }
  };

  const toggleSimulation = async () => {
    try {
      const endpoint = simRunning ? '/api/lab/stop' : '/api/lab/start';
      await fetch(`${API_BASE}${endpoint}`, { method: 'POST' });
      await fetchDevices();
    } catch (err) {
      console.error('Simulation toggle failed', err);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🔬 Virtual IoT Security Laboratory
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
            Cyber Operations & Monitoring Dashboard · Live Simulation Fleet
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={toggleSimulation}
            style={{
              background: simRunning ? 'var(--color-severity-critical)' : 'var(--color-status-online)',
              border: 'none',
              color: '#fff',
              fontWeight: 600,
              padding: '8px 16px',
              borderRadius: 'var(--border-radius)',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'background 0.2s',
            }}
          >
            {simRunning ? '⏹ Stop Simulation' : '▶ Start Simulation'}
          </button>
          <button
            onClick={fetchDevices}
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
              padding: '8px 14px',
              borderRadius: 'var(--border-radius)',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '8px',
        borderBottom: '1px solid var(--color-border)',
        marginBottom: '24px',
        paddingBottom: '2px',
      }}>
        {[
          { id: 'operations', label: '📊 Operations & Telemetry' },
          { id: 'attacks', label: '⚔️ Attack Simulator (A–G)' },
          { id: 'soc', label: '🚨 SOC Alerts & Defense' },
          { id: 'audit', label: '⛓️ Cryptographic Audit Ledger' },
          { id: 'forensics', label: '🔍 Forensic Investigation' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              background: activeTab === tab.id ? 'var(--color-bg-secondary)' : 'transparent',
              border: '1px solid',
              borderColor: activeTab === tab.id ? 'var(--color-border)' : 'transparent',
              borderBottomColor: activeTab === tab.id ? 'var(--color-bg-secondary)' : 'transparent',
              borderTopLeftRadius: 'var(--border-radius)',
              borderTopRightRadius: 'var(--border-radius)',
              color: activeTab === tab.id ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
              fontWeight: 600,
              fontSize: '14px',
              padding: '10px 18px',
              cursor: 'pointer',
              marginBottom: activeTab === tab.id ? '-1px' : '0',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OPERATIONS & TELEMETRY */}
      {activeTab === 'operations' && (
        <>
          {/* Summary Metrics */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px',
          }}>
            {[
              { label: 'Total Fleet', value: summary.total, color: 'var(--color-text-primary)' },
              { label: 'Provisioned', value: summary.provisioned, color: '#58a6ff' },
              { label: 'Online Nodes', value: summary.online, color: 'var(--color-status-online)' },
              { label: 'Suspended', value: summary.suspended, color: 'var(--color-status-suspended)' },
            ].map((m, i) => (
              <div key={i} style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--border-radius)',
                padding: '16px',
              }}>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  {m.label}
                </div>
                <div style={{ fontSize: '28px', fontWeight: 700, color: m.color }}>
                  {m.value}
                </div>
              </div>
            ))}
          </div>

          {/* Telemetry Visual Gauges */}
          <TelemetryGauges
            devices={devices}
            telemetryMap={telemetryMap}
            onInspectDevice={(dev) => setSelectedDevice(dev)}
          />

          {/* Device Registry Table */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Device Registry & Hardware Nodes
              </h2>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                Click "Inspect" to view telemetry logs & access control capabilities
              </span>
            </div>
            <DeviceList
              devices={devices}
              onAction={handleDeviceAction}
              onInspect={(dev) => setSelectedDevice(dev)}
              loading={loading}
            />
          </div>

          {/* Live Event Stream */}
          <LiveTelemetryFeed events={events} wsConnected={wsConnected} />
        </>
      )}

      {/* TAB 2: ATTACK SIMULATOR (A–G) */}
      {activeTab === 'attacks' && (
        <AttackLauncher
          onAttackLaunched={() => {
            fetchDevices();
            setRefreshTrigger((prev) => prev + 1);
          }}
        />
      )}

      {/* TAB 3: SOC ALERTS & DEFENSE */}
      {activeTab === 'soc' && (
        <SOCAlertsFeed
          onQuarantineDevice={(devId) => handleDeviceAction(devId, 'suspend')}
          refreshTrigger={refreshTrigger}
        />
      )}

      {/* TAB 4: CRYPTOGRAPHIC AUDIT LEDGER */}
      {activeTab === 'audit' && (
        <AuditChainVisualizer />
      )}

      {/* TAB 5: FORENSIC INVESTIGATION */}
      {activeTab === 'forensics' && (
        <ForensicTimeline devices={devices} />
      )}

      {/* Slide-over Device Detail Modal */}
      {selectedDevice && (
        <DeviceDetailModal
          device={selectedDevice}
          onClose={() => setSelectedDevice(null)}
          onAction={handleDeviceAction}
        />
      )}
    </div>
  );
};