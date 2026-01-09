/**
 * Tests for home.js
 * Testing localStorage, DOM manipulation, and Bootstrap integration
 */

beforeEach(() => {
  document.body.innerHTML = '';
  localStorage.clear();
  jest.clearAllMocks();
  global.fetch = jest.fn();
  document.cookie = '';
});

describe('getCSRFToken', () => {
  let getCSRFToken;

  beforeAll(() => {
    const code = `
      function getCSRFToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
      }
      return getCSRFToken;
    `;
    getCSRFToken = new Function(code)();
  });

  test('should extract CSRF token from cookie', () => {
    document.cookie = 'csrftoken=abc123def456';
    const token = getCSRFToken();
    expect(token).toBe('abc123def456');
  });

  test('should return empty string when no CSRF token exists', () => {
    document.cookie = '';
    const token = getCSRFToken();
    expect(token).toBe('');
  });

  test('should decode URI encoded CSRF token', () => {
    document.cookie = 'csrftoken=abc%20123';
    const token = getCSRFToken();
    expect(token).toBe('abc 123');
  });

  test('should extract CSRF token from multiple cookies', () => {
    document.cookie = 'sessionid=xyz789; csrftoken=token123; other=value';
    const token = getCSRFToken();
    expect(token).toBe('token123');
  });

  test('should handle special characters in CSRF token', () => {
    const specialToken = 'abc-123_DEF.456';
    document.cookie = `csrftoken=${specialToken}`;
    const token = getCSRFToken();
    expect(token).toBe(specialToken);
  });
});

describe('getChatHistory', () => {
  let getChatHistory;

  beforeAll(() => {
    const code = `
      function getChatHistory() {
        return JSON.parse(localStorage.getItem('chatHistory')) || [];
      }
      return getChatHistory;
    `;
    getChatHistory = new Function(code)();
  });

  test('should return empty array when no chat history exists', () => {
    const history = getChatHistory();
    expect(history).toEqual([]);
  });

  test('should return parsed chat history from localStorage', () => {
    const mockHistory = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' }
    ];
    localStorage.setItem('chatHistory', JSON.stringify(mockHistory));
    
    const history = getChatHistory();
    expect(history).toEqual(mockHistory);
  });

  test('should handle empty chat history array', () => {
    localStorage.setItem('chatHistory', JSON.stringify([]));
    const history = getChatHistory();
    expect(history).toEqual([]);
  });

  test('should return empty array for null localStorage value', () => {
    localStorage.setItem('chatHistory', null);
    const history = getChatHistory();
    expect(history).toEqual([]);
  });
});

