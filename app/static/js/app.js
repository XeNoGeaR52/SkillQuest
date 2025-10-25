// SkillQuest Frontend JavaScript

// Initialize htmx event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Show loading states
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        console.log('Request started:', event.detail.path);
    });

    document.body.addEventListener('htmx:afterRequest', function(event) {
        console.log('Request completed:', event.detail.path);
    });

    // Handle errors
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('Request failed:', event.detail);
        alert('An error occurred. Please try again.');
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        });
    }, 5000);
});

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Utility function to calculate XP to next level
function xpToNextLevel(currentXp, currentLevel) {
    const nextLevelXp = Math.pow(currentLevel, 2) * 100;
    return nextLevelXp - currentXp;
}
