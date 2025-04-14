const navHome = document.getElementById("nav-home");
const navFeature = document.getElementById("nav-feature");
const contentArea = document.getElementById("content-area");
const mainTitle = document.getElementById("main-title");

navHome.addEventListener("click", () => {
  setActiveNav(navHome);
  mainTitle.textContent = "Home";
  contentArea.innerHTML = "<p>Welcome to the dashboard. Select a feature to get started.</p>";
});

navFeature.addEventListener("click", () => {
  setActiveNav(navFeature);
  mainTitle.textContent = "Feature";
  loadFeatureTabs();
});

function setActiveNav(activeEl) {
  document.querySelectorAll(".nav-link").forEach(link => {
    link.classList.remove("active");
  });
  activeEl.classList.add("active");
}

function loadFeatureTabs() {
  contentArea.innerHTML = `
    <div class="d-flex mb-3">
      <button class="tab-button active btn btn-light me-2" data-id="1">FEATURE 1</button>
      <button class="tab-button btn btn-light me-2" data-id="2">FEATURE 2</button>
      <button class="tab-button btn btn-light me-2" data-id="3">FEATURE 3</button>
      <button class="tab-button btn btn-light me-2" data-id="4">FEATURE 4</button>
    </div>
    <div id="feature-content" class="border p-3 rounded bg-white shadow-sm">
      <p>Loading feature...</p>
    </div>
  `;

  showFeatureContent("1"); // default load

  document.querySelectorAll(".tab-button").forEach(button => {
    button.addEventListener("click", function () {
      document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
      this.classList.add("active");

      const id = this.getAttribute("data-id");
      showFeatureContent(id);
    });
  });
}

function showFeatureContent(num) {
  const content = document.getElementById("feature-content");
  fetch(`/feature${num}`)
    .then(response => response.text())
    .then(html => {
      content.innerHTML = html;
    });
}
  
document.addEventListener("submit", function(e) {
    if (e.target && e.target.id === "feature1-form") {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        fetch("/feature1", {
            method: "POST",
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.getElementById("feature-content").innerHTML = html;
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Terjadi kesalahan saat memproses prediksi.");
        });
    }

    if (e.target && e.target.id === "feature2-form") {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        fetch("/feature2", {
            method: "POST",
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.getElementById("feature-content").innerHTML = html;
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Terjadi kesalahan saat memproses strategi.");
        });
    }

    if (e.target && e.target.id === "feature3-form") {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);

      fetch("/feature3", {
          method: "POST",
          body: formData
      })
      .then(response => response.text())
      .then(html => {
          document.getElementById("feature-content").innerHTML = html;
      })
      .catch(error => {
          console.error("Error:", error);
          alert("Terjadi kesalahan saat memproses optimasi.");
      });
    }

    if (e.target && e.target.id === "feature4-form") {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    fetch("/feature4", {
        method: "POST",
        body: formData
    })
    .then(response => response.text())
    .then(html => {
        document.getElementById("feature-content").innerHTML = html;
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Terjadi kesalahan saat memproses optimasi.");
    });

  }
});


// Tambah baris baru
document.addEventListener("click", function(e) {
    if (e.target && e.target.id === "tambah-baris") {
        const tbody = document.querySelector("#data-table tbody");
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><input type="number" name="jumlah_pesanan[]" class="form-control"></td>
            <td><input type="number" name="bahan_baku[]" class="form-control" step="any"></td>
            <td><button type="button" class="btn btn-danger btn-sm hapus-baris">🗑️</button></td>
        `;
        tbody.appendChild(row);
    }
});

// Hapus baris
document.addEventListener("click", function(e) {
    if (e.target && e.target.classList.contains("hapus-baris")) {
        e.target.closest("tr").remove();
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const links = document.querySelectorAll(".nav-link");
    const contentArea = document.getElementById("feature-content");

    links.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const feature = this.getAttribute("data-feature");
            fetchFeatureContent(feature);
        });
    });

    function fetchFeatureContent(feature) {
        fetch(`/feature/${feature}`)
            .then(response => response.text())
            .then(html => {
                contentArea.innerHTML = html;
                window.history.pushState(null, "", `#${feature}`);
            })
            .catch(err => {
                contentArea.innerHTML = `<div class="alert alert-danger">Gagal memuat fitur: ${feature}</div>`;
                console.error("Error loading feature:", err);
            });
    }

    // Auto-load fitur saat pertama kali halaman dibuka berdasarkan hash
    const initialFeature = window.location.hash.substring(1) || "1";
    fetchFeatureContent(initialFeature);
});
