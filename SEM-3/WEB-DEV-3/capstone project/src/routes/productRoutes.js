const express = require("express");
const { body, validationResult } = require("express-validator");
const {
  createProduct,
  getProducts,
  getProductById,
  updateProduct,
  deleteProduct,
} = require("../controllers/productController");
const { protect } = require("../middlewares/authMiddleware");
const { authorize } = require("../middlewares/roleMiddleware");
const AppError = require("../utils/AppError");

const router = express.Router();

const validate = (req, res, next) => {
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

router.get("/", getProducts);
router.get("/:id", getProductById);

router.post(
  "/",
  protect,
  authorize("seller", "admin"),
  [
    body("name").trim().notEmpty().withMessage("Product name is required"),
    body("price").isFloat({ min: 0 }).withMessage("Price must be a non-negative number"),
    body("stock").isInt({ min: 0 }).withMessage("Stock must be a non-negative integer"),
    body("category").notEmpty().withMessage("Category ID is required"),
  ],
  validate,
  createProduct
);

router.patch(
  "/:id",
  protect,
  authorize("seller", "admin"),
  [
    body("price").optional().isFloat({ min: 0 }).withMessage("Price must be non-negative number"),
    body("stock").optional().isInt({ min: 0 }).withMessage("Stock must be non-negative integer"),
  ],
  validate,
  updateProduct
);

router.delete("/:id", protect, authorize("seller", "admin"), deleteProduct);

module.exports = router;
