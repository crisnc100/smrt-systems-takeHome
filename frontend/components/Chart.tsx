import * as React from 'react';
import { View, Dimensions, ScrollView } from 'react-native';
import { Text } from 'react-native-paper';
import { BarChart, LineChart } from 'react-native-chart-kit';

type Series = { name: string; data: [string, number][] };

export default function Chart({ type, series }: { type: 'bar' | 'line' | string; series: Series[] }) {
  if (!series || series.length === 0) return <Text>No data</Text>;
  
  const screenWidth = Dimensions.get('window').width;
  const labels = series[0].data.map(([x]) => x);
  const datasets = series.map(s => ({
    data: s.data.map(([, y]) => y),
    color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
    strokeWidth: 2
  }));

  const chartConfig = {
    backgroundColor: '#ffffff',
    backgroundGradientFrom: '#ffffff',
    backgroundGradientTo: '#ffffff',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16
    },
    propsForDots: {
      r: '6',
      strokeWidth: '2',
      stroke: '#ffa726'
    }
  };

  const data = {
    labels,
    datasets,
    legend: series.map(s => s.name)
  };

  return (
    <ScrollView horizontal={true}>
      <View>
        {type === 'line' ? (
          <LineChart
            data={data}
            width={Math.max(screenWidth - 32, labels.length * 60)}
            height={220}
            yAxisLabel="$"
            yAxisSuffix=""
            chartConfig={chartConfig}
            bezier
            style={{
              marginVertical: 8,
              borderRadius: 16
            }}
          />
        ) : (
          <BarChart
            data={data}
            width={Math.max(screenWidth - 32, labels.length * 60)}
            height={220}
            yAxisLabel="$"
            yAxisSuffix=""
            chartConfig={chartConfig}
            style={{
              marginVertical: 8,
              borderRadius: 16
            }}
          />
        )}
      </View>
    </ScrollView>
  );
}

