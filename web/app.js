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

const projectFileInput = document.getElementById(
    "project-file-input"
);
const uploadFileButton = document.getElementById(
    "upload-file-button"
);
const projectFileList = document.getElementById(
    "project-file-list"
);

let apiKey = sessionStorage.getItem("anya_api_key") || "";
let requestInProgress = false;
let selectedProjectId = "";
let selectedProjectLabel = "All Chats";
let currentChatId = null;
let projects = [];
let chats = [];
let projectFiles = [];
let fileOperationInProgress = false;


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


function formatFileSize(sizeBytes) {
    if (sizeBytes < 1024) {
        return `${sizeBytes} B`;
    }

    if (sizeBytes < 1024 * 1024) {
        return `${(sizeBytes / 1024).toFixed(1)} KB`;
    }

    return `${(
        sizeBytes / (1024 * 1024)
    ).toFixed(1)} MB`;
}


function updateUploadButton() {
    uploadFileButton.disabled = (
        !selectedProjectId
        || fileOperationInProgress
    );

    uploadFileButton.textContent = (
        fileOperationInProgress
        ? "Scanning..."
        : "+ Upload File"
    );
}


function renderProjectFiles() {
    projectFileList.innerHTML = "";
    updateUploadButton();

    if (!selectedProjectId) {
        const empty = document.createElement("p");

        empty.className = "sidebar-empty";
        empty.textContent = (
            "Select a project to manage files."
        );

        projectFileList.appendChild(empty);
        return;
    }

    if (projectFiles.length === 0) {
        const empty = document.createElement("p");

        empty.className = "sidebar-empty";
        empty.textContent = "No uploaded files.";

        projectFileList.appendChild(empty);
        return;
    }

    for (const file of projectFiles) {
        const item = document.createElement("div");
        item.className = "project-file-item";

        const name = document.createElement("div");
        name.className = "project-file-name";
        name.textContent = file.stored_name;
        name.title = file.original_name;

        const metadata = document.createElement("div");
        metadata.className = "project-file-meta";

        const scanStatus = document.createElement("span");
        scanStatus.className = "project-file-status";
        scanStatus.textContent = (
            file.scan_status === "clean"
            ? "Clean"
            : file.scan_status
        );

        metadata.append(
            `${formatFileSize(file.size_bytes)} ? `,
            scanStatus
        );

        const actions = document.createElement("div");
        actions.className = "project-file-actions";

        const downloadButton = document.createElement(
            "button"
        );

        downloadButton.type = "button";
        downloadButton.className = "file-action-button";
        downloadButton.textContent = "Download";

        downloadButton.addEventListener(
            "click",
            () => downloadProjectFile(file)
        );

        const deleteButton = document.createElement(
            "button"
        );

        deleteButton.type = "button";
        deleteButton.className = (
            "file-action-button delete"
        );
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener(
            "click",
            () => deleteProjectFile(file)
        );

        actions.append(
            downloadButton,
            deleteButton
        );

        item.append(
            name,
            metadata,
            actions
        );

        projectFileList.appendChild(item);
    }
}


async function loadProjectFiles() {
    if (!selectedProjectId) {
        projectFiles = [];
        renderProjectFiles();
        return;
    }

    const data = await apiRequest(
        `/api/projects/${
            encodeURIComponent(selectedProjectId)
        }/files`
    );

    projectFiles = data.files || [];
    renderProjectFiles();
}


async function uploadSelectedFile() {
    const file = projectFileInput.files[0];

    if (
        !file
        || !selectedProjectId
        || fileOperationInProgress
    ) {
        return;
    }

    const formData = new FormData();
    formData.append("upload", file);
    formData.append("description", "");

    fileOperationInProgress = true;
    updateUploadButton();

    try {
        await apiRequest(
            `/api/projects/${
                encodeURIComponent(selectedProjectId)
            }/files`,
            {
                method: "POST",
                body: formData,
            }
        );

        await loadProjectFiles();

        addMessage(
            "assistant",
            `${file.name} was scanned and stored successfully.`
        );

        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `The file upload failed: ${error.message}`
        );

        setConnectionStatus(false);
    } finally {
        fileOperationInProgress = false;
        projectFileInput.value = "";
        updateUploadButton();
    }
}


async function downloadProjectFile(file) {
    try {
        if (!apiKey && !requestApiKey()) {
            throw new Error(
                "An API key is required."
            );
        }

        const response = await fetch(
            `/api/files/${
                encodeURIComponent(file.id)
            }/download`,
            {
                headers: {
                    "X-API-Key": apiKey,
                },
            }
        );

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
            let detail = "Download failed.";

            try {
                const data = await response.json();
                detail = data.detail || detail;
            } catch {
                // Keep the generic error.
            }

            throw new Error(detail);
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);

        const downloadLink = document.createElement("a");

        downloadLink.href = objectUrl;
        downloadLink.download = file.stored_name;

        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();

        URL.revokeObjectURL(objectUrl);
    } catch (error) {
        addMessage(
            "assistant",
            `The file download failed: ${error.message}`
        );
    }
}


async function deleteProjectFile(file) {
    const confirmed = window.confirm(
        `Delete "${file.stored_name}" permanently?`
    );

    if (!confirmed) {
        return;
    }

    try {
        await apiRequest(
            `/api/files/${encodeURIComponent(file.id)}`,
            {
                method: "DELETE",
            }
        );

        await loadProjectFiles();

        addMessage(
            "assistant",
            `${file.stored_name} was deleted.`
        );
    } catch (error) {
        addMessage(
            "assistant",
            `The file could not be deleted: ${error.message}`
        );
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


uploadFileButton.addEventListener(
    "click",
    () => {
        if (selectedProjectId) {
            projectFileInput.click();
        }
    }
);


projectFileInput.addEventListener(
    "change",
    uploadSelectedFile
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
        renderProjectFiles();
        messageInput.focus();
    }
);
