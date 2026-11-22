const Cart = require("../models/Cart");
const Product = require("../models/Product");
const AppError = require("../utils/AppError");

const buildCartPayload = async (userId) => {
  let cart = await Cart.findOne({ user: userId }).populate(
    "items.product",
    "name price stock category"
  );

  if (!cart) {
    cart = await Cart.create({ user: userId, items: [] });
    cart = await Cart.findOne({ user: userId }).populate(
      "items.product",
      "name price stock category"
    );
  }

  let totalItems = 0;
  let subtotal = 0;

  const formattedItems = cart.items
    .filter((item) => item.product !== null)
    .map((item) => {
      const lineTotal = Number((item.product.price * item.quantity).toFixed(2));
      totalItems += item.quantity;
      subtotal = Number((subtotal + lineTotal).toFixed(2));
      return {
        product: item.product._id,
        name: item.product.name,
        price: item.product.price,
        availableStock: item.product.stock,
        quantity: item.quantity,
        lineTotal,
      };
    });

  return {
    _id: cart._id,
    user: cart.user,
    items: formattedItems,
    totalItems,
    subtotal,
  };
};

const getCart = async (req, res, next) => {
  try {
    const payload = await buildCartPayload(req.user._id);
    res.status(200).json({ success: true, data: payload });
  } catch (err) {
    next(err);
  }
};

const addOrUpdateCartItem = async (req, res, next) => {
  try {
    const { productId, quantity } = req.body;
    const qty = Number(quantity);

    if (!productId || !Number.isInteger(qty) || qty < 1) {
      return next(new AppError("Valid productId and integer quantity >= 1 are required", 400));
    }

    const product = await Product.findById(productId);
    if (!product) {
      return next(new AppError("Product not found", 404));
    }

    if (product.stock < qty) {
      return next(
        new AppError(`Only ${product.stock} unit(s) available in stock`, 400)
      );
    }

    let cart = await Cart.findOne({ user: req.user._id });
    if (!cart) {
      cart = await Cart.create({
        user: req.user._id,
        items: [{ product: productId, quantity: qty }],
      });
    } else {
      const existingIndex = cart.items.findIndex(
        (item) => item.product.toString() === productId.toString()
      );
      if (existingIndex > -1) {
        cart.items[existingIndex].quantity = qty;
      } else {
        cart.items.push({ product: productId, quantity: qty });
      }
      await cart.save();
    }

    const payload = await buildCartPayload(req.user._id);
    res.status(200).json({
      success: true,
      message: "Cart updated successfully",
      data: payload,
    });
  } catch (err) {
    next(err);
  }
};

const removeCartItem = async (req, res, next) => {
  try {
    const { productId } = req.params;
    const cart = await Cart.findOne({ user: req.user._id });

    if (!cart) {
      return next(new AppError("Cart not found", 404));
    }

    const initialLength = cart.items.length;
    cart.items = cart.items.filter(
      (item) => item.product.toString() !== productId.toString()
    );

    if (cart.items.length === initialLength) {
      return next(new AppError("Item not found in cart", 404));
    }

    await cart.save();
    const payload = await buildCartPayload(req.user._id);

    res.status(200).json({
      success: true,
      message: "Item removed from cart",
      data: payload,
    });
  } catch (err) {
    next(err);
  }
};

const clearCart = async (req, res, next) => {
  try {
    await Cart.findOneAndUpdate(
      { user: req.user._id },
      { $set: { items: [] } },
      { upsert: true }
    );
    const payload = await buildCartPayload(req.user._id);
    res.status(200).json({
      success: true,
      message: "Cart cleared",
      data: payload,
    });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getCart,
  addOrUpdateCartItem,
  removeCartItem,
  clearCart,
};
