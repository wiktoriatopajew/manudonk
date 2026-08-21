/*
 * Panel layout editing for the internal dashboards (/panel, /kalkulator).
 *
 * A lock button in the header gates all editing: while locked the dashboard is
 * read-only. When unlocked every panel can be dragged to reorder and hidden
 * with the eye-off button; hidden panels are listed in the "Ukryte panele"
 * toolbar below the grid so they can be restored.
 *
 * - Grid panels (store cards / GMC timers): order + hidden persist via
 *   POST /api/layout (DB).
 * - Side panels on /panel (Domeny / GMC / Google Ads): order + hidden persist
 *   in localStorage (pure UI sections, nothing server-side).
 */
(function () {
  'use strict';

  var LOCK_KEY = 'panelLocked';
  var SIDE_KEY = 'panelSideLayout';

  var locked = true;
  var lockBtn = null;
  var btnWired = false;
  var groups = [];

  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function loadLock() {
    try { return localStorage.getItem(LOCK_KEY) !== 'false'; } catch (e) { return true; }
  }

  function saveLock(v) {
    try { localStorage.setItem(LOCK_KEY, v ? 'true' : 'false'); } catch (e) {}
  }

  function syncBtn() {
    if (!lockBtn) return;
    lockBtn.textContent = locked ? '🔒' : '🔓';
    lockBtn.classList.toggle('unlocked', !locked);
    lockBtn.title = locked ? 'Odblokuj panele' : 'Zablokuj panele';
    lockBtn.setAttribute('aria-pressed', locked ? 'false' : 'true');
  }

  function wire(btn) {
    if (btnWired || !btn) return;
    btnWired = true;
    lockBtn = btn;
    btn.addEventListener('click', function () {
      locked = !locked;
      saveLock(locked);
      document.body.classList.toggle('editing', !locked);
      syncBtn();
      groups.forEach(function (g) { g.refresh(); });
    });
  }

  function toolbarHtml(kind, hidden) {
    var html = '<div class="edit-hint">🔓 Tryb edycji — przeciągnij panele za górny pasek, ' +
      'aby je przenosić. Ukrywaj przyciskiem 🙈.</div>';
    if (hidden.length) {
      html += '<div class="hidden-title">Ukryte panele (' + hidden.length + ')</div><div class="hidden-list">';
      hidden.forEach(function (p) {
        html += '<span class="hidden-chip"><span>' + esc(p.name) + '</span>' +
          '<button type="button" class="panel-show" data-show="' + esc(p.id) + '" data-show-kind="' + kind + '">Pokaż</button></span>';
      });
      html += '</div>';
    }
    return html;
  }

  /* ------------------------------------------------------------------ *
   * Grid group: draggable .card panels (stores / GMC timers)
   * ------------------------------------------------------------------ */

  function createGridGroup(o) {
    var grid = o.grid;
    var host = o.host || (grid ? grid.parentNode : null);
    var getPanels = o.getPanels;
    var onReorder = o.onReorder;
    var onSetHidden = o.onSetHidden;
    var toolbar = null;
    var drag = null;

    function isPanelCard(c) {
      return c && c.classList && c.classList.contains('card') &&
        !c.classList.contains('add-card') && !c.classList.contains('empty');
    }

    function getCards() {
      return Array.prototype.filter.call(grid.querySelectorAll('.card'), isPanelCard);
    }

    function buildToolbar() {
      var bar = document.createElement('div');
      bar.className = 'edit-toolbar';
      var hidden = (getPanels() || []).filter(function (p) { return p.hidden; });
      bar.innerHTML = toolbarHtml('grid', hidden);
      bar.addEventListener('click', function (e) {
        var btn = e.target.closest('.panel-show');
        if (btn && onSetHidden) onSetHidden(btn.dataset.show, false);
      });
      return bar;
    }

    function addControls(card) {
      if (card.querySelector('.panel-controls')) return;
      var id = card.dataset.panelId;
      if (id == null) return;
      var ctrl = document.createElement('div');
      ctrl.className = 'panel-controls';
      ctrl.innerHTML = '<span class="drag-handle">⠿ <em>przenieś</em></span>' +
        '<button type="button" class="panel-hide" data-hide="' + esc(id) + '" title="Ukryj panel">🙈</button>';
      card.prepend(ctrl);
    }

    function removeControls(card) {
      var c = card.querySelector('.panel-controls');
      if (c) c.remove();
    }

    function refresh() {
      if (toolbar) { toolbar.remove(); toolbar = null; }
      if (locked) { getCards().forEach(removeControls); return; }
      if (host) {
        toolbar = buildToolbar();
        host.appendChild(toolbar);
      }
      getCards().forEach(addControls);
    }

    grid.addEventListener('pointerdown', function (e) {
      if (locked) return;
      var ctrl = e.target.closest('.panel-controls');
      if (!ctrl) return;
      if (e.target.closest('.panel-hide')) return;
      var card = ctrl.closest('.card');
      if (!card || !isPanelCard(card)) return;
      e.preventDefault();
      drag = { card: card, x: e.clientX, y: e.clientY, rect: card.getBoundingClientRect(), moved: false };
    });

    window.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) > 4) {
        drag.moved = true;
        document.body.classList.add('is-dragging');
        drag.card.classList.add('dragging');
        drag.card.style.position = 'fixed';
        drag.card.style.left = drag.rect.left + 'px';
        drag.card.style.top = drag.rect.top + 'px';
        drag.card.style.width = drag.rect.width + 'px';
        drag.card.style.zIndex = '80';
      }
      if (!drag.moved) return;
      drag.card.style.left = drag.rect.left + dx + 'px';
      drag.card.style.top = drag.rect.top + dy + 'px';

      var cards = getCards().filter(function (c) { return c !== drag.card; });
      for (var i = 0; i < cards.length; i++) {
        var r = cards[i].getBoundingClientRect();
        if (e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom) {
          var after = e.clientY - r.top > r.height / 2;
          if (after) {
            if (cards[i].nextElementSibling !== drag.card) {
              grid.insertBefore(drag.card, cards[i].nextElementSibling);
            }
          } else {
            if (drag.card.nextElementSibling !== cards[i]) {
              grid.insertBefore(drag.card, cards[i]);
            }
          }
          break;
        }
      }
    });

    window.addEventListener('pointerup', function () {
      if (!drag) return;
      var card = drag.card, moved = drag.moved;
      drag = null;
      document.body.classList.remove('is-dragging');
      card.classList.remove('dragging');
      card.style.position = '';
      card.style.left = '';
      card.style.top = '';
      card.style.width = '';
      card.style.zIndex = '';
      if (moved && onReorder) {
        onReorder(getCards().map(function (c) { return c.dataset.panelId; }));
        refresh();
      }
    });

    grid.addEventListener('click', function (e) {
      if (locked) return;
      var btn = e.target.closest('.panel-hide');
      if (btn && onSetHidden) onSetHidden(btn.dataset.hide, true);
    });

    var g = { refresh: refresh };
    groups.push(g);
    return g;
  }

  /* ------------------------------------------------------------------ *
   * Side group: the /panel sidebar cards (Domeny, GMC, Google Ads)
   * ------------------------------------------------------------------ */

  function createSideGroup(o) {
    var aside = o.aside;
    var sections = o.sections; // [{key, el, name}]
    var toolbar = null;
    var drag = null;
    var layout = loadSideLayout();

    function loadSideLayout() {
      var def = { order: sections.map(function (s) { return s.key; }), hidden: [] };
      try {
        var raw = JSON.parse(localStorage.getItem(SIDE_KEY) || 'null');
        if (raw && Array.isArray(raw.order)) {
          def.order = raw.order.filter(function (k) {
            return sections.some(function (s) { return s.key === k; });
          });
          def.hidden = (raw.hidden || []).filter(function (k) {
            return sections.some(function (s) { return s.key === k; });
          });
        }
      } catch (e) {}
      return def;
    }

    function saveSideLayout() {
      try { localStorage.setItem(SIDE_KEY, JSON.stringify(layout)); } catch (e) {}
    }

    function applyOrder() {
      var order = layout.order.slice();
      sections.forEach(function (s) {
        if (order.indexOf(s.key) === -1) order.push(s.key);
      });
      layout.order = order;
      sections.slice().sort(function (a, b) {
        return layout.order.indexOf(a.key) - layout.order.indexOf(b.key);
      }).forEach(function (s) { aside.appendChild(s.el); });
    }

    function applyHidden() {
      sections.forEach(function (s) {
        s.el.classList.toggle('side-hidden', layout.hidden.indexOf(s.key) !== -1);
      });
    }

    function buildToolbar() {
      var bar = document.createElement('div');
      bar.className = 'edit-toolbar side-toolbar';
      var hidden = layout.hidden.map(function (k) {
        return sections.find(function (s) { return s.key === k; });
      }).filter(Boolean);
      var html = '<div class="edit-hint">🔓 Przeciągnij panele boczne za górny pasek, aby zmienić kolejność.</div>';
      if (hidden.length) {
        html += '<div class="hidden-title">Ukryte panele boczne (' + hidden.length + ')</div><div class="hidden-list">';
        hidden.forEach(function (s) {
          html += '<span class="hidden-chip"><span>' + esc(s.name) + '</span>' +
            '<button type="button" class="panel-show" data-show="' + esc(s.key) + '" data-show-kind="side">Pokaż</button></span>';
        });
        html += '</div>';
      }
      bar.innerHTML = html;
      bar.addEventListener('click', function (e) {
        var btn = e.target.closest('.panel-show');
        if (!btn) return;
        var key = btn.dataset.show;
        layout.hidden = layout.hidden.filter(function (k) { return k !== key; });
        saveSideLayout();
        applyHidden();
        refresh();
      });
      return bar;
    }

    function addControls(s) {
      if (s.el.querySelector('.side-controls')) return;
      var ctrl = document.createElement('div');
      ctrl.className = 'side-controls';
      ctrl.innerHTML = '<span class="drag-handle">⠿ <em>przenieś</em></span>' +
        '<button type="button" class="panel-hide" data-side-hide="' + esc(s.key) + '" title="Ukryj panel">🙈</button>';
      s.el.prepend(ctrl);
    }

    function removeControls(s) {
      var c = s.el.querySelector('.side-controls');
      if (c) c.remove();
    }

    function refresh() {
      if (toolbar) { toolbar.remove(); toolbar = null; }
      if (locked) {
        sections.forEach(removeControls);
        return;
      }
      applyOrder();
      applyHidden();
      if (aside) {
        toolbar = buildToolbar();
        aside.appendChild(toolbar);
      }
      sections.forEach(function (s) {
        if (layout.hidden.indexOf(s.key) === -1) addControls(s);
      });
    }

    aside.addEventListener('pointerdown', function (e) {
      if (locked) return;
      var ctrl = e.target.closest('.side-controls');
      if (!ctrl) return;
      if (e.target.closest('.panel-hide')) return;
      var el = ctrl.closest('.side-card');
      if (!el) return;
      e.preventDefault();
      drag = { el: el, x: e.clientX, y: e.clientY, rect: el.getBoundingClientRect(), moved: false };
    });

    window.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) > 4) {
        drag.moved = true;
        document.body.classList.add('is-dragging');
        drag.el.classList.add('dragging');
        drag.el.style.position = 'fixed';
        drag.el.style.left = drag.rect.left + 'px';
        drag.el.style.top = drag.rect.top + 'px';
        drag.el.style.width = drag.rect.width + 'px';
        drag.el.style.zIndex = '80';
      }
      if (!drag.moved) return;
      drag.el.style.left = drag.rect.left + dx + 'px';
      drag.el.style.top = drag.rect.top + dy + 'px';

      var els = sections.map(function (s) { return s.el; }).filter(function (el) {
        return el !== drag.el && layout.hidden.indexOf(el.dataset.side) === -1;
      });
      for (var i = 0; i < els.length; i++) {
        var r = els[i].getBoundingClientRect();
        if (e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom) {
          var after = e.clientY - r.top > r.height / 2;
          if (after) {
            if (els[i].nextElementSibling !== drag.el) aside.insertBefore(drag.el, els[i].nextElementSibling);
          } else {
            if (drag.el.nextElementSibling !== els[i]) aside.insertBefore(drag.el, els[i]);
          }
          break;
        }
      }
    });

    window.addEventListener('pointerup', function () {
      if (!drag) return;
      var el = drag.el, moved = drag.moved;
      drag = null;
      document.body.classList.remove('is-dragging');
      el.classList.remove('dragging');
      el.style.position = '';
      el.style.left = '';
      el.style.top = '';
      el.style.width = '';
      el.style.zIndex = '';
      if (moved) {
        layout.order = sections.slice().sort(function (a, b) {
          return Array.prototype.indexOf.call(aside.children, a.el) -
                 Array.prototype.indexOf.call(aside.children, b.el);
        }).map(function (s) { return s.key; });
        saveSideLayout();
        refresh();
      }
    });

    aside.addEventListener('click', function (e) {
      if (locked) return;
      var btn = e.target.closest('.panel-hide');
      if (!btn) return;
      var key = btn.dataset.sideHide;
      if (layout.hidden.indexOf(key) === -1) layout.hidden.push(key);
      saveSideLayout();
      applyHidden();
      refresh();
    });

    sections.forEach(function (s) { s.el.dataset.side = s.key; });
    applyOrder();
    applyHidden();

    var g = { refresh: refresh };
    groups.push(g);
    return g;
  }

  /* ------------------------------------------------------------------ *
   * init
   * ------------------------------------------------------------------ */

  function init(options) {
    locked = loadLock();
    document.body.classList.toggle('editing', !locked);
    wire(options.lockBtn);
    if (options.grid) createGridGroup(options.grid);
    if (options.side) createSideGroup(options.side);
    syncBtn();
    groups.forEach(function (g) { g.refresh(); });
  }

  function refreshAll() {
    locked = loadLock();
    document.body.classList.toggle('editing', !locked);
    syncBtn();
    groups.forEach(function (g) { g.refresh(); });
  }

  window.PanelLayout = {
    init: init,
    refreshAll: refreshAll
  };
})();
