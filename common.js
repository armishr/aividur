// common.js

function logout() {
    // Implement your logout logic here
    // For example, make a call to a REST API to invalidate the session

    const logoutApiUrl = 'http://127.0.0.1:5000/logout';

    // Make an AJAX request to the logout API
    fetch(logoutApiUrl, {
        method: 'POST', // or 'GET' depending on your server setup
        headers: {
            'Content-Type': 'application/json',
            // You might need to include authentication headers here
            // for example, if you are using tokens
        },
        credentials: 'include', // include cookies in the request
    })
    .then(response => {
        if (response.ok) {
            // If the server successfully handles the logout, redirect the user to the desired page
            window.location.href = '/loginpage'; // Replace with the desired page
        } else {
            console.error('Logout failed');
        }
    })
    .catch(error => {
        console.error('Error during logout:', error);
    });
}

// Function to toggle the collapse on load
function collapseOnLoad() {
    var box1 = document.getElementById('box1');
    box1.style.width = '0px';
    box1.style.visibility = 'hidden'; // Set initial width to 0px
}

// Function to toggle the collapse on button click
function collapseBox() {
    var box1 = document.getElementById('box1');

    // Toggle the width of box1 between 0 and 300px
    if (box1.style.width === '0px' || box1.style.width === '') {
        box1.style.width = '200px';
        box1.style.visibility = 'visible';
    } else {
        box1.style.width = '0px';
        box1.style.visibility = 'hidden';
    }
}

// Call the function on form load
window.onload = collapseOnLoad;
