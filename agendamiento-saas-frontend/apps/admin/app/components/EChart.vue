<script setup lang="ts">
/**
 * Thin ECharts wrapper. Registers only the chart types + components we use
 * (tree-shaken) and renders client-side. Pass a full ECharts `option` object.
 */
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, HeatmapChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  TitleComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  TitleComponent
])

defineProps<{ option: Record<string, unknown> }>()
</script>

<template>
  <ClientOnly>
    <VChart :option="option" autoresize class="h-72 w-full" />
  </ClientOnly>
</template>
