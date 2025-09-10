import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { TextInput, Button, Text, Chip, ActivityIndicator, Switch, Card, IconButton } from 'react-native-paper';
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
  const [sqlMode, setSqlMode] = React.useState(false);
  const [sqlQuery, setSqlQuery] = React.useState('');
  const [showSqlEditor, setShowSqlEditor] = React.useState(false);

  const ask = async (prompt?: string) => {
    const text = prompt || message;
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await callChat(text.trim());
      setResult(res);
      if (res.sql) {
        setSqlQuery(res.sql);
      }
      if (!prompt) setMessage('');
    } catch (e) {
      setResult({ error: String(e), suggestion: 'Check API URL in Settings' });
    } finally {
      setLoading(false);
    }
  };

  const executeSql = async () => {
    if (!sqlQuery.trim()) return;
    setLoading(true);
    try {
      // Send SQL directly to backend (you'd need to add this endpoint)
      const res = await callChat(`SQL: ${sqlQuery}`);
      setResult(res);
    } catch (e) {
      setResult({ error: String(e), suggestion: 'Invalid SQL or check API' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }} keyboardShouldPersistTaps="handled">
      <Text variant="titleLarge" style={{ marginBottom: 8 }}>Ask about your data</Text>
      
      {/* Ask→SQL Toggle */}
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
        <Text style={{ flex: 1 }}>SQL Mode</Text>
        <Switch value={sqlMode} onValueChange={setSqlMode} />
      </View>

      {!sqlMode ? (
        <>
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
        </>
      ) : (
        <>
          <TextInput
            mode="outlined"
            label="SQL Query (SELECT only)"
            value={sqlQuery}
            onChangeText={setSqlQuery}
            multiline
            numberOfLines={4}
            placeholder="SELECT SUM(order_total) FROM Inventory WHERE order_date > '2024-08-01'"
          />
          <Button mode="contained" style={{ marginTop: 10 }} onPress={executeSql} disabled={loading}>
            Execute SQL
          </Button>
          {result?.sql && (
            <Card style={{ marginTop: 8, padding: 8 }}>
              <Text variant="labelSmall">Last Generated SQL:</Text>
              <Text style={{ fontFamily: 'monospace', fontSize: 12 }}>{result.sql}</Text>
            </Card>
          )}
        </>
      )}
      
      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}
      {result && (
        <AnswerCard data={result} onFollowUp={(p) => ask(p)} showSqlToggle={!sqlMode} />
      )}
    </ScrollView>
  );
}

