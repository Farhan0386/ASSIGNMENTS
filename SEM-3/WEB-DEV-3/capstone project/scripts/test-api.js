const BASE_URL = process.env.API_URL || "http://localhost:5000/api";

const request = async (path, options = {}) => {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
};

const runTests = async () => {
  const health = await request("/health");
  console.log("1. Health check:", health.status, health.data.success);

  const badLogin = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: "not-an-email", password: "" }),
  });
  console.log("2. Validation failure (400):", badLogin.status);

  const unauthOrders = await request("/orders");
  console.log("3. Missing token (401):", unauthOrders.status);

  const customerLogin = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email: "customer@store.test",
      password: "Password123",
    }),
  });
  console.log("4. Customer login (200):", customerLogin.status);
  const customerToken = customerLogin.data.data?.accessToken;

  const forbiddenReport = await request("/reports/sales-summary", {
    headers: { Authorization: `Bearer ${customerToken}` },
  });
  console.log("5. Forbidden role on report (403):", forbiddenReport.status);

  const productsRes = await request("/products");
  console.log("6. List products (200):", productsRes.status, "count:", productsRes.data.data?.length);

  const firstProduct = productsRes.data.data?.[0];
  if (firstProduct && customerToken) {
    const addCart = await request("/cart/items", {
      method: "POST",
      headers: { Authorization: `Bearer ${customerToken}` },
      body: JSON.stringify({ productId: firstProduct._id, quantity: 1 }),
    });
    console.log("7. Add item to cart (200):", addCart.status);

    const checkout = await request("/orders", {
      method: "POST",
      headers: { Authorization: `Bearer ${customerToken}` },
      body: JSON.stringify({ shippingAddress: "123 Campus Road, Room 12" }),
    });
    console.log("8. Place order (201):", checkout.status, "orderId:", checkout.data.data?._id);
  }

  const missingItem = await request("/products/000000000000000000000000");
  console.log("9. Non-existent product (404):", missingItem.status);
};

runTests().catch((err) => {
  console.error("Test script failed:", err.message);
  process.exit(1);
});
