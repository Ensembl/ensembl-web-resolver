function closeTooltip() {
  const tooltip = document.getElementById('tooltip');
  if (tooltip) {
    tooltip.style.display = 'none';
    tooltip.setAttribute('aria-hidden', 'true');
  }
}

function showTooltip(el) {
  const tooltip = document.getElementById('tooltip');
  if (!tooltip) return;

  const genomeBrowserLink = document.getElementById('genome-browser-link');
  const entityViewerLink = document.getElementById('entity-viewer-link');

  if (genomeBrowserLink) {
    genomeBrowserLink.href = el.dataset.genomeBrowserUrl || '#';
  }
  if (entityViewerLink) {
    entityViewerLink.href = el.dataset.entityViewerUrl || '#';
  }

  const target = el.querySelector('.genome-detail-tooltip');
  if (!target) return;

  tooltip.style.display = 'block';
  tooltip.setAttribute('aria-hidden', 'false');
  const rect = target.getBoundingClientRect();
  tooltip.style.top = (rect.top - 15 + window.scrollY) + 'px';
  tooltip.style.left = (rect.right + 10 + window.scrollX) + 'px';
}

document.querySelectorAll('.genome-detail-container').forEach(function(el) {
  el.addEventListener('keydown', function(e) {
    if (e.target.classList.contains('genome-detail') && e.key === 'Enter') {
      showTooltip(el);
    }
  })

  el.addEventListener('click', function(e) {
    if (e.target.classList.contains('genome-detail')) {
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
