/* فرم ثبت‌نام — لندینگ پیج */
(function () {
  const modal = document.getElementById("modal");
  const modalWorkshop = document.getElementById("modalWorkshop");
  const fWorkshop = document.getElementById("fWorkshop");
  const form = document.getElementById("regForm");
  const toast = document.getElementById("toast");
  const submitBtn = document.getElementById("submitBtn");
  let toastTimer;

  function openModal(id, title) {
    fWorkshop.value = id;
    modalWorkshop.textContent = "کارگاه: " + title;
    form.reset();
    document.querySelectorAll(".err").forEach(e => (e.textContent = ""));
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  document.querySelectorAll(".js-register").forEach(btn =>
    btn.addEventListener("click", () => openModal(btn.dataset.id, btn.dataset.title))
  );
  document.getElementById("modalClose").addEventListener("click", closeModal);
  modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

  function showToast(msg, isError) {
    toast.textContent = msg;
    toast.classList.toggle("error", !!isError);
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast.hidden = true), isError ? 6000 : 4500);
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "در حال ارسال…";
    document.querySelectorAll(".err").forEach(el => (el.textContent = ""));

    const data = Object.fromEntries(new FormData(form).entries());

    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();

      if (json.ok) {
        closeModal();
        showToast(json.message);
        form.reset();
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
})();
