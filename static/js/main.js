// BrokerBuddy Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Print results functionality
    const printButton = document.getElementById('print-results');
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }

    // Form validation
    const clientForm = document.querySelector('form[action*="submit-client"]');
    if (clientForm) {
        clientForm.addEventListener('submit', function(event) {
            const requiredFields = clientForm.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('invalid');
                } else {
                    field.classList.remove('invalid');
                }
            });

            if (!isValid) {
                event.preventDefault();
                alert('Please fill out all required fields.');
            }
        });
    }

    // Toggle match details
    const detailsToggles = document.querySelectorAll('.toggle-details');
    detailsToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const details = this.nextElementSibling;
            if (details.style.display === 'none') {
                details.style.display = 'block';
                this.textContent = 'Hide Details';
            } else {
                details.style.display = 'none';
                this.textContent = 'Show Details';
            }
        });
    });

    // Admin panel functionality
    const deleteButtons = document.querySelectorAll('.delete-lender');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this lender?')) {
                event.preventDefault();
            }
        });
    });
});
