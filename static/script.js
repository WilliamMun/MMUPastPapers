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

function addAnswerField() {
    const container = document.getElementById('answer-fields');

    const newField = document.createElement('div');
    newField.className = 'answer-field';
    newField.innerHTML = `
        <br>
        <input type="text" name="question" id="question" placeholder="Enter Question Number/Question">
        <label for="type-ans">Type of Answer Field: </label>
        <select class="type-ans" name="type-ans" id="type-ans" onchange="handleAnswerFieldType(this)">
            <option value="text">Text</option>
            <option value="mcq">MCQ</option>
            <option value="file">File</option>
        </select>
        
        <div class="mcq-setup" id="mcq-setup" style="display: none;">
            <div class="mcq-option" id="mcq-option">
                <div class="option" id="option">
                    <input type="radio" name="mcqAnswer" id="mcqAnswer" class="mcqAnswer" value="option1">
                    <input type="text" name="option1-text" id="option1-text" class="option1-text"
                        placeholder="Enter your answer option 1.">
                </div>
            </div>
            <button type="button" onclick="addMcqOptions(this)">Add Answer Option</button>
        </div>

        <button onclick="deleteAnswerField(this)">Delete</button>
    `;

    container.appendChild(newField);
}

function deleteAnswerField(button) {
  const field = button.closest('.answer-field');
  if (field) {
    field.remove();
  }
}

function addMcqOptions(button) {
    const mcqSetup = button.closest('.mcq-setup');
    const container = button.closest('.mcq-setup').querySelector('.mcq-option');

    let optionCount = parseInt(mcqSetup.getAttribute('data-option-count')) || 2;

    const newField = document.createElement('div');
    newField.className = 'option';
    const optionId = `option ${optionCount}`;
    newField.innerHTML = `
        <br>
        <input type="radio" name="mcqAnswer" value="${optionId}">
        <input type="text" name="${optionId}-text" placeholder="Enter your answer ${optionId}.">
        <button onclick="deleteOption(this)">Delete Option</button>
    `;

    mcqSetup.querySelector('.mcq-option').appendChild(newField);
    mcqSetup.setAttribute('data-option-count', optionCount + 1);
}

function deleteOption(button) {
    const field = button.closest('.option');
    if (field) {
        const mcqSetup = button.closest('.mcq-setup');
        field.remove();

        if(mcqSetup) {
            const remaining = mcqSetup.querySelectorAll('.option').length;
            mcqSetup.setAttribute('data-option-count', remaining + 1);
        }
    }
}

function handleAnswerFieldType(select) {
    const answerField = select.closest('.answer-field');
    const mcqSetup = answerField.querySelector('.mcq-setup');

    mcqSetup.style.display = 'none';

    if (select.value == 'mcq') {
        mcqSetup.style.display = 'block';
    } else {
        mcqSetup.style.display = 'none';
        mcqSetup.querySelector('.mcq-option').innerHTML = '';
    }
}