describe('saveChatHistory', () => {
  let saveChatHistory;

  beforeAll(() => {
    const code = `
      function saveChatHistory(history) {
        localStorage.setItem('chatHistory', JSON.stringify(history));
      }
      return saveChatHistory;
    `;
    saveChatHistory = new Function(code)();
  });

  test('should save chat history to localStorage', () => {
    const mockHistory = [
      { role: 'user', content: 'Test message' },
      { role: 'assistant', content: 'Test response' }
    ];
    
    saveChatHistory(mockHistory);
    
    const saved = localStorage.getItem('chatHistory');
    expect(JSON.parse(saved)).toEqual(mockHistory);
  });

  test('should save empty array to localStorage', () => {
    saveChatHistory([]);
    
    const saved = localStorage.getItem('chatHistory');
    expect(JSON.parse(saved)).toEqual([]);
  });

  test('should overwrite existing chat history', () => {
    localStorage.setItem('chatHistory', JSON.stringify([{ role: 'old', content: 'old' }]));
    
    const newHistory = [{ role: 'user', content: 'new' }];
    saveChatHistory(newHistory);
    
    const saved = localStorage.getItem('chatHistory');
    expect(JSON.parse(saved)).toEqual(newHistory);
  });

  test('should handle multiple messages in history', () => {
    const longHistory = Array.from({ length: 10 }, (_, i) => ({
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i}`
    }));
    
    saveChatHistory(longHistory);
    
    const saved = localStorage.getItem('chatHistory');
    expect(JSON.parse(saved)).toEqual(longHistory);
  });
});

describe('fillChatHistory', () => {
  let fillChatHistory;

  beforeAll(() => {
    const code = `
      function fillChatHistory(payload){
        const chatEl = document.getElementById('chat');
        chatEl.innerHTML = '';
          
        if(payload.length === 0){
          chatEl.innerHTML = '<div class="text-secondary small">Нет сообщений...</div>';
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
            div.innerHTML = \`<div class="px-3 py-2 rounded-3 \${msg.role == 'user'?'bg-primary':'bg-secondary' } text-white chat-bubble">\${msg.content}</div>\`;
            chatEl.appendChild(div);
          }

          const chatContainer = document.querySelector('#chat_scroller .bg-body');
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        }
      }
      return fillChatHistory;
    `;
    fillChatHistory = new Function(code)();
  });

  beforeEach(() => {
    document.body.innerHTML = `
      <div id="chat"></div>
      <div id="chat_scroller">
        <div class="bg-body"></div>
      </div>
    `;
  });

  test('should display "no messages" text when history is empty', () => {
    fillChatHistory([]);
    
    const chatEl = document.getElementById('chat');
    expect(chatEl.innerHTML).toContain('Нет сообщений...');
    expect(chatEl.querySelector('.text-secondary')).toBeTruthy();
  });

  test('should render user messages with correct styling', () => {
    const history = [{ role: 'user', content: 'Hello!' }];
    fillChatHistory(history);
    
    const chatEl = document.getElementById('chat');
    const messageDiv = chatEl.querySelector('.d-flex');
    
    expect(messageDiv).toBeTruthy();
    expect(messageDiv.classList.contains('justify-content-end')).toBe(true);
    expect(messageDiv.innerHTML).toContain('bg-primary');
    expect(messageDiv.innerHTML).toContain('Hello!');
  });

  test('should render assistant messages with correct styling', () => {
    const history = [{ role: 'assistant', content: 'Hi there!' }];
    fillChatHistory(history);
    
    const chatEl = document.getElementById('chat');
    const messageDiv = chatEl.querySelector('.d-flex');
    
    expect(messageDiv).toBeTruthy();
    expect(messageDiv.classList.contains('justify-content-start')).toBe(true);
    expect(messageDiv.innerHTML).toContain('bg-secondary');
    expect(messageDiv.innerHTML).toContain('Hi there!');
  });

  test('should render multiple messages in correct order', () => {
    const history = [
      { role: 'user', content: 'First' },
      { role: 'assistant', content: 'Second' },
      { role: 'user', content: 'Third' }
    ];
    fillChatHistory(history);
    
    const chatEl = document.getElementById('chat');
    const messages = chatEl.querySelectorAll('.d-flex');
    
    expect(messages.length).toBe(3);
    expect(messages[0].innerHTML).toContain('First');
    expect(messages[1].innerHTML).toContain('Second');
    expect(messages[2].innerHTML).toContain('Third');
  });

  test('should clear previous messages before rendering', () => {
    document.getElementById('chat').innerHTML = '<div>Old content</div>';
    
    const history = [{ role: 'user', content: 'New message' }];
    fillChatHistory(history);
    
    const chatEl = document.getElementById('chat');
    expect(chatEl.innerHTML).not.toContain('Old content');
    expect(chatEl.innerHTML).toContain('New message');
  });

  test('should handle messages with special HTML characters', () => {
    const history = [{ role: 'user', content: '<script>alert("test")</script>' }];
    fillChatHistory(history);
    
    const chatEl = document.getElementById('chat');
    expect(chatEl.innerHTML).toContain('&lt;script&gt;');
  });

  test('should scroll chat container to bottom', () => {
    const chatContainer = document.querySelector('#chat_scroller .bg-body');
    chatContainer.scrollHeight = 1000;
    chatContainer.scrollTop = 0;
    
    const history = [{ role: 'user', content: 'Test' }];
    fillChatHistory(history);
    
    expect(chatContainer.scrollTop).toBe(1000);
  });
});

describe('fillModelsSelector', () => {
  let fillModelsSelector;

  beforeAll(() => {
    const code = `
      function fillModelsSelector(cachedModels){
        const selectEl = document.getElementById('modelSelect');
        const cachedSelection = localStorage.getItem('selectedModel');  

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

          if(cachedSelection){
            selectEl.value = cachedSelection;
          }
        } catch (e) {
          console.error('Failed to parse cached models', e);
        }
      }
      return fillModelsSelector;
    `;
    fillModelsSelector = new Function(code)();
  });

  beforeEach(() => {
    document.body.innerHTML = '<select id="modelSelect"></select>';
  });

  test('should populate select with models', () => {
    const models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3'];
    fillModelsSelector(JSON.stringify(models));
    
    const selectEl = document.getElementById('modelSelect');
    const options = selectEl.querySelectorAll('option');
    
    expect(options.length).toBe(4);
    expect(options[0].textContent).toBe('Выбрать модель');
    expect(options[1].value).toBe('gpt-4');
    expect(options[2].value).toBe('gpt-3.5-turbo');
    expect(options[3].value).toBe('claude-3');
  });

  test('should add placeholder option', () => {
    const models = ['model1'];
    fillModelsSelector(JSON.stringify(models));
    
    const selectEl = document.getElementById('modelSelect');
    const placeholder = selectEl.options[0];
    
    expect(placeholder.value).toBe('');
    expect(placeholder.disabled).toBe(true);
    expect(placeholder.textContent).toBe('Выбрать модель');
  });

  test('should restore selected model from localStorage', () => {
    localStorage.setItem('selectedModel', 'gpt-4');
    const models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3'];
    
    fillModelsSelector(JSON.stringify(models));
    
    const selectEl = document.getElementById('modelSelect');
    expect(selectEl.value).toBe('gpt-4');
  });

  test('should clear existing options before populating', () => {
    const selectEl = document.getElementById('modelSelect');
    selectEl.innerHTML = '<option>Old option</option>';
    
    const models = ['new-model'];
    fillModelsSelector(JSON.stringify(models));
    
    expect(selectEl.innerHTML).not.toContain('Old option');
  });

  test('should handle empty models array', () => {
    const models = [];
    fillModelsSelector(JSON.stringify(models));
    
    const selectEl = document.getElementById('modelSelect');
    const options = selectEl.querySelectorAll('option');
    
    expect(options.length).toBe(1);
    expect(options[0].textContent).toBe('Выбрать модель');
  });

  test('should handle invalid JSON gracefully', () => {
    console.error = jest.fn();
    
    fillModelsSelector('invalid json');
    
    expect(console.error).toHaveBeenCalledWith(
      'Failed to parse cached models',
      expect.any(Error)
    );
  });

  test('should not restore selection when no cached selection exists', () => {
    const models = ['model1', 'model2'];
    fillModelsSelector(JSON.stringify(models));
    
    const selectEl = document.getElementById('modelSelect');
    expect(selectEl.value).toBe('');
  });
});

describe('fillTeachersSelector', () => {
  let fillTeachersSelector;

  beforeAll(() => {
    const code = `
      function fillTeachersSelector(cachedTeachers) {
        const selectEl = document.getElementById('teacherSelect');
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

          if (cachedSelection){
            selectEl.value = cachedSelection;
          }
          return;

        } catch (e) {
          console.error('Failed to parse cached teachers', e);
        }  
      }
      return fillTeachersSelector;
    `;
    fillTeachersSelector = new Function(code)();
  });

  beforeEach(() => {
    document.body.innerHTML = '<select id="teacherSelect"></select>';
  });

  test('should populate select with teachers', () => {
    const teachers = [
      { id: 1, name: 'Teacher One' },
      { id: 2, name: 'Teacher Two' }
    ];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const options = selectEl.querySelectorAll('option');
    
    expect(options.length).toBe(3);
    expect(options[1].value).toBe('1');
    expect(options[1].textContent).toBe('Teacher One');
    expect(options[2].value).toBe('2');
    expect(options[2].textContent).toBe('Teacher Two');
  });

  test('should add placeholder option', () => {
    const teachers = [{ id: 1, name: 'Test' }];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const placeholder = selectEl.options[0];
    
    expect(placeholder.value).toBe('');
    expect(placeholder.disabled).toBe(true);
    expect(placeholder.textContent).toBe('Выбрать учителя');
  });

  test('should restore selected teacher from localStorage', () => {
    localStorage.setItem('selectedTeacher', '2');
    const teachers = [
      { id: 1, name: 'Teacher One' },
      { id: 2, name: 'Teacher Two' }
    ];
    
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    expect(selectEl.value).toBe('2');
  });

  test('should skip teachers without id', () => {
    const teachers = [
      { id: 1, name: 'Valid' },
      { name: 'No ID' },
      null,
      { id: 2, name: 'Also Valid' }
    ];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const options = selectEl.querySelectorAll('option');
    
    expect(options.length).toBe(3);
  });

  test('should use id as text when name is missing', () => {
    const teachers = [{ id: 42 }];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const option = selectEl.options[1];
    
    expect(option.value).toBe('42');
    expect(option.textContent).toBe('42');
  });

  test('should handle empty teachers array', () => {
    const teachers = [];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const options = selectEl.querySelectorAll('option');
    
    expect(options.length).toBe(1);
    expect(options[0].textContent).toBe('Выбрать учителя');
  });

  test('should handle invalid JSON gracefully', () => {
    console.error = jest.fn();
    
    fillTeachersSelector('invalid json');
    
    expect(console.error).toHaveBeenCalledWith(
      'Failed to parse cached teachers',
      expect.any(Error)
    );
  });

  test('should convert numeric id to string', () => {
    const teachers = [{ id: 123, name: 'Test Teacher' }];
    fillTeachersSelector(JSON.stringify(teachers));
    
    const selectEl = document.getElementById('teacherSelect');
    const option = selectEl.options[1];
    
    expect(typeof option.value).toBe('string');
    expect(option.value).toBe('123');
  });
});

describe('checkBeforeSend', () => {
  let checkBeforeSend;

  beforeAll(() => {
    const code = `
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

        if(!document.getElementById('sendMessageInput').value.trim()){
          document.getElementById('sendMessageInput').classList.add('is-invalid');
          setTimeout(() => {
            document.getElementById('sendMessageInput').classList.remove('is-invalid');
          }, 3000);
          event.preventDefault();
          return 0;
        }
      }
      return checkBeforeSend;
    `;
    checkBeforeSend = new Function(code)();
  });

  beforeEach(() => {
    document.body.innerHTML = `
      <select id="modelSelect"><option value="">Select</option></select>
      <select id="teacherSelect"><option value="">Select</option></select>
      <input id="sendMessageInput" type="text" />
    `;
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should return 0 when model is not selected', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = 'Test message';
    
    const result = checkBeforeSend(event);
    
    expect(result).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  test('should return 0 when teacher is not selected', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('sendMessageInput').value = 'Test message';
    
    const result = checkBeforeSend(event);
    
    expect(result).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  test('should return 0 when message is empty', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = '';
    
    const result = checkBeforeSend(event);
    
    expect(result).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  test('should return 0 when message contains only whitespace', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = '   ';
    
    const result = checkBeforeSend(event);
    
    expect(result).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  test('should not return 0 when all fields are valid', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = 'Valid message';
    
    const result = checkBeforeSend(event);
    
    expect(result).toBeUndefined();
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  test('should add is-invalid class to model and teacher selects when empty', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('sendMessageInput').value = 'Message';
    
    checkBeforeSend(event);
    
    const modelSelect = document.getElementById('modelSelect');
    const teacherSelect = document.getElementById('teacherSelect');
    
    expect(modelSelect.classList.contains('is-invalid')).toBe(true);
    expect(teacherSelect.classList.contains('is-invalid')).toBe(true);
  });

  test('should remove is-invalid class after 3 seconds for selects', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('sendMessageInput').value = 'Message';
    
    checkBeforeSend(event);
    
    const modelSelect = document.getElementById('modelSelect');
    const teacherSelect = document.getElementById('teacherSelect');
    
    expect(modelSelect.classList.contains('is-invalid')).toBe(true);
    
    jest.advanceTimersByTime(3000);
    
    expect(modelSelect.classList.contains('is-invalid')).toBe(false);
    expect(teacherSelect.classList.contains('is-invalid')).toBe(false);
  });

  test('should add is-invalid class to message input when empty', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = '';
    
    checkBeforeSend(event);
    
    const messageInput = document.getElementById('sendMessageInput');
    expect(messageInput.classList.contains('is-invalid')).toBe(true);
  });

  test('should remove is-invalid class after 3 seconds for message input', () => {
    const event = { preventDefault: jest.fn() };
    document.getElementById('modelSelect').value = 'gpt-4';
    document.getElementById('teacherSelect').value = '1';
    document.getElementById('sendMessageInput').value = '';
    
    checkBeforeSend(event);
    
    const messageInput = document.getElementById('sendMessageInput');
    expect(messageInput.classList.contains('is-invalid')).toBe(true);
    
    jest.advanceTimersByTime(3000);
    
    expect(messageInput.classList.contains('is-invalid')).toBe(false);
  });

  test('should call preventDefault when validation fails', () => {
    const event = { preventDefault: jest.fn() };
    
    checkBeforeSend(event);
    
    expect(event.preventDefault).toHaveBeenCalled();
  });

  test('should handle mixed validation failures', () => {
    const event = { preventDefault: jest.fn() };
    
    const result = checkBeforeSend(event);
    
    expect(result).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
    
    const modelSelect = document.getElementById('modelSelect');
    const teacherSelect = document.getElementById('teacherSelect');
    
    expect(modelSelect.classList.contains('is-invalid')).toBe(true);
    expect(teacherSelect.classList.contains('is-invalid')).toBe(true);
  });
});
