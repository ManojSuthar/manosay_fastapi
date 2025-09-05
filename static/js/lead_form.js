// static/js/lead_form.js
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("lead-form");
  const statusDiv = document.getElementById("quote-status");
  const submitBtn = document.getElementById("lead-submit");

  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    statusDiv.style.display = "none";
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    const payload = {
      name: document.getElementById("lead-name").value.trim(),
      email: document.getElementById("lead-email").value.trim(),
      company: document.getElementById("lead-company").value.trim(),
      platform: document.getElementById("lead-platform").value,
      budget: document.getElementById("lead-budget").value,
      timeline: document.getElementById("lead-timeline").value.trim(),
      message: document.getElementById("lead-message").value.trim(),
    };

    try {
      const resp = await fetch("/api/request-quote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload),
        credentials: "same-origin"
      });

      const data = await resp.json();

      if (!resp.ok) {
        statusDiv.style.display = "block";
        statusDiv.style.color = "#dc3545";
        statusDiv.textContent = (data && data.detail) ? data.detail : "Failed to submit. Try again later.";
      } else {
        statusDiv.style.display = "block";
        statusDiv.style.color = "#1a7f37";
        statusDiv.textContent = "Thanks! Your request was received. We'll contact you soon.";
        form.reset();
      }
    } catch (err) {
      statusDiv.style.display = "block";
      statusDiv.style.color = "#dc3545";
      statusDiv.textContent = "Network error. Try again later.";
      console.error(err);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Request Quote";
    }
  });
});
