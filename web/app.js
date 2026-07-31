const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const connectionStatus = document.getElementById(
    "connection-status"
);

const projectList = document.getElementById("project-list");
const chatList = document.getElementById("chat-list");
const currentProjectName = document.getElementById(
    "current-project-name"
);

const newProjectButton = document.getElementById(
    "new-project-button"
);
const newChatButton = document.getElementById(
    "new-chat-button"
);

const sidebarToggle = document.getElementById(
    "sidebar-toggle"
);
const sidebarClose = document.getElementById(
    "sidebar-close"
);
const sidebarOverlay = document.getElementById(
    "sidebar-overlay"
);

let apiKey = sessionStorage.getItem("anya_api_key") || "";
let requestInProgress = false;
let selectedProjectId = "";
let selectedProjectLabel = "All Chats";
let currentChatId = null;
let projects = [];
let chats = [];


function requestApiKey() {
    const enteredKey = window.prompt(
        "Enter the A.N.Y.A API key:"
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


async function apiRequest(path, options = {}) {
    if (!apiKey && !requestApiKey()) {
        throw new Error(
            "An API key is required."
        );
    }

    const headers = {
        ...(options.headers || {}),
        "X-API-Key": apiKey,
    };

    const response = await fetch(
        path,
        {
            ...options,
            headers,
        }
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (response.status === 401) {
        sessionStorage.removeItem(
            "anya_api_key"
        );

        apiKey = "";

        throw new Error(
            "The API key was rejected."
        );
    }

    if (!response.ok) {
        throw new Error(
            data.detail
            || `Request failed with status ${response.status}.`
        );
    }

    return data;
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


function openSidebar() {
    document.body.classList.add(
        "sidebar-open"
    );
}


function closeSidebar() {
    document.body.classList.remove(
        "sidebar-open"
    );
}


function clearMessages() {
    messagesContainer.innerHTML = "";
}


function showWelcomeMessage() {
    clearMessages();

    addMessage(
        "assistant",
        "Good day, Shrish. Systems are ready."
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
        : "A.N.Y.A"
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
    newChatButton.disabled = isLoading;
    newProjectButton.disabled = isLoading;

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


function renderProjects() {
    projectList.innerHTML = "";

    const allChatsButton = document.createElement(
        "button"
    );

    allChatsButton.type = "button";
    allChatsButton.className = "sidebar-item";
    allChatsButton.textContent = "All Chats";

    if (!selectedProjectId) {
        allChatsButton.classList.add("active");
    }

    allChatsButton.addEventListener(
        "click",
        () => selectProject(
            "",
            "All Chats"
        )
    );

    projectList.appendChild(allChatsButton);

    for (const project of projects) {
        const button = document.createElement(
            "button"
        );

        button.type = "button";
        button.className = "sidebar-item";
        button.textContent = project.name;
        button.title = project.description || project.name;

        if (project.id === selectedProjectId) {
            button.classList.add("active");
        }

        button.addEventListener(
            "click",
            () => selectProject(
                project.id,
                project.name
            )
        );

        projectList.appendChild(button);
    }
}


function renderChats() {
    chatList.innerHTML = "";

    if (chats.length === 0) {
        const empty = document.createElement("p");

        empty.className = "sidebar-empty";
        empty.textContent = "No saved chats yet.";

        chatList.appendChild(empty);
        return;
    }

    for (const chat of chats) {
        const button = document.createElement(
            "button"
        );

        button.type = "button";
        button.className = "sidebar-item";
        button.textContent = chat.title;
        button.title = chat.title;

        if (chat.id === currentChatId) {
            button.classList.add("active");
        }

        button.addEventListener(
            "click",
            () => loadChat(chat.id)
        );

        chatList.appendChild(button);
    }
}


async function loadProjects() {
    const data = await apiRequest(
        "/api/projects"
    );

    projects = data.projects || [];
    renderProjects();
}


async function loadChats() {
    const query = selectedProjectId
        ? `?project_id=${encodeURIComponent(selectedProjectId)}`
        : "";

    const data = await apiRequest(
        `/api/chats${query}`
    );

    chats = data.chats || [];
    renderChats();
}


async function selectProject(projectId, projectName) {
    selectedProjectId = projectId;
    selectedProjectLabel = projectName;
    currentChatId = null;

    currentProjectName.textContent = (
        selectedProjectLabel
    );

    renderProjects();
    showWelcomeMessage();

    try {
        await loadChats();
        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `I encountered an error: ${error.message}`
        );

        setConnectionStatus(false);
    }

    closeSidebar();
}


async function loadChat(chatId) {
    try {
        const data = await apiRequest(
            `/api/chats/${encodeURIComponent(chatId)}/messages`
        );

        currentChatId = chatId;
        clearMessages();

        const savedMessages = data.messages || [];

        for (const message of savedMessages) {
            if (
                message.role === "user"
                || message.role === "assistant"
            ) {
                addMessage(
                    message.role,
                    message.content
                );
            }
        }

        if (savedMessages.length === 0) {
            showWelcomeMessage();
        }

        renderChats();
        setConnectionStatus(true);
        closeSidebar();
        messageInput.focus();
    } catch (error) {
        addMessage(
            "assistant",
            `I could not load that chat: ${error.message}`
        );

        setConnectionStatus(false);
    }
}


async function createProject() {
    const name = window.prompt(
        "Project name:"
    );

    if (!name || !name.trim()) {
        return;
    }

    const description = window.prompt(
        "Project description (optional):"
    ) || "";

    try {
        const project = await apiRequest(
            "/api/projects",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(
                    {
                        name: name.trim(),
                        description: description.trim(),
                    }
                ),
            }
        );

        await loadProjects();

        await selectProject(
            project.id,
            project.name
        );
    } catch (error) {
        addMessage(
            "assistant",
            `I could not create the project: ${error.message}`
        );

        setConnectionStatus(false);
    }
}


function startNewChat() {
    currentChatId = null;
    showWelcomeMessage();
    renderChats();
    closeSidebar();
    messageInput.focus();
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


async function initializeWorkspace() {
    try {
        await loadProjects();
        await loadChats();
        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `I could not load the workspace: ${error.message}`
        );

        setConnectionStatus(false);
    }
}


async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || requestInProgress) {
        return;
    }

    addMessage("user", message);

    messageInput.value = "";
    resizeInput();
    setRequestState(true);

    try {
        const data = await apiRequest(
            "/api/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(
                    {
                        message,
                        chat_id: currentChatId,
                        project_id: (
                            selectedProjectId
                            || null
                        ),
                    }
                ),
            }
        );

        currentChatId = data.chat_id;

        addMessage(
            "assistant",
            data.assistant
        );

        await loadChats();

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


newProjectButton.addEventListener(
    "click",
    createProject
);


newChatButton.addEventListener(
    "click",
    startNewChat
);


sidebarToggle.addEventListener(
    "click",
    openSidebar
);


sidebarClose.addEventListener(
    "click",
    closeSidebar
);


sidebarOverlay.addEventListener(
    "click",
    closeSidebar
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
    async () => {
        await checkConnection();
        resizeInput();
        await initializeWorkspace();
        messageInput.focus();
    }
);
