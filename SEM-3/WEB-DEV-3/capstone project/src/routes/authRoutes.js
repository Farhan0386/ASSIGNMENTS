const express = require("express");
const { body } = require("express-validator");
const { register, login, refresh, logout } = require("../controllers/authController");
const { protect } = require("../middlewares/authMiddleware");
const AppError = require("../utils/AppError");

const router = express.Router();

const validateRequest = (req, res, next) => {
  const { validationResult } = require("express-validator");
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return next(
      new AppError(
        errors.array().map((e) => e.msg).join(", "),
        400
      )
    );
  }
  next();
};

router.post(
  "/register",
  [
    body("name").trim().notEmpty().withMessage("Name is required"),
    body("email").isEmail().withMessage("Valid email is required"),
    body("password")
      .isLength({ min: 6 })
      .withMessage("Password must be at least 6 characters"),
  ],
  validateRequest,
  register
);

router.post(
  "/login",
  [
    body("email").isEmail().withMessage("Valid email is required"),
    body("password").notEmpty().withMessage("Password is required"),
  ],
  validateRequest,
  login
);

router.post("/refresh", refresh);
router.post("/logout", protect, logout);

module.exports = router;
