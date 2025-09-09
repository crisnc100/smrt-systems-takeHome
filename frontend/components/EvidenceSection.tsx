import * as React from 'react';
import { View } from 'react-native';
import { List, Text, Chip } from 'react-native-paper';
import type { ChatResponse } from '../lib/api';

export default function EvidenceSection({ data }: { data: ChatResponse }) {
  const [expanded, setExpanded] = React.useState(false);
  const toggle = () => setExpanded((e) => !e);

  const rowsScanned = data.rows_scanned ?? 0;
  const tables = data.tables_used || [];
  const validations = data.validations || [];
  const snippets = data.data_snippets || [];

  return (
    <List.Section>
      <List.Accordion
        title="Evidence"
        description="SQL, tables used, rows scanned, samples"
        expanded={expanded}
        onPress={toggle}
      >
        <View style={{ paddingHorizontal: 8, paddingBottom: 8 }}>
          <Text style={{ marginBottom: 6 }}>SQL</Text>
          <View style={{ backgroundColor: '#111', padding: 8, borderRadius: 6 }}>
            <Text style={{ color: '#eee', fontFamily: 'monospace' }}>{data.sql}</Text>
          </View>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 }}>
            <Chip icon="table" style={{ marginRight: 6, marginTop: 6 }}>Tables: {tables.join(', ')}</Chip>
            <Chip icon="database" style={{ marginRight: 6, marginTop: 6 }}>Rows Scanned: {rowsScanned}</Chip>
          </View>
          {validations.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text>Validations:</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
                {validations.map((v, idx) => (
                  <Chip key={idx} style={{ marginRight: 6, marginTop: 6 }}>
                    {v.name}: {v.status}
                  </Chip>
                ))}
              </View>
            </View>
          )}
          {snippets.length > 0 && (
            <View style={{ marginTop: 8 }}>
              <Text>Samples:</Text>
              {snippets.map((s, idx) => (
                <Text key={idx} style={{ opacity: 0.8 }}>
                  {s.date || 'n/a'} — {s.revenue !== undefined ? `$${s.revenue.toFixed(2)}` : ''}
                </Text>
              ))}
            </View>
          )}
        </View>
      </List.Accordion>
    </List.Section>
  );
}

