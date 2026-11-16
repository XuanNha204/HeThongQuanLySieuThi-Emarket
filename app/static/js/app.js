// Tien ich chung
window.EM = {
  csrf: () => document.querySelector('meta[name="csrf-token"]')?.content,
  vnd: (v) => Math.round(v || 0).toLocaleString('vi-VN') + ' đ',
  async postJSON(url, data) {
    const r = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': EM.csrf()},
      body: JSON.stringify(data),
    });
    let body = {};
    try { body = await r.json(); } catch (e) { body = {ok: false, loi: 'Lỗi máy chủ (' + r.status + ')'}; }
    return body;
  },
  async getJSON(url) { const r = await fetch(url); return r.json(); },
  esc: (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c])),
};

document.addEventListener('DOMContentLoaded', () => {
  // nut mo sidebar tren man hinh nho / tablet
  document.querySelectorAll('[data-toggle-sidebar]').forEach(b =>
    b.addEventListener('click', () => document.querySelector('.em-sidebar')?.classList.toggle('show')));
  // xac nhan truoc khi xoa / thao tac quan trong
  document.querySelectorAll('form[data-confirm]').forEach(f =>
    f.addEventListener('submit', (e) => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));
});
