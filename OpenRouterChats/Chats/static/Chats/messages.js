// real time Django messages

// This script displays Django messages in a Bootstrap alert container
// Messages are fetched from the server and shown with appropriate styling

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


function fetchMessagesFromServer() {
  fetch(window.location.origin + '/messages/', { credentials: 'same-origin' })
    .then(res => res.json())
    .then(data => {
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => showMessage(msg.text, msg.tags));
      }
    })
    .catch(err => console.error('Failed to fetch messages:', err));
}


if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', fetchMessagesFromServer);
} else {
  fetchMessagesFromServer();
}
