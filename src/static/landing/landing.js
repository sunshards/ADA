const ta = document.getElementById("mainTextArea")

ta.addEventListener("input", () => {
  ta.style.height = "auto"
  ta.style.height = Math.max( 150, ta.scrollHeight) + "px"
})
