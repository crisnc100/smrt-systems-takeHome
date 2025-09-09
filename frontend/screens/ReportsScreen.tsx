import * as React from 'react';
import { ScrollView, View } from 'react-native';
import { Text, Button, SegmentedButtons } from 'react-native-paper';

export default function ReportsScreen() {
  const [tab, setTab] = React.useState<'revenue_by_month' | 'top_customers'>('revenue_by_month');

  return (
    <ScrollView contentContainerStyle={{ padding: 16 }}>
      <Text variant="titleLarge">Reports</Text>
      <SegmentedButtons
        value={tab}
        onValueChange={(v: any) => setTab(v)}
        buttons={[
          { value: 'revenue_by_month', label: 'Revenue by Month' },
          { value: 'top_customers', label: 'Top Customers' },
        ]}
        style={{ marginVertical: 12 }}
      />
      <View style={{ padding: 12, borderRadius: 8, borderColor: '#ddd', borderWidth: 1 }}>
        <Text>
          {tab === 'revenue_by_month'
            ? 'Revenue by Month chart will appear here (coming soon).'
            : 'Top Customers chart will appear here (coming soon).'}
        </Text>
      </View>
      <Button mode="outlined" style={{ marginTop: 12 }} disabled>
        Export CSV (coming soon)
      </Button>
    </ScrollView>
  );
}

