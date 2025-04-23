document.getElementById("resetForm").addEventListener("submit", function (e) {
    var userID = document.getElementById('userID').value.trim();
    var newPass = document.getElementById('newPassword').value.trim();
    var confirmPass = document.getElementById('confirmPassword').value.trim();
    var questionId = document.getElementById('securityQuestion').value;
    var answer = document.getElementById('securityAnswer').value.trim();

    if (userID=="" || confirmPass=="" || newPass=="" || questionId=="" || answer==""){
        e.preventDefault();
        alert("Please fill up all information!")
        return;
    }

    if (newPass != confirmPass){
        e.preventDefault();
        alert("Password not match!")
        return;
    }
})

function toggleMenu() {
    var subMenu = document.getElementById("subMenu");
    subMenu.classList.toggle("open-menu");
}

function showInput() {
    var inputBox = document.getElementById("hidden-input-box");

    if(inputBox.style.display === 'none' || inputBox.style.display === '') {
        inputBox.style.display = 'block'
    } else {
        inputBox.style.display = 'none'
    }
}

function changePage() {
    window.location.href = "/securityQues";
}