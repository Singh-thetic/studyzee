document.addEventListener('DOMContentLoaded', () => {
    const flashcards = [
        { question: "What is and Apple?", answer: 'Fruit' },
        { question: 'What is 2+2?', answer: '4'}
    ];

    let currentCard = 0;

    const flashcardElement = document.getElementById('flashcard');
    const questionElement = document.getElementById('question');
    const answerElement = document.getElementById('answer');

    function displayCard() {
        questionElement.textContent = flashcards[currentCard].question;
        answerElement.textContent = flashcards[currentCard].answer;
        flashcardElement.classList.remove('is-flipped');
    }

    document.getElementById('flip-card').addEventListener('click', () => {
        flashcardElement.classList.toggle('is-flipped');
    });

    document.getElementById('next-card').addEventListener('click', () => {
        currentCard = (currentCard + 1) % flashcards.length;
        displayCard();
    })

    displayCard();
});