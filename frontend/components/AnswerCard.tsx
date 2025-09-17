import * as React from 'react';
import { View } from 'react-native';
import { Card, Text, Chip, Divider, Banner } from 'react-native-paper';
import EvidenceSection from './EvidenceSection';
import type { ChatResponse, QueryMode } from '../lib/api';
import Chart from './Chart';

type Props = {
  data: ChatResponse;
  onFollowUp: (prompt: string) => void;
  requestMessage?: string;
  mode?: QueryMode;
};

export default function AnswerCard({ data, onFollowUp, requestMessage, mode }: Props) {
  if (!data) return null;
  const { answer_text, follow_ups } = data;
  const validations = data.validations || [];
  const hasNonEmptyFail = validations.some(v => v.name === 'non_empty_result' && v.status === 'fail');
  const sampleRows = (data as any).sample_rows as Array<Record<string, any>> | undefined;
  const firstSample = sampleRows && sampleRows.length > 0 ? sampleRows[0] : undefined;
  const firstSamplePreview = firstSample
    ? Object.entries(firstSample).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join('  |  ')
    : null;
  return (
    <Card style={{ marginVertical: 8 }}>
      <Card.Content>
        {mode && (
          <Text variant="labelSmall" style={{ marginBottom: 6, opacity: 0.6 }}>
            {mode === 'ai' ? 'AI Smart Mode' : 'Classic Mode'}
          </Text>
        )}
        {(data.error || hasNonEmptyFail) && (
          <Banner
            visible
            icon="information"
            style={{ marginBottom: 8 }}
          >
            {data.error || 'No matching rows found.'}
            {data.suggestion ? ` ${data.suggestion}` : ' Try refining your question or expanding the date range.'}
          </Banner>
        )}
        {answer_text ? (
          <Text variant="titleMedium">{answer_text}</Text>
        ) : (
          <Text variant="titleMedium">{data.error || 'No answer'}</Text>
        )}
        {firstSamplePreview && (
          <View style={{ marginTop: 8, padding: 8, borderRadius: 6, backgroundColor: '#f3f4ff' }}>
            <Text style={{ fontSize: 12, color: '#3730a3' }}>{firstSamplePreview}</Text>
          </View>
        )}
        {(data as any).chart && (data as any).chart.series && (
          <>
            <Divider style={{ marginVertical: 8 }} />
            <Chart type={(data as any).chart.type || 'bar'} series={(data as any).chart.series || []} />
          </>
        )}
        <Divider style={{ marginVertical: 8 }} />
        <EvidenceSection data={data} requestMessage={requestMessage} />
        {follow_ups && follow_ups.length > 0 && (
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 }}>
            {follow_ups.map((f) => (
              <Chip key={f} onPress={() => onFollowUp(f)} style={{ marginRight: 6, marginTop: 6 }}>
                {f}
              </Chip>
            ))}
          </View>
        )}
      </Card.Content>
    </Card>
  );
}
