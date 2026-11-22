const Product = require("../models/Product");
const Category = require("../models/Category");
const AppError = require("../utils/AppError");

const createProduct = async (req, res, next) => {
  try {
    const { name, description, price, stock, category } = req.body;
    const categoryDoc = await Category.findById(category);
    if (!categoryDoc) return next(new AppError("Category not found", 404));

    const sellerId =
      req.user.role === "admin" && req.body.seller ? req.body.seller : req.user._id;

    const product = await Product.create({
      name,
      description,
      price,
      stock,
      category,
      seller: sellerId,
    });

    res.status(201).json({ success: true, message: "Product created", data: product });
  } catch (err) {
    next(err);
  }
};

const getProducts = async (req, res, next) => {
  try {
    const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
    const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 10, 1), 100);
    const skip = (page - 1) * limit;

    const filter = {};
    if (req.query.category) filter.category = req.query.category;
    if (req.query.seller) filter.seller = req.query.seller;
    if (req.query.search) filter.$text = { $search: req.query.search };
    if (req.query.minPrice || req.query.maxPrice) {
      filter.price = {};
      if (req.query.minPrice) filter.price.$gte = Number(req.query.minPrice);
      if (req.query.maxPrice) filter.price.$lte = Number(req.query.maxPrice);
    }

    const [products, total] = await Promise.all([
      Product.find(filter)
        .populate("category", "name")
        .populate("seller", "name email role")
        .sort(req.query.sort || "-createdAt")
        .skip(skip)
        .limit(limit),
      Product.countDocuments(filter),
    ]);

    res.status(200).json({
      success: true,
      data: products,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  } catch (err) {
    next(err);
  }
};

const getProductById = async (req, res, next) => {
  try {
    const product = await Product.findById(req.params.id)
      .populate("category", "name")
      .populate("seller", "name email role");
    if (!product) return next(new AppError("Product not found", 404));
    res.status(200).json({ success: true, data: product });
  } catch (err) {
    next(err);
  }
};

const updateProduct = async (req, res, next) => {
  try {
    const product = await Product.findById(req.params.id);
    if (!product) return next(new AppError("Product not found", 404));

    const isOwner = product.seller.toString() === req.user._id.toString();
    if (req.user.role !== "admin" && !isOwner) {
      return next(new AppError("You cannot modify another seller's product", 403));
    }

    if (req.body.category) {
      const categoryDoc = await Category.findById(req.body.category);
      if (!categoryDoc) return next(new AppError("Category not found", 404));
    }

    ["name", "description", "price", "stock", "category"].forEach((field) => {
      if (req.body[field] !== undefined) product[field] = req.body[field];
    });

    await product.save();
    res.status(200).json({ success: true, message: "Product updated", data: product });
  } catch (err) {
    next(err);
  }
};

const deleteProduct = async (req, res, next) => {
  try {
    const product = await Product.findById(req.params.id);
    if (!product) return next(new AppError("Product not found", 404));

    const isOwner = product.seller.toString() === req.user._id.toString();
    if (req.user.role !== "admin" && !isOwner) {
      return next(new AppError("You cannot delete another seller's product", 403));
    }

    await product.deleteOne();
    res.status(200).json({ success: true, message: "Product deleted" });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  createProduct,
  getProducts,
  getProductById,
  updateProduct,
  deleteProduct,
};
