const express = require("express");
const { getSalesSummary, getLowStockReport } = require("../controllers/reportController");
const { protect } = require("../middlewares/authMiddleware");
const { authorize } = require("../middlewares/roleMiddleware");

const router = express.Router();

router.use(protect, authorize("seller", "admin"));

router.get("/sales-summary", getSalesSummary);
router.get("/low-stock", getLowStockReport);

module.exports = router;
