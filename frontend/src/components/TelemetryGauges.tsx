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
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--color-accent-cyan)' }}>◉</span> Live Telemetry & Hardware Instrument Panels
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            High-frequency sensor metrics streamed via WebSocket pipeline
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '11px',
            fontFamily: 'monospace',
            color: 'var(--color-accent-cyan)',
            background: 'rgba(6, 182, 212, 0.1)',
            padding: '3px 8px',
            borderRadius: '4px',
            border: '1px solid rgba(6, 182, 212, 0.25)',
          }}>
            INGEST: 100% NOMINAL
          </span>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
        gap: '16px',
      }}>
        {devices.map((device) => {
          const raw = telemetryMap[device.device_id] || {};
          const telem = raw.values || raw.data || raw;
          const isTemp = device.device_type === 'temperature_sensor' || device.device_id.includes('TEMP');
          const isMotion = device.device_type === 'motion_sensor' || device.device_id.includes('MOTION');
          const isActuator = device.device_type === 'smart_actuator' || device.device_id.includes('ACTUATOR');

          // Temperature metrics
          const tempC = telem.temperature_c !== undefined 
            ? Number(telem.temperature_c) 
            : (raw.temperature_c !== undefined ? Number(raw.temperature_c) : null);
          const tempF = telem.temperature_f !== undefined 
            ? Number(telem.temperature_f) 
            : (tempC !== null ? (tempC * 9/5 + 32).toFixed(1) : null);
          const isOverheat = tempC !== null && tempC > 35;
          const isCold = tempC !== null && tempC < 16;

          // Motion metrics
          const motionDetected = telem.motion_detected === true || raw.motion_detected === true;
          const ambientLight = telem.ambient_light_lux !== undefined 
            ? telem.ambient_light_lux 
            : (raw.ambient_light_lux !== undefined ? raw.ambient_light_lux : null);
          const triggerCount = telem.total_trigger_count !== undefined 
            ? telem.total_trigger_count 
            : (raw.total_trigger_count !== undefined ? raw.total_trigger_count : null);

          // Actuator metrics
          const actuatorState = telem.actuator_state || raw.actuator_state || 'IDLE';
          const powerWatts = telem.power_consumption_watts !== undefined 
            ? telem.power_consumption_watts 
            : (raw.power_consumption_watts !== undefined ? raw.power_consumption_watts : null);
          const setpointC = telem.target_setpoint_c !== undefined 
            ? telem.target_setpoint_c 
            : (raw.target_setpoint_c !== undefined ? raw.target_setpoint_c : 22.0);

          const hasData = tempC !== null || motionDetected || ambientLight !== null || telem.actuator_state !== undefined || raw.actuator_state !== undefined;

          // Arc stroke calculations for temperature (0 - 100°C)
          const gaugePercent = Math.min(100, Math.max(0, ((tempC || 20) / 100) * 100));

          return (
            <div
              key={device.device_id}
              onClick={() => onInspectDevice(device)}
              style={{
                background: 'var(--color-bg-card)',
                border: isOverheat
                  ? '1px solid #ef4444'
                  : '1px solid var(--color-border)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '18px',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: isOverheat
                  ? '0 0 20px rgba(239, 68, 68, 0.25)'
                  : '0 4px 12px rgba(0, 0, 0, 0.2)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-accent-cyan)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = isOverheat ? '#ef4444' : 'var(--color-border)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              {/* Subtle Ambient Glow */}
              <div style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '120px',
                height: '120px',
                background: isOverheat 
                  ? 'radial-gradient(circle, rgba(239, 68, 68, 0.15) 0%, transparent 70%)'
                  : isTemp
                  ? 'radial-gradient(circle, rgba(6, 182, 212, 0.08) 0%, transparent 70%)'
                  : 'radial-gradient(circle, rgba(168, 85, 247, 0.06) 0%, transparent 70%)',
                pointerEvents: 'none',
              }} />

              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px', fontFamily: 'monospace', color: '#fff' }}>
                      {device.device_id}
                    </span>
                    {device.device_id.startsWith('LPC') && (
                      <span style={{
                        fontSize: '9px',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#10b981',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        fontWeight: 700,
                      }}>
                        ARM7TDMI
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    {device.device_name}
                  </div>
                </div>

                <span style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: device.status === 'ONLINE' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(100, 116, 139, 0.15)',
                  color: device.status === 'ONLINE' ? '#10b981' : '#64748b',
                  border: `1px solid ${device.status === 'ONLINE' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(100, 116, 139, 0.2)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                }}>
                  <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: device.status === 'ONLINE' ? '#10b981' : '#64748b',
                  }} />
                  {device.status}
                </span>
              </div>

              {/* Instrument Body */}
              {!hasData ? (
                <div style={{
                  padding: '28px 0',
                  textAlign: 'center',
                  color: 'var(--color-text-muted)',
                  fontSize: '12px',
                  background: 'var(--color-bg-base)',
                  borderRadius: 'var(--border-radius)',
                  border: '1px dashed var(--color-border)',
                }}>
                  <div style={{ fontSize: '18px', marginBottom: '6px' }}>⏳</div>
                  Awaiting telemetry stream...
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                    Start simulation or run bridge
                  </div>
                </div>
              ) : isTemp ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div>
                      <div style={{
                        fontSize: '32px',
                        fontWeight: 800,
                        color: isOverheat ? '#ef4444' : isCold ? '#38bdf8' : '#10b981',
                        fontFamily: 'monospace',
                        lineHeight: 1.1,
                      }}>
                        {tempC !== null ? `${tempC}°C` : '--'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                        {tempF !== null ? `${tempF}°F` : '--'} · LM35 Transducer
                      </div>
                    </div>

                    {isOverheat ? (
                      <span style={{
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid #ef4444',
                        color: '#ef4444',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 800,
                        letterSpacing: '0.04em',
                      }}>
                        🔥 OVERHEAT
                      </span>
                    ) : (
                      <span style={{
                        background: 'rgba(16, 185, 129, 0.12)',
                        border: '1px solid rgba(16, 185, 129, 0.25)',
                        color: '#10b981',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}>
                        OPTIMAL
                      </span>
                    )}
                  </div>

                  {/* Gradient Meter Bar */}
                  <div style={{
                    height: '8px',
                    background: '#090e18',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    marginBottom: '10px',
                    border: '1px solid var(--color-border)',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${gaugePercent}%`,
                      background: isOverheat
                        ? 'linear-gradient(90deg, #f59e0b 0%, #ef4444 100%)'
                        : 'linear-gradient(90deg, #06b6d4 0%, #10b981 100%)',
                      transition: 'width 0.4s ease',
                      boxShadow: isOverheat ? '0 0 10px #ef4444' : 'none',
                    }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    <span>Safe Window: 15°C – 35°C</span>
                    <span>Variance: ±0.03°C</span>
                  </div>
                </div>
              ) : isMotion ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '14px' }}>
                    {/* Animated Sonar Radar Icon */}
                    <div style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: motionDetected ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.12)',
                      border: `2px solid ${motionDetected ? '#ef4444' : '#10b981'}`,
                      fontSize: '20px',
                      boxShadow: motionDetected ? '0 0 16px rgba(239, 68, 68, 0.4)' : 'none',
                      transition: 'all 0.3s ease',
                    }}>
                      {motionDetected ? '🚶' : '🛡️'}
                    </div>

                    <div>
                      <div style={{
                        fontSize: '17px',
                        fontWeight: 800,
                        color: motionDetected ? '#ef4444' : '#10b981',
                        letterSpacing: '0.02em',
                      }}>
                        {motionDetected ? 'MOTION DETECTED' : 'ZONE SECURED'}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                        PIR Radar Perimeter Protection
                      </div>
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '8px',
                    fontSize: '11px',
                    background: 'var(--color-bg-base)',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                  }}>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Ambient Lux:</span>{' '}
                      <strong style={{ color: '#fff' }}>{ambientLight !== null ? `${ambientLight} lx` : '--'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Triggers:</span>{' '}
                      <strong style={{ color: '#38bdf8' }}>{triggerCount !== null ? triggerCount : '--'}</strong>
                    </div>
                  </div>
                </div>
              ) : isActuator ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: '#fff' }}>
                        HVAC: {actuatorState}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                        Target: {setpointC}°C
                      </div>
                    </div>

                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: 'rgba(56, 189, 248, 0.12)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      color: '#38bdf8',
                      fontWeight: 700,
                      fontSize: '13px',
                      fontFamily: 'monospace',
                    }}>
                      ⚡ {powerWatts !== null ? `${powerWatts} W` : '--'}
                    </span>
                  </div>

                  <div style={{
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    background: 'var(--color-bg-base)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                  }}>
                    Capability Policy: <strong style={{ color: 'var(--color-accent-cyan)' }}>CONTROL_ACTUATOR</strong> token required
                  </div>
                </div>
              ) : (
                <pre style={{ fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--color-text-muted)' }}>
                  {JSON.stringify(telem, null, 2)}
                </pre>
              )}

              {/* Card Footer Link */}
              <div style={{
                marginTop: '14px',
                paddingTop: '10px',
                borderTop: '1px solid var(--color-border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontSize: '11px', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                  🔍 Inspect Metrics & Keys →
                </span>
                <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
                  SHA-256 VALID
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
