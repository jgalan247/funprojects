function go(n) {
  const l = document.getElementById('l' + n);
  const wasOpen = l.classList.contains('open');
  document.querySelectorAll('.lesson').forEach(x => x.classList.remove('open'));
  document.querySelectorAll('.pstep').forEach(x => x.classList.remove('active'));
  if (!wasOpen) {
    l.classList.add('open');
    document.querySelectorAll('.pstep')[n - 1].classList.add('active');
    setTimeout(() => l.scrollIntoView({behavior:'smooth', block:'start'}), 60);
  }
}
// Open lesson 1 on load
go(1);