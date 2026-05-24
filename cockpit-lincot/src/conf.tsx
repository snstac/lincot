import { EnvVarDefinition } from './types';

export const CONF_PARAMS: Record<string, EnvVarDefinition> = {
    COT_URL: {
        type: 'url',
        description: 'URL of the CoT destination (Mesh SA, TAK Server, etc.)',
        defaultValue: 'udp+wo://239.2.3.1:6969',
        validation: /^(udp\+wo|http|https|udp|tcp|tls|file|log|tcp\+wo|udp\+broadcast):\/\/[^\s]+$/,
        requiresQuoting: false,
        required: true
    },

    CALLSIGN: {
        type: 'string',
        description: 'Marker callsign (default: system hostname)',
        defaultValue: '',
        requiresQuoting: false,
        required: false
    },

    COT_UID: {
        type: 'string',
        description: 'Stable CoT UID (default: /etc/machine-id)',
        defaultValue: '',
        requiresQuoting: false,
        required: false
    },

    STATIC_LAT: {
        type: 'number',
        description: 'Fixed latitude (requires STATIC_LON; disables gpsd mode)',
        defaultValue: '',
        validation: /^-?\d+(\.\d+)?$/,
        required: false
    },

    STATIC_LON: {
        type: 'number',
        description: 'Fixed longitude (requires STATIC_LAT; disables gpsd mode)',
        defaultValue: '',
        validation: /^-?\d+(\.\d+)?$/,
        required: false
    },

    STATIC_HAE: {
        type: 'number',
        description: 'Fixed altitude (HAE), optional',
        defaultValue: '',
        validation: /^-?\d+(\.\d+)?$/,
        required: false
    },

    GPS_INFO_CMD: {
        type: 'string',
        description: 'Command to fetch gpspipe TPV JSON',
        defaultValue: 'gpspipe --json -n 5',
        requiresQuoting: false,
        required: false
    },

    POLL_INTERVAL: {
        type: 'number',
        description: 'Seconds between position reports',
        defaultValue: '61',
        validation: /^\d+$/,
        range: [1, 86400],
        required: false
    },

    COT_TYPE: {
        type: 'string',
        description: 'CoT event type',
        defaultValue: 'a-f-G-E-S',
        validation: /^[a-zA-Z0-9\-_.]*$/,
        requiresQuoting: false,
        required: false
    },

    COT_STALE: {
        type: 'number',
        description: 'CoT stale period in seconds',
        defaultValue: '3600',
        validation: /^\d+$/,
        required: false
    },

    COCKPIT_URL: {
        type: 'url',
        description: 'Cockpit URL included in CoT remarks and link',
        defaultValue: '',
        validation: /^(?:https?):\/\/[^\s]+$/,
        requiresQuoting: false,
        required: false
    },

    SSH_USER: {
        type: 'string',
        description: 'SSH username hint in CoT remarks',
        defaultValue: 'pi',
        requiresQuoting: false,
        required: false
    },

    REMARKS_EXTRA: {
        type: 'string',
        description: 'Additional freeform remark text',
        defaultValue: '',
        requiresQuoting: false,
        required: false
    },

    DEBUG: {
        type: 'boolean',
        description: 'PyTAK debug logging',
        defaultValue: 'false',
        validation: /^(true|false|yes|no|1|0)$/i,
        required: false
    },

    TAK_PROTO: {
        type: 'number',
        description: 'PyTAK TAK protocol variant',
        defaultValue: '',
        validation: /^\d+$/,
        required: false
    },

    PREF_PACKAGE: {
        type: 'path',
        description: 'TAK Data Package (.zip) with connection settings',
        defaultValue: '',
        validation: /^(?:|[/][\w./-]*)$/,
        requiresQuoting: false,
        required: false
    },

    PYTAK_TLS_CLIENT_CERT: {
        type: 'path',
        description: 'TLS client certificate (PEM)',
        defaultValue: '',
        validation: /^(?:|[/][\w./-]*)$/,
        requiresQuoting: false,
        required: false
    },

    PYTAK_TLS_CLIENT_KEY: {
        type: 'path',
        description: 'TLS client private key (PEM)',
        defaultValue: '',
        validation: /^(?:|[/][\w./-]*)$/,
        requiresQuoting: false,
        required: false
    },

    PYTAK_TLS_CLIENT_PASSWORD: {
        type: 'string',
        description: 'Password for TLS client key/cert',
        defaultValue: '',
        requiresQuoting: false,
        required: false
    },

    PYTAK_TLS_DONT_VERIFY: {
        type: 'boolean',
        description: 'Disable TLS certificate verification',
        defaultValue: 'false',
        validation: /^(true|false|yes|no|1|0)$/i,
        required: false
    },

    PYTAK_TLS_DONT_CHECK_HOSTNAME: {
        type: 'boolean',
        description: 'Disable TLS hostname verification',
        defaultValue: 'false',
        validation: /^(true|false|yes|no|1|0)$/i,
        required: false
    },

    PYTAK_TLS_CLIENT_CAFILE: {
        type: 'path',
        description: 'CA trust store for TLS verification',
        defaultValue: '',
        validation: /^(?:|[/][\w./-]*)$/,
        requiresQuoting: false,
        required: false
    },

    PYTAK_TLS_SERVER_EXPECTED_HOSTNAME: {
        type: 'string',
        description: 'Expected TLS server hostname/CN',
        defaultValue: '',
        requiresQuoting: false,
        required: false
    },
};
