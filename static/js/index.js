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
function openModal() {
      document.getElementById("overlay").style.display = "flex";
    }

    function closeModal() {
      document.getElementById("overlay").style.display = "none";
    }

    function nextPage(pageNumber) {
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.getElementById("page" + pageNumber).classList.add("active");
    }

    function prevPage(pageNumber) {
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.getElementById("page" + pageNumber).classList.add("active");
    }