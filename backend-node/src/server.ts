import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import recipeRoutes from "./routes/recipeRoutes.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "backend-node" });
});

app.use("/api/recipes", recipeRoutes);

app.listen(PORT, () => {
  console.log(`Node backend running on http://localhost:${PORT}`);
});