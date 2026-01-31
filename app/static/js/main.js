// ===== Server Monitoring - Main JavaScript =====

document.addEventListener("DOMContentLoaded", function () {
  // Auto-submit filters when select changes
  initAutoSubmitFilters();

  // Search debounce
  initSearchDebounce();

  // Confirm delete actions
  initDeleteConfirmation();

  // Dashboard auto-refresh
  initDashboardAutoRefresh();

  // Clear filters button
  initClearFilters();
});

/**
 * Auto-submit form when select/filter changes
 */
function initAutoSubmitFilters() {
  const filterSelects = document.querySelectorAll(
    ".toolbar-group select:not([multiple])",
  );
  filterSelects.forEach(function (select) {
    select.addEventListener("change", function () {
      const form = this.closest("form");
      if (form) {
        form.submit();
      }
    });
  });
}

/**
 * Debounce search input to avoid too many requests
 */
function initSearchDebounce() {
  const searchInputs = document.querySelectorAll('input[name="search"]');
  let debounceTimer;

  searchInputs.forEach(function (input) {
    input.addEventListener("keyup", function (e) {
      // Submit on Enter key
      if (e.key === "Enter") {
        const form = this.closest("form");
        if (form) {
          form.submit();
        }
        return;
      }

      // Debounce for auto-search (optional - currently disabled)
      // Uncomment below to enable auto-search after typing
      /*
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                const form = input.closest('form');
                if (form && input.value.length >= 3) {
                    form.submit();
                }
            }, 500);
            */
    });
  });
}

/**
 * Confirm before delete actions
 */
function initDeleteConfirmation() {
  const deleteButtons = document.querySelectorAll(
    '.btn-danger[onclick*="confirm"], a.btn-danger',
  );
  deleteButtons.forEach(function (btn) {
    if (!btn.onclick) {
      btn.addEventListener("click", function (e) {
        if (!confirm("Are you sure you want to delete this item?")) {
          e.preventDefault();
          return false;
        }
      });
    }
  });

  // For forms with delete action
  const deleteForms = document.querySelectorAll('form[action*="delete"]');
  deleteForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm("Are you sure you want to delete this item?")) {
        e.preventDefault();
        return false;
      }
    });
  });
}

/**
 * Auto-refresh dashboard - handled in dashboard.html template
 * This function is kept for backward compatibility but does nothing
 * The actual auto-refresh is now done via AJAX in the dashboard template
 */
function initDashboardAutoRefresh() {
  // Auto-refresh is now handled in dashboard.html with AJAX
  // This function is kept for backward compatibility
  console.log('Dashboard auto-refresh is handled via AJAX in dashboard template');
}

/**
 * Update refresh time display
 */
function updateRefreshTime() {
  const refreshInfo = document.getElementById("last-refresh-time");
  if (refreshInfo) {
    const now = new Date();
    refreshInfo.textContent = "Updated: " + now.toLocaleTimeString('id-ID');
  }
}

/**
 * Clear all filters and reset form
 */
function initClearFilters() {
  const clearBtn = document.getElementById("clear-filters");
  if (clearBtn) {
    clearBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const form = this.closest("form");
      if (form) {
        // Clear all inputs
        form.querySelectorAll('input[type="text"]').forEach(function (input) {
          input.value = "";
        });

        // Reset all selects to first option
        form.querySelectorAll("select").forEach(function (select) {
          select.selectedIndex = 0;
        });

        // Submit form to clear URL params
        form.submit();
      } else {
        // If no form, just go to base URL
        window.location.href = window.location.pathname;
      }
    });
  }
}

/**
 * Format number with thousand separator
 */
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(function () {
      showToast("Copied to clipboard!");
    })
    .catch(function (err) {
      console.error("Failed to copy: ", err);
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  toast.textContent = message;
  toast.style.cssText =
    "position: fixed; bottom: 20px; right: 20px; padding: 1rem 1.5rem; border-radius: 6px; background: #2d3e50; color: #fff; z-index: 9999; animation: fadeIn 0.3s ease;";

  document.body.appendChild(toast);

  setTimeout(function () {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(function () {
      toast.remove();
    }, 300);
  }, 3000);
}

/**
 * Status color helper
 */
function getStatusClass(value, warningThreshold, criticalThreshold) {
  const numValue = parseFloat(value);
  if (isNaN(numValue)) return "unknown";
  if (numValue >= criticalThreshold) return "critical";
  if (numValue >= warningThreshold) return "warning";
  return "ok";
}
