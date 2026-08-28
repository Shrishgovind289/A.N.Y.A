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

const modelSelector = document.getElementById(
    "model-selector"
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
const attachFileButton = document.getElementById(
    "attach-file-button"
);
const attachmentPreview = document.getElementById(
    "attachment-preview"
);
const projectFileList = document.getElementById(
    "project-file-list"
);

let apiKey = sessionStorage.getItem("anya_api_key") || "";
let selectedModel = localStorage.getItem(
    "anya_selected_model"
) || "";
let requestInProgress = false;
let selectedProjectId = "";
let selectedProjectLabel = "All Chats";
let currentChatId = null;
let projects = [];
let chats = [];
let projectFiles = [];
let selectedFiles = [];
let fileOperationInProgress = false;

const DEFAULT_VISION_MODEL = "gemma3:4b";

const IMAGE_FILE_EXTENSIONS = new Set(
    [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    ]
);


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


function renderMessageMath(element) {
    if (
        typeof window.renderMathInElement
        !== "function"
    ) {
        return;
    }

    window.renderMathInElement(
        element,
        {
            delimiters: [
                {
                    left: "$$",
                    right: "$$",
                    display: true,
                },
                {
                    left: "\\[",
                    right: "\\]",
                    display: true,
                },
                {
                    left: "\\(",
                    right: "\\)",
                    display: false,
                },
                {
                    left: "$",
                    right: "$",
                    display: false,
                },
            ],
            throwOnError: false,
            strict: "ignore",
        }
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

    renderMessageMath(messageContent);

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
    modelSelector.disabled = (
        isLoading
        || modelSelector.options.length === 0
    );

    sendButton.textContent = (
        isLoading
        ? "..."
        : "Send"
    );

    updateAttachmentControls();

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
        const row = document.createElement("div");
        row.className = "sidebar-item-row";

        const button = document.createElement(
            "button"
        );

        button.type = "button";
        button.className = "sidebar-item";
        button.textContent = project.name;
        button.title = (
            project.description
            || project.name
        );

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

        const deleteButton = document.createElement(
            "button"
        );

        deleteButton.type = "button";
        deleteButton.className = (
            "sidebar-delete-button"
        );
        deleteButton.textContent = "×";
        deleteButton.title = (
            `Delete project ${project.name}`
        );
        deleteButton.setAttribute(
            "aria-label",
            `Delete project ${project.name}`
        );

        deleteButton.addEventListener(
            "click",
            () => deleteProject(project)
        );

        row.append(
            button,
            deleteButton
        );

        projectList.appendChild(row);
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
        const row = document.createElement("div");
        row.className = "sidebar-item-row";

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

        const deleteButton = document.createElement(
            "button"
        );

        deleteButton.type = "button";
        deleteButton.className = (
            "sidebar-delete-button"
        );
        deleteButton.textContent = "×";
        deleteButton.title = (
            `Delete chat ${chat.title}`
        );
        deleteButton.setAttribute(
            "aria-label",
            `Delete chat ${chat.title}`
        );

        deleteButton.addEventListener(
            "click",
            () => deleteChat(chat)
        );

        row.append(
            button,
            deleteButton
        );

        chatList.appendChild(row);
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


function updateAttachmentControls() {
    attachFileButton.disabled = (
        fileOperationInProgress
        || requestInProgress
    );

    attachFileButton.title = (
        selectedProjectId
        ? "Attach files and save them to project Resources"
        : "Attach files to this chat"
    );
}


function renderAttachmentPreview() {
    attachmentPreview.innerHTML = "";

    if (selectedFiles.length === 0) {
        attachmentPreview.hidden = true;
        updateAttachmentControls();
        return;
    }

    attachmentPreview.hidden = false;

    selectedFiles.forEach(
        (file, index) => {
            const chip = document.createElement("div");
            chip.className = "attachment-chip";

            const name = document.createElement("span");
            name.textContent = file.name;
            name.title = file.name;

            const removeButton = document.createElement(
                "button"
            );

            removeButton.type = "button";
            removeButton.className = (
                "attachment-remove-button"
            );
            removeButton.textContent = "\u00d7";
            removeButton.setAttribute(
                "aria-label",
                `Remove ${file.name}`
            );

            removeButton.addEventListener(
                "click",
                () => {
                    selectedFiles.splice(index, 1);
                    renderAttachmentPreview();
                }
            );

            chip.append(
                name,
                removeButton
            );

            attachmentPreview.appendChild(chip);
        }
    );

    updateAttachmentControls();
}


function renderProjectFiles() {
    projectFileList.innerHTML = "";
    updateAttachmentControls();

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


function isImageAttachment(file) {
    if (file.type?.startsWith("image/")) {
        return true;
    }

    const filename = file.name.toLowerCase();
    const extensionIndex = filename.lastIndexOf(".");

    if (extensionIndex < 0) {
        return false;
    }

    return IMAGE_FILE_EXTENSIONS.has(
        filename.slice(extensionIndex)
    );
}


function switchToVisionModel() {
    const visionOption = Array.from(
        modelSelector.options
    ).find(
        (option) => (
            option.value === DEFAULT_VISION_MODEL
        )
    );

    if (!visionOption) {
        return;
    }

    selectedModel = DEFAULT_VISION_MODEL;
    modelSelector.value = DEFAULT_VISION_MODEL;

    localStorage.setItem(
        "anya_selected_model",
        selectedModel
    );
}


function selectAttachmentFiles() {
    const incomingFiles = Array.from(
        projectFileInput.files
    );

    for (const file of incomingFiles) {
        const alreadySelected = selectedFiles.some(
            (existingFile) => (
                existingFile.name === file.name
                && existingFile.size === file.size
                && existingFile.lastModified
                    === file.lastModified
            )
        );

        if (!alreadySelected) {
            selectedFiles.push(file);
        }
    }

    const containsImage = incomingFiles.some(
        isImageAttachment
    );

    if (containsImage) {
        switchToVisionModel();
    }

    projectFileInput.value = "";
    renderAttachmentPreview();
}


async function ensureChat(message) {
    if (currentChatId) {
        return currentChatId;
    }

    const attachmentTitle = selectedFiles
        .map((file) => file.name)
        .join(", ");

    let title = (
        message
        || attachmentTitle
        || "New Chat"
    ).trim();

    if (title.length > 60) {
        title = title.slice(0, 57) + "...";
    }

    const chat = await apiRequest(
        "/api/chats",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(
                {
                    title,
                    project_id: (
                        selectedProjectId
                        || null
                    ),
                }
            ),
        }
    );

    currentChatId = chat.id;

    return currentChatId;
}


async function uploadPendingFiles(chatId) {
    if (selectedFiles.length === 0) {
        return [];
    }

    if (!chatId) {
        throw new Error(
            "A chat must exist before attachments can upload."
        );
    }

    fileOperationInProgress = true;
    updateAttachmentControls();

    const uploadedFiles = [];

    try {
        for (const file of selectedFiles) {
            const formData = new FormData();

            formData.append(
                "upload",
                file
            );

            formData.append(
                "description",
                selectedProjectId
                    ? "Uploaded through project chat"
                    : "Uploaded through chat"
            );

            const uploadedFile = await apiRequest(
                `/api/chats/${
                    encodeURIComponent(chatId)
                }/files`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            uploadedFiles.push(uploadedFile);
        }

        if (selectedProjectId) {
            await loadProjectFiles();
        }

        return uploadedFiles;
    } finally {
        fileOperationInProgress = false;
        updateAttachmentControls();
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


async function deleteProject(project) {
    const confirmation = window.prompt(
        `Deleting "${project.name}" permanently removes `
        + "its chats, resources, and workspace.\n\n"
        + `Type "${project.name}" to confirm:`
    );

    if (confirmation !== project.name) {
        return;
    }

    try {
        const currentChat = chats.find(
            (chat) => chat.id === currentChatId
        );

        const deletingCurrentWorkspace = (
            selectedProjectId === project.id
            || currentChat?.project_id === project.id
        );

        await apiRequest(
            `/api/projects/${
                encodeURIComponent(project.id)
            }`,
            {
                method: "DELETE",
            }
        );

        if (deletingCurrentWorkspace) {
            selectedProjectId = "";
            selectedProjectLabel = "All Chats";
            currentChatId = null;
            selectedFiles = [];
            projectFiles = [];

            currentProjectName.textContent = (
                "All Chats"
            );

            renderAttachmentPreview();
            renderProjectFiles();
            showWelcomeMessage();
        }

        await loadProjects();
        await loadChats();

        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `I could not delete that project: ${error.message}`
        );

        setConnectionStatus(false);
    }
}


async function deleteChat(chat) {
    const confirmed = window.confirm(
        `Delete the chat "${chat.title}" permanently?`
    );

    if (!confirmed) {
        return;
    }

    try {
        await apiRequest(
            `/api/chats/${
                encodeURIComponent(chat.id)
            }`,
            {
                method: "DELETE",
            }
        );

        if (currentChatId === chat.id) {
            currentChatId = null;
            selectedFiles = [];
            renderAttachmentPreview();
            showWelcomeMessage();
        }

        await loadChats();

        setConnectionStatus(true);
    } catch (error) {
        addMessage(
            "assistant",
            `I could not delete that chat: ${error.message}`
        );

        setConnectionStatus(false);
    }
}


async function loadModels() {
    const data = await apiRequest(
        "/api/models"
    );

    const installedModels = data.models || [];

    modelSelector.innerHTML = "";

    if (installedModels.length === 0) {
        const option = document.createElement(
            "option"
        );

        option.value = "";
        option.textContent = "No models installed";

        modelSelector.appendChild(option);
        modelSelector.disabled = true;
        selectedModel = "";
        return;
    }

    for (const modelName of installedModels) {
        const option = document.createElement(
            "option"
        );

        option.value = modelName;
        option.textContent = modelName;

        modelSelector.appendChild(option);
    }

    const defaultModel = data.default_model || "";

    if (installedModels.includes(selectedModel)) {
        modelSelector.value = selectedModel;
    } else if (installedModels.includes(defaultModel)) {
        selectedModel = defaultModel;
        modelSelector.value = defaultModel;
    } else {
        selectedModel = installedModels[0];
        modelSelector.value = selectedModel;
    }

    localStorage.setItem(
        "anya_selected_model",
        selectedModel
    );

    modelSelector.disabled = requestInProgress;
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
    selectedFiles = [];
    renderAttachmentPreview();

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
    selectedFiles = [];
    renderAttachmentPreview();
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
        await loadModels();
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
    const hasAttachments = selectedFiles.length > 0;

    if (
        (!message && !hasAttachments)
        || requestInProgress
    ) {
        return;
    }

    const attachmentNames = selectedFiles.map(
        (file) => file.name
    );

    let displayedMessage = (
        message
        || "Attached files."
    );

    if (attachmentNames.length > 0) {
        displayedMessage += (
            "\n\nAttachments:\n- "
            + attachmentNames.join("\n- ")
        );
    }

    addMessage(
        "user",
        displayedMessage
    );

    messageInput.value = "";
    resizeInput();
    setRequestState(true);

    try {
        const chatId = await ensureChat(
            message
        );

        let uploadedFiles = [];

        if (hasAttachments) {
            uploadedFiles = await uploadPendingFiles(
                chatId
            );

            selectedFiles = [];
            renderAttachmentPreview();
        }

        let modelMessage = (
            message
            || "Please review the attached files."
        );

        if (uploadedFiles.length > 0) {
            const attachmentSummary = uploadedFiles.map(
                (file) => (
                    `- ${file.stored_name} `
                    + `(${formatFileSize(file.size_bytes)}, `
                    + `scan: ${file.scan_status}, `
                    + `file ID: ${file.id})`
                )
            );

            const attachmentHeading = selectedProjectId
                ? "Attached project resources:"
                : "Attached chat files:";

            modelMessage += (
                `\n\n${attachmentHeading}\n`
                + attachmentSummary.join("\n")
            );
        }

        const data = await apiRequest(
            "/api/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(
                    {
                        message: modelMessage,
                        chat_id: chatId,
                        project_id: (
                            selectedProjectId
                            || null
                        ),
                        model: (
                            selectedModel
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

        if (selectedProjectId) {
            await loadProjectFiles();
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


modelSelector.addEventListener(
    "change",
    () => {
        selectedModel = modelSelector.value;

        localStorage.setItem(
            "anya_selected_model",
            selectedModel
        );
    }
);


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


attachFileButton.addEventListener(
    "click",
    () => {
        projectFileInput.click();
    }
);


projectFileInput.addEventListener(
    "change",
    selectAttachmentFiles
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
