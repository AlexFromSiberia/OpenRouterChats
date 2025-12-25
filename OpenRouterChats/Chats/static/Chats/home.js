// JS for Home page




// gets all the available openRouter LLM models
(function () {
  // селектор моделей
  const selectEl = document.getElementById('modelSelect');
  const hiddenInputEl = document.getElementById('selectedModelInput');
  // cached models
  const cachedModels = localStorage.getItem('cachedModels');
  // Restore selection from localStorage or hidden input
  const cachedSelection = localStorage.getItem('selectedModel');
  
  // If models are cached, populate select
  if (cachedModels) {
    try {
      const models = JSON.parse(cachedModels);
      selectEl.innerHTML = '';
      
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.disabled = true;
      placeholder.selected = !selectEl.value;
      placeholder.textContent = 'Выбрать модель';
      selectEl.appendChild(placeholder);
      
      for (const model of models) {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        if (model === selectEl.value) {
          option.selected = true;
        }
        selectEl.appendChild(option);
      }

      if (cachedSelection) {
        hiddenInputEl.value = cachedSelection;
        selectEl.value = cachedSelection;
      }

      return;
    } catch (e) {
      console.error('Failed to parse cached models', e);
    }
  }

  // Load models from API if no cache
  async function loadModels() {

    try {
      const response = await fetch(modelsUrl, { credentials: 'same-origin' });
      if (!response.ok) throw new Error('API request failed');
      
      const { models } = await response.json();
      if (!Array.isArray(models)) throw new Error('Invalid models format');
      
      localStorage.setItem('cachedModels', JSON.stringify(models));
      
      selectEl.innerHTML = '';
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.disabled = true;
      placeholder.selected = !selectEl.value;
      placeholder.textContent = 'Выбрать модель';
      selectEl.appendChild(placeholder);
      
      for (const model of models) {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        if (model === selectEl.value) {
          option.selected = true;
        }
        selectEl.appendChild(option);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  }
  
  if (!cachedModels) {
    loadModels();
  }


})();





// gets all the available teachers
(function () {
  const selectEl = document.getElementById('teacherSelect');
  const hiddenInputEl = document.getElementById('selectedTeacherInput');
  if (!selectEl || !hiddenInputEl) return;

  const teachersUrl = (selectEl.dataset.teachersUrl || '').trim();
  if (!teachersUrl) return;

  let teachersLoaded = false;

  function setPlaceholderSelected(selectEl) {
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.disabled = true;
    placeholder.selected = true;
    placeholder.textContent = 'Выбрать учителя';
    selectEl.appendChild(placeholder);
  }

  async function loadTeachersIfNeeded() {
    if (teachersLoaded) return;
    teachersLoaded = true;

    try {
      const res = await fetch(teachersUrl, { credentials: 'same-origin' });
      if (!res.ok) throw new Error('Bad response');
      const payload = await res.json();
      const teachers = Array.isArray(payload.teachers) ? payload.teachers : [];

      selectEl.innerHTML = '';
      setPlaceholderSelected(selectEl);

      for (const t of teachers) {
        if (!t || typeof t.id === 'undefined') continue;
        const opt = document.createElement('option');
        opt.value = String(t.id);
        opt.textContent = t.name || String(t.id);
        selectEl.appendChild(opt);
      }

      const preselected = (selectEl.dataset.selectedTeacher || '').trim() || (hiddenInputEl.value || '').trim();
      if (preselected) {
        selectEl.value = preselected;
        hiddenInputEl.value = preselected;
      }
    } catch (e) {
      console.log(e)
      teachersLoaded = false;
    }
  }

  selectEl.addEventListener('focus', loadTeachersIfNeeded);
  selectEl.addEventListener('mousedown', loadTeachersIfNeeded);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadTeachersIfNeeded);
  } else {
    loadTeachersIfNeeded();
  }

  selectEl.addEventListener('change', function () {
    hiddenInputEl.value = selectEl.value;
  });
})();


// 
document.addEventListener('DOMContentLoaded', function() {





});


// --------------------- NEW CODE ---------------------


let CHAT_HISTORY = [];


// 'Send message' button
document.getElementById('sendMessageButton').addEventListener('click', function (event) {
  if(checkBeforeSend(event) === 0){
    return;
  }
  sendMessage();
})

// 'Send message' button - sends message to server
async function sendMessage() {
  document.getElementById('sendMessageButton').disabled = true;
  let data = {
    model: document.getElementById('selectedModelInput').value,
    teacher: document.getElementById('selectedTeacherInput').value,
    message: document.getElementById('sendMessageInput').value,
    chat_history: CHAT_HISTORY,
  }

  try {
    const res = await fetch('send/', 
      { credentials: 'same-origin', 
        method: 'POST', 
        body: JSON.stringify(data), 
        headers: { 'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value } 
      }
    );

    const payload = await res.json();

    if (!res.ok) {
      console.log(payload.error)
      fetchMessagesFromServer();
    }else{
      document.getElementById('sendMessageInput').value = ''
      CHAT_HISTORY = payload.chat_history;
      fillChatHistory(payload.chat_history)
      fetchMessagesFromServer();
    }
  } catch (e) {
    console.log(e)
  }
  document.getElementById('sendMessageButton').disabled = false;
}


// real-time Django messages 
function fetchMessagesFromServer() {
  fetch('messages/', { credentials: 'same-origin' })
    .then(res => res.json())
    .then(data => {
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => {
          if (typeof showMessage === 'function') {
            showMessage(msg.text, msg.tags);
          }
        });
      }
    })
    .catch(err => console.error('Failed to fetch messages:', err));
}


