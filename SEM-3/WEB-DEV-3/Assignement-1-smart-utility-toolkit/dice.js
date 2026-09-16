// dice.js

const crypto = require("crypto");

console.log("Dice simulator started...");

function rollDice() {
    // randomInt(1, 7) generates a number from 1 to 6
    return crypto.randomInt(1, 7);
}

const numberOfRolls = 5;

for (let i = 1; i <= numberOfRolls; i++) {
    const diceValue = rollDice();
    console.log(`Roll ${i}: Dice Rolled: ${diceValue}`);
}

console.log("Dice simulation completed.");
