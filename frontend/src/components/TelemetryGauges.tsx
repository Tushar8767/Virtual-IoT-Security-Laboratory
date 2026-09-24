import React from 'react';
import { DeviceItem } from './DeviceList';

interface TelemetryGaugesProps {
  devices: DeviceItem[];
  telemetryMap: Record<string, any>;
  onInspectDevice: (device: DeviceItem) => void;
}

export const TelemetryGauges: React.FC<TelemetryGaugesProps> = ({
  devices,
  telemetryMap,
  onInspectDevice,
}) => {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
          📡 Live Telemetry & Visual Sensor Gauges
        </h2>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Auto-updating from WebSocket Stream
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
      }}>
        {devices.map((device) => {
          const raw = telemetryMap[device.device_id] || {};
          const telem = raw.values || raw.data || raw;
          const isTemp = device.device_type === 'temperature_sensor' || device.device_id.includes('TEMP');
          const isMotion = device.device_type === 'motion_sensor' || device.device_id.includes('MOTION');
          const isActuator = device.device_type === 'smart_actuator' || device.device_id.includes('ACTUATOR');

          // Temperature values
          const tempC = telem.temperature_c !== undefined 
            ? Number(telem.temperature_c) 
            : (raw.temperature_c !== undefined ? Number(raw.temperature_c) : null);
          const tempF = telem.temperature_f !== undefined 
            ? Number(telem.temperature_f) 
            : (tempC !== null ? (tempC * 9/5 + 32).toFixed(1) : null);
          const isOverheat = tempC !== null && tempC > 35;
          const isCold = tempC !== null && tempC < 16;

          // Motion values
          const motionDetected = telem.motion_detected === true || raw.motion_detected === true;
          const ambientLight = telem.ambient_light_lux !== undefined 
            ? telem.ambient_light_lux 
            : (raw.ambient_light_lux !== undefined ? raw.ambient_light_lux : null);
          const triggerCount = telem.total_trigger_count !== undefined 
            ? telem.total_trigger_count 
            : (raw.total_trigger_count !== undefined ? raw.total_trigger_count : null);

          // Actuator values
          const actuatorState = telem.actuator_state || raw.actuator_state || 'IDLE';
          const powerWatts = telem.power_consumption_watts !== undefined 
            ? telem.power_consumption_watts 
            : (raw.power_consumption_watts !== undefined ? raw.power_consumption_watts : null);
          const setpointC = telem.target_setpoint_c !== undefined 
            ? telem.target_setpoint_c 
            : (raw.target_setpoint_c !== undefined ? raw.target_setpoint_c : 22.0);

          const hasData = tempC !== null || motionDetected || ambientLight !== null || telem.actuator_state !== undefined || raw.actuator_state !== undefined;

          return (
            <div
              key={device.device_id}
              onClick={() => onInspectDevice(device)}
              style={{
                background: 'var(--color-bg-secondary)',
                border: isOverheat
                  ? '1px solid var(--color-severity-critical)'
                  : '1px solid var(--color-border)',
                borderRadius: 'var(--border-radius)',
                padding: '16px',
                cursor: 'pointer',
                transition: 'transform 0.15s ease, border-color 0.2s ease',
                boxShadow: isOverheat ? '0 0 12px rgba(248, 81, 73, 0.25)' : 'none',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent-blue)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = isOverheat ? 'var(--color-severity-critical)' : 'var(--color-border)')}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 600, fontSize: '14px', fontFamily: 'monospace' }}>
                      {device.device_id}
                    </span>
                    {device.device_id.startsWith('LPC') && (
                      <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: '#238636', color: '#fff', fontWeight: 600 }}>
                        PROTEUS
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    {device.device_name}
                  </div>
                </div>
                <span style={{
                  fontSize: '11px',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  background: device.status === 'ONLINE' ? 'rgba(63, 185, 80, 0.15)' : 'rgba(139, 148, 158, 0.15)',
                  color: device.status === 'ONLINE' ? 'var(--color-status-online)' : 'var(--color-status-offline)',
                  fontWeight: 600,
                }}>
                  ● {device.status}
                </span>
              </div>

              {/* Gauge Body */}
              {!hasData ? (
                <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '13px' }}>
                  ⏳ Awaiting telemetry stream...
                  <div style={{ fontSize: '11px', marginTop: '4px' }}>Click "Start Simulation" above</div>
                </div>
              ) : isTemp ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '34px',
                      fontWeight: 700,
                      color: isOverheat ? 'var(--color-severity-critical)' : isCold ? 'var(--color-accent-blue)' : 'var(--color-accent-green)',
                      fontFamily: 'monospace',
                    }}>
                      {tempC !== null ? `${tempC}°C` : '--'}
                    </span>
                    <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                      / {tempF !== null ? `${tempF}°F` : '--'}
                    </span>
                    {isOverheat && (
                      <span style={{
                        marginLeft: 'auto',
                        background: 'rgba(248, 81, 73, 0.2)',
                        color: 'var(--color-severity-critical)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}>
                        🔥 OVERHEAT ANOMALY
                      </span>
                    )}
                  </div>

                  {/* Temperature Range Bar */}
                  <div style={{ height: '6px', background: '#21262d', borderRadius: '3px', overflow: 'hidden', marginBottom: '10px' }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(100, Math.max(5, ((tempC || 20) / 100) * 100))}%`,
                      background: isOverheat ? 'var(--color-severity-critical)' : isCold ? 'var(--color-accent-blue)' : 'var(--color-accent-green)',
                      transition: 'width 0.4s ease, background 0.4s ease',
                    }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    <span>Threshold: 15°C – 35°C</span>
                    <span>Health: <strong style={{ color: isOverheat ? 'var(--color-severity-critical)' : 'var(--color-accent-green)' }}>{telem.sensor_health || 'OPTIMAL'}</strong></span>
                  </div>
                </div>
              ) : isMotion ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: motionDetected ? 'rgba(248, 81, 73, 0.2)' : 'rgba(63, 185, 80, 0.15)',
                      border: `2px solid ${motionDetected ? 'var(--color-severity-critical)' : 'var(--color-accent-green)'}`,
                      fontSize: '18px',
                      transition: 'all 0.3s ease',
                    }}>
                      {motionDetected ? '🚶' : '🛡️'}
                    </div>
                    <div>
                      <div style={{
                        fontSize: '18px',
                        fontWeight: 700,
                        color: motionDetected ? 'var(--color-severity-critical)' : 'var(--color-accent-green)',
                      }}>
                        {motionDetected ? 'MOTION DETECTED' : 'ZONE CLEAR'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                        PIR Security Radar
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px', background: 'var(--color-bg-primary)', padding: '8px', borderRadius: '4px' }}>
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Ambient Light:</span>{' '}
                      <strong>{ambientLight !== null ? `${ambientLight} lx` : '--'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Triggers:</span>{' '}
                      <strong>{triggerCount !== null ? triggerCount : '--'}</strong>
                    </div>
                  </div>
                </div>
              ) : isActuator ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div>
                      <span style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                        HVAC: {actuatorState}
                      </span>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                        Setpoint: {setpointC}°C
                      </div>
                    </div>
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: actuatorState === 'ON' ? 'rgba(47, 129, 247, 0.15)' : 'rgba(139, 148, 158, 0.15)',
                      color: actuatorState === 'ON' ? 'var(--color-accent-blue)' : 'var(--color-text-muted)',
                      fontWeight: 700,
                      fontSize: '12px',
                    }}>
                      ⚡ {powerWatts !== null ? `${powerWatts} W` : '--'}
                    </span>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-primary)', padding: '6px 8px', borderRadius: '4px' }}>
                    Capability Control: <strong>CONTROL_ACTUATOR</strong> token required
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  <pre style={{ fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {JSON.stringify(telem, null, 2)}
                  </pre>
                </div>
              )}

              {/* Footer action link */}
              <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--color-border-subtle)', textAlign: 'right' }}>
                <span style={{ fontSize: '11px', color: 'var(--color-accent-blue)', fontWeight: 500 }}>
                  🔍 View Full Details & Historical Packets →
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
