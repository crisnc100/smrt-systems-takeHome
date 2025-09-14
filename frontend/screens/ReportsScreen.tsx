import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { Text, Button, SegmentedButtons, ActivityIndicator } from 'react-native-paper';
import { callReport, getDataStatus } from '../lib/api';
import Chart from '../components/Chart';

export default function ReportsScreen() {
  const [tab, setTab] = React.useState<'revenue_by_month' | 'top_customers'>('revenue_by_month');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<any | null>(null);
  const [freshness, setFreshness] = React.useState<{ max?: string; orders?: number } | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await callReport(tab);
      if (res.error) {
        setError(res.error);
        setData(null);
      } else {
        setData(res);
      }
    } catch (e) {
      setError(String(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  React.useEffect(() => {
    load();
    (async () => {
      try {
        const ds = await getDataStatus();
        const max = ds?.date_analysis?.inventory?.max_date;
        const orders = ds?.tables?.Inventory?.count;
        setFreshness({ max, orders });
      } catch {}
    })();
  }, [tab, load]);

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }}>
      <Text variant="titleLarge">Reports</Text>
      {freshness && (
        <Text style={{ marginTop: 4, marginBottom: 8, opacity: 0.7 }}>
          Using data through {freshness.max || 'n/a'} {typeof freshness.orders === 'number' ? `(${freshness.orders} orders)` : ''}
        </Text>
      )}
      <SegmentedButtons
        value={tab}
        onValueChange={(v: any) => setTab(v)}
        buttons={[
          { value: 'revenue_by_month', label: 'Revenue by Month' },
          { value: 'top_customers', label: 'Top Customers' },
        ]}
        style={{ marginVertical: 12 }}
      />
      {loading && <ActivityIndicator />}
      {error && <Text style={{ color: 'red' }}>{error}</Text>}
      {data && (
        <View style={{ padding: 12, borderRadius: 8, borderColor: '#ddd', borderWidth: 1 }}>
          <Text style={{ marginBottom: 8 }}>{data.summary_text}</Text>
          {data.charts && data.charts[0] && (
            <Chart type={data.charts[0].type} series={data.charts[0].series} />
          )}
        </View>
      )}
      
    </ScrollView>
  );
}