// При клике "Отправить" проверяем, выбрана ли модель и учителя, если нет - селекторы выделим красным, данные не отправляем
function checkBeforeSend(event){
  const selectmodel = document.getElementById('modelSelect');
  const selectteacher = document.getElementById('teacherSelect');

  if (!selectmodel.value || !selectteacher.value) {
    event.preventDefault();
    selectmodel.classList.add('is-invalid');
    selectteacher.classList.add('is-invalid');

    setTimeout(() => {
      selectmodel.classList.remove('is-invalid');
      selectteacher.classList.remove('is-invalid');
    }, 3000);

    return 0;
  }

  // Пустые сообщения не отправляем
  if(!document.getElementById('sendMessageInput').value.trim()){
    document.getElementById('sendMessageInput').classList.add('is-invalid');
    setTimeout(() => {
      document.getElementById('sendMessageInput').classList.remove('is-invalid');
    }, 3000);
    event.preventDefault();
    return 0;
  }
}


// Update storage on selection model change
document.getElementById('modelSelect').addEventListener('change', function() {
  document.getElementById('selectedModelInput').value = this.value;
  localStorage.setItem('selectedModel', this.value);
});



// fill chat history
function fillChatHistory(payload){
  const chatEl = document.getElementById('chat');
  chatEl.innerHTML = '';
    
  if(payload.length === 0){
    chatEl.innerHTML = '<div class="text-secondary small">Напиши сообщение, чтобы начать чат.</div>';
    return;
  }else{
    for (const msg of payload){
      const div = document.createElement('div');
      div.classList.add('d-flex', 'mb-2')
      if (msg.role === 'user'){
        div.classList.add('justify-content-end');
      }else{
        div.classList.add('justify-content-start');
      }
      div.innerHTML = `<div class="px-3 py-2 rounded-3 ${msg.role == 'user'?'bg-primary':'bg-secondary' } text-white" style="max-width: 80%; white-space: pre-wrap;">${msg.content}</div>`;
      chatEl.appendChild(div);
    }

    // scroll chat to bottom
    const chatContainer = document.querySelector('#chat_scroller .bg-body');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }
}




// Clear chat history - modal
const clearChatModal = new bootstrap.Modal(document.getElementById('clearChatModal'));

// clearChatButton
document.getElementById('clearChatButton').addEventListener('click', function() {
  clearChatModal.show();
});

// Handle confirmation
document.getElementById('confirmClearChat').addEventListener('click', function() {
  CHAT_HISTORY = [];
  fillChatHistory(CHAT_HISTORY);
  clearChatModal.hide();
});



//------------------------real-time Django messages-----------------------------
function showMessage(text, tags) {
  const container = document.getElementById('messages-container');
  const alertDiv = document.createElement('div');
  const alertClass = tags === 'error' ? 'alert-danger' : tags ? `alert-${tags}` : 'alert-secondary';
  
  alertDiv.className = `alert ${alertClass} py-2 alert-dismissible fade show d-flex justify-content-between align-items-center`;
  alertDiv.setAttribute('role', 'alert');
  alertDiv.innerHTML = `
    <span>${text}</span>
    <button type="button" class="btn-close" aria-label="Close"></button>
  `;
  
  container.appendChild(alertDiv);
  
  const closeBtn = alertDiv.querySelector('.btn-close');
  closeBtn.addEventListener('click', function() {
    alertDiv.classList.remove('show');
    setTimeout(() => alertDiv.remove(), 150);
  });
  
  setTimeout(() => {
    alertDiv.classList.remove('show');
    setTimeout(() => alertDiv.remove(), 150);
  }, 6000);
}

function fetchMessages() {
  fetch('messages/', { credentials: 'same-origin' })
    .then(res => res.json())
    .then(data => {
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => showMessage(msg.text, msg.tags));
      }
    })
    .catch(err => console.error('Failed to fetch messages:', err));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', fetchMessages);
} else {
  fetchMessages();
}

//------------------------END real-time Django messages-----------------------------




// Teacher creation
document.getElementById('addTeacherButton').addEventListener('click', function (event) {
  async function addTeacher() {
    document.getElementById('addTeacherButton').disabled = true;
    let data = {
      name: document.getElementById('teacherName').value,
      prompt: document.getElementById('teacherPrompt').value,
    }

    try {
      const res = await fetch('teachers/create/', 
        { credentials: 'same-origin', 
          method: 'POST', 
          body: JSON.stringify(data), 
          headers: { 'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value } 
        }
      );

      const payload = await res.json();

      if (!res.ok) {
        console.log(payload.error)
      }else{
        console.log(payload)
        fillTeacersSelector(payload.teachers)
      }
      
    } catch (e) {
      console.log(e)
    }

    fetchMessagesFromServer();
    document.getElementById('addTeacherButton').disabled = false;
  }

  addTeacher()

})



function fillTeacersSelector(teachers){
  const selectEl = document.getElementById('teacherSelect');

  for (const teacher of teachers){
    const option = document.createElement('option');
    option.value = teacher.id;
    option.textContent = teacher.name;
    selectEl.appendChild(option);
  }

}