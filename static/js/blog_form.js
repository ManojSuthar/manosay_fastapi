// static/js/blog_form.js

document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("image_file");
  const statusDiv = document.getElementById("upload-status");
  const imageUrlInput = document.getElementById("image_url");
  const previewDiv = document.getElementById("image-preview");

  if (!fileInput) return; // only run on blog form page

  fileInput.addEventListener("change", async function () {
    const file = fileInput.files[0];
    if (!file) return;

    // Basic client-side validation
    const maxBytes = 5 * 1024 * 1024; // 5MB
    if (file.size > maxBytes) {
      statusDiv.textContent = "File too large (max 5MB)";
      fileInput.value = "";
      return;
    }

    // Show uploading status
    statusDiv.textContent = "Uploading...";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/admin/upload-image", {
        method: "POST",
        body: formData,
        credentials: "same-origin", // send cookies
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => null);
        statusDiv.textContent =
          "Upload failed: " + (err?.detail || resp.statusText);
        imageUrlInput.value = "";
        previewDiv.innerHTML = "";
        return;
      }

      const data = await resp.json();
      // Set hidden image field so create-post form will send this URL
      imageUrlInput.value = data.url || "";
      statusDiv.textContent = "Upload complete";

      // Show preview
      if (data.url) {
        previewDiv.innerHTML =
          '<img src="' +
          data.url +
          '" alt="Preview" style="max-width:300px;max-height:200px;border:1px solid #ddd;padding:4px;">';
      } else {
        previewDiv.innerHTML = "";
      }
    } catch (err) {
      console.error(err);
      statusDiv.textContent = "Upload error";
      imageUrlInput.value = "";
      previewDiv.innerHTML = "";
    }
  });
});
