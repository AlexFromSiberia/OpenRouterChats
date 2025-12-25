// JS for Home page
console.log('home.js script loaded');


debugger

// add teacher - modal
const addTeacherModal = new bootstrap.Modal(document.getElementById('addTeacherModal'));
// Clear chat history - modal
const clearChatModal = new bootstrap.Modal(document.getElementById('clearChatModal'));


let CHAT_HISTORY = [];



// load Teachers and Models
document.addEventListener('DOMContentLoaded', function() {
  get_models();
  get_teachers();
});


// -----------------------------------LLM Models----------------------------------------------

// Save selected model to storage on change
document.getElementById('modelSelect').addEventListener('change', function() {
  localStorage.setItem('selectedModel', this.value);
});


// gets all the available openRouter LLM models
function get_models() {
  // селектор моделей
  const selectEl = document.getElementById('modelSelect');
  // cached models
  const cachedModels = localStorage.getItem('cachedModels');
  // Restore selection from Storage 
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

      // set selected model from cache
      if(cachedSelection){
        selectEl.value = cachedSelection;
      }

      return;

    } catch (e) {
      console.error('Failed to parse cached models', e);
    }
  }else{
    loadModels()
  }


  // Load models from API if no cache
  async function loadModels() {
    try {
      const response = await fetch('models/', { credentials: 'same-origin' });

      if (!response.ok) {
        console.error('Failed to fetch models:', response.status);
        return;
      }
      const { models } = await response.json();
      if (!Array.isArray(models)) {
        console.error('Invalid models format');
        return;
      }
      
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
};



// ----------------------------------- end LLM Models----------------------------------------------


// -----------------------------------Teachers------------------------------------------------------

// Save selected teacher to storage on change
document.getElementById('teacherSelect').addEventListener('change', function() {
  localStorage.setItem('selectedTeacher', this.value);
});


// gets all available teachers
function get_teachers() {
  // cached teachers
  const cachedTeachers = localStorage.getItem('cachedTeachers');
  // If teachers are cached, populate select
  if (cachedTeachers) {
    fillTeachersSelector(cachedTeachers)
  }else{
    loadTeachers()
  }
};


// Load teachers from API if no cache
async function loadTeachers() {
  try {
    const response = await fetch('teachers/', { credentials: 'same-origin' });
    if (!response.ok) {
      console.error('Failed to fetch teachers:', response.status);
      return;
    }

    const { teachers: teacherList } = await response.json();
    if (!Array.isArray(teacherList)) {
      console.error('Invalid teachers format');
      return;
    }
    
    localStorage.setItem('cachedTeachers', JSON.stringify(teacherList));
    fillTeachersSelector(JSON.stringify(teacherList))
  } catch (error) {
    console.error('Failed to load teachers:', error);
  }
}


// Fill teacher selector
function fillTeachersSelector(cachedTeachers) {
  // селектор учителей
  const selectEl = document.getElementById('teacherSelect');
  // Restore selection from Storage 
  const cachedSelection = localStorage.getItem('selectedTeacher');

  try {
    const teachers = JSON.parse(cachedTeachers);
    selectEl.innerHTML = '';
    
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.disabled = true;
    placeholder.selected = !selectEl.value;
    placeholder.textContent = 'Выбрать учителя';
    selectEl.appendChild(placeholder);

    for (const t of teachers) {
      if (!t || typeof t.id === 'undefined') continue;
      const opt = document.createElement('option');
      opt.value = String(t.id);
      opt.textContent = t.name || String(t.id);
      selectEl.appendChild(opt);
    }

    // set selected teacher from cache
    if (cachedSelection){
      selectEl.value = cachedSelection;
    }
    return;

  } catch (e) {
    console.error('Failed to parse cached teachers', e);
  }  
}


// open add teacher modal button
document.getElementById('addNewTeacher').addEventListener('click', function() {
  addTeacherModal.show();
});


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

      if (res.ok) {
        loadTeachers()
      }else {
        console.error('Failed to create new teacher');
      }
      
    } catch (e) {
      console.log(e)
    }
    addTeacherModal.hide();
    fetchMessagesFromServer();
    document.getElementById('addTeacherButton').disabled = false;
  }

  addTeacher()
})

// -----------------------------------end Teachers------------------------------------------------------


// 'Send message' button
document.getElementById('sendMessageButton').addEventListener('click', function (event) {
  if(checkBeforeSend(event) === 0){
    return;
  }
  sendMessage();
})

// 'Send message' button - sends message to server
async function sendMessage() {
  const sendButton = document.getElementById('sendMessageButton');
  const sendButtonText = document.getElementById('sendButtonText');
  const sendButtonLoader = document.getElementById('sendButtonLoader');
  
  // Show loader and disable button
  sendButton.disabled = true;
  sendButtonText.textContent = 'Отправка...';
  sendButtonLoader.classList.remove('d-none');
  
  let data = {
    model: document.getElementById('modelSelect').value,     // localStorage.getItem('selectedModel');
    teacher: document.getElementById('teacherSelect').value, // localStorage.getItem('selectedTeacher');
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
    }else{
      document.getElementById('sendMessageInput').value = ''
      CHAT_HISTORY = payload.chat_history;
    }
  } catch (e) {
    console.log(e)
  }
  fetchMessagesFromServer();
  
  // Hide loader and restore button
  sendButton.disabled = false;
  sendButtonText.textContent = 'Отправить';
  sendButtonLoader.classList.add('d-none');
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


// clear Chat
document.getElementById('clearChatButton').addEventListener('click', function() {
  clearChatModal.show();
});

// clear Chat - Handle confirmation
document.getElementById('confirmClearChat').addEventListener('click', function() {
  CHAT_HISTORY = [];
  fillChatHistory(CHAT_HISTORY);
  clearChatModal.hide();
});



