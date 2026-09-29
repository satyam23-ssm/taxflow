/* ========================================
   TaxFlow AI — Landing Page Scripts
   ======================================== */

document.addEventListener('DOMContentLoaded', () => {
  /* ── Navbar Scroll Effect ────────────── */
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  /* ── Mobile Menu ─────────────────────── */
  const mobileToggle = document.getElementById('mobileToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileMenuClose = document.getElementById('mobileMenuClose');

  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      mobileMenu.classList.add('open');
      document.body.style.overflow = 'hidden';
    });

    mobileMenuClose.addEventListener('click', () => {
      closeMobileMenu();
    });
  }

  /* ── Smooth Scroll for Links ─────────── */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        const offsetTop = targetElement.getBoundingClientRect().top + window.pageYOffset;
        window.scrollTo({
          top: offsetTop - 80, // Adjust for navbar height
          behavior: 'smooth'
        });
      }
    });
  });

  /* ── Scroll Reveal Animation ─────────── */
  const revealElements = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target); // Trigger once
      }
    });
  }, {
    root: null,
    threshold: 0.15,
    rootMargin: "0px 0px -50px 0px"
  });

  revealElements.forEach(el => revealObserver.observe(el));

  /* ── Pricing Toggle ──────────────────── */
  const pricingToggle = document.getElementById('pricingToggle');
  const monthlyLabel = document.getElementById('monthlyLabel');
  const annualLabel = document.getElementById('annualLabel');
  const pricingAmounts = document.querySelectorAll('.pricing-amount[data-monthly]');

  if (pricingToggle) {
    pricingToggle.addEventListener('click', () => {
      const isAnnual = pricingToggle.classList.toggle('active');
      
      if (isAnnual) {
        annualLabel.classList.add('active');
        monthlyLabel.classList.remove('active');
      } else {
        monthlyLabel.classList.add('active');
        annualLabel.classList.remove('active');
      }

      pricingAmounts.forEach(el => {
        const value = isAnnual ? el.getAttribute('data-annual') : el.getAttribute('data-monthly');
        
        // Simple counter animation for price change
        animateValue(el, parseInt(el.textContent.replace(/,/g, '')), parseInt(value), 300);
      });
    });
  }

  /* ── Hero Mini Chart Simulation ──────── */
  const heroChart = document.getElementById('heroChart');
  if (heroChart) {
    // Create 12 bars
    for (let i = 0; i < 12; i++) {
      const bar = document.createElement('div');
      bar.className = 'bar';
      // Initial random height
      bar.style.height = `${Math.random() * 80 + 20}%`;
      heroChart.appendChild(bar);
    }

    // Periodically update heights for dynamic effect
    setInterval(() => {
      const bars = heroChart.querySelectorAll('.bar');
      bars.forEach(bar => {
        bar.style.height = `${Math.random() * 80 + 20}%`;
      });
    }, 2000);
  }

  /* ── Counter Animation for Stats ─────── */
  const counterElements = document.querySelectorAll('.hero-stat-value[data-count]');
  let countersAnimated = false;

  const counterObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !countersAnimated) {
      countersAnimated = true;
      counterElements.forEach(el => {
        const target = parseInt(el.getAttribute('data-count'));
        const isRupee = el.textContent.includes('₹');
        const isPercentage = el.textContent.includes('%');
        const isLakh = el.textContent.includes('L');
        const isPlus = el.textContent.includes('+');
        
        animateCounter(el, 0, target, 1500, isRupee, isPercentage, isLakh, isPlus);
      });
    }
  });

  if (counterElements.length > 0) {
    counterObserver.observe(counterElements[0]);
  }

  /* ── ROI Calculator Logic ────────────── */
  const clientSlider = document.getElementById('clientSlider');
  const turnoverSlider = document.getElementById('turnoverSlider');
  
  if (clientSlider && turnoverSlider) {
    const clientCountDisplay = document.getElementById('clientCount');
    const turnoverValueDisplay = document.getElementById('turnoverValue');
    
    const calcItcAtRisk = document.getElementById('calcItcAtRisk');
    const calcRecoverable = document.getElementById('calcRecoverable');
    const calcRoi = document.getElementById('calcRoi');

    const updateCalculator = () => {
      const clients = parseInt(clientSlider.value);
      const turnoverLakhs = parseInt(turnoverSlider.value);
      
      // UI Updates
      clientCountDisplay.textContent = clients;
      turnoverValueDisplay.textContent = `₹${turnoverLakhs}L`;

      // Business Logic / Formulas (Approximations for demo)
      // Assume 5% of turnover is ITC, and 1% of that is at risk (mismatched/missing)
      const avgMonthlyItc = turnoverLakhs * 0.05; 
      const monthlyAtRisk = avgMonthlyItc * 0.01;
      
      // Total annual at risk across all clients
      const annualAtRiskLakhs = (monthlyAtRisk * 12 * clients).toFixed(2);
      
      // Assume TaxFlow recovers 85% of at-risk ITC
      const annualRecoverableLakhs = (annualAtRiskLakhs * 0.85).toFixed(2);

      // Annual cost of TaxFlow (CA Firm Suite base)
      const annualCostLakhs = 47988 / 100000; // ₹47,988

      // ROI = Recoverable / Cost
      const roi = Math.round(annualRecoverableLakhs / annualCostLakhs);

      // Update DOM with simple animations
      calcItcAtRisk.textContent = `₹${annualAtRiskLakhs}L`;
      calcRecoverable.textContent = `₹${annualRecoverableLakhs}L`;
      calcRoi.textContent = `${roi}×`;
    };

    clientSlider.addEventListener('input', updateCalculator);
    turnoverSlider.addEventListener('input', updateCalculator);
    
    // Initial calculation
    updateCalculator();
  }
});

// Helper functions
window.closeMobileMenu = function() {
  const mobileMenu = document.getElementById('mobileMenu');
  if (mobileMenu) {
    mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
  }
};

function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeProgress = easeOutQuart(progress);
    
    // Format number with commas
    const currentVal = Math.floor(easeProgress * (end - start) + start);
    obj.innerHTML = currentVal.toLocaleString('en-IN');
    
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

function animateCounter(obj, start, end, duration, isRupee, isPercentage, isLakh, isPlus) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeProgress = easeOutQuart(progress);
    
    let currentVal = Math.floor(easeProgress * (end - start) + start);
    
    let formattedText = currentVal.toLocaleString('en-IN');
    if (isRupee) formattedText = '₹' + formattedText;
    if (isLakh) formattedText = formattedText + 'L';
    if (isPercentage) formattedText = formattedText + '%';
    if (isPlus) formattedText = formattedText + '+';
    
    obj.innerHTML = formattedText;
    
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

function easeOutQuart(x) {
  return 1 - Math.pow(1 - x, 4);
}
