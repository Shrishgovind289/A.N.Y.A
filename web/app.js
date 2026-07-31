const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const connectionStatus = document.getElementById(
    "connection-status"
);

const conversationHistory = [];

let apiKey = sessionStorage.getItem("anya_api_key") || "";
let requestInProgress = false;


function requestApiKey() {
    const enteredKey = window.prompt(
        "Enter the ANYA API key:"
    );

    if (!enteredKey) {
        return false;
    }

    apiKey = enteredKey.trim();

    sessionStorage.setItem(
        "anya_api_key",
        apiKey
    );

    return true;
}


function setConnectionStatus(isOnline) {
    connectionStatus.textContent = (
        isOnline
        ? "Online"
        : "Offline"
    );

    connectionStatus.classList.toggle(
        "online",
        isOnline
    );

    connectionStatus.classList.toggle(
        "offline",
        !isOnline
    );
}


function addMessage(role, content) {
    const article = document.createElement("article");

    article.className = (
        role === "user"
        ? "message user-message"
        : "message assistant-message"
    );

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = (
        role === "user"
        ? "SHRISH"
        : "ANYA"
    );

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.textContent = content;

    article.appendChild(label);
    article.appendChild(messageContent);

    messagesContainer.appendChild(article);

    messagesContainer.scrollTop = (
        messagesContainer.scrollHeight
    );
}


function setRequestState(isLoading) {
    requestInProgress = isLoading;

    sendButton.disabled = isLoading;
    messageInput.disabled = isLoading;

    sendButton.textContent = (
        isLoading
        ? "..."
        : "Send"
    );

    if (!isLoading) {
        messageInput.focus();
    }
}


function resizeInput() {
    messageInput.style.height = "auto";

    messageInput.style.height = (
        Math.min(
            messageInput.scrollHeight,
            180
        )
        + "px"
    );
}


async function checkConnection() {
    try {
        const response = await fetch(
            "/health",
            {
                cache: "no-store",
            }
        );

        setConnectionStatus(response.ok);
    } catch {
        setConnectionStatus(false);
    }
}


async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || requestInProgress) {
        return;
    }

    if (!apiKey && !requestApiKey()) {
        addMessage(
            "assistant",
            "An API key is required to communicate with ANYA."
        );

        return;
    }

    addMessage("user", message);

    messageInput.value = "";
    resizeInput();
    setRequestState(true);

    try {
        const response = await fetch(
            "/api/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey,
                },
                body: JSON.stringify(
                    {
                        message,
                        history: conversationHistory,
                    }
                ),
            }
        );

        const data = await response.json();

        if (response.status === 401) {
            sessionStorage.removeItem(
                "anya_api_key"
            );

            apiKey = "";

            throw new Error(
                "The API key was rejected. Reload the page and enter the correct key."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.detail
                || `Request failed with status ${response.status}.`
            );
        }

        const assistantMessage = data.assistant;

        addMessage(
            "assistant",
            assistantMessage
        );

        conversationHistory.push(
            {
                role: "user",
                content: message,
            },
            {
                role: "assistant",
                content: assistantMessage,
            }
        );

        if (conversationHistory.length > 20) {
            conversationHistory.splice(
                0,
                conversationHistory.length - 20
            );
        }

        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `I encountered an error: ${error.message}`
        );

        setConnectionStatus(false);
    } finally {
        setRequestState(false);
    }
}


sendButton.addEventListener(
    "click",
    sendMessage
);


messageInput.addEventListener(
    "input",
    resizeInput
);


messageInput.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }
    }
);


window.addEventListener(
    "load",
    () => {
        checkConnection();
        resizeInput();
        messageInput.focus();
    }
);
