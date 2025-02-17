document.addEventListener('DOMContentLoaded', async () => {
    let flashcards = [];
    let currentCard = 0;

    const flashcardElement = document.getElementById('flashcard');
    const questionElement = document.getElementById('question');
    const answerElement = document.getElementById('answer');
    const setList = document.getElementById('flashcard-sets');
    const flashcardContainer = document.querySelector('.flashcard-container');
    const setNameElement = document.getElementById('set-name');

    async function loadFlashcardSets() {
        try {
            const response = await fetch('/flashcard-sets');
            const data = await response.json();
            setList.innerHTML = ''; // Clear existing list
            data.sets.forEach(set => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.textContent = `Practice: ${set.name}`;
                button.addEventListener('click', () => loadFlashcards(set.set_id, set.name));
                li.appendChild(button);
                setList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading flashcard sets:', error);
        }
    }

    async function loadFlashcards(setId, setName) {
        try {
            const response = await fetch(`/flashcards/${setId}`);
            const data = await response.json();
            flashcards = data.flashcards;
            currentCard = 0;
            setNameElement.textContent = setName;
            flashcardContainer.style.display = 'block';
            displayCard();
        } catch (error) {
            console.error('Error loading flashcards:', error);
        }
    }

    function displayCard() {
        if (flashcards.length === 0) return;
        questionElement.textContent = flashcards[currentCard].question;
        answerElement.textContent = flashcards[currentCard].answer;
        flashcardElement.classList.remove('is-flipped');
    }

    document.getElementById('flip-card').addEventListener('click', () => {
        flashcardElement.classList.toggle('is-flipped');
    });

    document.getElementById('next-card').addEventListener('click', () => {
        if (flashcards.length === 0) return;
        currentCard = (currentCard + 1) % flashcards.length;
        displayCard();
    });

    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('notes-file');
        if (!fileInput.files.length) return;

        const formData = new FormData();
        formData.append('notes_file', fileInput.files[0]);

        try {
            const response = await fetch('/upload-notes', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            alert(result.message);
            loadFlashcardSets();
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    });

    loadFlashcardSets();
});
