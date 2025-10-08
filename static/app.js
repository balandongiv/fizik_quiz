document.addEventListener('DOMContentLoaded', () => {
  const progress = document.querySelector('.progress');
  if (!progress) {
    return;
  }

  const total = Number(progress.dataset.total || 0);
  const fill = progress.querySelector('.progress-fill');
  const label = progress.querySelector('.progress-label');
  const form = document.querySelector('.quiz form');

  if (!form || !fill || !label || !total) {
    return;
  }

  const updateProgress = () => {
    const answered = new Set();
    const inputs = form.querySelectorAll('input[type="radio"]');
    inputs.forEach((input) => {
      if (input.checked) {
        answered.add(input.name);
      }
    });

    const completed = answered.size;
    const percentage = Math.round((completed / total) * 100);
    fill.style.width = `${percentage}%`;
    label.textContent = `Question ${completed === 0 ? 1 : Math.min(completed + 1, total)} of ${total}`;
  };

  form.addEventListener('change', updateProgress);
  updateProgress();
});
