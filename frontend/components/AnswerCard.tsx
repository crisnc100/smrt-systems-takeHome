import * as React from 'react';
import { View } from 'react-native';
import { Card, Text, Chip, Divider } from 'react-native-paper';
import EvidenceSection from './EvidenceSection';
import type { ChatResponse } from '../lib/api';

type Props = {
  data: ChatResponse;
  onFollowUp: (prompt: string) => void;
};

export default function AnswerCard({ data, onFollowUp }: Props) {
  if (!data) return null;
  const { answer_text, follow_ups, confidence } = data;
  const confPct = typeof confidence === 'number' ? Math.round(confidence * 100) : undefined;
  return (
    <Card style={{ marginVertical: 8 }}>
      <Card.Content>
        {answer_text ? (
          <Text variant="titleMedium">{answer_text}</Text>
        ) : (
          <Text variant="titleMedium">{data.error || 'No answer'}</Text>
        )}
        {confPct !== undefined && (
          <Text style={{ marginTop: 4, opacity: 0.7 }}>Confidence: {confPct}%</Text>
        )}
        <Divider style={{ marginVertical: 8 }} />
        <EvidenceSection data={data} />
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

