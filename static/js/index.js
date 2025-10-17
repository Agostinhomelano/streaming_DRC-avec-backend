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
document.addEventListener('DOMContentLoaded', function() {
    const items = document.querySelectorAll('.carousel-netflix-item');
    const prevBtn = document.querySelector('.carousel-netflix-btn.prev');
    const nextBtn = document.querySelector('.carousel-netflix-btn.next');
    let current = 0;

    function getVisibleCount() {
        if(window.innerWidth <= 768) return 1; // mobile
        if(window.innerWidth <= 1024) return 2; // tablette
        return 5; // pc
    }

    function updateCarousel() {
        let visible = getVisibleCount();
        items.forEach((item, i) => {
            item.classList.remove('active', 'visible');
            item.style.display = 'none';
        });
        for (let i = 0; i < visible; i++) {
            let idx = (current + i) % items.length;
            items[idx].classList.add('visible');
            items[idx].style.display = 'block';
        }
        // Met en avant l'image du milieu (ou la seule sur mobile)
        let activeIdx = (current + Math.floor(visible/2)) % items.length;
        items[activeIdx].classList.add('active');
    }

    function resizeHandler() {
        updateCarousel();
    }

    if (prevBtn && nextBtn && items.length > 0) {
        prevBtn.addEventListener('click', function() {
            current = (current - 1 + items.length) % items.length;
            updateCarousel();
        });

        nextBtn.addEventListener('click', function() {
            current = (current + 1) % items.length;
            updateCarousel();
        });

        setInterval(function() {
            current = (current + 1) % items.length;
            updateCarousel();
        }, 5000);

        window.addEventListener('resize', resizeHandler);

        updateCarousel();
    }
});