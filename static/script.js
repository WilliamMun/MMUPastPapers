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

function addAnswerField(button) {
    const container = document.getElementById('answer-fields');

    let answerFieldCount = parseInt(container.getAttribute('data-answer-count'));

    const newField = document.createElement('div');
    newField.className = 'answer-field';
    newField.innerHTML = `
        <br>
        <input type="text" name="question${answerFieldCount}" id="question${answerFieldCount}" placeholder="Enter Question Number/Question ${answerFieldCount}">
        <button class="setup-delete-btn" onclick="deleteAnswerField(this)">✖</button>
        <label for="type-ans${answerFieldCount}">Type of Answer Field: </label>
        <select class="type-ans${answerFieldCount}" name="type-ans${answerFieldCount}" id="type-ans${answerFieldCount}" onchange="handleAnswerFieldType(this)">
            <option value="text">Text</option>
            <option value="mcq">MCQ</option>
            <option value="file">File</option>
        </select>
        
        <div class="mcq-setup" style="display: none;" data-option-count="2">
            <select class="type-ans" name="type-mcq${answerFieldCount}" id="type-mcq${answerFieldCount}">
                <option value="4">Four Answer Options</option>
                <option value="5">Five Answer Options</option>
            </select>
        </div>
        <br>
        <hr>
    `;

    container.appendChild(newField);
    container.setAttribute("data-answer-count", answerFieldCount + 1)
}

function deleteAnswerField(button) {
  const field = button.closest('.answer-field');
  if (field) {
    const answerField = button.closest('.answer-fields');
    field.remove();

    if(answerField) {
            const remaining = answerField.querySelectorAll('.answer-field').length;
            answerField.setAttribute('data-answer-count', remaining + 1);
        }
  }
}

function addMcqOptions(button) {
    const answerField = button.closest('.answer-field');
    const questionInput = answerField.querySelector('input[type="text"][name^="question"]');
    const match = questionInput.name.match(/^question(\d+)$/);
    const questionNumber = match ? match[1] : '0';  // default to '0' if not matched

    const mcqSetup = button.closest('.mcq-setup');
    let optionCount = parseInt(mcqSetup.getAttribute('data-option-count'));

    const newField = document.createElement('div');
    newField.className = 'option';
    const optionId = `option ${optionCount}`;
    newField.innerHTML = `
        <br>
        <input type="radio" name="mcqQuestion${questionNumber}Answer${optionCount}" value="question${questionNumber}${optionId}">
        <input type="text" name="question${questionNumber}-option${optionCount}-text" placeholder="Enter your answer question${questionNumber} ${optionId}.">
        <button class="setup-delete-btn" onclick="deleteOption(this)">✖</button>
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

function showTooltip(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.classList.add('show-tooltip');
        setTimeout(() => {
            container.classList.remove('show-tooltip');
        }, 1500);
    }
}

function copyClassCode() {
    const text = document.getElementById('classCode').innerText;
    navigator.clipboard.writeText(text).then(() => {
        showTooltip('codeTooltip');
    });
}

function copyClassLink() {
    const input = document.getElementById('joinLink');
    navigator.clipboard.writeText(input.value).then(() => {
        showTooltip('linkCopyContainer');
    });
}