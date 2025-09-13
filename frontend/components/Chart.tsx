import * as React from 'react';
import { View, Dimensions, ScrollView } from 'react-native';
import { Text } from 'react-native-paper';
import { BarChart, LineChart } from 'react-native-chart-kit';

type Series = { name: string; data: [string, number][] };

export default function Chart({ type, series }: { type: 'bar' | 'line' | string; series: Series[] }) {
  if (!series || series.length === 0) return <Text>No data</Text>;
  
  const screenWidth = Dimensions.get('window').width;
  
  // Format labels to be shorter
  const formatLabel = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) {
        // For dates, just show MM/DD
        return `${date.getMonth() + 1}/${date.getDate()}`;
      }
    } catch {}
    // For products or other labels, truncate if too long
    if (dateStr.length > 8) {
      return dateStr.substring(0, 6) + '...';
    }
    return dateStr;
  };
  
  // Limit data points based on screen width
  const maxPoints = 7; // Show max 7 points for cleaner view
  const dataSlice = series[0].data.slice(-maxPoints);
  
  const labels = dataSlice.map(([x]) => formatLabel(x));
  const datasets = series.map(s => ({
    data: s.data.slice(-maxPoints).map(([, y]) => Math.round(y)),
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`, // Softer blue
    strokeWidth: 2
  }));

  const chartConfig = {
    backgroundColor: '#ffffff',
    backgroundGradientFrom: '#ffffff',
    backgroundGradientTo: '#ffffff',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`, // Blue theme
    labelColor: (opacity = 1) => `rgba(100, 100, 100, ${opacity})`, // Softer labels
    style: {
      borderRadius: 8,
      paddingRight: 0
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#3b82f6'
    },
    propsForBackgroundLines: {
      strokeDasharray: '', // solid lines
      stroke: '#f0f0f0', // very light gray
      strokeWidth: 1
    }
  };

  const data = {
    labels,
    datasets,
    legend: series.map(s => s.name)
  };

  // Fixed width chart, no scrolling
  const chartWidth = screenWidth - 48; // Full width minus padding
  
  const chartElement = type === 'line' ? (
    <LineChart
      data={data}
      width={chartWidth}
      height={200}
      yAxisLabel=""
      yAxisSuffix=""
      yAxisInterval={1}
      chartConfig={chartConfig}
      bezier
      style={{
        marginVertical: 8,
        marginLeft: -15, // Adjust for padding
        borderRadius: 8
      }}
      withInnerLines={true}
      withOuterLines={false}
      withVerticalLabels={true}
      withHorizontalLabels={true}
      segments={4}
      formatYLabel={(value) => {
        const num = parseFloat(value);
        if (num >= 1000) return `$${(num/1000).toFixed(0)}k`;
        return `$${num}`;
      }}
    />
  ) : (
    <BarChart
      data={data}
      width={chartWidth}
      height={200}
      yAxisLabel=""
      yAxisSuffix=""
      chartConfig={chartConfig}
      style={{
        marginVertical: 8,
        marginLeft: -15,
        borderRadius: 8
      }}
      withInnerLines={true}
      showBarTops={false}
      withVerticalLabels={true}
      formatYLabel={(value) => {
        const num = parseFloat(value);
        if (num >= 1000) return `${(num/1000).toFixed(0)}k`;
        return `${num}`;
      }}
    />
  );
  
  return <View>{chartElement}</View>;
}

