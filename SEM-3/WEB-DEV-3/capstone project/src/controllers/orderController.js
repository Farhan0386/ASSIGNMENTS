const mongoose = require("mongoose");
const Cart = require("../models/Cart");
const Product = require("../models/Product");
const Order = require("../models/Order");
const appEvents = require("../events/appEvents");
const AppError = require("../utils/AppError");

const LOW_STOCK_THRESHOLD = 5;

const ALLOWED_STATUS_TRANSITIONS = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["shipped", "cancelled"],
  shipped: ["delivered"],
  delivered: [],
  cancelled: [],
};

const placeOrder = async (req, res, next) => {
  const decrementedItems = [];

  try {
    const { shippingAddress } = req.body;
    if (!shippingAddress || !shippingAddress.trim()) {
      return next(new AppError("Shipping address is required", 400));
    }

    const cart = await Cart.findOne({ user: req.user._id }).populate("items.product");
    if (!cart || cart.items.length === 0) {
      return next(new AppError("Cart is empty", 400));
    }

    const orderItems = [];
    let totalAmount = 0;

    for (const item of cart.items) {
      if (!item.product) {
        throw new AppError("One or more products in cart no longer exist", 404);
      }

      const qty = item.quantity;
      const updatedProduct = await Product.findOneAndUpdate(
        { _id: item.product._id, stock: { $gte: qty } },
        { $inc: { stock: -qty } },
        { returnDocument: "after" }
      );

      if (!updatedProduct) {
        throw new AppError(
          `Insufficient stock for "${item.product.name}" (requested ${qty})`,
          400
        );
      }

      decrementedItems.push({ productId: updatedProduct._id, quantity: qty });

      const lineTotal = Number((updatedProduct.price * qty).toFixed(2));
      totalAmount = Number((totalAmount + lineTotal).toFixed(2));

      orderItems.push({
        product: updatedProduct._id,
        seller: updatedProduct.seller,
        name: updatedProduct.name,
        priceAtPurchase: updatedProduct.price,
        quantity: qty,
      });
    }

    const order = await Order.create({
      customer: req.user._id,
      items: orderItems,
      totalAmount,
      shippingAddress: shippingAddress.trim(),
      paymentStatus: "SIMULATED_PAID",
      status: "pending",
    });

    cart.items = [];
    await cart.save();

    appEvents.emit("order-placed", {
      orderId: order._id,
      customerId: req.user._id,
      totalAmount: order.totalAmount,
      items: order.items,
    });

    for (const dec of decrementedItems) {
      const prod = await Product.findById(dec.productId);
      if (prod && prod.stock <= LOW_STOCK_THRESHOLD) {
        appEvents.emit("stock-low", {
          productId: prod._id,
          name: prod.name,
          stock: prod.stock,
          sellerId: prod.seller,
        });
      }
    }

    res.status(201).json({
      success: true,
      message: "Order placed successfully (simulated payment)",
      data: order,
    });
  } catch (err) {
    for (const dec of decrementedItems) {
      await Product.findByIdAndUpdate(dec.productId, {
        $inc: { stock: dec.quantity },
      }).catch(() => {});
    }
    next(err);
  }
};

const getOrders = async (req, res, next) => {
  try {
    let filter = {};
    if (req.user.role === "customer") {
      filter = { customer: req.user._id };
    } else if (req.user.role === "seller") {
      filter = { "items.seller": req.user._id };
    }

    const orders = await Order.find(filter)
      .populate("customer", "name email")
      .sort("-createdAt");

    res.status(200).json({ success: true, data: orders });
  } catch (err) {
    next(err);
  }
};

const getOrderById = async (req, res, next) => {
  try {
    if (!mongoose.Types.ObjectId.isValid(req.params.id)) {
      return next(new AppError("Invalid order ID", 400));
    }

    const order = await Order.findById(req.params.id).populate("customer", "name email");
    if (!order) {
      return next(new AppError("Order not found", 404));
    }

    const isCustomer = order.customer._id.toString() === req.user._id.toString();
    const isSeller = order.items.some(
      (i) => i.seller.toString() === req.user._id.toString()
    );

    if (req.user.role !== "admin" && !isCustomer && !isSeller) {
      return next(new AppError("You are not authorized to view this order", 403));
    }

    res.status(200).json({ success: true, data: order });
  } catch (err) {
    next(err);
  }
};

const updateOrderStatus = async (req, res, next) => {
  try {
    const { status } = req.body;
    const order = await Order.findById(req.params.id);
    if (!order) {
      return next(new AppError("Order not found", 404));
    }

    const isSeller = order.items.some(
      (i) => i.seller.toString() === req.user._id.toString()
    );
    if (req.user.role !== "admin" && !isSeller) {
      return next(new AppError("Not authorized to update this order", 403));
    }

    const allowedNext = ALLOWED_STATUS_TRANSITIONS[order.status] || [];
    if (!allowedNext.includes(status)) {
      return next(
        new AppError(
          `Cannot transition order from "${order.status}" to "${status}"`,
          400
        )
      );
    }

    if (status === "cancelled" && order.status !== "cancelled") {
      for (const item of order.items) {
        await Product.findByIdAndUpdate(item.product, {
          $inc: { stock: item.quantity },
        });
      }
      order.paymentStatus = "SIMULATED_REFUNDED";
    }

    order.status = status;
    await order.save();

    appEvents.emit("order-status-updated", {
      orderId: order._id,
      customerId: order.customer,
      status: order.status,
      paymentStatus: order.paymentStatus,
    });

    res.status(200).json({
      success: true,
      message: "Order status updated",
      data: order,
    });
  } catch (err) {
    next(err);
  }
};

const cancelOrder = async (req, res, next) => {
  try {
    const order = await Order.findById(req.params.id);
    if (!order) {
      return next(new AppError("Order not found", 404));
    }

    const isOwner = order.customer.toString() === req.user._id.toString();
    if (!isOwner && req.user.role !== "admin") {
      return next(new AppError("You cannot cancel another user's order", 403));
    }

    if (!["pending", "confirmed"].includes(order.status)) {
      return next(
        new AppError(`Order cannot be cancelled once "${order.status}"`, 400)
      );
    }

    for (const item of order.items) {
      await Product.findByIdAndUpdate(item.product, {
        $inc: { stock: item.quantity },
      });
    }

    order.status = "cancelled";
    order.paymentStatus = "SIMULATED_REFUNDED";
    await order.save();

    appEvents.emit("order-status-updated", {
      orderId: order._id,
      customerId: order.customer,
      status: order.status,
      paymentStatus: order.paymentStatus,
    });

    res.status(200).json({
      success: true,
      message: "Order cancelled and stock restored",
      data: order,
    });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  placeOrder,
  getOrders,
  getOrderById,
  updateOrderStatus,
  cancelOrder,
};
