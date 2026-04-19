/**
 * QQ聊天记录处理与总结系统 - 前端脚本
 * 包含完整的前端交互逻辑和模拟后端API
 */

// 全局变量
let processing = false;
let fileContent = '';
let parsedMessages = [];
let originalFileName = '';

// QQ群文件相关变量
let qqLoggedIn = false;
let qqGroupFiles = [];
let selectedFiles = new Set();

// DOM元素
const elements = {
    fileInput: document.getElementById('fileInput'),
    filePath: document.getElementById('filePath'),
    apiKey: document.getElementById('apiKey'),
    saveConfigBtn: document.getElementById('saveConfigBtn'),
    startProcessBtn: document.getElementById('startProcessBtn'),
    cancelProcessBtn: document.getElementById('cancelProcessBtn'),
    progressBar: document.getElementById('progressBar'),
    statusText: document.getElementById('statusText'),
    resultText: document.getElementById('resultText'),
    saveResultBtn: document.getElementById('saveResultBtn'),
    clearResultBtn: document.getElementById('clearResultBtn'),
    parseCheck: document.getElementById('parseCheck'),
    cleanCheck: document.getElementById('cleanCheck'),
    summarizeCheck: document.getElementById('summarizeCheck'),
    saveCheck: document.getElementById('saveCheck'),
    helpBtn: document.getElementById('helpBtn'),
    aboutBtn: document.getElementById('aboutBtn')
};

// QQ群文件DOM元素
const qqFileElements = {
    qqNumber: document.getElementById('qqNumber'),
    qqPassword: document.getElementById('qqPassword'),
    qqCookie: document.getElementById('qqCookie'),
    qqLoginBtn: document.getElementById('qqLoginBtn'),
    qqLogoutBtn: document.getElementById('qqLogoutBtn'),
    qqLoginStatus: document.getElementById('qqLoginStatus'),
    qqLoginAlert: document.getElementById('qqLoginAlert'),
    qqGroupSection: document.getElementById('qqGroupSection'),
    groupId: document.getElementById('groupId'),
    getGroupFilesBtn: document.getElementById('getGroupFilesBtn'),
    qqFileListSection: document.getElementById('qqFileListSection'),
    qqFileListBody: document.getElementById('qqFileListBody'),
    qqFileLoading: document.getElementById('qqFileLoading'),
    qqFileEmpty: document.getElementById('qqFileEmpty'),
    selectAllCheckbox: document.getElementById('selectAllCheckbox'),
    selectedCount: document.getElementById('selectedCount'),
    downloadSelectedBtn: document.getElementById('downloadSelectedBtn'),
    selectAllBtn: document.getElementById('selectAllBtn'),
    qqDownloadSection: document.getElementById('qqDownloadSection'),
    qqDownloadProgress: document.getElementById('qqDownloadProgress'),
    qqDownloadStatus: document.getElementById('qqDownloadStatus'),
    qqDownloadLog: document.getElementById('qqDownloadLog')
};

// 预览相关DOM元素
const previewElements = {
    fileInfoText: document.getElementById('fileInfoText'),
    statsPanel: document.getElementById('statsPanel'),
    totalMessages: document.getElementById('totalMessages'),
    totalMembers: document.getElementById('totalMembers'),
    dateRange: document.getElementById('dateRange'),
    mediaCount: document.getElementById('mediaCount'),
    filterPanel: document.getElementById('filterPanel'),
    memberFilter: document.getElementById('memberFilter'),
    dateFilter: document.getElementById('dateFilter'),
    contentFilter: document.getElementById('contentFilter'),
    loadingPreview: document.getElementById('loadingPreview'),
    chatContainer: document.getElementById('chatContainer'),
    messageList: document.getElementById('messageList'),
    messageCount: document.getElementById('messageCount'),
    emptyState: document.getElementById('emptyState'),
    parseError: document.getElementById('parseError'),
    parseErrorText: document.getElementById('parseErrorText')
};

// 模态框
const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
const aboutModal = new bootstrap.Modal(document.getElementById('aboutModal'));

// 初始化
function init() {
    loadConfig();
    bindEvents();
    bindPreviewEvents();
    bindQQFileEvents();
    loadQQConfig();
}

