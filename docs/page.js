/* Bold Raven
   Keyboard navigation for the generated pages under /naics/.

   The lookup tool at / keeps its whole dataset in memory and swaps panels.
   A generated page has only itself, so the same keys become real navigations
   to the sibling URLs already present in the rail.

   Tab, Home and End are deliberately left alone here: these are ordinary
   documents full of links, and hijacking those keys would break normal
   keyboard use for the sake of matching the tool.
*/
(function () {
  'use strict';

  var rail = document.querySelector('.rail');
  if (!rail) return;

  var links = rail.querySelectorAll('a.rail-item');
  if (!links.length) return;

  var active = -1;
  for (var i = 0; i < links.length; i++) {
    if (links[i].className.indexOf('active') !== -1) active = i;
  }

  function go(index) {
    var count = links.length;
    var next = ((index % count) + count) % count;
    if (next === active) return;
    window.location.href = links[next].getAttribute('href');
  }

  document.addEventListener('keydown', function (event) {
    if (event.ctrlKey || event.metaKey || event.altKey) return;

    var tag = (event.target && event.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if (event.key === 'Escape') {
      event.preventDefault();
      window.location.href = '/';
      return;
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      go(active + 1);
      return;
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      go(active - 1);
      return;
    }
    if (event.key >= '1' && event.key <= '8') {
      event.preventDefault();
      go(Number(event.key) - 1);
    }
  });
})();
