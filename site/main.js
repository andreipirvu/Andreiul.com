// Mobile menu toggle
const navLinks = document.querySelector('.nav-links');
const menuToggle = document.querySelector('.menu-toggle');
menuToggle.addEventListener('click', () => navLinks.classList.toggle('open'));

// Expand/collapse experience cards (was inline onclick; moved here so CSP can forbid inline scripts)
document.querySelectorAll('.company-header').forEach(header => {
  header.addEventListener('click', () => header.parentElement.classList.toggle('open'));
});

// Close menu on link click
document.querySelectorAll('.nav-links a').forEach(a => {
  a.addEventListener('click', () => navLinks.classList.remove('open'));
});

// Close menu when tapping outside
document.addEventListener('click', (e) => {
  if (navLinks.classList.contains('open') &&
      !navLinks.contains(e.target) &&
      !menuToggle.contains(e.target)) {
    navLinks.classList.remove('open');
  }
});

// Fade-in on scroll
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

// Smooth scroll offset for sticky nav
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const targetId = this.getAttribute('href');
    if (targetId === '#') return;
    const target = document.querySelector(targetId);
    if (!target) return;
    e.preventDefault();
    const navHeight = document.querySelector('nav').offsetHeight;
    const targetPos = target.getBoundingClientRect().top + window.scrollY - navHeight - 16;
    window.scrollTo({ top: targetPos, behavior: 'smooth' });
  });
});
