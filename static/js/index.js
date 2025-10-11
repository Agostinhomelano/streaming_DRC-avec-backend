document.getElementById('burgerBtn').onclick = function() {
  document.getElementById('menuNav').classList.toggle('open');
};
document.addEventListener('click', function(e) {
  const menu = document.getElementById('menuNav');
  const burger = document.getElementById('burgerBtn');
  if (!menu.contains(e.target) && !burger.contains(e.target)) {
    menu.classList.remove('open');
  }
});