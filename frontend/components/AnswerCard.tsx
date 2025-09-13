import * as React from 'react';
import { View } from 'react-native';
import { Card, Text, Chip, Divider, Banner } from 'react-native-paper';
import EvidenceSection from './EvidenceSection';
import type { ChatResponse } from '../lib/api';
import Chart from './Chart';

type Props = {
  data: ChatResponse;
  onFollowUp: (prompt: string) => void;
  requestMessage?: string;
};

export default function AnswerCard({ data, onFollowUp, requestMessage }: Props) {
  if (!data) return null;
  const { answer_text, follow_ups } = data;
  const validations = data.validations || [];
  const hasNonEmptyFail = validations.some(v => v.name === 'non_empty_result' && v.status === 'fail');
  return (
    <Card style={{ marginVertical: 8 }}>
      <Card.Content>
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
