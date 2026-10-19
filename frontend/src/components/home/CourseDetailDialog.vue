<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import ModalPanel from '@/components/console/ModalPanel.vue'
import type { CourseCardData } from '@/mocks/home'
import { useAuthStore } from '@/stores/auth'
import defaultTeacher from '@/assets/images/女老師3.png'

// 首頁點課程卡後的課程詳情。「與老師接洽」：訪客先註冊，學生直接打開聊天。
const props = defineProps<{ course: CourseCardData | null }>()
const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const auth = useAuthStore()

const isTeacher = computed(() => auth.user?.role === 'teacher' || auth.user?.role === 'admin')
const contactLabel = computed(() => (auth.user?.role === 'student' ? '與老師接洽' : '註冊並與老師接洽'))

function contact() {
  if (!props.course) return
  emit('close')
  router.push({ name: 'contact-teacher', params: { id: props.course.id } })
}
</script>

<template>
  <ModalPanel :open="course !== null" :title="course?.title ?? ''" wide @close="emit('close')">
    <template v-if="course">
      <div class="detail">
        <img v-if="course.cover" class="detail__cover" :src="course.cover" :alt="course.title" />
        <div class="detail__teacher">
          <img :src="course.teacherPhoto ?? defaultTeacher" :alt="`${course.teacherName}的照片`" />
          <div>
            <strong>{{ course.teacherName }}</strong>
            <span>{{ course.category }}</span>
          </div>
        </div>
        <dl class="detail__facts">
          <div>
            <dt>程度</dt>
            <dd>{{ course.level }}</dd>
          </div>
          <div>
            <dt>上課方式</dt>
            <dd>{{ course.format }}</dd>
          </div>
          <div>
            <dt>地區</dt>
            <dd>{{ course.region || '未填' }}</dd>
          </div>
          <div>
            <dt>時段</dt>
            <dd>{{ course.timeSlots || '洽詢時確認' }}</dd>
          </div>
          <div>
            <dt>價格</dt>
            <dd>{{ course.price === null ? '洽詢時確認' : `NT$ ${course.price.toLocaleString('zh-TW')} / 堂` }}</dd>
          </div>
        </dl>
        <p v-if="course.description" class="detail__description">{{ course.description }}</p>
      </div>
    </template>
    <template #footer>
      <p v-if="isTeacher" class="detail__teacher-note">請用學生帳號與老師接洽。</p>
      <button type="button" class="btn btn--ghost" @click="emit('close')">再看看</button>
      <button type="button" class="btn btn--primary" :disabled="isTeacher" @click="contact">{{ contactLabel }}</button>
    </template>
  </ModalPanel>
</template>

<style scoped>
.detail__cover {
  width: 100%;
  aspect-ratio: 16 / 7;
  object-fit: cover;
  border-radius: 20px;
}

.detail__teacher {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.detail__teacher img {
  width: 52px;
  height: 52px;
  object-fit: cover;
  object-position: center 20%;
  border-radius: 50%;
}

.detail__teacher div {
  display: flex;
  flex-direction: column;
}

.detail__teacher span {
  color: var(--home-accent);
  font-size: 13px;
}

.detail__facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin: 16px 0 0;
}

.detail__facts div {
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--home-bg);
}

.detail__facts dt {
  color: var(--home-muted);
  font-size: 12px;
}

.detail__facts dd {
  margin: 2px 0 0;
  font-size: 14px;
}

.detail__description {
  margin: 16px 0 0;
  line-height: 1.8;
  white-space: pre-wrap;
}

.detail__teacher-note {
  margin: 0 auto 0 0;
  color: var(--home-muted);
  font-size: 13px;
  align-self: center;
}
</style>
