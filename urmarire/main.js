/* /assets/js/main.js */
(function() {
  'use strict';

  /**
   * Active navigation link highlighting on scroll
   */
  const navLinks = document.querySelectorAll('nav a[href^="#"]');
  const sections = Array.from(document.querySelectorAll('section[id]'));

  if (navLinks.length > 0 && sections.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const id = entry.target.getAttribute('id');
        const link = document.querySelector('nav a[href="#' + id + '"]');
        if (link) {
          if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        }
      });
    }, { rootMargin: '-40% 0px -50% 0px', threshold: 0.3 });

    sections.forEach(s => observer.observe(s));
  }

  /**
   * Price Calculator Logic
   */
  const calcForm = document.getElementById('calc-form');
  const calcOut = document.getElementById('calc-out');

  function calculatePrice() {
    if (!calcForm || !calcOut) return;

    const tip = calcForm.querySelector('[name="tip"]').value;
    const sup = parseFloat(calcForm.querySelector('[name="sup"]').value || '0');
    const instrEl = calcForm.querySelector('[name="instr"]');
    const instr = instrEl ? instrEl.checked : false;

    let baseLei = 0;
    if (tip === 'bloc') baseLei = 3990;
    else if (tip === 'casa') baseLei = 2990;
    else if (tip === 'hala') baseLei = 5490;
    else if (tip === 'birouri') baseLei = 4490;

    const supFactor = Math.ceil(sup / 100) * 0.15;
    let total = Math.round(baseLei * (1 + supFactor));
    if (instr) {
      total += 1500; // Base instrumentation fee
    }

    const formattedTotal = new Intl.NumberFormat('ro-RO').format(total);
    calcOut.innerHTML = `
      <div class="card">
        <strong>Estimare:</strong><br>
        <span style="font-size: 2rem; font-weight: 700;">~ ${formattedTotal} lei/an</span><br>
        <small>+ TVA. Include 1 vizită & raport</small>
      </div>`;
  }

  if (calcForm) {
    calcForm.addEventListener('input', calculatePrice);
    calculatePrice(); // Initial calculation
  }

  /**
   * Mailto Contact Form Logic
   */
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const data = new FormData(contactForm);
      const nume = data.get('nume') || '';
      const email = data.get('email') || '';
      const tel = data.get('telefon') || '';
      const sub = (data.get('subiect') || 'Solicitare UCE') + ' – ' + nume;
      const msg = data.get('mesaj') || '';
      const body = `Nume: ${nume}%0AEmail: ${email}%0ATelefon: ${tel}%0A%0AMesaj:%0A${encodeURIComponent(msg)}`;

      window.location.href = `mailto:contact@urmarire-constructii.ro?subject=${encodeURIComponent(sub)}&body=${body}`;

      const formStatus = document.getElementById('form-status');
      if (formStatus) {
        formStatus.textContent = 'S-a deschis clientul de e-mail pentru trimitere. Vă mulțumim!';
      }
    });
  }

})();
