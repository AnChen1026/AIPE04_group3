<script setup lang="ts">
// 聊天頁的左右兩欄：左邊是對話列表（default slot），右邊是選到的對話（子路由）。
// 點左邊另一個人就直接換右邊，不用先按返回。手機寬度只顯示其中一邊。
defineProps<{
  // 網址有沒有選到一段對話
  hasRoom: boolean
  // 手機上「回對話列表」要去的網址
  backTo: string
}>()
</script>

<template>
  <div class="chat-split" :class="{ 'chat-split--open': hasRoom }">
    <aside class="chat-split__list" aria-label="對話列表">
      <slot />
    </aside>
    <section class="chat-split__room">
      <RouterLink v-if="hasRoom" :to="backTo" class="chat-split__back">‹ 回對話列表</RouterLink>
      <RouterView v-slot="{ Component, route }">
        <component :is="Component" v-if="Component" :key="route.path" />
      </RouterView>
      <div v-if="!hasRoom" class="chat-split__empty">從左邊選一個對話</div>
    </section>
  </div>
</template>

<style scoped>
.chat-split {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.chat-split__list {
  max-height: min(70vh, 640px);
  overflow-y: auto;
  padding-right: 4px;
}

.chat-split__room {
  min-width: 0;
}

.chat-split__back {
  display: none;
  margin-bottom: 10px;
  color: var(--home-muted);
  font-size: 14px;
}

.chat-split__empty {
  display: grid;
  place-items: center;
  height: min(70vh, 640px);
  border: 1px dashed var(--home-line);
  border-radius: 22px;
  color: var(--home-muted);
}

@media (max-width: 900px) {
  .chat-split {
    grid-template-columns: minmax(0, 1fr);
  }

  .chat-split__list {
    max-height: none;
    overflow: visible;
  }

  .chat-split--open .chat-split__list,
  .chat-split:not(.chat-split--open) .chat-split__room {
    display: none;
  }

  .chat-split__back {
    display: inline-block;
  }
}
</style>
