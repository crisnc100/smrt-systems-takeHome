import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { Text, TextInput, Button, HelperText } from 'react-native-paper';
import { getBaseUrl, setBaseUrl, refreshData } from '../lib/api';

export default function SettingsScreen() {
  const [url, setUrl] = React.useState('');
  const [status, setStatus] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getBaseUrl().then(setUrl);
  }, []);

  const save = async () => {
    try {
      await setBaseUrl(url);
      setStatus('Saved');
      setError(null);
    } catch (e) {
      setError(String(e));
      setStatus(null);
    }
  };

  const refresh = async () => {
    setStatus('Refreshing...');
    setError(null);
    try {
      const res = await refreshData();
      if (res.error) {
        setError(res.error);
        setStatus(null);
      } else {
        setStatus('Data refreshed');
      }
    } catch (e) {
      setError(String(e));
      setStatus(null);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }}>
      <Text variant="titleLarge" style={{ marginBottom: 12 }}>Settings</Text>
      <TextInput label="API Base URL" value={url} onChangeText={setUrl} mode="outlined" />
      <HelperText type="info">Default: http://localhost:8000</HelperText>
      <View style={{ flexDirection: 'row', marginTop: 8 }}>
        <Button mode="contained" onPress={save} style={{ marginRight: 8 }}>Save</Button>
        <Button mode="outlined" onPress={refresh}>Refresh Data</Button>
      </View>
      {status && <Text style={{ marginTop: 12 }}>{status}</Text>}
      {error && <Text style={{ marginTop: 12, color: 'red' }}>{error}</Text>}
    </ScrollView>
  );
}

