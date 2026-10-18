<template>
  <footer class="footer">
    <div class="footer__inner">
      <div>
        <p class="footer__brand">琴室</p>
        <p>一對一的鋼琴課，從找到老師開始。</p>
      </div>
      <nav aria-label="頁尾">
        <a href="#teachers">老師</a>
        <a href="#courses">課程</a>
        <RouterLink to="/login">Login</RouterLink>
      </nav>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  margin-top: var(--section-space);
  border-top: 1px solid var(--home-line);
  background: #f3eadf;
}

.footer__inner {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  width: min(1120px, calc(100% - 48px));
  margin: 0 auto;
  padding: 36px 0;
  color: var(--home-muted);
}

.footer__brand {
  margin: 0 0 6px;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 24px;
}

.footer p {
  margin: 0;
}

.footer nav {
  display: flex;
  gap: 18px;
}

.footer a:hover {
  color: var(--home-ink);
}

@media (max-width: 640px) {
  .footer__inner {
    flex-direction: column;
    align-items: flex-start;
    width: calc(100% - 32px);
  }
}
</style>
