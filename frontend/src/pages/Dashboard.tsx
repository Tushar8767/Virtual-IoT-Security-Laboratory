import React, { useState, useEffect } from 'react';
import { DeviceList, DeviceItem } from '../components/DeviceList';
import { LiveTelemetryFeed, FeedEvent } from '../components/LiveTelemetryFeed';
import { TelemetryGauges } from '../components/TelemetryGauges';
import { DeviceDetailModal } from '../components/DeviceDetailModal';
import { AttackLauncher } from '../components/AttackLauncher';
import { SOCAlertsFeed } from '../components/SOCAlertsFeed';
import { AuditChainVisualizer } from '../components/AuditChainVisualizer';
import { ForensicTimeline } from '../components/ForensicTimeline';
import { Navbar } from '../components/Navbar';
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
  const [activeAlertsCount, setActiveAlertsCount] = useState(0);
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

      const alertRes = await fetch(`${API_BASE}/api/security/alerts?status=ACTIVE`);
      if (alertRes.ok) {
        const alertData = await alertRes.json();
        setActiveAlertsCount(alertData.alerts?.length || alertData.count || 0);
      }

      const telemRes = await fetch(`${API_BASE}/api/telemetry/latest`);
      if (telemRes.ok) {
        const telemData = await telemRes.json();
        const map: Record<string, any> = {};
        (telemData.records || telemData.telemetry || telemData || []).forEach((item: any) => {
          if (item.device_id) {
            map[item.device_id] = item.values || item.data || item;
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
    const interval = setInterval(fetchDevices, 4000);

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
        const telemValues = (evt as any).values || evt.data || evt;
        setTelemetryMap((prev) => ({
          ...prev,
          [dId]: telemValues,
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Enterprise Cyber Navbar */}
      <Navbar
        simRunning={simRunning}
        onToggleSim={toggleSimulation}
        onRefresh={fetchDevices}
        wsConnected={wsConnected}
        activeAlertsCount={activeAlertsCount}
      />

      <main style={{ padding: '0 28px 40px', maxWidth: '1360px', margin: '0 auto', width: '100%' }}>
        {/* Navigation Tabs with Badges */}
        <div style={{
          display: 'flex',
          gap: '10px',
          borderBottom: '1px solid var(--color-border)',
          marginBottom: '26px',
          paddingBottom: '2px',
          overflowX: 'auto',
        }}>
          {[
            { id: 'operations', label: '📊 Live Device Data' },
            { id: 'attacks', label: '🧪 Security Tests' },
            { id: 'soc', label: '🚨 Security Alerts', badge: activeAlertsCount },
            { id: 'audit', label: '⛓️ Audit Log & Tamper Check' },
            { id: 'forensics', label: '🔍 Incident Investigation' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  background: isActive ? 'var(--color-bg-card)' : 'transparent',
                  border: '1px solid',
                  borderColor: isActive ? 'var(--color-border)' : 'transparent',
                  borderBottomColor: isActive ? 'var(--color-bg-card)' : 'transparent',
                  borderTopLeftRadius: 'var(--border-radius)',
                  borderTopRightRadius: 'var(--border-radius)',
                  color: isActive ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
                  fontWeight: 700,
                  fontSize: '13px',
                  padding: '12px 20px',
                  cursor: 'pointer',
                  marginBottom: isActive ? '-1px' : '0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{tab.label}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '10px',
                    background: '#ef4444',
                    color: '#fff',
                    boxShadow: '0 0 8px rgba(239, 68, 68, 0.4)',
                  }}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OPERATIONS & TELEMETRY */}
        {activeTab === 'operations' && (
          <>
            {/* Stat Cards */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '28px',
            }}>
              {[
                { label: 'Total Devices', value: summary.total, sub: 'All registered devices', color: '#fff', accent: 'var(--color-accent-cyan)' },
                { label: 'Online Devices', value: summary.online, sub: 'Sending live data', color: '#10b981', accent: '#10b981' },
                { label: 'New Devices', value: summary.provisioned, sub: 'Ready to connect', color: '#38bdf8', accent: '#38bdf8' },
                { label: 'Blocked Devices', value: summary.suspended, sub: 'Blocked for safety', color: summary.suspended > 0 ? '#ef4444' : '#64748b', accent: '#ef4444' },
              ].map((m, i) => (
                <div key={i} style={{
                  background: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--border-radius-lg)',
                  padding: '18px 20px',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                }}>
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: m.accent,
                  }} />
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.04em' }}>
                    {m.label}
                  </div>
                  <div style={{ fontSize: '30px', fontWeight: 800, color: m.color, marginTop: '4px', lineHeight: 1.1 }}>
                    {m.value}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                    {m.sub}
                  </div>
                </div>
              ))}
            </div>

            {/* Hardware Telemetry Instrument Panels */}
            <TelemetryGauges
              devices={devices}
              telemetryMap={telemetryMap}
              onInspectDevice={(dev) => setSelectedDevice(dev)}
            />

            {/* Device Registry Table */}
            <div style={{ marginBottom: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    Registered Devices
                  </h2>
                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    List of all connected devices, their current status, and quick actions
                  </p>
                </div>
              </div>
              <DeviceList
                devices={devices}
                onAction={handleDeviceAction}
                onInspect={(dev) => setSelectedDevice(dev)}
                loading={loading}
              />
            </div>

            {/* Live Terminal Stream */}
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
      </main>
    </div>
  );
};