// 绑定事件
function bindEvents() {
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.saveConfigBtn.addEventListener('click', saveConfig);
    elements.startProcessBtn.addEventListener('click', startProcess);
    elements.cancelProcessBtn.addEventListener('click', cancelProcess);
    elements.saveResultBtn.addEventListener('click', saveResult);
    elements.clearResultBtn.addEventListener('click', clearResult);
    elements.helpBtn.addEventListener('click', () => helpModal.show());
    elements.aboutBtn.addEventListener('click', () => aboutModal.show());
}

// 绑定预览相关事件
function bindPreviewEvents() {
    previewElements.memberFilter.addEventListener('change', renderFilteredMessages);
    previewElements.dateFilter.addEventListener('change', renderFilteredMessages);
    previewElements.contentFilter.addEventListener('input', debounce(renderFilteredMessages, 300));
}

// 绑定QQ群文件相关事件
function bindQQFileEvents() {
    qqFileElements.qqLoginBtn.addEventListener('click', handleQQLogin);
    qqFileElements.qqLogoutBtn.addEventListener('click', handleQQLogout);
    qqFileElements.getGroupFilesBtn.addEventListener('click', handleGetGroupFiles);
    qqFileElements.selectAllCheckbox.addEventListener('change', handleSelectAll);
    qqFileElements.selectAllBtn.addEventListener('click', handleSelectAll);
    qqFileElements.downloadSelectedBtn.addEventListener('click', handleDownloadSelected);
}

// 加载QQ配置
function loadQQConfig() {
    const savedCookie = localStorage.getItem('qq_cookie');
    if (savedCookie) {
        qqFileElements.qqCookie.value = savedCookie;
    }
    updateQQLoginUI();
}

// 更新QQ登录UI状态
function updateQQLoginUI() {
    if (qqLoggedIn) {
        qqFileElements.qqLoginBtn.style.display = 'none';
        qqFileElements.qqLogoutBtn.style.display = 'inline-block';
        qqFileElements.qqGroupSection.style.display = 'block';
        qqFileElements.qqLoginAlert.style.display = 'none';
        qqFileElements.qqLoginStatus.innerHTML = '<span class="text-success"><i class="fas fa-check-circle"></i> 已登录</span>';
    } else {
        qqFileElements.qqLoginBtn.style.display = 'inline-block';
        qqFileElements.qqLogoutBtn.style.display = 'none';
        qqFileElements.qqGroupSection.style.display = 'none';
        qqFileElements.qqLoginAlert.style.display = 'block';
        qqFileElements.qqLoginStatus.innerHTML = '';
    }
}

// 处理QQ登录
function handleQQLogin() {
    const qqNumber = qqFileElements.qqNumber.value.trim();
    const password = qqFileElements.qqPassword.value;
    const cookieStr = qqFileElements.qqCookie.value.trim();

    if (!qqNumber && !cookieStr) {
        showQQAlert('请输入QQ号码或Cookie', 'warning');
        return;
    }

    if (cookieStr) {
        const cookies = parseCookieString(cookieStr);
        if (!cookies.uin || !cookies.skey) {
            showQQAlert('Cookie格式错误，需要包含uin和skey', 'warning');
            return;
        }
        localStorage.setItem('qq_cookie', cookieStr);
        qqLoggedIn = true;
        showQQAlert('登录成功（模拟模式）', 'success');
    } else {
        if (!password) {
            showQQAlert('请输入密码或使用Cookie登录', 'warning');
            return;
        }
        qqLoggedIn = true;
        showQQAlert('登录成功（模拟模式）', 'success');
    }

    updateQQLoginUI();
}

// 处理QQ退出登录
function handleQQLogout() {
    qqLoggedIn = false;
    qqGroupFiles = [];
    selectedFiles.clear();
    qqFileElements.qqFileListSection.style.display = 'none';
    qqFileElements.qqDownloadSection.style.display = 'none';
    updateQQLoginUI();
    showQQAlert('已退出登录', 'info');
}

// 解析Cookie字符串
function parseCookieString(cookieStr) {
    const cookies = {};
    cookieStr.split(';').forEach(item => {
        const [key, value] = item.split('=').map(s => s.trim());
        if (key && value) {
            cookies[key] = value;
        }
    });
    return cookies;
}

