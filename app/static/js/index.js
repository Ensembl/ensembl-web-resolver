function closeTooltip() {
  const tooltip = document.getElementById('tooltip');
  if (tooltip) {
    tooltip.style.display = 'none';
  }
}

function showTooltip(el) {
  const tooltip = document.getElementById('tooltip');
  if (!tooltip) return;

  const genomeBrowserLink = document.getElementById('genome-browser-link');
  const featureExplorerLink = document.getElementById('feature-explorer-link');

  if (genomeBrowserLink) {
    genomeBrowserLink.href = el.dataset.genomeBrowserUrl;
  }
  if (featureExplorerLink) {
    featureExplorerLink.href = el.dataset.featureExplorerUrl;
  }

  const target = el.querySelector('.genome-detail-tooltip');
  if (!target) return;

  tooltip.style.display = 'block';
  tooltip.setAttribute('aria-hidden', 'false');
  const rect = target.getBoundingClientRect();
  tooltip.style.top = (rect.top - 15 + window.scrollY) + 'px';
  tooltip.style.left = (rect.right + 10 + window.scrollX) + 'px';
  genomeBrowserLink.focus();
}

document.querySelectorAll('.genome-detail-container').forEach(function(el) {
  el.addEventListener('keydown', function(e) {
    const link = e.target.closest('.genome-detail');
    if (link && el.contains(link) && e.key === 'Enter') {
      e.preventDefault();
      showTooltip(el);
    }
  })

  el.addEventListener('click', function(e) {
    const link = e.target.closest('.genome-detail');
    if (link && el.contains(link)) {
      e.preventDefault();
      showTooltip(el);
    }
  });
});

document.addEventListener('click', function(e) {
  if (!e.target.closest('.genome-detail-container') && !e.target.closest('#tooltip')) {
    closeTooltip();
  }
});

window.addEventListener('resize', function() {
  closeTooltip();
});

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeTooltip();
  }
});
