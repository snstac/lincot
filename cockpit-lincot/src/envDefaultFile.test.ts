/*
 * Copyright Sensors & Signals LLC https://www.snstac.com/
 */

import { describe, expect, it } from 'vitest';

import { CONF_PARAMS } from './conf';
import {
    defaultFormFromConf,
    mergeFormValues,
    parseEnvDefault,
    serializeEnvDefault,
    shellQuoteValue,
} from './envDefaultFile';

const KNOWN = new Set(Object.keys(CONF_PARAMS));

describe('parseEnvDefault', () => {
    it('preserves comments, blanks, and unknown assignments', () => {
        const src = '# banner\n\nUNKNOWN_KEEP=val\n\n# end\n';
        const { lines, values } = parseEnvDefault(src, KNOWN);
        expect(values.UNKNOWN_KEEP).toBeUndefined();
        const form = mergeFormValues(defaultFormFromConf(CONF_PARAMS), values);
        const out = serializeEnvDefault(lines, form, CONF_PARAMS);
        expect(out).toContain('# banner');
        expect(out).toContain('UNKNOWN_KEEP=val');
        expect(out).toContain('# end');
    });

    it('parses export-prefixed known variables', () => {
        const src = 'export COT_URL=tls://host:1234\n';
        const { lines, values } = parseEnvDefault(src, KNOWN);
        expect(values.COT_URL).toBe('tls://host:1234');
        expect(lines.some(l => l.kind === 'known' && l.exportVar)).toBe(true);
    });
});

describe('serializeEnvDefault', () => {
    it('updates known keys in place', () => {
        const src = '# c\nCOT_URL=udp+wo://old:1\n';
        const { lines, values } = parseEnvDefault(src, KNOWN);
        const form = mergeFormValues(defaultFormFromConf(CONF_PARAMS), values);
        form.COT_URL = 'udp+wo://new:2';
        const out = serializeEnvDefault(lines, form, CONF_PARAMS);
        expect(out).toContain('# c');
        expect(out).toMatch(/COT_URL=.*udp\+wo:\/\/new:2/);
        expect(out).not.toContain('old:1');
    });
});

describe('shellQuoteValue', () => {
    it('quotes values with spaces', () => {
        const q = shellQuoteValue('a b', CONF_PARAMS.COT_URL);
        expect(q.startsWith('"')).toBe(true);
        expect(q.endsWith('"')).toBe(true);
    });
});
