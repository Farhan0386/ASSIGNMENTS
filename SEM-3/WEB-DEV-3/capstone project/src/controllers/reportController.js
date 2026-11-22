const Order = require("../models/Order");
const Product = require("../models/Product");

const getSalesSummary = async (req, res, next) => {
  try {
    const matchStage = {
      status: { $ne: "cancelled" },
    };

    if (req.query.startDate || req.query.endDate) {
      matchStage.createdAt = {};
      if (req.query.startDate) {
        matchStage.createdAt.$gte = new Date(req.query.startDate);
      }
      if (req.query.endDate) {
        matchStage.createdAt.$lte = new Date(req.query.endDate);
      }
    }

    const pipeline = [
      { $match: matchStage },
      { $unwind: "$items" },
    ];

    if (req.user.role === "seller") {
      pipeline.push({
        $match: { "items.seller": req.user._id },
      });
    }

    pipeline.push(
      {
        $group: {
          _id: "$items.product",
          productName: { $first: "$items.name" },
          sellerId: { $first: "$items.seller" },
          totalUnitsSold: { $sum: "$items.quantity" },
          totalRevenue: {
            $sum: { $multiply: ["$items.priceAtPurchase", "$items.quantity"] },
          },
          orderCount: { $sum: 1 },
        },
      },
      { $sort: { totalRevenue: -1 } },
      {
        $project: {
          _id: 0,
          productId: "$_id",
          productName: 1,
          sellerId: 1,
          totalUnitsSold: 1,
          totalRevenue: { $round: ["$totalRevenue", 2] },
          orderCount: 1,
        },
      }
    );

    const summary = await Order.aggregate(pipeline);

    res.status(200).json({
      success: true,
      data: summary,
    });
  } catch (err) {
    next(err);
  }
};

const getLowStockReport = async (req, res, next) => {
  try {
    const threshold = Math.max(parseInt(req.query.threshold, 10) || 5, 0);

    const matchStage = {
      stock: { $lte: threshold },
    };

    if (req.user.role === "seller") {
      matchStage.seller = req.user._id;
    }

    const report = await Product.aggregate([
      { $match: matchStage },
      {
        $lookup: {
          from: "categories",
          localField: "category",
          foreignField: "_id",
          as: "categoryInfo",
        },
      },
      {
        $lookup: {
          from: "users",
          localField: "seller",
          foreignField: "_id",
          as: "sellerInfo",
        },
      },
      { $unwind: { path: "$categoryInfo", preserveNullAndEmptyArrays: true } },
      { $unwind: { path: "$sellerInfo", preserveNullAndEmptyArrays: true } },
      { $sort: { stock: 1, name: 1 } },
      {
        $project: {
          _id: 0,
          productId: "$_id",
          name: 1,
          price: 1,
          stock: 1,
          category: "$categoryInfo.name",
          sellerName: "$sellerInfo.name",
          sellerEmail: "$sellerInfo.email",
        },
      },
    ]);

    res.status(200).json({
      success: true,
      threshold,
      data: report,
    });
  } catch (err) {
    next(err);
  }
};

module.exports = {
  getSalesSummary,
  getLowStockReport,
};