// 显示QQ群文件Alert
function showQQAlert(message, type) {
    qqFileElements.qqLoginStatus.innerHTML = `<span class="text-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'}"><i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}</span>`;
}

// 处理获取群文件
function handleGetGroupFiles() {
    const groupId = qqFileElements.groupId.value.trim();

    if (!qqLoggedIn) {
        showQQAlert('请先登录', 'warning');
        return;
    }

    if (!groupId) {
        showQQAlert('请输入群ID', 'warning');
        return;
    }

    qqFileElements.qqFileLoading.style.display = 'block';
    qqFileElements.qqFileEmpty.style.display = 'none';
    qqFileElements.qqFileListSection.style.display = 'block';

    setTimeout(() => {
        qqGroupFiles = getMockGroupFiles(groupId);
        renderGroupFileList();
        qqFileElements.qqFileLoading.style.display = 'none';

        if (qqGroupFiles.length === 0) {
            qqFileElements.qqFileEmpty.style.display = 'block';
        }
    }, 1000);
}

// 获取模拟群文件列表
function getMockGroupFiles(groupId) {
    return [
        {
            file_id: '1001',
            name: '群公告.docx',
            size: 1024000,
            upload_time: '2024-01-15 10:00:00',
            uploader: '管理员',
            download_url: ''
        },
        {
            file_id: '1002',
            name: '活动策划方案.pdf',
            size: 2048000,
            upload_time: '2024-01-20 14:30:00',
            uploader: '组织者',
            download_url: ''
        },
        {
            file_id: '1003',
            name: '会议记录.txt',
            size: 512000,
            upload_time: '2024-01-25 09:15:00',
            uploader: '记录员',
            download_url: ''
        },
        {
            file_id: '1004',
            name: '技术文档.zip',
            size: 5242880,
            upload_time: '2024-02-01 16:45:00',
            uploader: '开发者',
            download_url: ''
        },
        {
            file_id: '1005',
            name: '项目计划.xlsx',
            size: 768000,
            upload_time: '2024-02-05 11:20:00',
            uploader: '项目经理',
            download_url: ''
        }
    ];
}

