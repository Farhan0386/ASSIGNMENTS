const express = require("express");
const {
  placeOrder,
  getOrders,
  getOrderById,
  updateOrderStatus,
  cancelOrder,
} = require("../controllers/orderController");
const { protect } = require("../middlewares/authMiddleware");
const { authorize } = require("../middlewares/roleMiddleware");

const router = express.Router();

router.use(protect);

router.post("/", authorize("customer"), placeOrder);
router.get("/", getOrders);
router.get("/:id", getOrderById);
router.patch("/:id/status", authorize("seller", "admin"), updateOrderStatus);
router.post("/:id/cancel", cancelOrder);

module.exports = router;
