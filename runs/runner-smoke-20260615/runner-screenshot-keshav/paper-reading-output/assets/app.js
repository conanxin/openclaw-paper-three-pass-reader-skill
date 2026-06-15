// paper-three-pass-reader app.js — local-only, vanilla JS, no dependencies.
// Interactions: tabs, claim filter, reading-mode badge styling.

(function () {
  'use strict';

  // ---- Tabs ---------------------------------------------------------------
  function setupTabs() {
    var buttons = document.querySelectorAll('.tab-btn');
    var panels  = document.querySelectorAll('.tab-panel');
    if (!buttons.length) return;

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var target = btn.getAttribute('data-tab');
        buttons.forEach(function (b) { b.classList.toggle('active', b === btn); });
        panels.forEach(function (p) {
          p.classList.toggle('active', p.getAttribute('data-panel') === target);
        });
      });
    });
  }

  // ---- Claims-Evidence filter --------------------------------------------
  function setupClaimFilter() {
    var conf   = document.getElementById('filter-confidence');
    var label  = document.getElementById('filter-label');
    var needs  = document.getElementById('filter-needs');
    var rows   = document.querySelectorAll('.claims-table tbody tr');
    if (!rows.length) return;

    function apply() {
      var cv = conf ? conf.value : '';
      var lv = label ? label.value : '';
      var nv = needs ? needs.checked : false;

      rows.forEach(function (tr) {
        var rc = tr.getAttribute('data-confidence') || '';
        var rl = tr.getAttribute('data-label') || '';
        var rn = tr.getAttribute('data-needs') === 'true';
        var show = true;
        if (cv && rc !== cv) show = false;
        if (lv && rl !== lv) show = false;
        if (nv && !rn) show = false;
        tr.style.display = show ? '' : 'none';
      });
    }

    if (conf)  conf.addEventListener('change', apply);
    if (label) label.addEventListener('change', apply);
    if (needs) needs.addEventListener('change', apply);
  }

  // ---- Reading-mode badge styling ----------------------------------------
  function styleReadingModeBadge() {
    var body = document.body;
    var mode = body.getAttribute('data-reading-mode');
    if (!mode) return;
    body.classList.add('mode-' + mode.replace('_', '-'));
    var badge = document.querySelector('.badge-mode');
    if (badge) {
      badge.style.background =
        mode === 'full_text'      ? 'rgba(47,133,90,0.18)' :
        mode === 'partial_text'   ? 'rgba(183,121,31,0.18)' :
        mode === 'abstract_only'  ? 'rgba(107,70,193,0.18)' :
                                     'rgba(197,48,48,0.18)';
      badge.style.color =
        mode === 'full_text'      ? '#9ae6b4' :
        mode === 'partial_text'   ? '#fbd38d' :
        mode === 'abstract_only'  ? '#d6bcfa' :
                                     '#feb2b2';
      badge.style.borderColor = badge.style.color;
    }
  }

  // ---- Glossary chips: close others on open ------------------------------
  function setupGlossary() {
    var chips = document.querySelectorAll('.chips .chip');
    chips.forEach(function (c) {
      c.addEventListener('toggle', function () {
        if (c.open) {
          chips.forEach(function (o) { if (o !== c) o.open = false; });
        }
      });
    });
  }

  // ---- Persist checkbox state in localStorage ----------------------------
  function setupChecklist() {
    var KEY = 'p3pr_checklist_' + (document.title || 'paper');
    var items = document.querySelectorAll('.checklist input[type="checkbox"]');
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}

    items.forEach(function (cb, i) {
      cb.checked = !!saved[i];
      cb.addEventListener('change', function () {
        saved[i] = cb.checked;
        try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
      });
    });
  }

  // ---- Init --------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    setupTabs();
    setupClaimFilter();
    styleReadingModeBadge();
    setupGlossary();
    setupChecklist();
  });
})();