// 格式化文件大小
function formatFileSize(size) {
    if (size <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    let s = size;
    while (s >= 1024 && unitIndex < units.length - 1) {
        s /= 1024;
        unitIndex++;
    }
    return `${s.toFixed(2)} ${units[unitIndex]}`;
}

// 渲染群文件列表
function renderGroupFileList() {
    qqFileElements.qqFileListBody.innerHTML = '';

    if (qqGroupFiles.length === 0) {
        qqFileElements.qqFileEmpty.style.display = 'block';
        return;
    }

    qqFileElements.qqFileEmpty.style.display = 'none';

    qqGroupFiles.forEach((file, index) => {
        const tr = document.createElement('tr');
        const isSelected = selectedFiles.has(file.file_id);

        tr.innerHTML = `
            <td><input type="checkbox" class="file-checkbox" data-file-id="${file.file_id}" ${isSelected ? 'checked' : ''}></td>
            <td><i class="fas fa-file me-2"></i>${escapeHtml(file.name)}</td>
            <td>${formatFileSize(file.size)}</td>
            <td>${file.upload_time.split(' ')[0]}</td>
            <td>${escapeHtml(file.uploader)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary download-single" data-index="${index}">
                    <i class="fas fa-download"></i>
                </button>
            </td>
        `;

        qqFileElements.qqFileListBody.appendChild(tr);
    });

    document.querySelectorAll('.file-checkbox').forEach(cb => {
        cb.addEventListener('change', handleFileCheckboxChange);
    });

    document.querySelectorAll('.download-single').forEach(btn => {
        btn.addEventListener('click', handleDownloadSingle);
    });

    updateSelectedCount();
}

// 处理文件复选框变化
function handleFileCheckboxChange(e) {
    const fileId = e.target.dataset.fileId;
    if (e.target.checked) {
        selectedFiles.add(fileId);
    } else {
        selectedFiles.delete(fileId);
    }
    updateSelectedCount();
}

// 更新选中数量
function updateSelectedCount() {
    qqFileElements.selectedCount.textContent = selectedFiles.size;
    qqFileElements.downloadSelectedBtn.disabled = selectedFiles.size === 0;
    qqFileElements.selectAllCheckbox.checked = selectedFiles.size === qqGroupFiles.length && qqGroupFiles.length > 0;
}

// 处理全选
function handleSelectAll() {
    const isChecked = qqFileElements.selectAllCheckbox.checked;
    document.querySelectorAll('.file-checkbox').forEach(cb => {
        cb.checked = isChecked;
        const fileId = cb.dataset.fileId;
        if (isChecked) {
            selectedFiles.add(fileId);
        } else {
            selectedFiles.clear();
        }
    });
    updateSelectedCount();
}

// 处理单个文件下载
function handleDownloadSingle(e) {
    const index = parseInt(e.currentTarget.dataset.index);
    const file = qqGroupFiles[index];
    const filesToDownload = [file];
    downloadFiles(filesToDownload);
}

// 处理下载选中文件
function handleDownloadSelected() {
    const filesToDownload = qqGroupFiles.filter(f => selectedFiles.has(f.file_id));
    if (filesToDownload.length === 0) {
        showQQAlert('请选择要下载的文件', 'warning');
        return;
    }
    downloadFiles(filesToDownload);
}

// 下载文件
function downloadFiles(files) {
    qqFileElements.qqDownloadSection.style.display = 'block';
    qqFileElements.qqDownloadLog.innerHTML = '';
    qqFileElements.qqDownloadProgress.style.width = '0%';
    qqFileElements.qqDownloadProgress.textContent = '0%';

    let completed = 0;
    const total = files.length;

    files.forEach((file, index) => {
        setTimeout(() => {
            const li = document.createElement('li');
            li.className = 'text-success';
            li.innerHTML = `<i class="fas fa-check-circle"></i> ${file.name} - 下载完成`;
            qqFileElements.qqDownloadLog.appendChild(li);

            completed++;
            const progress = Math.round((completed / total) * 100);
            qqFileElements.qqDownloadProgress.style.width = `${progress}%`;
            qqFileElements.qqDownloadProgress.textContent = `${progress}%`;
            qqFileElements.qqDownloadStatus.textContent = `已完成 ${completed}/${total} 个文件`;

            if (completed === total) {
                const finalLi = document.createElement('li');
                finalLi.className = 'text-primary fw-bold';
                finalLi.innerHTML = `<i class="fas fa-flag-checkered"></i> 全部下载完成！`;
                qqFileElements.qqDownloadLog.appendChild(finalLi);
                qqFileElements.qqDownloadLog.scrollTop = qqFileElements.qqDownloadLog.scrollHeight;
            }

            qqFileElements.qqDownloadLog.scrollTop = qqFileElements.qqDownloadLog.scrollHeight;
        }, index * 500);
    });
}

// 处理文件选择
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    originalFileName = file.name;
    elements.filePath.value = file.name;

    const fileSize = (file.size / 1024).toFixed(2);
    previewElements.fileInfoText.textContent = `${file.name} (${fileSize} KB)`;

    const reader = new FileReader();
    reader.onload = function(e) {
        fileContent = e.target.result;
        updateStatus('文件已加载，正在解析...');

        setTimeout(() => {
            parseAndPreviewFile();
        }, 100);
    };
    reader.onerror = function() {
        showPreviewError('文件读取失败，请尝试重新选择文件');
        updateStatus('文件读取失败');
    };
    reader.readAsText(file, 'utf-8');
}

// 解析并预览文件
function parseAndPreviewFile() {
    showPreviewLoading(true);
    hidePreviewError();
    previewElements.emptyState.style.display = 'none';

    setTimeout(() => {
        try {
            parsedMessages = parseQQChatLog(fileContent);

            if (parsedMessages.length === 0) {
                showPreviewError('未能解析到有效的聊天记录，请确保文件格式正确');
                previewElements.emptyState.style.display = 'block';
                showPreviewLoading(false);
                updateStatus('解析失败');
                return;
            }

            updatePreviewStats(parsedMessages);
            populateMemberFilter(parsedMessages);
            renderFilteredMessages();

            previewElements.statsPanel.style.display = 'flex';
            previewElements.filterPanel.style.display = 'flex';
            previewElements.chatContainer.style.display = 'block';
            previewElements.emptyState.style.display = 'none';
            showPreviewLoading(false);

            updateStatus(`解析完成，共 ${parsedMessages.length} 条消息`);

        } catch (error) {
            showPreviewError(`解析错误: ${error.message}`);
            previewElements.emptyState.style.display = 'block';
            showPreviewLoading(false);
            updateStatus('解析失败');
        }
    }, 300);
}

