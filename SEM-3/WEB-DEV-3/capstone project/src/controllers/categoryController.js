const Category = require("../models/Category");
const AppError = require("../utils/AppError");

const createCategory = async (req, res, next) => {
  try {
    const category = await Category.create({
      name: req.body.name,
      description: req.body.description,
    });
    res.status(201).json({ success: true, message: "Category created", data: category });
  } catch (err) {
    next(err);
  }
};

const getCategories = async (req, res, next) => {
  try {
    const categories = await Category.find().sort("name");
    res.status(200).json({ success: true, data: categories });
  } catch (err) {
    next(err);
  }
};

const deleteCategory = async (req, res, next) => {
  try {
    const category = await Category.findByIdAndDelete(req.params.id);
    if (!category) return next(new AppError("Category not found", 404));
    res.status(200).json({ success: true, message: "Category deleted" });
  } catch (err) {
    next(err);
  }
};

module.exports = { createCategory, getCategories, deleteCategory };
