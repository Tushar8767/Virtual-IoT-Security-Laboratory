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
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            📡 Device Sensors & Live Readings
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
            Live data sent by devices every few seconds over the network
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
          Live Updating
        </span>
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
                transition: 'border-color 0.2s, transform 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-accent-blue)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = isOverheat ? '#ef4444' : 'var(--color-border)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px', fontFamily: 'monospace', color: '#fff' }}>
                      {device.device_id}
                    </span>
                    {device.device_id.startsWith('LPC') && (
                      <span style={{
                        fontSize: '10px',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#10b981',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        fontWeight: 600,
                      }}>
                        Hardware Node
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
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
                }}>
                  ● {device.status === 'ONLINE' ? 'Online' : device.status}
                </span>
              </div>

              {/* Sensor Reading */}
              {!hasData ? (
                <div style={{
                  padding: '24px 0',
                  textAlign: 'center',
                  color: 'var(--color-text-muted)',
                  fontSize: '13px',
                  background: 'var(--color-bg-base)',
                  borderRadius: 'var(--border-radius)',
                  border: '1px dashed var(--color-border)',
                }}>
                  ⏳ Waiting for device readings...
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                    Click "Start Devices" above to begin
                  </div>
                </div>
              ) : isTemp ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div>
                      <div style={{
                        fontSize: '32px',
                        fontWeight: 800,
                        color: isOverheat ? '#ef4444' : isCold ? '#38bdf8' : '#10b981',
                        fontFamily: 'monospace',
                        lineHeight: 1.1,
                      }}>
                        {tempC !== null ? `${tempC} °C` : '--'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '3px' }}>
                        {tempF !== null ? `(${tempF} °F)` : ''} · Temperature Sensor
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
                        fontWeight: 700,
                      }}>
                        🔥 High Temp Warning
                      </span>
                    ) : (
                      <span style={{
                        background: 'rgba(16, 185, 129, 0.12)',
                        border: '1px solid rgba(16, 185, 129, 0.25)',
                        color: '#10b981',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                      }}>
                        Normal
                      </span>
                    )}
                  </div>

                  {/* Range Progress Bar */}
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
                    }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    <span>Normal Range: 15°C to 35°C</span>
                    <span>Status: <strong>{isOverheat ? 'Abnormal' : 'Healthy'}</strong></span>
                  </div>
                </div>
              ) : isMotion ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '14px' }}>
                    <div style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: motionDetected ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
                      border: `2px solid ${motionDetected ? '#ef4444' : '#10b981'}`,
                      fontSize: '20px',
                    }}>
                      {motionDetected ? '🚶' : '🛡️'}
                    </div>

                    <div>
                      <div style={{
                        fontSize: '16px',
                        fontWeight: 700,
                        color: motionDetected ? '#ef4444' : '#10b981',
                      }}>
                        {motionDetected ? 'Motion Detected' : 'No Motion Detected'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                        Area Motion Sensor
                      </div>
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '8px',
                    fontSize: '12px',
                    background: 'var(--color-bg-base)',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                  }}>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Room Light:</span>{' '}
                      <strong>{ambientLight !== null ? `${ambientLight} lux` : '--'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Times Triggered:</span>{' '}
                      <strong>{triggerCount !== null ? triggerCount : '--'}</strong>
                    </div>
                  </div>
                </div>
              ) : isActuator ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
                        Air Conditioner: {actuatorState}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                        Target Temperature: {setpointC}°C
                      </div>
                    </div>

                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: 'rgba(56, 189, 248, 0.12)',
                      color: '#38bdf8',
                      fontWeight: 700,
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                    }}>
                      ⚡ {powerWatts !== null ? `${powerWatts} W` : '--'}
                    </span>
                  </div>

                  <div style={{
                    fontSize: '12px',
                    color: 'var(--color-text-secondary)',
                    background: 'var(--color-bg-base)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--color-border)',
                  }}>
                    Security Policy: Only authorized operators can change settings
                  </div>
                </div>
              ) : null}

              {/* Footer */}
              <div style={{
                marginTop: '14px',
                paddingTop: '10px',
                borderTop: '1px solid var(--color-border-subtle)',
                textAlign: 'right',
              }}>
                <span style={{ fontSize: '12px', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                  View Device Details & History →
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