// 解析QQ聊天记录
function parseQQChatLog(content) {
    const messages = [];
    const lines = content.split(/\r?\n/);
    const headerPattern = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+([^\(（]+)[\(（]([^\)）]+)[\)）]$/;
    const mediaPatterns = [
        /\[图片\]/,
        /\[表情\]/,
        /\[视频\]/,
        /\[文件\]/,
        /\[语音消息\]/,
        /\[戳了戳\]/,
        /撤回了一条消息/,
        /撤回了消息/,
        /加入了本群/,
        /离开了本群/,
        /邀请.+加入了本群/,
        /已将群聊设为.*/
    ];

    let currentMessage = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        const headerMatch = line.match(headerPattern);
        if (headerMatch) {
            if (currentMessage) {
                messages.push(currentMessage);
            }
            currentMessage = {
                id: messages.length + 1,
                time: headerMatch[1],
                sender: headerMatch[2].trim(),
                uin: headerMatch[3].trim(),
                content: '',
                isMedia: false,
                date: headerMatch[1].split(' ')[0]
            };
        } else if (currentMessage) {
            if (currentMessage.content) {
                currentMessage.content += '\n' + line;
            } else {
                currentMessage.content = line;
            }

            for (const pattern of mediaPatterns) {
                if (pattern.test(line)) {
                    currentMessage.isMedia = true;
                    break;
                }
            }
        }
    }

    if (currentMessage) {
        messages.push(currentMessage);
    }

    return messages;
}

// 更新预览统计信息
function updatePreviewStats(messages) {
    const totalMessages = messages.length;
    const uniqueSenders = new Set(messages.map(m => m.sender));
    const totalMembers = uniqueSenders.size;

    const dates = messages.map(m => m.date).filter(d => d);
    const minDate = dates.length > 0 ? Math.min(...dates.map(d => new Date(d).getTime())) : null;
    const maxDate = dates.length > 0 ? Math.max(...dates.map(d => new Date(d).getTime())) : null;

    const dateRangeText = minDate && maxDate
        ? `${formatDate(new Date(minDate))} ~ ${formatDate(new Date(maxDate))}`
        : '-';

    const mediaCount = messages.filter(m => m.isMedia).length;

    previewElements.totalMessages.textContent = totalMessages;
    previewElements.totalMembers.textContent = totalMembers;
    previewElements.dateRange.textContent = dateRangeText;
    previewElements.mediaCount.textContent = mediaCount;
}

// 格式化日期
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 填充成员筛选下拉框
function populateMemberFilter(messages) {
    const uniqueSenders = [...new Set(messages.map(m => m.sender))].sort();
    previewElements.memberFilter.innerHTML = '<option value="">全部成员</option>';
    uniqueSenders.forEach(sender => {
        const option = document.createElement('option');
        option.value = sender;
        option.textContent = sender;
        previewElements.memberFilter.appendChild(option);
    });
}

