/* Bold Raven
   Static, zero-runtime-request lookup tool.
   All data comes from data.js, which is loaded once with the page.
*/
(function () {
  'use strict';

  var DB = window.BOLD_RAVEN;
  var POLICIES = DB.policies;                 // [abbr, name, url-slug], 8 entries
  var TITLES = DB.titles;
  var DATA = DB.data;

  // Valid codes, and every prefix of every valid code, for constrained typing.
  var CODES = Object.create(null);
  var PREFIXES = Object.create(null);
  for (var i = 0; i < DB.codes.length; i++) {
    var code = DB.codes[i];
    CODES[code] = true;
    for (var n = 1; n <= code.length; n++) PREFIXES[code.slice(0, n)] = true;
  }

  // Known reason fields, rendered in this order. Anything else in the schema
  // is still rendered, after these, with an auto-generated label.
  var FIELD_LABELS = {
    why_this_business: 'WHY',
    loss_scenario: 'LOSS',
    rhetorical_question: 'ASK'
  };
  var FIELD_ORDER = ['why_this_business', 'loss_scenario', 'rhetorical_question'];
  var REASON_SKIP = { rank: true, headline: true };
  var POLICY_SKIP = { naics_code: true, naics_title: true, sector: true, policy: true };

  var rootView = document.getElementById('root-view');
  var codeView = document.getElementById('code-view');
  var input = document.getElementById('code-input');
  var fieldWrap = input.parentNode;
  var codeNumber = document.getElementById('code-number');
  var codeTitle = document.getElementById('code-title');
  var rail = document.getElementById('rail');
  var panel = document.getElementById('panel');

  var current = null;      // null = root view, otherwise the active 6-digit code
  var policyIndex = 0;     // 0..7, position in POLICIES
  var lastGood = '';       // last accepted input value
  var railItems = [];

  /* ------------------------------------------------------------- utilities */

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function labelFor(key) {
    if (FIELD_LABELS[key]) return FIELD_LABELS[key];
    return key.replace(/_/g, ' ').toUpperCase();
  }

  function pad2(value) {
    var s = String(value);
    return s.length < 2 ? '0' + s : s;
  }

  function isPlainObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  // A policy object holds one array of reason objects. Prefer the known key,
  // otherwise take the first array of objects found.
  function reasonsOf(policy) {
    var preferred = policy.reasons_ranked_by_importance;
    if (Array.isArray(preferred)) return preferred;
    for (var key in policy) {
      var value = policy[key];
      if (Array.isArray(value) && value.length && isPlainObject(value[0])) return value;
    }
    return [];
  }

  /* ---------------------------------------------------------------- render */

  function renderReason(reason, position) {
    var item = el('li', 'reason');

    var head = el('div', 'reason-head');
    head.appendChild(el('span', 'rank', pad2(reason.rank !== undefined ? reason.rank : position)));
    head.appendChild(el('h3', null, reason.headline !== undefined ? reason.headline : ''));
    item.appendChild(head);

    var list = el('dl', 'fields');
    var seen = Object.create(null);
    var key;

    for (var i = 0; i < FIELD_ORDER.length; i++) {
      key = FIELD_ORDER[i];
      seen[key] = true;
      if (reason[key] === undefined || reason[key] === null || reason[key] === '') continue;
      list.appendChild(el('dt', null, labelFor(key)));
      list.appendChild(el('dd', null, String(reason[key])));
    }

    for (key in reason) {
      if (seen[key] || REASON_SKIP[key]) continue;
      var value = reason[key];
      if (value === undefined || value === null || value === '') continue;
      list.appendChild(el('dt', null, labelFor(key)));
      list.appendChild(el('dd', null, isPlainObject(value) || Array.isArray(value)
        ? JSON.stringify(value) : String(value)));
    }

    if (list.childNodes.length) item.appendChild(list);
    return item;
  }

  function renderPanel() {
    var entry = POLICIES[policyIndex];
    var abbr = entry[0];
    var name = entry[1];
    var policy = DATA[current] ? DATA[current][abbr] : undefined;

    panel.textContent = '';

    var head = el('div', 'policy-head');
    head.appendChild(el('h2', null, name));
    head.appendChild(el('span', 'abbr', abbr));
    panel.appendChild(head);

    if (!policy) {
      panel.appendChild(el('p', 'empty-state', 'No data'));
    } else {
      // Any scalar field on the policy that is not metadata and not the
      // reasons array is shown above the reasons, with the same formatting.
      var extras = el('dl', 'fields');
      for (var key in policy) {
        if (POLICY_SKIP[key]) continue;
        var value = policy[key];
        if (Array.isArray(value) || isPlainObject(value)) continue;
        if (value === undefined || value === null || value === '') continue;
        extras.appendChild(el('dt', null, labelFor(key)));
        extras.appendChild(el('dd', null, String(value)));
      }
      if (extras.childNodes.length) panel.appendChild(extras);

      var reasons = reasonsOf(policy);
      if (!reasons.length) {
        panel.appendChild(el('p', 'empty-state', 'No data'));
      } else {
        var list = el('ol', 'reasons');
        for (var i = 0; i < reasons.length; i++) {
          list.appendChild(renderReason(reasons[i], i + 1));
        }
        panel.appendChild(list);
      }
    }

    for (var r = 0; r < railItems.length; r++) {
      if (r === policyIndex) railItems[r].classList.add('active');
      else railItems[r].classList.remove('active');
    }

    panel.classList.remove('swap');
    void panel.offsetWidth;              // restart the animation
    panel.classList.add('swap');

    // Every policy always starts at the top of its content.
    window.scrollTo(0, 0);
  }

  function buildRail() {
    rail.textContent = '';
    railItems = [];
    for (var i = 0; i < POLICIES.length; i++) {
      var abbr = POLICIES[i][0];
      var has = !!(DATA[current] && DATA[current][abbr]);
      var button = el('button', 'rail-item' + (has ? '' : ' empty'));
      button.type = 'button';
      button.setAttribute('tabindex', '-1');
      button.appendChild(el('span', 'idx', String(i + 1)));
      button.appendChild(el('span', 'abbr', abbr));
      button.appendChild(el('span', 'name', POLICIES[i][1]));
      button.addEventListener('click', selectHandler(i));
      rail.appendChild(button);
      railItems.push(button);
    }
  }

  function selectHandler(index) {
    return function () { selectPolicy(index); };
  }

  function selectPolicy(index) {
    var count = POLICIES.length;
    var next = ((index % count) + count) % count;
    if (next === policyIndex) return;
    policyIndex = next;
    renderPanel();
    // Stepping through policies replaces rather than pushes, so Back leaves
    // the code instead of walking every policy the user passed through.
    syncUrl(true);
  }

  function renderCode() {
    codeNumber.textContent = current;
    codeTitle.textContent = TITLES[current] || '';
    buildRail();
    renderPanel();
    rootView.hidden = true;
    codeView.hidden = false;
    // Older engines ignore the options argument, which is harmless.
    panel.focus({ preventScroll: true });
  }

  function renderRoot() {
    codeView.hidden = true;
    rootView.hidden = false;
    clearInput();
    input.focus();
  }

  /* ----------------------------------------------------------- navigation */

  // Every code and policy also exists as a real page under /naics/, generated
  // by build.py. The tool renders instantly from memory but keeps the address
  // bar on that real URL, so a shared or reloaded link lands on the crawlable
  // page rather than on a fragment no search engine ever sees.
  var PATH = /^\/naics\/(\d{6})(?:\/([a-z-]+))?\/?$/;

  function indexOfSlug(slug) {
    if (!slug) return 0;
    for (var i = 0; i < POLICIES.length; i++) {
      if (POLICIES[i][2] === slug) return i;
    }
    return 0;
  }

  function pathFor(code, index) {
    if (!code) return '/';
    var slug = POLICIES[index] && POLICIES[index][2];
    return slug ? '/naics/' + code + '/' + slug + '/' : '/naics/' + code + '/';
  }

  function syncUrl(replace) {
    if (!window.history || !history.pushState) return;
    var target = pathFor(current, policyIndex);
    if (location.pathname === target && !location.hash) return;
    try {
      history[replace ? 'replaceState' : 'pushState'](null, '', target);
    } catch (err) {
      // Unsupported origin, e.g. opened straight off the filesystem.
    }
  }

  // Reads the real path first, then the legacy #111110 fragment. `legacy`
  // marks the fragment case, which the caller rewrites to the real path.
  function readLocation() {
    var match = PATH.exec(location.pathname);
    if (match && CODES[match[1]]) {
      return { code: match[1], index: indexOfSlug(match[2]), legacy: false };
    }
    var raw = location.hash.replace(/^#/, '');
    if (/^\d{6}$/.test(raw) && CODES[raw]) {
      return { code: raw, index: 0, legacy: true };
    }
    return { code: null, index: 0, legacy: false };
  }

  function navigate(code) {
    if (code === current) return;
    current = code;
    policyIndex = 0;
    if (code) renderCode();
    else renderRoot();
    syncUrl(false);
  }

  // Fires on back and forward, and also on a same-document jump to a legacy
  // #111110 link, which is why the rewrite has to happen here too and not only
  // on first load.
  window.addEventListener('popstate', function () {
    var target = readLocation();
    current = target.code;
    policyIndex = target.index;
    if (target.code) renderCode();
    else renderRoot();
    if (target.legacy) syncUrl(true);
  });

  /* ---------------------------------------------------------------- input */

  function clearInput() {
    lastGood = '';
    input.value = '';
    fieldWrap.classList.remove('filled');
  }

  function markFilled() {
    if (input.value.length) fieldWrap.classList.add('filled');
    else fieldWrap.classList.remove('filled');
  }

  function flashReject() {
    fieldWrap.classList.remove('reject');
    void fieldWrap.offsetWidth;
    fieldWrap.classList.add('reject');
    window.setTimeout(function () { fieldWrap.classList.remove('reject'); }, 130);
  }

  function shakeAndClear() {
    fieldWrap.classList.remove('shake');
    void fieldWrap.offsetWidth;
    fieldWrap.classList.add('shake');
    clearInput();
    window.setTimeout(function () { fieldWrap.classList.remove('shake'); }, 240);
  }

  // Only digit sequences that are a prefix of a real code survive. Everything
  // else restores the last accepted value, so an invalid value cannot exist.
  input.addEventListener('input', function () {
    var candidate = input.value.replace(/\D/g, '').slice(0, 6);
    if (candidate === lastGood) {
      if (input.value !== lastGood) input.value = lastGood;
      markFilled();
      return;
    }
    if (candidate === '' || PREFIXES[candidate]) {
      lastGood = candidate;
      if (input.value !== candidate) input.value = candidate;
      markFilled();
      return;
    }
    input.value = lastGood;
    input.setSelectionRange(lastGood.length, lastGood.length);
    markFilled();
    flashReject();
  });

  input.addEventListener('keydown', function (event) {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    var value = input.value;
    if (value.length === 6 && CODES[value]) navigate(value);
    else shakeAndClear();
  });

  /* ------------------------------------------------------------- keyboard */

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      clearInput();
      if (current === null) input.focus();
      else navigate(null);
      return;
    }

    if (current === null) {
      // Root view: any typing belongs to the input.
      if (document.activeElement !== input && !event.ctrlKey && !event.metaKey &&
          !event.altKey && event.key.length === 1) {
        input.focus();
      }
      return;
    }

    if (event.ctrlKey || event.metaKey || event.altKey) return;

    switch (event.key) {
      case 'Tab':
        event.preventDefault();
        selectPolicy(policyIndex + (event.shiftKey ? -1 : 1));
        return;
      case 'ArrowRight':
        event.preventDefault();
        selectPolicy(policyIndex + 1);
        return;
      case 'ArrowLeft':
        event.preventDefault();
        selectPolicy(policyIndex - 1);
        return;
      case 'Home':
        event.preventDefault();
        selectPolicy(0);
        return;
      case 'End':
        event.preventDefault();
        selectPolicy(POLICIES.length - 1);
        return;
      default:
        break;
    }

    if (event.key >= '1' && event.key <= '8') {
      event.preventDefault();
      selectPolicy(Number(event.key) - 1);
    }
  });

  // Clicking anywhere on the root view returns focus to the input.
  rootView.addEventListener('mousedown', function (event) {
    if (event.target !== input) {
      event.preventDefault();
      input.focus();
    }
  });

  /* ----------------------------------------------------------------- boot */

  var initial = readLocation();
  if (initial.code) {
    current = initial.code;
    policyIndex = initial.index;
    renderCode();
    syncUrl(true);            // upgrades a legacy #111110 link to its real path
  } else {
    current = null;
    renderRoot();
  }
})();
