/* پنل مدیریت — شمارش و نمایش لیست ثبت‌نام‌ها */
(function () {
  if (!IS_ADMIN) return;

  const faDigits = n => String(n).replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);

  // شمارنده‌ی هر کارگاه
  fetch("/api/admin/stats")
    .then(r => r.json())
    .then(json => {
      if (!json.ok) return;
      for (const [id, n] of Object.entries(json.stats)) {
        const el = document.querySelector(`[data-count="${id}"]`);
        if (el) {
          el.textContent = faDigits(n);
          el.title = `${n} ثبت‌نام`;
        }
      }
    });

  // نمایش لیست هر کارگاه
  document.querySelectorAll(".js-view").forEach(btn =>
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const wrap = btn.closest(".admin-card").querySelector(".table-wrap");

      if (!wrap.hidden) { wrap.hidden = true; return; } // باز بود → ببند

      const tbody = wrap.querySelector("tbody");
      const empty = wrap.querySelector(".empty");
      tbody.innerHTML = "";
      empty.hidden = true;

      try {
        const res = await fetch(`/api/admin/registrations/${id}`);
        const json = await res.json();

        if (json.ok && json.rows.length) {
          json.rows.forEach(r => {
            const tr = document.createElement("tr");
            const cells = [
              { v: r.full_name, fa: true },
              { v: r.student_id },
              { v: r.mobile },
              { v: r.email },
              { v: r.degree, fa: true },
              { v: r.major, fa: true },
              { v: r.term, fa: true },
              { v: r.interest, fa: true },
              { v: r.cv_file ? `<a href="/admin/cv/${encodeURIComponent(r.cv_file)}">⬇ دانلود</a>` : "—" },
              { v: r.created_at },
            ];
            tr.innerHTML =
              `<td>${r.id}</td>` +
              cells.map(c =>
                `<td class="${c.fa ? "fa-cell" : ""}">${c.fa ? escapeHtml(c.v ?? "") : (c.v ?? "")}</td>`
              ).join("");
            tbody.appendChild(tr);
          });
        } else {
          empty.hidden = false;
        }
        wrap.hidden = false;
      } catch {
        alert("خطا در دریافت لیست ثبت‌نام‌ها.");
      }
    })
  );

  function escapeHtml(v) {
    const d = document.createElement("div");
    d.textContent = v ?? "";
    return d.innerHTML;
  }
})();
