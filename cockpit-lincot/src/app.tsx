/*
 * Copyright Sensors & Signals LLC https://www.snstac.com/
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Alert } from '@patternfly/react-core/dist/esm/components/Alert/index.js';
import {
    DataList,
    DataListCell,
    DataListItem,
    DataListItemCells,
    DataListItemRow,
} from '@patternfly/react-core/dist/esm/components/DataList/index.js';
import {
    Card,
    CardBody,
    CardExpandableContent,
    CardHeader,
    CardTitle,
} from '@patternfly/react-core/dist/esm/components/Card/index.js';
import { Checkbox } from '@patternfly/react-core';

import cockpit from 'cockpit';

import { CONF_PARAMS } from './conf';
import {
    type DefaultEnvLine,
    defaultFormFromConf,
    mergeFormValues,
    parseEnvDefault,
    serializeEnvDefault,
} from './envDefaultFile';
import { ServiceManagementCard, type ToastMessage } from './serviceCard';
import { TlsUploadCard } from './tlsCard';

const _ = cockpit.gettext;

const SERVICE_NAME = 'lincot';
const CONFIG_FILE = `/etc/default/${SERVICE_NAME}`;
const KNOWN_KEYS = new Set(Object.keys(CONF_PARAMS));

function StatusOutput({ serviceName }: { serviceName: string }) {
    const [statusOutput, setStatusOutput] = useState<string>('Loading...');
    useEffect(() => {
        let cancelled = false;
        async function fetchStatus() {
            try {
                const out = await cockpit.spawn(
                    ['systemctl', 'status', serviceName, '--no-pager'],
                    { superuser: 'try' }
                );
                if (!cancelled) setStatusOutput(out);
            } catch {
                if (!cancelled) setStatusOutput(_('Failed to get status output.'));
            }
        }
        fetchStatus();
        const interval = setInterval(fetchStatus, 4000);
        return () => {
            cancelled = true;
            clearInterval(interval);
        };
    }, [serviceName]);
    return (
        <pre
            style={{
                background: '#222',
                color: '#eee',
                padding: '1em',
                borderRadius: '4px',
                fontSize: '0.95em',
                overflowX: 'auto',
                maxHeight: 300,
            }}
        >
            {statusOutput}
        </pre>
    );
}

export const Application: React.FC = () => {
    const [fileLines, setFileLines] = useState<DefaultEnvLine[]>([]);
    const [envVarForm, setEnvVarForm] = useState<Record<string, string>>(() =>
        defaultFormFromConf(CONF_PARAMS)
    );
    const [formErrors, setFormErrors] = useState<Record<string, string>>({});
    const [configFileContents, setConfigFileContents] = useState<string>('');
    const [configLoadError, setConfigLoadError] = useState<string | null>(null);
    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    dirtyRef.current = dirty;

    const [toast, setToast] = useState<ToastMessage | null>(null);
    const [saveBusy, setSaveBusy] = useState(false);
    const [saveAndRestart, setSaveAndRestart] = useState(false);

    const [isConfigExpanded, setIsConfigExpanded] = useState(true);
    const [isDebugExpanded, setIsDebugExpanded] = useState(false);
    const [isAdvancedExpanded, setIsAdvancedExpanded] = useState(false);

    const [logsOutput, setLogsOutput] = useState<string>('');
    const logFollowProcess = useRef<{ close?:() => void } | null>(null);

    const applyContent = useCallback((content: string) => {
        const { lines, values } = parseEnvDefault(content, KNOWN_KEYS);
        setFileLines(lines);
        setEnvVarForm(mergeFormValues(defaultFormFromConf(CONF_PARAMS), values));
        setConfigFileContents(content);
        setConfigLoadError(null);
        setDirty(false);
    }, []);

    const loadFromDisk = useCallback(async () => {
        try {
            const content = await cockpit.file(CONFIG_FILE, { superuser: 'try' }).read();
            if (dirtyRef.current)
                return;
            applyContent(content);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            if (!dirtyRef.current) {
                const empty = parseEnvDefault('', KNOWN_KEYS);
                setFileLines(empty.lines);
                setEnvVarForm(defaultFormFromConf(CONF_PARAMS));
                setConfigLoadError(_('Failed to read configuration file: {error}.').replace('{error}', msg));
                setConfigFileContents('');
            }
        }
    }, [applyContent]);

    useEffect(() => {
        loadFromDisk();
    }, [loadFromDisk]);

    useEffect(() => {
        const watcher = cockpit.file(CONFIG_FILE, { superuser: 'try' }).watch(() => {
            loadFromDisk();
        });
        return () => {
            if (watcher && typeof watcher.close === 'function') watcher.close();
        };
    }, [loadFromDisk]);

    function validateField(key: string, value: string): string {
        const def = CONF_PARAMS[key];
        if (!def)
            return '';
        if (def.required !== true && (value === '' || value == null))
            return '';
        if (def.validation && !def.validation.test(value))
            return _('Invalid value');
        if (def.type === 'number' && def.range) {
            const num = Number(value);
            if (isNaN(num) || num < def.range[0] || num > def.range[1]) {
                return _('Value must be between ') + def.range[0] + ' and ' + def.range[1];
            }
        }
        if (def.type === 'enum' && def.options && !def.options.includes(value))
            return _('Invalid option');
        return '';
    }

    function handleEnvVarChange(key: string, value: string) {
        setEnvVarForm(prev => ({ ...prev, [key]: value }));
        setFormErrors(prev => ({ ...prev, [key]: validateField(key, value) }));
        setDirty(true);
    }

    const handleEnvVarFormSubmit = useCallback(
        async (e: React.FormEvent) => {
            e.preventDefault();
            const errors: Record<string, string> = {};
            for (const key of Object.keys(CONF_PARAMS)) {
                const err = validateField(key, envVarForm[key]);
                if (err) errors[key] = err;
            }
            setFormErrors(errors);
            if (Object.keys(errors).length > 0) {
                setToast({ variant: 'danger', title: _('Fix validation errors before saving.') });
                return;
            }

            const newConfig = serializeEnvDefault(fileLines, envVarForm, CONF_PARAMS);
            setSaveBusy(true);
            try {
                await cockpit
                        .file(CONFIG_FILE, { superuser: 'try' })
                        .replace(newConfig + (newConfig.endsWith('\n') ? '' : '\n'));
                const parsed = parseEnvDefault(newConfig, KNOWN_KEYS);
                setFileLines(parsed.lines);
                setEnvVarForm(mergeFormValues(defaultFormFromConf(CONF_PARAMS), parsed.values));
                setConfigFileContents(newConfig);
                setDirty(false);
                if (saveAndRestart) {
                    try {
                        await cockpit.spawn(['systemctl', 'restart', SERVICE_NAME], {
                            superuser: 'try',
                        });
                        setToast({
                            variant: 'success',
                            title: _('Configuration saved and service restarted.'),
                        });
                    } catch (e: unknown) {
                        const msg = e instanceof Error ? e.message : String(e);
                        setToast({
                            variant: 'warning',
                            title: _('Saved, but restart failed: {0}').replace('{0}', msg),
                        });
                    }
                } else {
                    setToast({ variant: 'success', title: _('Configuration saved.') });
                }
            } catch (err: unknown) {
                const msg = err instanceof Error ? err.message : String(err);
                setToast({
                    variant: 'danger',
                    title: _('Failed to update configuration file: {0}').replace('{0}', msg),
                });
            } finally {
                setSaveBusy(false);
            }
        },
        [fileLines, envVarForm, saveAndRestart]
    );

    function showServiceLogs(): void {
        cockpit
                .spawn(['journalctl', '-u', SERVICE_NAME, '--no-pager', '--since', 'today'], {
                    superuser: 'try',
                })
                .then((output: string) => {
                    setLogsOutput(output || _('No logs found for this service.'));
                })
                .catch(() => {
                    setLogsOutput(_('Failed to retrieve service logs.'));
                });
    }

    function stopFollowingLogs(): void {
        if (logFollowProcess.current && typeof logFollowProcess.current.close === 'function') {
            logFollowProcess.current.close();
            logFollowProcess.current = null;
            setLogsOutput(_('Stopped following logs.'));
        } else {
            setLogsOutput(_('Not currently following logs.'));
        }
    }

    function followServiceLogs(): void {
        if (logFollowProcess.current) {
            setLogsOutput(_('Already following logs.'));
            return;
        }
        setLogsOutput('');
        const proc = cockpit.spawn(['journalctl', '-u', SERVICE_NAME, '-f', '--no-pager'], {
            superuser: 'try',
        });
        logFollowProcess.current = proc;
        proc.stream((data: string) => {
            setLogsOutput(prev => prev + data);
        });
        proc.done(() => {
            logFollowProcess.current = null;
        });
        proc.fail(() => {
            setLogsOutput(_('Failed to follow logs.'));
            logFollowProcess.current = null;
        });
    }

    useEffect(() => {
        return () => {
            if (logFollowProcess.current && typeof logFollowProcess.current.close === 'function')
                logFollowProcess.current.close();
        };
    }, []);

    const dismissToast = useCallback(() => setToast(null), []);

    const onTlsInstalled = useCallback((paths: { cert?: string; key?: string; ca?: string }) => {
        setEnvVarForm(prev => ({
            ...prev,
            ...(paths.cert ? { PYTAK_TLS_CLIENT_CERT: paths.cert } : {}),
            ...(paths.key ? { PYTAK_TLS_CLIENT_KEY: paths.key } : {}),
            ...(paths.ca ? { PYTAK_TLS_CLIENT_CAFILE: paths.ca } : {}),
        }));
        setDirty(true);
    }, []);

    return (
        <div data-testid="adsbcot-app">
            {toast && (
                <Alert
                    variant={toast.variant}
                    title={toast.title}
                    style={{ marginBottom: '1rem' }}
                    actionClose={
                        <button
                            type="button"
                            className="pf-c-button pf-m-plain"
                            onClick={dismissToast}
                            aria-label={_('Dismiss')}
                        >
                            ×
                        </button>
                    }
                />
            )}

            <ServiceManagementCard serviceName={SERVICE_NAME} onToast={setToast} />

            <TlsUploadCard onToast={setToast} onInstalledPaths={onTlsInstalled} />

            <Card
                className="adsbcot-expandable-card"
                isExpanded={isConfigExpanded}
                data-testid="adsbcot-config-card"
            >
                <CardHeader
                    className="ct-card-expandable-header"
                    onExpand={() => setIsConfigExpanded(!isConfigExpanded)}
                    toggleButtonProps={{
                        id: 'adsbcot-config-expand',
                        'aria-label': isConfigExpanded
                            ? _('Collapse configuration')
                            : _('Expand configuration'),
                    }}
                >
                    <CardTitle>
                        {_('Configuration')} {dirty ? `(${_('unsaved changes')})` : ''}
                    </CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    {configLoadError && <Alert variant="warning" title={configLoadError} />}
                    <form onSubmit={handleEnvVarFormSubmit}>
                        <div className="adsbcot-config-form-layout" data-testid="adsbcot-config-form-layout">
                            <div className="adsbcot-config-body-scroll" data-testid="adsbcot-config-scroll">
                                <DataList aria-label={_('Environment Variable Configuration')}>
                                    {Object.entries(CONF_PARAMS).map(([key, def]) => (
                                        <DataListItem key={key} aria-labelledby={`envvar-${key}`}>
                                            <DataListItemRow>
                                                <DataListItemCells
                                            dataListCells={[
                                                <DataListCell key="label">
                                                    <label htmlFor={`envvar-input-${key}`}>
                                                        <strong>{key}</strong>
                                                        {def.required && (
                                                            <span
                                                                style={{ color: 'red', marginLeft: 8 }}
                                                            >
                                                                {_('Required')}
                                                            </span>
                                                        )}
                                                        <div
                                                            style={{ fontSize: '0.95em', color: '#888' }}
                                                        >
                                                            {def.description}
                                                        </div>
                                                        <div style={{ fontSize: 'smaller', color: '#888' }}>
                                                            {_('Default')}: <code>{def.defaultValue}</code>
                                                            {def.type === 'number' && def.range
                                                                ? ` (${_('Range')}: ${def.range[0]} - ${def.range[1]})`
                                                                : ''}
                                                            {def.type === 'enum' && def.options
                                                                ? ` (${_('Options')}: ${def.options.join(', ')})`
                                                                : ''}
                                                        </div>
                                                    </label>
                                                </DataListCell>,
                                                <DataListCell key="input">
                                                    {def.type === 'boolean'
                                                        ? (
                                                            <select
                                                            id={`envvar-input-${key}`}
                                                            value={envVarForm[key]}
                                                            onChange={ev =>
                                                                handleEnvVarChange(key, ev.target.value)}
                                                            >
                                                                <option value="true">{_('True')}</option>
                                                                <option value="false">{_('False')}</option>
                                                            </select>
                                                        )
                                                        : def.type === 'enum' && def.options
                                                            ? (
                                                                <select
                                                            id={`envvar-input-${key}`}
                                                            value={envVarForm[key]}
                                                            onChange={ev =>
                                                                handleEnvVarChange(key, ev.target.value)}
                                                                >
                                                                    {def.options.map(opt => (
                                                                        <option key={opt} value={opt}>
                                                                            {opt}
                                                                        </option>
                                                                    ))}
                                                                </select>
                                                            )
                                                            : (
                                                                <input
                                                            id={`envvar-input-${key}`}
                                                            type={
                                                                def.type === 'number' ? 'number' : 'text'
                                                            }
                                                            value={envVarForm[key]}
                                                            min={
                                                                def.type === 'number' && def.range
                                                                    ? def.range[0]
                                                                    : undefined
                                                            }
                                                            max={
                                                                def.type === 'number' && def.range
                                                                    ? def.range[1]
                                                                    : undefined
                                                            }
                                                            onChange={ev =>
                                                                handleEnvVarChange(key, ev.target.value)}
                                                            style={{ width: '300px', fontFamily: 'monospace' }}
                                                                />
                                                            )}
                                                    {formErrors[key] && (
                                                        <div style={{ color: 'red' }}>{formErrors[key]}</div>
                                                    )}
                                                </DataListCell>,
                                            ]}
                                                />
                                            </DataListItemRow>
                                        </DataListItem>
                                    ))}
                                </DataList>
                            </div>
                            <div className="adsbcot-config-actions">
                                <Checkbox
                                id="adsbcot-save-restart"
                                label={_('Restart lincot after save')}
                                isChecked={saveAndRestart}
                                onChange={(_ev, checked) => setSaveAndRestart(checked)}
                                />
                                <button
                                type="submit"
                                className="pf-c-button pf-m-primary"
                                style={{ marginTop: '1em', display: 'block' }}
                                disabled={saveBusy}
                                >
                                    {saveBusy ? _('Saving…') : _('Validate & Save')}
                                </button>
                            </div>
                        </div>
                    </form>
                </CardExpandableContent>
            </Card>

            <Card className="adsbcot-expandable-card" isExpanded={isDebugExpanded}>
                <CardHeader
                    className="ct-card-expandable-header"
                    onExpand={() => setIsDebugExpanded(!isDebugExpanded)}
                    toggleButtonProps={{
                        id: 'adsbcot-debug-expand',
                        'aria-label': isDebugExpanded
                            ? _('Collapse debug')
                            : _('Expand debug'),
                    }}
                >
                    <CardTitle>{_('Debug Logs')}</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    <CardBody>
                        <CardTitle>{_('Status Output')}</CardTitle>
                        <StatusOutput serviceName={SERVICE_NAME} />
                        <CardTitle>{_('Service Logs')}</CardTitle>
                        <div
                            style={{
                                display: 'flex',
                                gap: '1em',
                                flexWrap: 'wrap',
                                marginBottom: '1em',
                            }}
                        >
                            <button
                                type="button"
                                className="pf-c-button pf-m-primary"
                                onClick={() => showServiceLogs()}
                            >
                                {_('Show Logs')}
                            </button>
                            <button
                                type="button"
                                className="pf-c-button pf-m-secondary"
                                onClick={() => followServiceLogs()}
                            >
                                {_('Follow Logs')}
                            </button>
                            <button
                                type="button"
                                className="pf-c-button pf-m-secondary"
                                onClick={() => stopFollowingLogs()}
                            >
                                {_('Stop Following')}
                            </button>
                        </div>
                        <pre
                            style={{
                                background: '#222',
                                color: '#eee',
                                padding: '1em',
                                borderRadius: '4px',
                                fontSize: '0.95em',
                                overflowX: 'auto',
                                maxHeight: 300,
                                minHeight: 100,
                            }}
                        >
                            {logsOutput || _('No logs to display.')}
                        </pre>
                    </CardBody>
                </CardExpandableContent>
            </Card>

            <Card className="adsbcot-expandable-card" isExpanded={isAdvancedExpanded}>
                <CardHeader
                    className="ct-card-expandable-header"
                    onExpand={() => setIsAdvancedExpanded(!isAdvancedExpanded)}
                    toggleButtonProps={{
                        id: 'adsbcot-advanced-expand',
                        'aria-label': isAdvancedExpanded
                            ? _('Collapse advanced')
                            : _('Expand advanced'),
                    }}
                >
                    <CardTitle>{_('Advanced Details')}</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    <CardBody>
                        <strong>{_('Raw Configuration File Contents')}:</strong>
                        <pre
                            style={{
                                background: '#222',
                                color: '#eee',
                                padding: '1em',
                                borderRadius: '4px',
                                fontSize: '0.95em',
                                overflowX: 'auto',
                                maxHeight: 300,
                                minHeight: 100,
                            }}
                        >
                            {configFileContents}
                        </pre>
                    </CardBody>
                </CardExpandableContent>
            </Card>
        </div>
    );
};
