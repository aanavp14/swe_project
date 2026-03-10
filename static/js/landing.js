/**
 * RoadMapper landing page — Create / Join trip buttons.
 */
(function () {
  const joinBtn = document.getElementById("join-trip-btn");
  const joinSection = document.getElementById("join-section");
  const inviteInput = document.getElementById("invite-link-input");
  const goBtn = document.getElementById("go-to-trip-btn");
  const joinError = document.getElementById("join-error");

  // Toggle join link field when "Let's join a trip" is clicked
  if (joinBtn && joinSection) {
    joinBtn.addEventListener("click", function () {
      joinSection.hidden = !joinSection.hidden;
      if (!joinSection.hidden) {
        inviteInput.focus();
      }
      if (joinError) {
        joinError.hidden = true;
        joinError.textContent = "";
      }
    });
  }

  // Extract invite code from pasted URL and redirect to trip page
  function extractInviteCode(input) {
    const trimmed = (input || "").trim();
    if (!trimmed) return null;
    // Match /trip/CODE or trip/CODE at end of URL
    const match = trimmed.match(/\/trip\/([A-Za-z0-9_-]+)/);
    if (match) return match[1];
    // If it's just the code (alphanumeric, 6-12 chars), use it
    if (/^[A-Za-z0-9_-]{4,20}$/.test(trimmed)) return trimmed;
    return null;
  }

  function goToTrip() {
    if (!inviteInput || !goBtn || !joinError) return;
    const code = extractInviteCode(inviteInput.value);
    if (code) {
      window.location.href = "/trip/" + encodeURIComponent(code);
    } else {
      joinError.textContent = "Please paste a valid invite link (e.g. …/trip/ABC123) or enter the invite code.";
      joinError.hidden = false;
    }
  }

  if (goBtn && inviteInput) {
    goBtn.addEventListener("click", goToTrip);
    inviteInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        goToTrip();
      }
    });
  }
})();
