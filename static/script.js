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

let defaultMcqOption = null;

function handleMcqDefaultSelect(selectElement) {
    if (defaultMcqOption === null) {
        defaultMcqOption = selectElement.value;
    }
}

function addAnswerField(button) {
    const container = document.getElementById('answer-fields');

    let answerFieldCount = parseInt(container.getAttribute('data-answer-count'));

    const newField = document.createElement('div');
    newField.className = 'answer-field';

    let mcqOptionsHtml = `
        <option value="4" ${defaultMcqOption === '4' ? 'selected' : ''}>Four Answer Options</option>
        <option value="5" ${defaultMcqOption === '5' ? 'selected' : ''}>Five Answer Options</option>
    `;
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
                ${mcqOptionsHtml}
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

function handleAnswerFieldTypeEdit(selectElem) {
    const answerFieldDiv = selectElem.closest('.answer-field');
    const selectedValue = selectElem.value;
    const index = Array.from(document.querySelectorAll('.answer-field')).indexOf(answerFieldDiv) + 1;

    // Check if mcq-setup already exists
    let mcqSetup = answerFieldDiv.querySelector('.mcq-setup');

    if (selectedValue === 'mcq') {
        if (!mcqSetup) {
            // Create and append the mcq-setup dynamically
            mcqSetup = document.createElement('div');
            mcqSetup.className = 'mcq-setup';
            mcqSetup.innerHTML = `
                <label for="type-mcq${index}">Answer Options:</label>
                <select class="type-ans" name="type-mcq${index}" id="type-mcq${index}" onchange="handleMcqDefaultSelect(this)">
                    <option value="4">Four Answer Options</option>
                    <option value="5">Five Answer Options</option>
                </select>
            `;
            answerFieldDiv.appendChild(mcqSetup);
        } else {
            mcqSetup.style.display = 'block';
        }
    } else {
        // Hide mcq-setup if it exists
        if (mcqSetup) {
            mcqSetup.style.display = 'none';
        }
    }
}

function addAnswerFieldEdit(button) {
    const container = document.getElementById('answer-fields');
    const buttonContainer = container.querySelector('.field-buttons'); 

    let answerFieldCount = parseInt(container.getAttribute('data-answer-count'));

    const newField = document.createElement('div');
    newField.className = 'answer-field';

    let mcqOptionsHtml = `
        <option value="4" ${defaultMcqOption === '4' ? 'selected' : ''}>Four Answer Options</option>
        <option value="5" ${defaultMcqOption === '5' ? 'selected' : ''}>Five Answer Options</option>
    `;
    newField.innerHTML = `
        <br>
        <input type="hidden" name="ques_id${answerFieldCount}" id="ques_id${answerFieldCount}" value="">
        <input type="text" name="question${answerFieldCount}" id="question${answerFieldCount}" placeholder="Enter Question Number/Question ${answerFieldCount}">
        <button class="setup-delete-btn" onclick="deleteAnswerField(this)">✖</button>
        <label for="type-ans${answerFieldCount}">Type of Answer Field: </label>
        <select class="type-ans${answerFieldCount}" name="type-ans${answerFieldCount}" id="type-ans${answerFieldCount}" onchange="handleAnswerFieldTypeEdit(this)">
            <option value="text">Text</option>
            <option value="mcq">MCQ</option>
            <option value="file">File</option>
        </select>
        
        <div class="mcq-setup" style="display: none;" data-option-count="2">
            <select class="type-ans" name="type-mcq${answerFieldCount}" id="type-mcq${answerFieldCount}" onchange="handleMcqDefaultSelect(this)">
                ${mcqOptionsHtml}
            </select>
        </div>
        <br>
        <hr>
    `;

    container.insertBefore(newField, buttonContainer);
    container.setAttribute("data-answer-count", answerFieldCount + 1)
}

let deletedIDs = [] 
function deleteAnswerFieldEdit(button) {
    const field = button.closest('.answer-field');
    const hiddenInput = field.querySelector('input[type="hidden"]');
  
    if (hiddenInput && hiddenInput.value) {
        deletedIDs.push(hiddenInput.value);
    }

    if (field) {
        const answerField = button.closest('.answer-fields');
        field.remove();
        document.getElementById("deleted_questions").value = deletedIDs.join(',');
        renumberQuestions();
    
        if(answerField) {
            const remaining = answerField.querySelectorAll('.answer-field').length;
            answerField.setAttribute('data-answer-count', remaining + 1);
        }
    }
}

function renumberQuestions() {
    const fields = document.querySelectorAll('.answer-field');
    fields.forEach((field, index) => {
        const label = field.querySelector('label');
        label.textContent = `Question ${index + 1}`;

        field.querySelectorAll('input, select').forEach(input => {
            if (input.name.includes('question')) {
                input.name = `question${index + 1}`;
                input.id = `question${index + 1}`;
            } else if (input.name.includes('type-ans')) {
                input.name = `type-ans${index + 1}`;
                input.id = `type-ans${index + 1}`;
            } else if (input.name.includes('type-mcq')) {
                input.name = `type-mcq${index + 1}`;
                input.id = `type-mcq${index + 1}`;
            } else if (input.name.includes('ques_id')) {
                input.name = `ques_id${index + 1}`;
                input.id = `ques_id${index + 1}`;
            }
        });
    });

  document.getElementById('answer-fields').setAttribute('data-answer-count', fields.length + 1);

}

function openCommentBox(answerId) {
    var commentBox = document.getElementById('commenting-box-' + answerId);

    if (commentBox.style.display === 'none' || commentBox.style.display === '') {
        commentBox.style.display = "block";
    } else {
        commentBox.style.display = 'none';
    }
}

function closeCommentBox(answerId) {
    var commentBox = document.getElementById('commenting-box-' + answerId);

    if (commentBox.style.display === 'block') {
        commentBox.style.display = 'none'; 
    }
}

function toggleComments(answerId, linkElement) {
    const comments = document.querySelectorAll(`.std-comment[data-answer='${answerId}']`);
    comments.forEach((comment, index) => {
        if (index >= 3) {
            if (comment.style.display === "none") {
                comment.style.display = "block";
                linkElement.textContent = "Show Less";
            } else {
                comment.style.display = "none";
                linkElement.textContent = "View More";
            }
        }
    });
}

function toggleAnswers(fieldId, link) {
    const group = document.getElementById(`answer-group-${fieldId}`);
    const answers = group.querySelectorAll(`.answer-field-${fieldId}`);

    answers.forEach((el, index) => {
        if (index >= 3) {
            if (el.style.display === "none") {
                el.style.display = "block";
                link.textContent = "Show Less";
            } else if (el.style.display === "block") {
                el.style.display = "none";
                link.textContent = "View More";
            }
        }
    });
}

function openLightbox(src) {
    document.getElementById("lightbox-img").src = src;
    document.getElementById("lightbox").style.display = "flex";
    }

function closeLightbox(event) {
    event.preventDefault();
    document.getElementById("lightbox").style.display = "none";
}

let selected = null;

function selectImage(container, filename) {
    document.querySelectorAll('.photo-container').forEach(c => {
        c.classList.remove('selected');
    });

    container.classList.add('selected');
    console.log("Class List is added");
    selected = container;

    document.getElementById('selectedFilename').value = filename;
    console.log(filename);
}