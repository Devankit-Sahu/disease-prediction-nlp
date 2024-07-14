function showLoader() {
  const submitBtn = document.getElementById("submitBtn");
  const loader = document.getElementById("loader");
  const btnText = document.getElementById("btnText");

  loader.classList.remove("hidden");
  submitBtn.disabled = true;
  btnText.textContent = "Processing...";
}