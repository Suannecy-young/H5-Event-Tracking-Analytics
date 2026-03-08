const endpoint = "http://127.0.0.1:5000/track";

function getUserId() {
    let uid = localStorage.getItem("uid");
    if (!uid) {
        uid = "user_" + Math.random().toString(36).substring(2,8);
        localStorage.setItem("uid", uid);
    }
    return uid;
}

function sendEvent(eventName) {
    fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            event_name: eventName,
            user_id: getUserId(),
            timestamp: new Date().toISOString()
        })
    });
}

document.getElementById("visit").onclick = () => sendEvent("page_view");
document.getElementById("signup").onclick = () => sendEvent("signup");
document.getElementById("purchase").onclick = () => sendEvent("purchase");