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

