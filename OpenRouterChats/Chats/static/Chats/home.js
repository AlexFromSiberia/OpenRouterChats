// JS for Home page


// gets all the available openRouter LLM models
(function () {
  const selectEl = document.getElementById('modelSelect');
  const hiddenInputEl = document.getElementById('selectedModelInput');
  if (!selectEl || !hiddenInputEl) return;

  const modelsUrl = (selectEl.dataset.modelsUrl || '').trim();
  if (!modelsUrl) return;

  // skip the function, if models already hav been loaded
  let modelsLoaded = false;

  async function loadModelsIfNeeded() {
    if (modelsLoaded) return;
    modelsLoaded = true;

    try {
      const res = await fetch(modelsUrl, { credentials: 'same-origin' });
      if (!res.ok) throw new Error('Bad response');
      const payload = await res.json();
      const models = Array.isArray(payload.models) ? payload.models : [];

      selectEl.innerHTML = '';

      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.disabled = true;
      placeholder.selected = true;
      placeholder.textContent = 'Выбрать модель';
      selectEl.appendChild(placeholder);

      for (const m of models) {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        selectEl.appendChild(opt);
      }

      const preselected = (selectEl.dataset.selectedModel || '').trim();
      if (preselected) {
        selectEl.value = preselected;
        hiddenInputEl.value = preselected;
      }
    } catch (e) {
      modelsLoaded = false;
    }
  }

  selectEl.addEventListener('focus', loadModelsIfNeeded);
  selectEl.addEventListener('mousedown', loadModelsIfNeeded);

  selectEl.addEventListener('change', function () {
    hiddenInputEl.value = selectEl.value;
  });
})();


// gets all the available teachers
(function () {
  const selectEl = document.getElementById('teacherSelect');
  const hiddenInputEl = document.getElementById('selectedTeacherInput');
  if (!selectEl || !hiddenInputEl) return;

  const teachersUrl = (selectEl.dataset.teachersUrl || '').trim();
  if (!teachersUrl) return;

  let teachersLoaded = false;

  debugger

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

