<script setup lang="ts">
import AccountProfileForm from '@/components/console/AccountProfileForm.vue'

// 老師的帳號基本資料。姓名就是學生在課程頁看到的老師姓名，個人資料頁的姓名也會一起更新
</script>

<template>
  <AccountProfileForm id-prefix="ta" description="姓名會顯示在課程頁、聊天與學生名單；個人資料頁的姓名也會一起更新。Email 是登入帳號，不能修改。" />
</template>
