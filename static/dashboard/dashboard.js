(() => {
  const monthly = JSON.parse(document.getElementById('monthly-data').textContent);
  const statuses = JSON.parse(document.getElementById('status-data').textContent);
  const hours = JSON.parse(document.getElementById('hours-data').textContent);
  const colors = ['#55ad9b', '#7894c3', '#e59b78', '#a298cb'];

  function chart(canvasId, labels, values, color, money = false, bars = false) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const ratio = window.devicePixelRatio || 1;
      canvas.width = rect.width * ratio;
      canvas.height = rect.height * ratio;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      const w = rect.width, h = rect.height;
      const pad = { top: 12, right: 8, bottom: 26, left: money ? 48 : 29 };
      const cw = w - pad.left - pad.right, ch = h - pad.top - pad.bottom;
      const max = Math.max(1, ...values);
      const cap = max * 1.2;
      ctx.clearRect(0, 0, w, h);
      ctx.font = '9px DM Sans, sans-serif';
      ctx.textBaseline = 'middle';
      for (let i = 0; i <= 3; i++) {
        const y = pad.top + ch * i / 3;
        ctx.strokeStyle = '#edf2ef'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
        const amount = cap * (1 - i / 3);
        ctx.fillStyle = '#a0adaa'; ctx.textAlign = 'right';
        ctx.fillText(money ? (amount >= 1000 ? `${(amount / 1000).toFixed(1)}k` : Math.round(amount)) : Math.round(amount), pad.left - 7, y);
      }
      const slot = cw / Math.max(1, labels.length);
      if (bars) {
        values.forEach((v, i) => {
          const bw = Math.min(23, slot * .52), bh = ch * v / cap;
          const x = pad.left + slot * i + (slot - bw) / 2, y = pad.top + ch - bh;
          ctx.fillStyle = '#9fcfc2';
          const radius = Math.min(4, bw / 2);
          ctx.beginPath(); ctx.roundRect(x, y, bw, Math.max(radius, bh), [radius, radius, 0, 0]); ctx.fill();
        });
      } else {
        const pts = values.map((v, i) => ({ x: pad.left + (labels.length === 1 ? cw / 2 : slot * i + slot / 2), y: pad.top + ch - ch * v / cap }));
        if (pts.length > 1) {
          ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
          pts.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
          ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
          ctx.lineTo(pts[pts.length - 1].x, pad.top + ch); ctx.lineTo(pts[0].x, pad.top + ch); ctx.closePath();
          ctx.fillStyle = color === '#7894c3' ? 'rgba(120,148,195,.10)' : 'rgba(85,173,155,.10)'; ctx.fill();
        }
        pts.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke(); });
      }
      ctx.fillStyle = '#98a5a1'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      labels.forEach((label, i) => ctx.fillText(label, pad.left + slot * i + slot / 2, h - 17));
    };
    new ResizeObserver(draw).observe(canvas);
    draw();
  }

  chart('appointmentsChart', monthly.map(x => x.label), monthly.map(x => x.appointments), '#55ad9b');
  chart('revenueChart', monthly.map(x => x.label), monthly.map(x => x.revenue), '#7894c3', true);
  chart('hoursChart', hours.map(x => x.label), hours.map(x => x.value), '#55ad9b', false, true);

  const total = statuses.reduce((sum, item) => sum + item.value, 0);
  const donut = document.getElementById('statusDonut');
  if (total && donut) {
    let offset = 0;
    const segments = statuses.map((item, i) => {
      const from = offset; offset += item.value / total * 100;
      return `${colors[i % colors.length]} ${from}% ${offset}%`;
    });
    donut.style.background = `conic-gradient(${segments.join(',')})`;
  }
  const legend = document.getElementById('statusLegend');
  if (legend) legend.innerHTML = statuses.map((item, i) => `<div class="legend-row"><i style="background:${colors[i % colors.length]}"></i><span>${item.label}</span><b>${item.value}</b></div>`).join('') || '<span class="empty-state">Sem consultas no período.</span>';

  const links = document.querySelectorAll('.switch-item');
  const panels = document.querySelectorAll('.dashboard-panel');
  function select(panelId) {
    panels.forEach(panel => { panel.hidden = panel.id !== panelId; });
    links.forEach(link => link.classList.toggle('selected', link.dataset.panel === panelId));
    if (location.hash !== `#${panelId}`) history.replaceState(null, '', `#${panelId}`);
    window.dispatchEvent(new Event('resize'));
  }
  links.forEach(link => link.addEventListener('click', event => { event.preventDefault(); select(link.dataset.panel); }));
  document.querySelectorAll('[data-goto]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); select(link.dataset.goto); window.scrollTo({ top: 0, behavior: 'smooth' }); }));
  select(location.hash === '#financeiro' ? 'financeiro' : 'operacional');
})();
