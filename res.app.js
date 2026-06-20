/* Loki CLI Documentation - res.app.js */

(function () {
  'use strict';

  // Active nav link tracking
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section');

  function updateActiveNav() {
    let current = '';
    const scrollPos = window.scrollY + 100;

    sections.forEach(function (section) {
      if (section.offsetTop <= scrollPos) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(function (link) {
      link.classList.remove('active');
      if (link.getAttribute('href') === '#' + current) {
        link.classList.add('active');
      }
    });
  }

  // Smooth scroll for nav links
  navLinks.forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var targetId = this.getAttribute('href').substring(1);
      var target = document.getElementById(targetId);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Scroll spy
  var scrollTimeout;
  window.addEventListener('scroll', function () {
    if (scrollTimeout) {
      cancelAnimationFrame(scrollTimeout);
    }
    scrollTimeout = requestAnimationFrame(updateActiveNav);
  });

  // Initial state
  updateActiveNav();

  // Expand all / collapse all for lists
  document.addEventListener('click', function (e) {
    if (e.target.matches('.expand-toggle')) {
      var parent = e.target.closest('.card, .cmd-card, .file-card, .bug-card');
      if (parent) {
        var lists = parent.querySelectorAll('ul, ol');
        lists.forEach(function (list) {
          if (list.style.display === 'none') {
            list.style.display = '';
            e.target.textContent = 'Collapse';
          } else {
            list.style.display = 'none';
            e.target.textContent = 'Expand';
          }
        });
      }
    }
  });

  // Code block click to copy
  document.querySelectorAll('pre code').forEach(function (block) {
    block.style.cursor = 'pointer';
    block.title = 'Click to copy';

    block.addEventListener('click', function () {
      var text = this.textContent;
      navigator.clipboard.writeText(text).then(function () {
        var original = block.style.outline;
        block.style.outline = '2px solid var(--accent-green)';
        block.style.outlineOffset = '2px';
        setTimeout(function () {
          block.style.outline = original;
          block.style.outlineOffset = '';
        }, 800);
      });
    });
  });

  // Keyboard navigation
  document.addEventListener('keydown', function (e) {
    // Alt + arrow keys to navigate sections
    if (e.altKey && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      var currentSection = null;
      var scrollPos = window.scrollY + 100;

      sections.forEach(function (section) {
        if (section.offsetTop <= scrollPos) {
          currentSection = section;
        }
      });

      if (currentSection) {
        var allSections = Array.from(sections);
        var idx = allSections.indexOf(currentSection);

        if (e.key === 'ArrowDown' && idx < allSections.length - 1) {
          allSections[idx + 1].scrollIntoView({ behavior: 'smooth' });
        } else if (e.key === 'ArrowUp' && idx > 0) {
          allSections[idx - 1].scrollIntoView({ behavior: 'smooth' });
        }
      }
    }
  });

})();
