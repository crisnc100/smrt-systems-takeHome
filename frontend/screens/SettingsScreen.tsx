import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { Text, TextInput, Button, HelperText, SegmentedButtons } from 'react-native-paper';
import { getBaseUrl, setBaseUrl, refreshData, runSelfCheck, getQueryMode, setQueryMode as persistQueryMode, type QueryMode } from '../lib/api';
import * as DocumentPicker from 'expo-document-picker';

export default function SettingsScreen() {
  const [url, setUrl] = React.useState('');
  const [status, setStatus] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [uploading, setUploading] = React.useState<boolean>(false);
  const [checking, setChecking] = React.useState<boolean>(false);
  const [checkResult, setCheckResult] = React.useState<any | null>(null);
  const [queryMode, setQueryMode] = React.useState<QueryMode>('classic');
  const [savingMode, setSavingMode] = React.useState<boolean>(false);

  React.useEffect(() => {
    getBaseUrl().then(setUrl);
    getQueryMode().then(setQueryMode);
  }, []);

  const updateQueryMode = async (mode: QueryMode) => {
    if (mode === queryMode) {
      return;
    }
    setSavingMode(true);
    setError(null);
    try {
      await persistQueryMode(mode);
      setQueryMode(mode);
      setStatus(mode === 'ai' ? 'AI Smart Mode enabled' : 'Classic mode enabled');
    } catch (e) {
      setError(String(e));
    } finally {
      setSavingMode(false);
    }
  };

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

  const upload = async () => {
    setError(null);
    setStatus(null);
    setUploading(true);
    try {
      // Pick one or more files (ZIP or CSVs). Multiple selection is not supported on all platforms.
      const picked = await DocumentPicker.getDocumentAsync({ multiple: true });
      if (picked.canceled) {
        setUploading(false);
        return;
      }

      const assets = (picked as any).assets || [];
      if (!assets || assets.length === 0) {
        setUploading(false);
        return;
      }

      const base = await getBaseUrl();
      const form: any = new FormData();

      // Helper to append file with proper metadata for RN fetch
      const appendFile = (field: string, asset: any) => {
        const uri = asset.uri;
        const name = asset.name || 'file';
        const type = asset.mimeType || 'application/octet-stream';
        // @ts-ignore RN FormData file structure
        form.append(field, { uri, name, type });
      };

      let appended = 0;
      for (const asset of assets) {
        const name: string = (asset.name || '').toLowerCase();
        if (name.endsWith('.zip')) {
          appendFile('zip', asset);
          appended++;
        } else if (name.includes('customer') && name.endsWith('.csv')) {
          appendFile('customer', asset);
          appended++;
        } else if (name.includes('inventory') && name.endsWith('.csv')) {
          appendFile('inventory', asset);
          appended++;
        } else if (name.includes('detail') && name.endsWith('.csv')) {
          appendFile('detail', asset);
          appended++;
        } else if (name.includes('pricelist') && name.endsWith('.csv')) {
          appendFile('pricelist', asset);
          appended++;
        } else if (name.endsWith('.csv') && appended === 0) {
          // Fallback: if a single CSV is selected with unknown name, try as inventory
          appendFile('inventory', asset);
          appended++;
        }
      }

      if (appended === 0) {
        setError('No supported files selected. Choose a ZIP or CSVs named Customer/Inventory/Detail/Pricelist.');
        setUploading(false);
        return;
      }

      const res = await fetch(`${base}/datasource/upload`, {
        method: 'POST',
        headers: {
          // Let fetch set the correct multipart boundary
        } as any,
        body: form,
      });
      const data = await res.json();
      if ((data as any).error || res.status >= 400) {
        setError((data as any).detail || (data as any).error || 'Upload failed');
        setUploading(false);
        return;
      }
      setStatus('Upload complete. Refreshing data...');
      await refresh();
      setStatus('Data uploaded and refreshed.');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setUploading(false);
    }
  };

  const selfCheck = async () => {
    setChecking(true);
    setError(null);
    setStatus('Running self-check...');
    try {
      const res = await runSelfCheck();
      setCheckResult(res);
      setStatus('Self-check complete');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setChecking(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }}>
      <Text variant="titleLarge" style={{ marginBottom: 12 }}>Settings</Text>
      <Text variant="titleMedium" style={{ marginBottom: 8 }}>Query Mode</Text>
      <SegmentedButtons
        value={queryMode}
        onValueChange={(value) => updateQueryMode(value as QueryMode)}
        buttons={[
          { value: 'classic', label: 'Classic', disabled: savingMode },
          { value: 'ai', label: 'AI Smart', disabled: savingMode },
        ]}
        style={{ marginBottom: 4 }}
      />
      <HelperText type="info">
        Classic uses pattern-matched queries; AI Smart lets an LLM generate SQL with guardrails.
      </HelperText>
      <TextInput label="API Base URL" value={url} onChangeText={setUrl} mode="outlined" />
      <HelperText type="info">Default: http://localhost:8000</HelperText>
      <View style={{ flexDirection: 'row', marginTop: 8 }}>
        <Button mode="contained" onPress={save} style={{ marginRight: 8 }}>Save</Button>
        <Button mode="outlined" onPress={refresh}>Refresh Data</Button>
      </View>
      <View style={{ flexDirection: 'row', marginTop: 8 }}>
        <Button mode="outlined" onPress={upload} loading={uploading} disabled={uploading}>
          Upload CSVs (ZIP or CSV)
        </Button>
      </View>
      <View style={{ flexDirection: 'row', marginTop: 8 }}>
        <Button mode="outlined" onPress={selfCheck} loading={checking} disabled={checking}>
          Run Self-Check
        </Button>
      </View>
      {status && <Text style={{ marginTop: 12 }}>{status}</Text>}
      {error && <Text style={{ marginTop: 12, color: 'red' }}>{error}</Text>}
      {checkResult && (
        <View style={{ marginTop: 12, padding: 12, borderWidth: 1, borderColor: '#ddd', borderRadius: 8 }}>
          <Text variant="titleMedium" style={{ marginBottom: 8 }}>Self-Check Results</Text>
          {(() => {
            const rows: { label: string; ok: boolean; detail?: string }[] = [];
            const r = checkResult || {};
            const isErr = (v: any) => typeof v === 'string' && v.startsWith('ERROR');
            
            // Total revenue (dynamic date range)
            if (r.total_revenue) {
              const revenue = r.total_revenue;
              const label = revenue.date_range ? `Revenue ${revenue.date_range}` : 'Total Revenue';
              const detail = revenue.amount ? `$${revenue.amount.toFixed(2)}` : String(revenue);
              rows.push({ label, ok: !isErr(revenue), detail });
            }
            
            // Top 5 Products
            rows.push({ label: 'Top 5 Products', ok: !isErr(r.top_5_products), detail: Array.isArray(r.top_5_products) ? `${r.top_5_products.length} items` : String(r.top_5_products) });
            
            // Dynamic Orders (find key that starts with orders_cid_)
            const ordersKey = Object.keys(r).find(k => k.startsWith('orders_cid_'));
            if (ordersKey) {
              const cid = ordersKey.replace('orders_cid_', '');
              const orders = r[ordersKey];
              rows.push({ label: `Orders CID ${cid}`, ok: !isErr(orders), detail: Array.isArray(orders) ? `${orders.length} orders` : String(orders) });
            }
            
            // Dynamic Details (find key that starts with details_iid_)
            const detailsKey = Object.keys(r).find(k => k.startsWith('details_iid_'));
            if (detailsKey) {
              const iid = detailsKey.replace('details_iid_', '');
              const details = r[detailsKey];
              rows.push({ label: `Details IID ${iid}`, ok: !isErr(details), detail: Array.isArray(details) ? `${details.length} lines` : String(details) });
            }
            return rows.map((row, idx) => (
              <View key={idx} style={{ flexDirection: 'row', alignItems: 'center', marginTop: 6 }}>
                <Text style={{ width: 160 }}>{row.label}</Text>
                <Text style={{ color: row.ok ? 'green' : 'red', marginLeft: 8 }}>{row.ok ? 'PASS' : 'FAIL'}</Text>
                {row.detail && <Text style={{ marginLeft: 12, opacity: 0.7 }}>{row.detail}</Text>}
              </View>
            ));
          })()}
        </View>
      )}
    </ScrollView>
  );
}
