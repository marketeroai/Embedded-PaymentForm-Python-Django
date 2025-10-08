// Countdown Timer
function startCountdown() {
    const targetDate = new Date("2025-10-08T23:59:59-05:00").getTime();

    function updateCountdown() {
        const now = new Date().getTime();
        const difference = targetDate - now;

        if (difference <= 0) {
            document.getElementById('countdown-timer').innerHTML = `
                <div class="time-block">
                    <div class="time-number">0</div>
                    <div class="time-label">Días</div>
                </div>
                <div class="time-block">
                    <div class="time-number">0</div>
                    <div class="time-label">Horas</div>
                </div>
                <div class="time-block">
                    <div class="time-number">0</div>
                    <div class="time-label">Min</div>
                </div>
                <div class="time-block">
                    <div class="time-number">0</div>
                    <div class="time-label">Seg</div>
                </div>
            `;
            return;
        }

        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((difference % (1000 * 60)) / 1000);

        document.querySelectorAll('.time-number')[0].textContent = days;
        document.querySelectorAll('.time-number')[1].textContent = hours;
        document.querySelectorAll('.time-number')[2].textContent = minutes;
        document.querySelectorAll('.time-number')[3].textContent = seconds;
    }

    updateCountdown();
    setInterval(updateCountdown, 1000);
}

// Form Handling
function handleFormSubmit(event) {
    event.preventDefault();

    // Clear previous errors
    document.querySelectorAll('.error').forEach(el => el.textContent = '');

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    let hasErrors = false;

    // Validate name
    if (!data.name.trim()) {
        document.getElementById('name-error').textContent = 'El nombre es requerido';
        hasErrors = true;
    }

    // Validate phone
    const phoneRegex = /^[0-9+\-\s()]{9,20}$/;
    if (!data.phone.trim() || !phoneRegex.test(data.phone.trim())) {
        document.getElementById('phone-error').textContent = 'Ingresa un número válido';
        hasErrors = true;
    }

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!data.email.trim() || !emailRegex.test(data.email.trim())) {
        document.getElementById('email-error').textContent = 'Ingresa un email válido';
        hasErrors = true;
    }

    if (hasErrors) return;

    // Simulate successful submission
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.textContent = 'Enviando...';
    submitBtn.disabled = true;

    setTimeout(() => {
        alert('¡Registro exitoso! 🎉\nTe contactaremos pronto con los detalles de tu inscripción.');
        event.target.reset();
        submitBtn.textContent = 'Inscribirme con 20% de descuento';
        submitBtn.disabled = false;
    }, 1500);
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab panels
    const tabPanels = document.querySelectorAll('.tab-panel');
    tabPanels.forEach(panel => panel.classList.remove('active'));

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => button.classList.remove('active'));

    // Show selected tab panel
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked tab button
    event.target.classList.add('active');
}

// Smooth scroll function
function scrollToForm() {
    const form = document.getElementById('registro');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize countdown
    startCountdown();

    // Form submission
    const form = document.getElementById('registration-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Smooth scrolling for all anchor links
    const links = document.querySelectorAll('a[href^="#"]');

    for (const link of links) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    }

    // Add animation classes when elements come into view
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all animated elements
    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
        observer.observe(el);
    });
});
