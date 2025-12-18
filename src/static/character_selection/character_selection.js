var buttons = document.getElementsByClassName("play-button");

async function sendPostRequest(character_id) {
    const res = await fetch(redirectURL, { 
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ "character_id": character_id }) 
    });
    
    // Redirect to game chat after creating character
    window.location.href = chatURL;
}

function propagateCharacterID() {
    var character_id = this.getAttribute("data-character-id");
    sendPostRequest(character_id); // Fixed variable name here
};

for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener('click', propagateCharacterID, false);
}