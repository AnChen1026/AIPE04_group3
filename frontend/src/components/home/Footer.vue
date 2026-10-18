<template>
  <footer class="footer">
    <div class="footer__inner">
      <div class="footer__brand">
        <p class="footer__logo">琴室</p>
        <p>一對一的鋼琴課，從找到老師開始。</p>
      </div>
      <nav class="footer__nav" aria-label="頁尾">
        <div>
          <p class="footer__title">找課</p>
          <a href="#courses">熱門課程</a>
          <a href="#teachers">認識老師</a>
          <a href="#flow">上課流程</a>
        </div>
        <div>
          <p class="footer__title">帳號</p>
          <RouterLink to="/login">Login</RouterLink>
          <RouterLink to="/signup">Sign up</RouterLink>
        </div>
        <div>
          <p class="footer__title">幫助</p>
          <a href="#faq">常見問題</a>
        </div>
      </nav>
    </div>
    <p class="footer__bottom">© 琴室 鋼琴課程平台</p>
  </footer>
</template>

<style scoped>
.footer {
  margin-top: var(--section-space);
  padding: 64px 0 28px;
  border-top: 1px solid var(--home-line);
  background: var(--home-cream);
  color: var(--home-muted);
}

.footer__inner {
  display: flex;
  justify-content: space-between;
  gap: 48px;
  width: min(1160px, calc(100% - 48px));
  margin: 0 auto;
}

.footer p {
  margin: 0;
}

.footer__logo {
  margin-bottom: 8px !important;
  color: var(--home-ink);
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.footer__nav {
  display: flex;
  gap: 64px;
}

.footer__nav div {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 14px;
}

.footer__title {
  color: var(--home-ink);
  font-weight: 500;
}

.footer a:hover {
  color: var(--home-ink);
}

.footer__bottom {
  width: min(1160px, calc(100% - 48px));
  margin: 48px auto 0 !important;
  padding-top: 20px;
  border-top: 1px solid var(--home-line);
  font-size: 13px;
}

@media (max-width: 760px) {
  .footer__inner {
    flex-direction: column;
    width: calc(100% - 32px);
  }

  .footer__nav {
    gap: 40px;
    flex-wrap: wrap;
  }

  .footer__bottom {
    width: calc(100% - 32px);
  }
}
</style>
