const form = document.querySelector('#signup-form');
const message = document.querySelector('#form-message');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
  message.className = 'form-message';

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const button = form.querySelector('button');
  const originalText = button.innerHTML;
  button.disabled = true;
  button.textContent = 'Enviando...';

  try {
    const response = await fetch('/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const result = await response.json();
    message.textContent = result.message;
    message.classList.add(result.success ? 'success' : 'error');
    if (result.success) form.reset();
  } catch {
    message.textContent = 'Não foi possível concluir sua inscrição. Tente novamente.';
    message.classList.add('error');
  } finally {
    button.disabled = false;
    button.innerHTML = originalText;
  }
});
