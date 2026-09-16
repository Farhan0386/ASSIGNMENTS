const express = require("express");
const router = express.Router();
const students = require("../data/students");

// GET /students - Get all students
router.get("/", (req, res) => {
  res.status(200).json(students);
});

// GET /students/:id - Get student by ID
router.get("/:id", (req, res) => {
  const id = Number(req.params.id);

  if (isNaN(id) || !Number.isInteger(id) || id <= 0) {
    res.status(400).json({ message: "Invalid Student ID provided." });
    return;
  }

  const student = students.find((s) => s.id === id);

  if (!student) {
    res.status(404).json({ message: "Student not found." });
    return;
  }

  res.status(200).json(student);
});

// POST /students - Add a new student
router.post("/", (req, res) => {
  const { name, age, course, email } = req.body;

  if (!name || !age || !course || !email) {
    res.status(400).json({
      message: "Missing required fields: name, age, course, and email are all required."
    });
    return;
  }

  const parsedAge = Number(age);
  if (isNaN(parsedAge) || parsedAge <= 0) {
    res.status(400).json({ message: "Age must be a positive number." });
    return;
  }

  const newStudent = {
    id: students.length > 0 ? Math.max(...students.map((s) => s.id)) + 1 : 1,
    name: String(name).trim(),
    age: parsedAge,
    course: String(course).trim(),
    email: String(email).trim()
  };

  students.push(newStudent);

  res.status(201).json({
    message: "Student created successfully.",
    student: newStudent
  });
});

// PUT /students/:id - Update an existing student
router.put("/:id", (req, res) => {
  const id = Number(req.params.id);

  if (isNaN(id) || !Number.isInteger(id) || id <= 0) {
    res.status(400).json({ message: "Invalid Student ID provided." });
    return;
  }

  const student = students.find((s) => s.id === id);

  if (!student) {
    res.status(404).json({ message: "Student not found." });
    return;
  }

  const { name, age, course, email } = req.body;

  if (!name || !age || !course || !email) {
    res.status(400).json({
      message: "Missing required fields: name, age, course, and email are all required."
    });
    return;
  }

  const parsedAge = Number(age);
  if (isNaN(parsedAge) || parsedAge <= 0) {
    res.status(400).json({ message: "Age must be a positive number." });
    return;
  }

  student.name = String(name).trim();
  student.age = parsedAge;
  student.course = String(course).trim();
  student.email = String(email).trim();

  res.status(200).json({
    message: "Student updated successfully.",
    student
  });
});

// DELETE /students/:id - Delete a student
router.delete("/:id", (req, res) => {
  const id = Number(req.params.id);

  if (isNaN(id) || !Number.isInteger(id) || id <= 0) {
    res.status(400).json({ message: "Invalid Student ID provided." });
    return;
  }

  const index = students.findIndex((s) => s.id === id);

  if (index === -1) {
    res.status(404).json({ message: "Student not found." });
    return;
  }

  const deletedStudent = students.splice(index, 1)[0];

  res.status(200).json({
    message: "Student deleted successfully.",
    student: deletedStudent
  });
});

module.exports = router;