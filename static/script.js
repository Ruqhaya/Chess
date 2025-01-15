function updateBoard(data) {
    console.log(data)
    const squares = document.querySelectorAll('.square');
    squares.forEach(square => {
        square.innerHTML = '';  // Clear the square
    });

    for (let row = 0; row < data.board.length; row++) {
        for (let col = 0; col < data.board[row].length; col++) {
            if (data.board[row][col]) {
                const piece = document.createElement('img');
                piece.src = `/static/assets/images/${data.board[row][col]}.png`;
                piece.classList.add('piece');
                const square = document.querySelector(`.square[data-row='${row}'][data-col='${col}']`);
                square.appendChild(piece);
            }
        }
    }
    if (data.captured) {
        console.log(data.captured)
        updateCapturedPieces('white', data.captured.white);
        updateCapturedPieces('black', data.captured.black);
    } else {
        console.warn("Captured pieces data is missing.");
    }
}

function checkGameOver(data) {
    console.log(data.turn)
    updateTurn(data.turn); // Ensure the turn is always updated

    if (data.game_over) {
        const messageText=document.getElementById('message-text')
        messageText.innerText=`Game Over! Winner: ${data.winner}`
        document.getElementById('game-over-message').classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const gameId = new URLSearchParams(window.location.search).get('game_id');
    if (gameId) {
        fetch(`/board/${gameId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Game not found');
                } else {
                    updateBoard(data);
                    checkGameOver(data);
                }
            });
    } else {
        alert('No game ID provided');
    }
});


function disableBoard() {
    const squares = document.querySelectorAll('.square');
    squares.forEach(square => {
        square.removeEventListener('click', () => selectSquare(square));
    });
}

function updateCapturedPieces(color, pieces) {
    const capturedContainer = document.getElementById(`${color}-captured-pieces`);
    capturedContainer.innerHTML = '';
    pieces.forEach(piece => {
        const img = document.createElement('img');
        img.src = `/static/assets/images/${piece}.png`;
        img.classList.add('captured-piece');
        capturedContainer.appendChild(img);
    });
}
function updateTurn(turn) {
    document.getElementById('turn').innerHTML = `<h1>Turn: ${turn}`;
}


const board = document.querySelector('.board');

function createBoard() {
    const initialPositions = [
        ['black rook', 'black knight', 'black bishop', 'black queen', 'black king', 'black bishop', 'black knight', 'black rook'],
        ['black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn'],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn'],
        ['white rook', 'white knight', 'white bishop', 'white queen', 'white king', 'white bishop', 'white knight', 'white rook']
    ];

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const square = document.createElement('div');
            square.classList.add('square');
            square.classList.add((row + col) % 2 === 0 ? 'light' : 'dark');
            square.dataset.row = row;
            square.dataset.col = col;

            // Create an image element for the piece if there is one
            if (initialPositions[row][col]) {
                const piece = document.createElement('img');
                piece.src = `/static/assets/images/${initialPositions[row][col]}.png`;
                piece.classList.add('piece');
                square.appendChild(piece);
            }

            // Add click event listener to each square
            square.addEventListener('click', () => selectSquare(square));

            board.appendChild(square);
        }
    }
}

let selectedPiece = null;  // Declare these variables outside of any function
let selectedSquare = null;
let highlightedSquares = [];

function selectSquare(square) {
    const turn = document.getElementById('turn').textContent.split(': ')[1];

    // Clear previously highlighted squares
    clearHighlightedSquares();

    // If a piece is already selected, attempt to make a move
    if (selectedPiece) {
        const startPos = [selectedSquare.dataset.row, selectedSquare.dataset.col];
        const endPos = [square.dataset.row, square.dataset.col];
        const gameId = new URLSearchParams(window.location.search).get('game_id');

        fetch('/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                game_id: gameId,
                start: startPos,
                end: endPos,
            }),
        })
            .then(response => response.json())
            .then(data => {
                // console.log(data)
                if (data.status === 'move made') {
                    // updateBoard(data.board);
                    // updateTurn(data.turn);

                    // if (data.game_over) {
                    //     alert(`Game Over! Winner: ${data.winner}`);
                    //     disableBoard();
                    // }
                    updateBoard(data);
                    checkGameOver(data);
                } else {
                    alert('Invalid move');
                }
                selectedPiece = null;
                selectedSquare.classList.remove('selected');
            });
    }
    // If no piece is selected, select a piece but only if it matches the turn
    else if (square.firstChild) {
        const pieceColor = square.firstChild.src.includes('white') ? 'white' : 'black';
        if (pieceColor === turn) {
            selectedPiece = square.firstChild;
            selectedSquare = square;
            square.classList.add('selected');

            // Fetch legal moves for the selected piece from the server
            const row = square.dataset.row;
            const col = square.dataset.col;
            const gameId = new URLSearchParams(window.location.search).get('game_id');

            fetch('/legal_moves', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_id: gameId,
                    row: row,
                    col: col,
                }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.legal_moves) {
                        highlightLegalMoves(data.legal_moves);
                    }
                });
        } else {
            alert(`It's ${turn}'s turn!`);
        }
    }
}

function highlightLegalMoves(legalMoves) {
    legalMoves.forEach(move => {
        const row = move[0];
        const col = move[1];
        const square = document.querySelector(`.square[data-row='${row}'][data-col='${col}']`);
        square.classList.add('highlight');
        highlightedSquares.push(square);  // Track highlighted squares to clear later
    });
}

function clearHighlightedSquares() {
    highlightedSquares.forEach(square => {
        square.classList.remove('highlight');
    });
    highlightedSquares = [];
}

function restartGame() {
    const gameId = new URLSearchParams(window.location.search).get('game_id');
    if (!gameId) {
        alert('No game ID provided');
        return;
    }

    fetch('/restart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            game_id: gameId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(data.message);
            fetch(`/board/${gameId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Game not found');
                    } else {
                        document.getElementById('game-over-message').classList.add('hidden');
                        updateBoard(data);
                        checkGameOver(data);
                        const capturedContainer = document.getElementById(`white-captured-pieces`);
                        capturedContainer.innerHTML = '';
                        capturedContainer=document.getElementById(`black-captured-pieces`);
                        capturedContainer.innerHTML='';
                    }
                });
        } else {
            alert('Failed to restart the game');
        }
    });
}

function undoMove() {
    const gameId = new URLSearchParams(window.location.search).get('game_id');
    if (!gameId) {
        alert('No game ID provided');
        return;
    }

    fetch('/undo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            game_id: gameId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(data.message);
            updateBoard(data);
            checkGameOver(data);
        } else {
            alert(data.message);
        }
    });
}



createBoard();