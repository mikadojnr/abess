// Function to automatically hide the alert after a specified time
function autoDismissAlert(selector, delay) {
    setTimeout(function() {
      $(selector).alert('close'); // Use jQuery to close the alert
    }, delay);
  }

  // Call the function with the alert selector and delay in milliseconds
  autoDismissAlert('.auto-dismissible-alert', 5000); // 5000 milliseconds = 5 seconds



// NAVBAR DISPLAY ON SCROLL
document.addEventListener('DOMContentLoaded', function() {
  var navbar = document.querySelector('.nav');

  window.addEventListener('scroll', function() {
      var currentScroll = window.scrollY;
      console.log('Scroll detected. Current scroll position:', currentScroll); // Debugging output

      currentScroll > 500 ? navbar.classList.add('scrolled-navbar') : navbar.classList.remove('scrolled-navbar');
      
  });
});

// Menu button to open menu on click
const navButton = document.querySelector('.nav-button');
const navMenu = document.querySelector('.nav-menu');
const overlay = document.querySelector('#overlay');
const body = document.querySelector('body');

navButton.addEventListener('click', () => {
  navButton.classList.toggle('active-menu');
  navMenu.classList.toggle('show-menu');
  overlay.classList.toggle('show-overlay');
  // body.classList.toggle('no-scroll');
})