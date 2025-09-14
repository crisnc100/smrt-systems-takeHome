import * as React from 'react';
import { ScrollView, View, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, Chip, ActivityIndicator, Card, IconButton, HelperText } from 'react-native-paper';
import AnswerCard from '../components/AnswerCard';
import { callChat, type ChatResponse, getDataStatus } from '../lib/api';

type MessageItem = { role: 'user' | 'assistant'; text?: string; data?: ChatResponse; request?: string };

// Default suggestions - will be updated with actual IDs from data
const DEFAULT_SUGGESTIONS = [
  'Revenue last 30 days',
  'Top 5 products',
  'Top customers',
  'Revenue this month',
];

export default function ChatScreen() {
  const [message, setMessage] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [history, setHistory] = React.useState<MessageItem[]>([]);
  const scrollRef = React.useRef<ScrollView>(null);
  const [freshness, setFreshness] = React.useState<{ max?: string; orders?: number } | null>(null);
  const [suggestions, setSuggestions] = React.useState(DEFAULT_SUGGESTIONS);

  const scrollToEnd = React.useCallback(() => {
    // Add longer delay for charts and complex content to render
    setTimeout(() => {
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 300);
  }, []);

  // Only scroll on initial load, not on every history change
  React.useEffect(() => {
    scrollToEnd();
    (async () => {
      try {
        const ds = await getDataStatus();
        const max = ds?.date_analysis?.inventory?.max_date;
        const orders = ds?.tables?.Inventory?.count;
        setFreshness({ max, orders });
        
        // Update suggestions with actual IDs from data
        if (ds?.sample_ids) {
          const { first_iid, first_cid } = ds.sample_ids;
          const dynamicSuggestions = [
            'Revenue last 30 days',
            'Top 5 products',
            first_cid ? `Orders for CID ${first_cid}` : 'Top customers',
            first_iid ? `Order details ${first_iid}` : 'Revenue this month',
          ];
          setSuggestions(dynamicSuggestions);
        }
      } catch {}
    })();
  }, []);

  const ask = async (prompt?: string) => {
    const text = (prompt ?? message).trim();
    if (!text) return;
    setLoading(true);
    setHistory((h) => [...h, { role: 'user', text }]);
    if (!prompt) setMessage('');
    
    // Scroll to bottom when sending new message
    scrollToEnd();
    
    try {
      const res = await callChat(text);
      setHistory((h) => [...h, { role: 'assistant', data: res, request: text }]);
      // Scroll again after response
      scrollToEnd();
    } catch (e) {
      setHistory((h) => [...h, { role: 'assistant', data: { error: String(e), suggestion: 'Check API URL in Settings' }, request: text }]);
      scrollToEnd();
    } finally {
      setLoading(false);
    }
  };

  const clear = () => setHistory([]);

  return (
    <KeyboardAvoidingView 
      style={{ flex: 1 }} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      keyboardVerticalOffset={Platform.select({ ios: 90, android: 100 })}
    >
      <View style={{ flex: 1 }}>
        <ScrollView 
          ref={scrollRef} 
          contentContainerStyle={{ padding: 16, paddingBottom: 120 }} 
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={true}
          maintainVisibleContentPosition={{ minIndexForVisible: 0 }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
            <Text variant="titleLarge" style={{ flex: 1 }}>Data Answers</Text>
            {history.length > 0 && (
              <IconButton icon="delete-outline" onPress={clear} accessibilityLabel="Clear" />
            )}
          </View>
          {freshness && (
            <Text style={{ marginBottom: 8, opacity: 0.7 }}>
              Using data through {freshness.max || 'n/a'} {typeof freshness.orders === 'number' ? `(${freshness.orders} orders)` : ''}
            </Text>
          )}

          {/* Quick suggestions */}
          {history.length === 0 && (
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 }}>
              {suggestions.map((s) => (
                <Chip key={s} style={{ marginRight: 6, marginBottom: 6 }} onPress={() => ask(s)}>
                  {s}
                </Chip>
              ))}
            </View>
          )}

          {/* Transcript */}
          {history.map((m, idx) => (
            m.role === 'user' ? (
              <Card key={idx} style={{ 
                alignSelf: 'flex-end', 
                backgroundColor: '#e8f0fe', 
                marginVertical: 4, 
                maxWidth: '80%' 
              }}>
                <Card.Content>
                  <Text>{m.text}</Text>
                </Card.Content>
              </Card>
            ) : (
              <View key={idx} style={{ 
                alignSelf: 'flex-start', 
                marginVertical: 4, 
                width: '100%'
              }}>
                {m.data && (
                  <AnswerCard data={m.data} onFollowUp={(p) => ask(p)} requestMessage={m.request} />
                )}
              </View>
            )
          ))}

          {loading && <ActivityIndicator style={{ marginTop: 12 }} />}
        </ScrollView>

        {/* Sticky input bar */}
        <View style={{ 
          padding: 12, 
          borderTopWidth: 1, 
          borderTopColor: '#eee',
          backgroundColor: '#fff',
          paddingBottom: Platform.OS === 'ios' ? 20 : 12
        }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <TextInput
              mode="outlined"
              placeholder="Ask about your data"
              value={message}
              onChangeText={setMessage}
              onSubmitEditing={() => ask()}
              style={{ flex: 1 }}
              dense
              autoCorrect={false}
            />
            <IconButton 
              icon="send" 
              mode="contained"
              onPress={() => ask()} 
              disabled={loading || !message.trim()}
              style={{ margin: 0 }}
            />
          </View>
          <HelperText type="info">
            Try: "Revenue last 30 days", "Top 5 products", "orders 1001", "August 2024 revenue"
          </HelperText>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
