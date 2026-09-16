// calculator.js

console.log("Calculator started...");

const operation = process.argv[2];
const num1 = Number(process.argv[3]);
const num2 = Number(process.argv[4]);

console.log("Input:", operation, num1, num2);

if (isNaN(num1) || isNaN(num2)) {
    console.log("Error: Please enter valid numbers.");
    process.exit();
}

let result;

switch (operation) {
    case "add":
        result = num1 + num2;
        break;

    case "sub":
        result = num1 - num2;
        break;

    case "mul":
        result = num1 * num2;
        break;

    case "div":
        if (num2 === 0) {
            console.log("Error: Cannot divide by zero.");
            process.exit();
        }
        result = num1 / num2;
        break;

    default:
        console.log("Invalid operation.");
        console.log("Use: add, sub, mul, or div");
        process.exit();
}

console.log("Result:", result);
console.log("Calculator finished.");
