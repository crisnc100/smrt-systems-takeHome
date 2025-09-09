import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { TextInput, Button, Text, Chip, ActivityIndicator } from 'react-native-paper';
import AnswerCard from '../components/AnswerCard';
import { callChat, type ChatResponse } from '../lib/api';

const SUGGESTIONS = [
  'Revenue last 30 days',
  'Top 5 products',
  'Orders for CID 1001',
  'Order details IID 2001',
];

export default function ChatScreen() {
  const [message, setMessage] = React.useState('Revenue last 30 days');
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<ChatResponse | null>(null);

  const ask = async (prompt?: string) => {
    const text = prompt || message;
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await callChat(text.trim());
      setResult(res);
      if (!prompt) setMessage('');
    } catch (e) {
      setResult({ error: String(e), suggestion: 'Check API URL in Settings' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }} keyboardShouldPersistTaps="handled">
      <Text variant="titleLarge" style={{ marginBottom: 8 }}>Ask about your data</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 }}>
        {SUGGESTIONS.map((s) => (
          <Chip key={s} style={{ marginRight: 6, marginBottom: 6 }} onPress={() => ask(s)}>
            {s}
          </Chip>
        ))}
      </View>
      <TextInput
        mode="outlined"
        label="Your question"
        value={message}
        onChangeText={setMessage}
        right={<TextInput.Icon icon="send" onPress={() => ask()} />}
      />
      <Button mode="contained" style={{ marginTop: 10 }} onPress={() => ask()} disabled={loading}>
        Ask
      </Button>
      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}
      {result && (
        <AnswerCard data={result} onFollowUp={(p) => ask(p)} />
      )}
    </ScrollView>
  );
}

