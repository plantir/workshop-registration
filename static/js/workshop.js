/* صفحه‌ی اختصاصی کارگاه — فرم ثبت‌نام (با آپلود رزومه) */
(function () {
  const form = document.getElementById("regForm");
  if (!form) return; // کارگاه بسته است

  const toast = document.getElementById("toast");
  const submitBtn = document.getElementById("submitBtn");
  const successBox = document.getElementById("successBox");
  const successMsg = document.getElementById("successMsg");
  const cvInput = form.querySelector('input[name="cv"]');
  let toastTimer;

  function showToast(msg, isError) {
    toast.textContent = msg;
    toast.classList.toggle("error", !!isError);
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast.hidden = true), isError ? 6000 : 4500);
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    document.querySelectorAll(".err").forEach(el => (el.textContent = ""));

    const values = Object.fromEntries(new FormData(form).entries());
    values.workshop_id = form.dataset.workshop;

    // ─── اعتبارسنجی سمت کاربر ───
    let bad = null;
    if (!values.full_name || values.full_name.trim().length < 3)
      bad = ["full_name", "نام و نام خانوادگی را کامل وارد کنید."];
    else if (!/^\d{6,14}$/.test(values.student_id.trim()))
      bad = ["student_id", "شماره دانشجویی باید فقط شامل ۶ تا ۱۴ رقم باشد."];
    else if (!/^09\d{9}$/.test(normalizeMobile(values.mobile)))
      bad = ["mobile", "شماره موبایل باید به شکل 09xxxxxxxxx باشد."];
    else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(values.email.trim()))
      bad = ["email", "ایمیل معتبر وارد کنید."];
    else if (!values.degree)
      bad = ["degree", "مقطع تحصیلی را انتخاب کنید."];
    else if (!values.major || !values.major.trim())
      bad = ["major", "رشته تحصیلی را وارد کنید."];
    else if (!values.term)
      bad = ["term", "ترم تحصیلی را انتخاب کنید."];
    else if (!values.interest || !values.interest.trim())
      bad = ["interest", "حوزه علاقه‌مندی را وارد کنید."];
    else if (cvInput.files[0] && cvInput.files[0].size > 5 * 1024 * 1024)
      bad = ["cv", "حجم فایل رزومه باید حداکثر ۵ مگابایت باشد."];

    if (bad) {
      document.querySelector(`[data-err="${bad[0]}"]`).textContent = bad[1];
      return;
    }

    // ─── ارسال ───
    const fd = new FormData(form);
    fd.append("workshop_id", form.dataset.workshop);
    fd.set("mobile", normalizeMobile(values.mobile));
    fd.set("email", values.email.trim().toLowerCase());
    fd.set("full_name", values.full_name.trim());
    fd.set("student_id", values.student_id.trim());
    fd.set("major", values.major.trim());
    fd.set("interest", values.interest.trim());

    submitBtn.disabled = true;
    submitBtn.textContent = "در حال ارسال…";

    try {
      const res = await fetch("/api/register", { method: "POST", body: fd });
      const json = await res.json();

      if (json.ok) {
        successMsg.textContent = json.message;
        form.hidden = true;
        const hint = document.querySelector(".form-hint");
        if (hint) hint.hidden = true;
        successBox.hidden = false;
        successBox.scrollIntoView({ behavior: "smooth", block: "center" });
        showToast(json.message);
      } else {
        const errors = json.errors || { general: "خطایی رخ داد." };
        for (const [key, msg] of Object.entries(errors)) {
          const el = document.querySelector(`[data-err="${key}"]`);
          if (el) el.textContent = msg;
        }
      }
    } catch {
      showToast("ارتباط با سرور برقرار نشد. اتصال اینترنت خود را بررسی کنید.", true);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "ثبت‌نام";
    }
  });

  function normalizeMobile(m) {
    let v = (m || "").replace(/[^\d]/g, "");
    if (v.startsWith("98")) v = "0" + v.slice(2);
    return v;
  }
})();
