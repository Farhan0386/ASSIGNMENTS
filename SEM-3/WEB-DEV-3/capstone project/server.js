require("dotenv").config();
const http = require("http");
const jwt = require("jsonwebtoken");
const { Server } = require("socket.io");
const connectDB = require("./src/config/db");
const app = require("./src/app");
const appEvents = require("./src/events/appEvents");

const PORT = process.env.PORT || 5000;

const startServer = async () => {
  await connectDB();

  const server = http.createServer(app);
  const io = new Server(server, {
    cors: { origin: "*" },
  });

  io.use((socket, next) => {
    try {
      const token =
        socket.handshake.auth?.token ||
        socket.handshake.headers?.authorization?.split(" ")[1];
      if (!token) {
        return next(new Error("Authentication token required for Socket.IO"));
      }
      const decoded = jwt.verify(token, process.env.JWT_ACCESS_SECRET);
      socket.user = { id: decoded.id, role: decoded.role };
      next();
    } catch (err) {
      next(new Error("Invalid or expired Socket.IO token"));
    }
  });

  io.on("connection", (socket) => {
    const { id, role } = socket.user;
    socket.join(`user:${id}`);
    socket.join(`role:${role}`);
    console.log(`Socket connected: user=${id}, role=${role}`);

    socket.on("disconnect", () => {
      console.log(`Socket disconnected: user=${id}`);
    });
  });

  appEvents.on("order-placed", (payload) => {
    const sellerIds = [...new Set(payload.items.map((i) => i.seller.toString()))];
    sellerIds.forEach((sellerId) => {
      io.to(`user:${sellerId}`).emit("new-order", payload);
    });
    io.to("role:admin").emit("new-order", payload);
  });

  appEvents.on("stock-low", (payload) => {
    io.to(`user:${payload.sellerId.toString()}`).emit("low-stock-alert", payload);
    io.to("role:admin").emit("low-stock-alert", payload);
  });

  appEvents.on("order-status-updated", (payload) => {
    io.to(`user:${payload.customerId.toString()}`).emit("order-status", payload);
  });

  server.listen(PORT, () => {
    console.log(`Server listening on http://localhost:${PORT}`);
  });
};

startServer();
