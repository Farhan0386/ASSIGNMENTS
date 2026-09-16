// fileManager.js

const fs = require("fs");

const fileName = "sample.txt";

console.log("Starting file manager...");

// CREATE FILE
fs.writeFile(fileName, "Hello! This is the original file content.", (err) => {
    if (err) {
        console.log("Error creating file:", err.message);
        return;
    }

    console.log("File created successfully.");

    // READ FILE
    fs.readFile(fileName, "utf8", (err, data) => {
        if (err) {
            console.log("Error reading file:", err.message);
            return;
        }

        console.log("File content:", data);

        // UPDATE FILE
        fs.appendFile(fileName, "\nThis line was added during update.", (err) => {
            if (err) {
                console.log("Error updating file:", err.message);
                return;
            }

            console.log("File updated successfully.");

            // READ UPDATED FILE
            fs.readFile(fileName, "utf8", (err, updatedData) => {
                if (err) {
                    console.log("Error reading updated file:", err.message);
                    return;
                }

                console.log("Updated content:");
                console.log(updatedData);

                // DELETE FILE
                fs.unlink(fileName, (err) => {
                    if (err) {
                        console.log("Error deleting file:", err.message);
                        return;
                    }

                    console.log("File deleted successfully.");
                    console.log("File manager completed.");
                });
            });
        });
    });
});
