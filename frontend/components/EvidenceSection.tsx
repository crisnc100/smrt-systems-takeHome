import * as React from 'react';
import { View } from 'react-native';
import { List, Text, Chip, IconButton, HelperText } from 'react-native-paper';
import * as Clipboard from 'expo-clipboard';
import type { ChatResponse } from '../lib/api';
import { getBaseUrl } from '../lib/api';

export default function EvidenceSection({ data, requestMessage }: { data: ChatResponse, requestMessage?: string }) {
  const [expanded, setExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const [baseUrl, setBaseUrl] = React.useState<string>('http://localhost:8000');
  const toggle = () => setExpanded((e) => !e);

  const rowsScanned = data.rows_scanned ?? 0;
  const tables = data.tables_used || [];
  const validations = data.validations || [];
  const snippets = data.data_snippets || [];
  const sampleRows = (data as any).sample_rows as Array<Record<string, any>> | undefined;
  const qualityBadges = (data as any).quality_badges || [];

  React.useEffect(() => {
    getBaseUrl().then(setBaseUrl).catch(() => {});
  }, []);

  React.useEffect(() => {
    // Auto-expand when there is an error or failed validations
    const hasError = !!(data as any).error;
    const hasFail = validations.some((v) => v.status === 'fail');
    const hasWarn = qualityBadges.some((b: any) => b.type !== 'success');
    setExpanded(hasError || hasFail || hasWarn);
  }, [JSON.stringify(data)]);

  return (
    <List.Section>
      <List.Accordion
        title="📊 How we got this answer"
        description={`Analyzed ${rowsScanned} rows from ${tables.length} table${tables.length !== 1 ? 's' : ''}`}
        expanded={expanded}
        onPress={toggle}
        style={{ backgroundColor: '#f8f9fa', borderRadius: 8, marginTop: 8 }}
      >
        <View style={{ paddingHorizontal: 12, paddingVertical: 8, backgroundColor: '#fff' }}>
          {/* Simple summary stats */}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
            <Chip icon="table-large" style={{ marginRight: 8, marginBottom: 8, backgroundColor: '#e8f4fd' }}>
              {tables.length > 0 ? tables.join(', ') : 'No tables'}
            </Chip>
            <Chip icon="database-search" style={{ marginRight: 8, marginBottom: 8, backgroundColor: '#e8f4fd' }}>
              {rowsScanned} rows checked
            </Chip>
            {typeof (data as any).exec_ms === 'number' && (
              <Chip icon="lightning-bolt" style={{ marginRight: 8, marginBottom: 8, backgroundColor: '#e8f4fd' }}>
                {(data as any).exec_ms < 1000 ? `${Math.round((data as any).exec_ms)}ms` : 'Fast'}
              </Chip>
            )}
          </View>

          {/* Show SQL in a cleaner way */}
          {data.sql && (
            <View style={{ marginBottom: 12 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ flex: 1, fontWeight: 'bold', color: '#374151' }}>Database Query</Text>
                <IconButton
                  icon="content-copy"
                  size={20}
                  onPress={async () => {
                    try {
                      await Clipboard.setStringAsync(data.sql || '');
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    } catch {}
                  }}
                  accessibilityLabel="Copy"
                />
              </View>
              <View style={{ backgroundColor: '#f3f4f6', padding: 10, borderRadius: 6, borderLeftWidth: 3, borderLeftColor: '#3b82f6' }}>
                <Text style={{ color: '#1f2937', fontSize: 12, lineHeight: 18, fontFamily: 'monospace' }}>
                  {data.sql}
                </Text>
              </View>
            </View>
          )}
          {copied && (
            <HelperText type="info" visible style={{ marginTop: 4 }}>
              Copied to clipboard
            </HelperText>
          )}
          
          {/* Sample data if available */}
          {sampleRows && sampleRows.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text style={{ fontWeight: 'bold', color: '#374151', marginBottom: 4 }}>Sample Rows</Text>
              <View style={{ backgroundColor: '#eef2ff', padding: 8, borderRadius: 6 }}>
                {sampleRows.slice(0, 3).map((row, idx) => (
                  <View key={idx} style={{ marginBottom: 4 }}>
                    {Object.entries(row).map(([key, value]) => (
                      <Text key={key} style={{ color: '#312e81', fontSize: 12 }}>
                        {key}: {String(value)}
                      </Text>
                    ))}
                  </View>
                ))}
              </View>
            </View>
          )}
          {!sampleRows && snippets.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text style={{ fontWeight: 'bold', color: '#374151', marginBottom: 4 }}>Sample Results</Text>
              <View style={{ backgroundColor: '#fef3c7', padding: 8, borderRadius: 6 }}>
                {snippets.slice(0, 3).map((s, idx) => (
                  <Text key={idx} style={{ color: '#92400e', fontSize: 12 }}>
                    {s.date || s.product_id || 'Row ' + (idx + 1)}: ${s.revenue?.toFixed(0) || s.total || s.qty || 'N/A'}
                  </Text>
                ))}
                {snippets.length > 3 && (
                  <Text style={{ color: '#92400e', fontSize: 12, fontStyle: 'italic' }}>
                    ...and {snippets.length - 3} more
                  </Text>
                )}
              </View>
            </View>
          )}

          {/* Only show validation issues if there are problems */}
          {validations.some(v => v.status === 'fail') && (
            <View style={{ marginTop: 8 }}>
              <Text style={{ fontWeight: 'bold', color: '#dc2626', marginBottom: 4 }}>⚠️ Issues Found</Text>
              {validations.filter(v => v.status === 'fail').map((v, idx) => (
                <Text key={idx} style={{ color: '#dc2626', fontSize: 12 }}>
                  • {v.name.replace(/_/g, ' ')}: {v.message || 'Failed'}
                </Text>
              ))}
            </View>
          )}
        </View>
      </List.Accordion>
    </List.Section>
  );
}
