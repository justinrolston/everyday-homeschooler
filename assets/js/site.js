// Minimal replacements for the Squarespace runtime: mobile menu + folder panels.
(function () {
  var header = document.querySelector('header.header');
  var burgers = document.querySelectorAll('.header-burger-btn');
  burgers.forEach(function (b) {
    b.addEventListener('click', function () {
      var open = !document.body.classList.contains('header--menu-open');
      document.body.classList.toggle('header--menu-open', open);
      if (header) header.classList.toggle('header--menu-open', open);
      burgers.forEach(function (x) { x.classList.toggle('burger--active', open); x.setAttribute('aria-expanded', open); });
    });
  });
  // Mobile folder navigation
  var root = document.querySelector('.header-menu-nav-folder[data-folder="root"]');
  if (root) document.querySelectorAll('.header-menu-nav-folder:not([data-folder="root"])').forEach(function (f) {
    root.parentElement.appendChild(f);
  });
  document.querySelectorAll('.header-menu [data-folder-id]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var target = document.querySelector('.header-menu-nav-folder[data-folder="' + a.getAttribute('data-folder-id') + '"]');
      if (!target || !root) return;
      e.preventDefault();
      root.classList.add('header-menu-nav-folder--open');
      target.classList.add('header-menu-nav-folder--active');
    });
  });
  document.querySelectorAll('.header-menu [data-action="back"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelectorAll('.header-menu-nav-folder--active').forEach(function (f) { f.classList.remove('header-menu-nav-folder--active'); });
      if (root) root.classList.remove('header-menu-nav-folder--open');
    });
  });
  // Lazy images that the Squarespace loader used to handle
  document.querySelectorAll('img[data-src]').forEach(function (img) { if (!img.getAttribute('src')) img.src = img.dataset.src; });
})();
// Dropdown chevrons + current-page highlight (were injected by Squarespace JS)
(function () {
  document.querySelectorAll('.header-nav-folder-title').forEach(function (b) {
    if (b.querySelector('.header-dropdown-icon')) return;
    var s = document.createElement('span');
    s.className = 'header-dropdown-icon header-dropdown-flip';
    s.style.cssText = 'margin-left:1em;width:1.08em;height:1.08em;display:inline-block';
    s.innerHTML = '<svg viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round" stroke-width="1px"><use href="#openArrowHead"></use></svg>';
    b.appendChild(s);
  });
  var path = location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('.header-nav-item--active').forEach(function (n) { n.classList.remove('header-nav-item--active'); });
  document.querySelectorAll('.header-nav-item a, .header-nav-folder-item a').forEach(function (a) {
    if ((a.getAttribute('href') || '').replace(/\/$/, '') === path) {
      var item = a.closest('.header-nav-item'); if (item) item.classList.add('header-nav-item--active');
    }
  });
})();
// Accordions (curriculum picks)
document.querySelectorAll('.accordion-item__click-target').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var item = btn.closest('.accordion-item');
    var dd = item && item.querySelector('.accordion-item__dropdown');
    if (!dd) return;
    var open = !dd.classList.contains('accordion-item__dropdown--open');
    dd.classList.toggle('accordion-item__dropdown--open', open);
    btn.setAttribute('aria-expanded', open);
    item.classList.toggle('accordion-item--expanded', open);
  });
});
// Video blocks: Squarespace stored the YouTube iframe in data-html
document.querySelectorAll('.sqs-video-wrapper[data-html]').forEach(function (w) {
  if (w.querySelector('iframe')) return;
  var holder = document.createElement('div');
  holder.className = 'eh-video';
  holder.innerHTML = w.getAttribute('data-html');
  var f = holder.querySelector('iframe');
  if (f) { f.removeAttribute('width'); f.removeAttribute('height'); f.setAttribute('loading', 'lazy'); }
  w.innerHTML = '';
  w.appendChild(holder);
});
