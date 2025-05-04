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

function showClassCodeInput() {
    var classCodeBox = document.getElementById("classCodeBox");
    classCodeBox.classList.toggle("openClassCodeBox");
}

function toggleClassCode() {
    const box = document.getElementById("classCodeBox");
    box.classList.toggle("openClassCodeBox");
    if (box.classList.contains("openClassCodeBox")) {
        setTimeout(() => box.style.opacity = 1, 10);
    }
}

async function loadStudentPerformance(classId) {
    try {
        const response = await fetch(`/api/class/${classId}/analytics`);
        const data = await response.json();
        renderPerformanceChart(data);
    } catch (error) {
        Swal.fire('错误', '无法加载学习数据', 'error');
    }
}


function renderPerformanceChart(data) {
}