<script setup lang="ts">
withDefaults(defineProps<{
  minWidth?: number;
  cellAlign?: "left" | "center";
}>(), {
  minWidth: 680,
  cellAlign: "left",
});
</script>

<template>
  <div class="teacher-data-table-wrap">
    <table
      class="teacher-data-table"
      :class="{ 'teacher-data-table--centered': cellAlign === 'center' }"
      :style="{ minWidth: `${minWidth}px` }"
    >
      <thead><slot name="head" /></thead>
      <tbody><slot name="body" /></tbody>
    </table>
  </div>
</template>

<style scoped>
.teacher-data-table-wrap{overflow-x:auto}.teacher-data-table{width:100%;border-collapse:collapse}.teacher-data-table th,.teacher-data-table td{padding:13px;border-bottom:1px solid #dce3de;text-align:left;white-space:nowrap}.teacher-data-table th{color:#687970;font-size:12px;font-weight:800}.teacher-data-table td{color:#334b40;font-size:13px}

/* 业务行来自具名插槽，居中变体必须显式穿透 scoped 边界作用到真实单元格。 */
.teacher-data-table--centered :deep(th),
.teacher-data-table--centered :deep(td) {
  text-align: center;
}
</style>
