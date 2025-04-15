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
