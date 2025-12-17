const avatarImg = document.getElementById('character-avatar-image')
const avatarInput = document.getElementById('character-avatar-input')
const avatarUploadButton = document.getElementById('character-avatar-button')

avatarUploadButton.addEventListener('click', () => {
  avatarInput.click(); // programmatically open file picker
});

avatarInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // sets the image on the webpage with AJAX
    const reader = new FileReader();
    reader.onload = (e) => {
        avatarImg.src = e.target.result; // base64 URL of the file
    };
    reader.readAsDataURL(file); // reads the file as a data URL

    // sends the image with POST request to flask
    const formData = new FormData();
    formData.append('image', file);
    const res = await fetch(uploadUrl, { method: 'POST', body: formData });

    // reading the response
    // const data = await res.json();

});
