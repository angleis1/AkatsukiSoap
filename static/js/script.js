// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // ==================== Анимированное переключение темы ====================
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        if (currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.classList.add('active');
        } else {
            themeToggle.classList.remove('active');
            document.body.classList.remove('dark-theme');
        }

        themeToggle.addEventListener('click', function() {
            themeToggle.classList.toggle('active');
            document.body.classList.toggle('dark-theme');
            const newTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme);
        });
    }

    // ==================== Автоскрытие сообщений ====================
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // ==================== Плавный скролл для якорей ====================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // ==================== Анимация фильтров ====================
    const filterCard = document.querySelector('.filter-card');
    if (filterCard) {
        filterCard.style.opacity = '0';
        filterCard.style.transform = 'translateY(20px)';
        setTimeout(() => {
            filterCard.style.transition = 'opacity 0.5s, transform 0.5s';
            filterCard.style.opacity = '1';
            filterCard.style.transform = 'translateY(0)';
        }, 200);
    }

    // ==================== Предпросмотр изображения ====================
    (function() {
        const imageInput = document.getElementById('id_image');
        const imagePreview = document.getElementById('imagePreview');
        const clearImageBtn = document.getElementById('clear-image-btn');

        if (!imageInput || !imagePreview || !clearImageBtn) return;

        const newInput = imageInput.cloneNode(true);
        imageInput.parentNode.replaceChild(newInput, imageInput);

        const newClearBtn = clearImageBtn.cloneNode(true);
        clearImageBtn.parentNode.replaceChild(newClearBtn, clearImageBtn);

        const finalInput = document.getElementById('id_image');
        const finalPreview = document.getElementById('imagePreview');
        const finalClearBtn = document.getElementById('clear-image-btn');

        finalClearBtn.style.display = 'none';

        finalInput.addEventListener('change', function(e) {
            finalPreview.innerHTML = '';
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(ev) {
                    const img = document.createElement('img');
                    img.src = ev.target.result;
                    img.className = 'preview-image';
                    finalPreview.appendChild(img);
                    finalClearBtn.style.display = 'inline-block';
                };
                reader.readAsDataURL(file);
            }
        });

        finalClearBtn.addEventListener('click', function() {
            finalInput.value = '';
            finalPreview.innerHTML = '';
            finalClearBtn.style.display = 'none';
            const errorDiv = finalInput.closest('.mb-3')?.querySelector('.text-danger');
            if (errorDiv) errorDiv.innerHTML = '';
        });
    })();
});


var phoneInput = document.getElementById('phone-input');
if (phoneInput) {
    var mask = IMask(phoneInput, {
        mask: '+{7} (000) 000-00-00',
        lazy: false,
        placeholderChar: '_'
    });
}


document.addEventListener('DOMContentLoaded', function () {
    const carousel = document.getElementById('aboutCarousel');
    if (!carousel) return;

    // Запуск первого видео
    const firstVideo = carousel.querySelector('.carousel-item.active video');
    if (firstVideo) {
        firstVideo.play().catch(e => console.log('play error:', e));
    }

    carousel.addEventListener('slide.bs.carousel', function (event) {
        // Останавливаем видео в текущем активном слайде
        const currentActive = carousel.querySelector('.carousel-item.active');
        if (currentActive) {
            const oldVideo = currentActive.querySelector('video');
            if (oldVideo) {
                oldVideo.pause();
                oldVideo.currentTime = 0;
            }
        }
        // Запускаем видео в новом слайде
        const nextItem = event.relatedTarget;
        if (nextItem) {
            const newVideo = nextItem.querySelector('video');
            if (newVideo) {
                newVideo.play().catch(e => console.log('play error on slide:', e));
            }
        }
    });
});


// Плавный скролл к карусели отзывов
document.querySelector('.all-reviews-link')?.addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('reviewsCarousel').scrollIntoView({ behavior: 'smooth' });
});
