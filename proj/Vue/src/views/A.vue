<template>
  <div class="counter">
    <h1>计数器11</h1>
    <p>当前数量：{{ count }}</p>
    <button @click="add">增加</button>
    <button @click="reduce">减少</button>
    <button @click="reset">重置</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const count = ref<number>(0)

function add() {
  count.value++
}

function reduce() {
  count.value--
}

function reset() {
  count.value = 0
}
</script>

<style scoped>
.counter {
  padding: 20px;
}

button {
  margin-right: 10px;
}
</style>