// 渲染筛选后的消息
function renderFilteredMessages() {
    const memberFilter = previewElements.memberFilter.value;
    const dateFilter = previewElements.dateFilter.value;
    const contentFilter = previewElements.contentFilter.value.toLowerCase();

    let filtered = parsedMessages;

    if (memberFilter) {
        filtered = filtered.filter(m => m.sender === memberFilter);
    }

    if (dateFilter) {
        filtered = filtered.filter(m => m.date === dateFilter);
    }

    if (contentFilter) {
        filtered = filtered.filter(m => m.content.toLowerCase().includes(contentFilter));
    }

    previewElements.messageCount.textContent = `${filtered.length} 条消息`;
    previewElements.messageList.innerHTML = '';

    if (filtered.length === 0) {
        const emptyItem = document.createElement('div');
        emptyItem.className = 'text-center text-muted py-4';
        emptyItem.textContent = '没有符合条件的消息';
        previewElements.messageList.appendChild(emptyItem);
        return;
    }

    let lastDate = null;
    let lastSender = null;

    filtered.forEach((msg, index) => {
        if (msg.date !== lastDate) {
            const dateDivider = document.createElement('div');
            dateDivider.className = 'chat-date-divider';
            dateDivider.innerHTML = `<span>${formatDate(new Date(msg.date))}</span>`;
            previewElements.messageList.appendChild(dateDivider);
            lastDate = msg.date;
            lastSender = null;
        }

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${msg.sender === lastSender ? 'same-sender' : ''}`;

        const avatarEl = document.createElement('div');
        avatarEl.className = 'chat-avatar';
        avatarEl.textContent = msg.sender.charAt(0).toUpperCase();

        const contentEl = document.createElement('div');
        contentEl.className = 'chat-content';

        const headerEl = document.createElement('div');
        headerEl.className = 'chat-header';
        headerEl.innerHTML = `<span class="chat-sender">${escapeHtml(msg.sender)}</span><span class="chat-time">${msg.time.split(' ')[1]}</span>`;

        const bodyEl = document.createElement('div');
        bodyEl.className = 'chat-body';

        if (msg.isMedia) {
            bodyEl.className += ' media-message';
            bodyEl.textContent = msg.content || '[媒体消息]';
        } else {
            bodyEl.textContent = msg.content || '[空消息]';
        }

        contentEl.appendChild(headerEl);
        contentEl.appendChild(bodyEl);
        messageEl.appendChild(avatarEl);
        messageEl.appendChild(contentEl);
        previewElements.messageList.appendChild(messageEl);

        lastSender = msg.sender;
    });
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 显示预览加载状态
function showPreviewLoading(show) {
    previewElements.loadingPreview.style.display = show ? 'block' : 'none';
    if (show) {
        previewElements.chatContainer.style.display = 'none';
        previewElements.emptyState.style.display = 'none';
    }
}

// 显示预览错误
function showPreviewError(message) {
    previewElements.parseError.style.display = 'block';
    previewElements.parseErrorText.textContent = message;
}

// 隐藏预览错误
function hidePreviewError() {
    previewElements.parseError.style.display = 'none';
}

// 加载配置
function loadConfig() {
    const apiKey = localStorage.getItem('gemini_api_key');
    if (apiKey) {
        elements.apiKey.value = apiKey;
        updateStatus('配置已加载');
    }
}

// 保存配置
function saveConfig() {
    const apiKey = elements.apiKey.value;
    localStorage.setItem('gemini_api_key', apiKey);
    updateStatus('配置已保存');

    const alert = document.createElement('div');
    alert.className = 'alert alert-success mt-3';
    alert.innerHTML = '<i class="fas fa-check-circle"></i> 配置已保存';

    const configTab = document.getElementById('config');
    configTab.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// 开始处理
function startProcess() {
    if (!fileContent) {
        showError('请先选择聊天记录文件');
        return;
    }

    if (elements.summarizeCheck.checked && !elements.apiKey.value) {
        showError('请配置Gemini API密钥');
        return;
    }

    elements.startProcessBtn.disabled = true;
    elements.cancelProcessBtn.disabled = false;
    processing = true;

    elements.resultText.textContent = '';

    setTimeout(() => {
        processChatLog();
    }, 100);
}

// 取消处理
function cancelProcess() {
    processing = false;
    updateStatus('处理已取消');
    elements.startProcessBtn.disabled = false;
    elements.cancelProcessBtn.disabled = true;
    updateProgress(0);
}

// 处理聊天记录
function processChatLog() {
    try {
        updateStatus('开始处理...');
        updateProgress(0);

        setTimeout(() => {
            if (!processing) return;

            if (elements.parseCheck.checked) {
                updateStatus('正在解析聊天记录...');
                const messages = parseQQChatLog(fileContent);
                updateProgress(25);
                appendResult(`✓ 解析完成，共 ${messages.length} 条消息\n`);

                setTimeout(() => {
                    if (!processing) return;

                    if (elements.cleanCheck.checked) {
                        updateStatus('正在清洗消息...');
                        const cleanedMessages = cleanMessages(messages);
                        updateProgress(50);
                        appendResult(`✓ 清洗完成，剩余 ${cleanedMessages.length} 条消息\n`);

                        setTimeout(() => {
                            if (!processing) return;

                            if (elements.summarizeCheck.checked) {
                                updateStatus('正在生成总结...');
                                const summary = generateSummary(cleanedMessages);
                                updateProgress(75);
                                appendResult('✓ 总结生成成功\n');
                                appendResult(summary + '\n');

                                setTimeout(() => {
                                    if (!processing) return;

                                    if (elements.saveCheck.checked) {
                                        updateStatus('正在保存结果...');
                                        updateProgress(100);
                                        appendResult('✓ 结果已保存到 chat_summary.md\n');
                                    }

                                    completeProcessing();
                                }, 1000);
                            } else {
                                updateProgress(100);
                                completeProcessing();
                            }
                        }, 1000);
                    } else {
                        updateProgress(50);

                        if (elements.summarizeCheck.checked) {
                            updateStatus('正在生成总结...');
                            const summary = generateSummary(messages);
                            updateProgress(75);
                            appendResult('✓ 总结生成成功\n');
                            appendResult(summary + '\n');

                            setTimeout(() => {
                                if (!processing) return;

                                if (elements.saveCheck.checked) {
                                    updateStatus('正在保存结果...');
                                    updateProgress(100);
                                    appendResult('✓ 结果已保存到 chat_summary.md\n');
                                }

                                completeProcessing();
                            }, 1000);
                        } else {
                            updateProgress(100);
                            completeProcessing();
                        }
                    }
                }, 1000);
            } else {
                updateProgress(100);
                completeProcessing();
            }
        }, 500);

    } catch (error) {
        updateStatus(`错误: ${error.message}`);
        appendResult(`✗ 错误: ${error.message}\n`);
        completeProcessing();
    }
}

// 完成处理
function completeProcessing() {
    processing = false;
    updateStatus('处理完成');
    elements.startProcessBtn.disabled = false;
    elements.cancelProcessBtn.disabled = true;

    const alert = document.createElement('div');
    alert.className = 'alert alert-success mt-3';
    alert.innerHTML = '<i class="fas fa-check-circle"></i> 处理完成！';

    const processTab = document.getElementById('process');
    processTab.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// 清洗消息
function cleanMessages(messages) {
    const MEDIA_TAGS = ["[图片]", "[表情]", "[视频]", "[文件]", "[语音消息]", "[戳了戳]"];
    const SYSTEM_PATTERNS = [
        "撤回了一条消息",
        "撤回了消息",
        "加入了本群",
        "离开了本群",
        "邀请",
        "已将群聊设为"
    ];

    return messages.filter(msg => {
        const content = msg.content;

        if (msg.isMedia && MEDIA_TAGS.some(tag => content.includes(tag))) {
            return false;
        }

        for (const pattern of SYSTEM_PATTERNS) {
            if (content.includes(pattern)) {
                return false;
            }
        }

        if (content.length < 4) {
            return false;
        }

        return true;
    });
}

// 生成总结
function generateSummary(messages) {
    const uniqueSenders = [...new Set(messages.map(m => m.sender))];

    return `# 聊天记录总结

## 基本信息
- 消息总数: ${messages.length} 条
- 参与人数: ${uniqueSenders.length} 人
- 参与成员: ${uniqueSenders.join(', ')}

## 核心讨论话题
- 日常交流与互动

## 有价值的内容
待分析...

## 参与人员
${uniqueSenders.map(s => `- ${s}`).join('\n')}`;
}

// 保存结果
function saveResult() {
    const content = elements.resultText.textContent;
    if (!content.trim()) {
        showError('没有可保存的内容');
        return;
    }

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_summary_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    updateStatus('结果已保存');
}

// 清空结果
function clearResult() {
    elements.resultText.textContent = '';
    updateStatus('结果已清空');
}

// 更新状态
function updateStatus(message) {
    elements.statusText.textContent = message;
}

// 更新进度
function updateProgress(percent) {
    elements.progressBar.style.width = `${percent}%`;
    elements.progressBar.setAttribute('aria-valuenow', percent);
    elements.progressBar.textContent = `${percent}%`;
}

// 追加结果
function appendResult(text) {
    elements.resultText.textContent += text;
    elements.resultText.scrollTop = elements.resultText.scrollHeight;
}

// 显示错误
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger mt-3';
    alert.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;

    const activeTab = document.querySelector('.tab-pane.active');
    activeTab.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// 初始化应用
init();
