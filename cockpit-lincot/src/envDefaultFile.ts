/*
 * Copyright Sensors & Signals LLC https://www.snstac.com/
 *
 * Parse and serialize systemd EnvironmentFile-style key=value lines while
 * preserving comments, blanks, unknown variables, and export prefixes.
 */

import type { EnvVarDefinition } from './types';

export type DefaultEnvLine =
    | { kind: 'raw'; text: string }
    | { kind: 'known'; key: string; exportVar: boolean }
    | { kind: 'unknown'; text: string };

const ASSIGN_RE = /^([A-Za-z0-9_]+)=(.*)$/;

function stripWrappingQuotes(value: string): string {
    if (value.length >= 2) {
        if (value.startsWith('"') && value.endsWith('"'))
            return value.slice(1, -1).replace(/\\"/g, '"')
                    .replace(/\\\\/g, '\\');
        if (value.startsWith("'") && value.endsWith("'"))
            return value.slice(1, -1);
    }
    return value;
}

export function shellQuoteValue(value: string, def: EnvVarDefinition | undefined): string {
    const force = def?.requiresQuoting === true;
    const needs =
        force ||
        value === '' ||
        /[\s#'"$`\\]/.test(value) ||
        /[^\w@%+=:,./-]/i.test(value);
    if (!needs)
        return value;
    const escaped = value
            .replace(/\\/g, '\\\\')
            .replace(/"/g, '\\"')
            .replace(/\$/g, '\\$')
            .replace(/`/g, '\\`');
    return `"${escaped}"`;
}

export function parseEnvDefault(
    content: string,
    knownKeys: Set<string>
): { lines: DefaultEnvLine[]; values: Record<string, string> } {
    const values: Record<string, string> = {};
    const lines: DefaultEnvLine[] = [];
    const rawLines = content.split('\n');

    for (const line of rawLines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) {
            lines.push({ kind: 'raw', text: line });
            continue;
        }
        let exportVar = false;
        let rest = trimmed;
        if (rest.startsWith('export ')) {
            exportVar = true;
            rest = rest.slice(7).trimStart();
        }
        const m = rest.match(ASSIGN_RE);
        if (!m) {
            lines.push({ kind: 'raw', text: line });
            continue;
        }
        const key = m[1];
        const rawVal = m[2];
        const value = stripWrappingQuotes(rawVal);
        if (knownKeys.has(key)) {
            values[key] = value;
            lines.push({ kind: 'known', key, exportVar });
        } else {
            lines.push({ kind: 'unknown', text: line });
        }
    }
    return { lines, values };
}

function shouldAppendKey(key: string, value: string, def: EnvVarDefinition | undefined): boolean {
    if (!def)
        return value !== '';
    if (def.required === true)
        return true;
    return value !== (def.defaultValue ?? '');
}

export function serializeEnvDefault(
    lines: DefaultEnvLine[],
    form: Record<string, string>,
    confParams: Record<string, EnvVarDefinition>
): string {
    const knownKeysInFile = new Set<string>();
    for (const item of lines) {
        if (item.kind === 'known')
            knownKeysInFile.add(item.key);
    }

    const out: string[] = [];
    for (const item of lines) {
        if (item.kind === 'raw') {
            out.push(item.text);
        } else if (item.kind === 'unknown') {
            out.push(item.text);
        } else {
            const def = confParams[item.key];
            const v = form[item.key] ?? '';
            const exp = item.exportVar ? 'export ' : '';
            out.push(`${exp}${item.key}=${shellQuoteValue(v, def)}`);
        }
    }

    const toAppend: string[] = [];
    for (const key of Object.keys(confParams)) {
        if (knownKeysInFile.has(key))
            continue;
        const v = form[key] ?? '';
        if (!shouldAppendKey(key, v, confParams[key]))
            continue;
        const def = confParams[key];
        toAppend.push(`${key}=${shellQuoteValue(v, def)}`);
    }

    if (toAppend.length) {
        if (out.length && out[out.length - 1] !== '')
            out.push('');
        out.push('# Added by Cockpit LINCOT');
        for (const l of toAppend)
            out.push(l);
    }

    return out.join('\n');
}

export function defaultFormFromConf(confParams: Record<string, EnvVarDefinition>): Record<string, string> {
    return Object.fromEntries(Object.entries(confParams).map(([k, d]) => [k, d.defaultValue]));
}

export function mergeFormValues(
    base: Record<string, string>,
    fromFile: Record<string, string>
): Record<string, string> {
    return { ...base, ...fromFile };
}
