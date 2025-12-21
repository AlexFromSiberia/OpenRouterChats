// JS for Home page


// При клике "Отправить" проверяем, выбрана ли модель и учителя, если нет - селекторы выделим красным, данные не отправляем
document.getElementById('sendMessageButton').addEventListener('click', function (event) {
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

    return;
  }

  // Пустые сообщения не отправляем
  if(!document.getElementById('sendMessageInput').value.trim()){
    document.getElementById('sendMessageInput').classList.add('is-invalid');
    setTimeout(() => {
      document.getElementById('sendMessageInput').classList.remove('is-invalid');
    }, 3000);
    event.preventDefault();
    return;
  }
});


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

    debugger

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


// Update storage on selection model change
document.getElementById('modelSelect').addEventListener('change', function() {
  document.getElementById('selectedModelInput').value = this.value;
  localStorage.setItem('selectedModel', this.value);
  debugger

});


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


// Auto-scroll chat to bottom on page load
document.addEventListener('DOMContentLoaded', function() {

  setTimeout(() => {
    const chatContainer = document.querySelector('#chat .bg-body');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }  
  }, 500);

});

