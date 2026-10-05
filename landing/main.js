/* ===========================================================================
   ScholarBot AI — landing page behaviour
   Every animation here is additive: with JS disabled or reduced motion on,
   the page still reads as a finished document.
   ======================================================================== */

(function () {
  'use strict';
  document.documentElement.classList.add('js');

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------ scroll reveals ----- */
  var reveals = document.querySelectorAll('.reveal');

  if (reduced || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    // stagger hero children in source order
    document.querySelectorAll('.hero .reveal').forEach(function (el, i) {
      el.style.setProperty('--i', i);
    });

    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, i) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        // elements that enter together cascade rather than pop at once
        el.style.animationDelay = (el.closest('.hero') ? '' : (i * 70) + 'ms');
        el.classList.add('is-in');
        revealObserver.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    reveals.forEach(function (el) { revealObserver.observe(el); });
  }

  /* ------------------------------------------- nav + read progress ----- */
  var nav = document.querySelector('.nav');
  var progress = document.getElementById('progress');
  var ticking = false;

  function onScroll() {
    var y = window.scrollY;
    if (nav) nav.classList.toggle('is-stuck', y > 8);
    if (progress) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
    }
    parallax();
    ticking = false;
  }

  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(onScroll);
  }, { passive: true });

  /* --------------------------------------------------- parallax -------- */
  var parallaxEls = reduced ? [] : Array.prototype.slice.call(document.querySelectorAll('[data-parallax]'));

  function parallax() {
    var vh = window.innerHeight;
    parallaxEls.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > vh) return;
      // -1 (entering from below) .. 1 (leaving above)
      var p = (rect.top + rect.height / 2 - vh / 2) / vh;
      el.style.transform = 'translate3d(0,' + (p * -22).toFixed(2) + 'px,0) scale(1.06)';
    });
  }

  /* ------------------------------------------------ count-up stats ----- */
  var counters = document.querySelectorAll('[data-count]');

  function runCounter(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    if (reduced || target === 0) { el.textContent = String(target); return; }
    var start = performance.now();
    var dur = 1100;
    (function tick(now) {
      var t = Math.min((now - start) / dur, 1);
      // easeOutExpo keeps the last digits from crawling
      var eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      el.textContent = String(Math.round(target * eased));
      if (t < 1) requestAnimationFrame(tick);
    })(start);
  }

  if ('IntersectionObserver' in window) {
    var countObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        runCounter(entry.target);
        countObserver.unobserve(entry.target);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { countObserver.observe(el); });
  } else {
    counters.forEach(runCounter);
  }

  /* ------------------------------------------- pipeline line + steps --- */
  var pipeline = document.querySelector('.pipeline');
  if (pipeline && 'IntersectionObserver' in window) {
    var pipeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        pipeline.style.setProperty('--pipe', '100%');
        pipeline.querySelectorAll('.step').forEach(function (step, i) {
          setTimeout(function () { step.classList.add('is-in'); }, reduced ? 0 : i * 180);
        });
        pipeObserver.disconnect();
      });
    }, { threshold: 0.35 });
    pipeObserver.observe(pipeline);
  } else if (pipeline) {
    pipeline.style.setProperty('--pipe', '100%');
    pipeline.querySelectorAll('.step').forEach(function (s) { s.classList.add('is-in'); });
  }

  /* ------------------------------------------------- the chat demo ----- */
  var demo = document.querySelector('[data-demo]');
  if (!demo) return;

  var userBubble = demo.querySelector('[data-step="1"]');
  var botBubble = demo.querySelector('[data-step="2"]');
  var srcCard = demo.querySelector('[data-step="3"]');
  var typing = demo.querySelector('.typing');
  var answerEl = demo.querySelector('.answer');
  var replayBtn = demo.querySelector('[data-replay]');

  var ANSWER = 'Karena beras adalah kebutuhan pokok — orang tetap membelinya meski harga naik, jadi koefisien elastisitasnya di bawah satu.';
  var timers = [];

  function clearTimers() {
    timers.forEach(clearTimeout);
    timers = [];
  }

  function at(ms, fn) { timers.push(setTimeout(fn, ms)); }

  function lightSource(on) {
    srcCard.classList.toggle('is-lit', on);
    var badge = answerEl.querySelector('.srcbadge');
    if (badge) badge.classList.toggle('is-active', on);
  }

  function addBadge() {
    var badge = document.createElement('button');
    badge.type = 'button';
    badge.className = 'srcbadge';
    badge.textContent = '1';
    badge.setAttribute('aria-label', 'Lihat sumber 1');
    badge.addEventListener('click', function () {
      lightSource(true);
      srcCard.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
    });
    badge.addEventListener('mouseenter', function () { lightSource(true); });
    badge.addEventListener('mouseleave', function () { lightSource(false); });
    answerEl.appendChild(document.createTextNode(' '));
    answerEl.appendChild(badge);
    return badge;
  }

  function finalState() {
    clearTimers();
    userBubble.classList.add('is-in');
    botBubble.classList.add('is-in');
    typing.classList.add('is-done');
    answerEl.textContent = ANSWER;
    addBadge();
    srcCard.classList.add('is-in');
  }

  function typeOut(text, done) {
    var i = 0;
    (function step() {
      answerEl.textContent = text.slice(0, ++i);
      if (i < text.length) {
        // slight jitter reads more like generation than a metronome
        timers.push(setTimeout(step, 14 + Math.random() * 16));
      } else if (done) {
        done();
      }
    })();
  }

  function play() {
    clearTimers();
    userBubble.classList.remove('is-in');
    botBubble.classList.remove('is-in');
    srcCard.classList.remove('is-in', 'is-lit');
    typing.classList.remove('is-done');
    answerEl.textContent = '';

    if (reduced) { finalState(); return; }

    at(150, function () { userBubble.classList.add('is-in'); });
    at(850, function () { botBubble.classList.add('is-in'); });
    at(1900, function () {
      typing.classList.add('is-done');
      typeOut(ANSWER, function () {
        at(120, function () {
          addBadge();
          at(420, function () {
            srcCard.classList.add('is-in');
            // one brief nudge to teach the interaction, then let it rest
            at(700, function () { lightSource(true); });
            at(1700, function () { lightSource(false); });
          });
        });
      });
    });
  }

  if ('IntersectionObserver' in window) {
    var demoObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        play();
        demoObserver.disconnect();
      });
    }, { threshold: 0.4 });
    demoObserver.observe(demo);
  } else {
    finalState();
  }

  if (replayBtn) replayBtn.addEventListener('click', play);

  onScroll();
})();
