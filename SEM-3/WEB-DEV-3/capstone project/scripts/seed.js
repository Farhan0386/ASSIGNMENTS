require("dotenv").config();
const mongoose = require("mongoose");
const connectDB = require("../src/config/db");
const User = require("../src/models/User");
const Category = require("../src/models/Category");
const Product = require("../src/models/Product");

const seed = async () => {
  await connectDB();

  await Promise.all([
    User.deleteMany({}),
    Category.deleteMany({}),
    Product.deleteMany({}),
  ]);

  const [admin, seller, customer] = await User.create([
    {
      name: "Admin User",
      email: "admin@store.test",
      password: "Password123",
      role: "admin",
    },
    {
      name: "Seller One",
      email: "seller@store.test",
      password: "Password123",
      role: "seller",
    },
    {
      name: "Customer One",
      email: "customer@store.test",
      password: "Password123",
      role: "customer",
    },
  ]);

  const [electronics, books] = await Category.create([
    { name: "Electronics", description: "Gadgets and accessories" },
    { name: "Books", description: "Technical and academic books" },
  ]);

  await Product.create([
    {
      name: "Mechanical Keyboard",
      description: "Compact tactile keyboard",
      price: 3499,
      stock: 8,
      category: electronics._id,
      seller: seller._id,
    },
    {
      name: "USB-C Hub",
      description: "Multi-port adapter",
      price: 1299,
      stock: 3,
      category: electronics._id,
      seller: seller._id,
    },
    {
      name: "System Design Handbook",
      description: "Backend architecture guide",
      price: 899,
      stock: 15,
      category: books._id,
      seller: seller._id,
    },
  ]);

  console.log("Seed completed:");
  console.log({
    admin: admin.email,
    seller: seller.email,
    customer: customer.email,
    categories: [electronics.name, books.name],
  });

  await mongoose.disconnect();
};

seed().catch((err) => {
  console.error("Seed error:", err);
  process.exit(1);
});
