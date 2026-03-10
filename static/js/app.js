/**
 * Smart Vacation Itinerary Planner — frontend entry.
 *
 * - Health check: verify backend is running on page load
 * - Create trip form: POST to /api/trips, show invite link on success
 */
(function () {
  // --- Health check: call /api/health and update status message ---
  const statusEl = document.getElementById("status");
  if (statusEl) {
    fetch("/api/health")
      .then(function (res) { return res.json(); })
      .then(function (data) {
        statusEl.textContent = data.message || "Connected.";
        statusEl.classList.add("ok");
      })
      .catch(function () {
        statusEl.textContent = "Could not reach server. Is the Flask app running?";
        statusEl.classList.add("error");
      });
  }

  // --- AI status on create page: show if API key is set and working ---
  const aiStatusEl = document.getElementById("ai-status-msg");
  if (aiStatusEl) {
    fetch("/api/ai-status")
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.configured) {
          fetch("/api/ai-verify")
            .then(function (r) { return r.json(); })
            .then(function (v) {
              if (v.ok) {
                aiStatusEl.textContent = "AI connected.";
                aiStatusEl.style.color = "#2d7a3e";
              } else {
                aiStatusEl.textContent = "AI key invalid or error: " + (v.error || "unknown");
                aiStatusEl.style.color = "#c00";
              }
            })
            .catch(function () {
              aiStatusEl.textContent = "Could not verify AI. Check server logs.";
              aiStatusEl.style.color = "#c00";
            });
        } else {
          aiStatusEl.textContent = "Add OPENAI_API_KEY to .env for AI suggestions.";
          aiStatusEl.style.color = "#c00";
        }
      })
      .catch(function () {
        aiStatusEl.textContent = "Could not reach server.";
        aiStatusEl.style.color = "#c00";
      });
  }

  // --- Create trip form: submit to API and display invite link ---
  const form = document.getElementById("create-trip-form");
  const errorEl = document.getElementById("create-error");
  const inviteSection = document.getElementById("invite-section");
  const inviteLink = document.getElementById("invite-link");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();  // Don't reload page; we'll handle with fetch
      if (errorEl) {
        errorEl.hidden = true;
        errorEl.textContent = "";
      }
      const origin = document.getElementById("origin").value.trim();
      const destination = document.getElementById("destination").value.trim();
      const per_person_budget = document.getElementById("per_person_budget").value;
      const num_people = document.getElementById("num_people").value;
      const start_date = document.getElementById("start_date").value;
      const end_date = document.getElementById("end_date").value;
      const activity_preferences = document.getElementById("activity_preferences").value.trim();

      fetch("/api/trips", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin: origin,
          destination: destination,
          per_person_budget: parseFloat(per_person_budget) || 0,
          num_people: parseInt(num_people, 10) || 1,
          start_date: start_date,
          end_date: end_date,
          activity_preferences: activity_preferences,
        }),
      })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
          if (result.ok) {
            // Success: redirect to trip page so user can get AI suggestions
            window.location.href = result.data.invite_url;
          } else {
            // API returned 4xx: show error message
            errorEl.textContent = result.data.error || "Something went wrong.";
            errorEl.hidden = false;
          }
        })
        .catch(function () {
          errorEl.textContent = "Could not create trip. Try again.";
          errorEl.hidden = false;
        });
    });
  }
})();
